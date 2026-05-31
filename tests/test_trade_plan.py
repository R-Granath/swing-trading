import unittest
from datetime import date, timedelta

from app.trade_plan import (
    PULLBACK_TRADE_PLAN_ID,
    build_pullback_trade_plan,
    summarize_pullback_trade_plans,
)


def score_row(**overrides) -> dict:
    row = {
        "symbol": "ABB.ST",
        "date": "2026-01-10",
        "strategy_id": "PULLBACK_SCORING_V1",
        "model_version": "PULLBACK_SCORING_V1",
        "heat": 82,
        "status": "HOT",
        "trend_score": 35,
        "pullback_score": 24,
        "resumption_score": 15,
        "risk_score": 8,
        "comment": "",
        "positive_drivers": [],
        "negative_drivers": [],
        "warnings": [],
    }
    row.update(overrides)
    return row


def market_rows(closes: list[float]) -> list[dict]:
    start = date(2026, 1, 1)
    rows = []
    for index, close in enumerate(closes):
        rows.append(
            {
                "date": (start + timedelta(days=index)).isoformat(),
                "open": close - 1,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "adjusted_close": close,
                "volume": 1000,
            }
        )
    return rows


def feature_rows(
    closes: list[float],
    *,
    pullback_depth: str = "-5.0000",
    distance_sma20: str = "0.4000",
    distance_sma50: str = "1.2000",
    close_position: str = "0.8000",
    volume: str = "1.2000",
    range_vs_atr: str = "1.0000",
    gap: str = "0.0000",
) -> list[dict]:
    start = date(2026, 1, 1)
    rows = []
    for index, _close in enumerate(closes):
        rows.append(
            {
                "date": (start + timedelta(days=index)).isoformat(),
                "pullback_depth_20d_pct": pullback_depth,
                "distance_to_sma20_atr": distance_sma20,
                "distance_to_sma50_atr": distance_sma50,
                "close_position_in_range": close_position,
                "is_green_candle": "true",
                "volume_vs_avg20": volume,
                "atr14_pct": "3.0000",
                "range_vs_atr14": range_vs_atr,
                "gap_pct": gap,
            }
        )
    return rows


class PullbackTradePlanTest(unittest.TestCase):
    def test_responding_near_sma20_can_be_ready_plan(self):
        closes = [100, 99, 98, 97, 96, 95, 96, 97, 98, 99]

        plan = build_pullback_trade_plan(score_row(), market_rows(closes), feature_rows(closes))

        self.assertEqual(plan.strategy, PULLBACK_TRADE_PLAN_ID)
        self.assertEqual(plan.setup_evolution, "RESPONDING")
        self.assertEqual(plan.setup_class, "SMA20_PULLBACK")
        self.assertEqual(plan.rr_hypothesis, "RR_GOOD")
        self.assertEqual(plan.plan_status, "READY_PLAN")

    def test_older_thin_green_day_does_not_block_later_volume_response(self):
        closes = [100, 99, 98, 97, 96, 95, 96, 95, 94, 97]
        markets = market_rows(closes)
        markets[7]["open"] = 96
        markets[7]["close"] = 95
        markets[8]["open"] = 95
        markets[8]["close"] = 94
        markets[9]["open"] = 95
        markets[9]["close"] = 97
        features = feature_rows(closes)
        features[6]["volume_vs_avg20"] = "0.7000"
        features[7]["volume_vs_avg20"] = "1.0000"
        features[8]["volume_vs_avg20"] = "1.0000"
        features[9]["volume_vs_avg20"] = "1.6000"

        plan = build_pullback_trade_plan(score_row(), markets, features)

        self.assertEqual(plan.setup_evolution, "RESPONDING")
        self.assertEqual(plan.rr_hypothesis, "RR_GOOD")
        self.assertEqual(plan.plan_status, "READY_PLAN")
        self.assertNotIn("thin_response", plan.warnings)

    def test_current_thin_response_blocks_ready_plan(self):
        closes = [100, 99, 98, 97, 96, 95, 96, 97, 98, 99]

        plan = build_pullback_trade_plan(
            score_row(),
            market_rows(closes),
            feature_rows(closes, volume="0.7000"),
        )

        self.assertEqual(plan.setup_evolution, "RESPONDING")
        self.assertEqual(plan.plan_status, "WATCH_PLAN")
        self.assertIn("thin_response", plan.warnings)

    def test_stabilizing_survives_as_watch_plan(self):
        closes = [100, 99, 98, 97, 96, 95.5, 95.6, 95.7, 95.8, 95.9]
        features = feature_rows(closes, close_position="0.5000", volume="1.0000")

        plan = build_pullback_trade_plan(score_row(heat=70, status="CANDIDATE"), market_rows(closes), features)

        self.assertEqual(plan.setup_evolution, "STABILIZING")
        self.assertEqual(plan.plan_status, "WATCH_PLAN")
        self.assertEqual(plan.rr_hypothesis, "RR_MEDIOCRE")

    def test_failed_structure_becomes_invalid_plan(self):
        closes = [100, 99, 98, 97, 96, 95, 94, 93, 92, 91]
        features = feature_rows(
            closes,
            pullback_depth="-16.0000",
            distance_sma20="-2.0000",
            distance_sma50="-1.5000",
            close_position="0.2000",
            range_vs_atr="1.7000",
        )

        plan = build_pullback_trade_plan(score_row(), market_rows(closes), features)

        self.assertEqual(plan.setup_evolution, "FAILED")
        self.assertEqual(plan.rr_hypothesis, "RR_BAD")
        self.assertEqual(plan.plan_status, "INVALID_PLAN")
        self.assertIn("failed_local_structure", plan.warnings)

    def test_extended_from_pullback_zone_becomes_late_plan_not_no_plan(self):
        closes = [100, 99, 98, 97, 96, 97, 98, 99, 100, 101]
        features = feature_rows(
            closes,
            pullback_depth="-0.5000",
            distance_sma20="2.2000",
            distance_sma50="3.0000",
        )

        plan = build_pullback_trade_plan(score_row(), market_rows(closes), features)

        self.assertEqual(plan.setup_evolution, "EXTENDED")
        self.assertEqual(plan.setup_class, "MOMENTUM_HANDOFF")
        self.assertEqual(plan.plan_status, "LATE_PLAN")
        self.assertIn("extended_from_pullback_zone", plan.warnings)

    def test_no_score_returns_no_plan_without_changing_scoring(self):
        closes = [100, 99, 98, 97, 96, 95, 96, 97, 98, 99]

        plan = build_pullback_trade_plan(
            score_row(heat=None, status="NO_SCORE"),
            market_rows(closes),
            feature_rows(closes),
        )

        self.assertEqual(plan.plan_status, "NO_PLAN")
        self.assertEqual(plan.source_status, "NO_SCORE")
        self.assertIn("insufficient_trade_plan_data", plan.warnings)

    def test_summary_counts_filter_effect(self):
        summary = summarize_pullback_trade_plans(
            "2026-01-10",
            [
                {
                    "setup_evolution": "RESPONDING",
                    "plan_status": "READY_PLAN",
                    "rr_hypothesis": "RR_GOOD",
                    "warnings": "",
                },
                {
                    "setup_evolution": "STABILIZING",
                    "plan_status": "WATCH_PLAN",
                    "rr_hypothesis": "RR_MEDIOCRE",
                    "warnings": "volume_missing_for_evolution, thin_response",
                },
            ],
        )

        self.assertEqual(summary.total_pullback_candidates, 2)
        self.assertEqual(summary.count_by_setup_evolution["RESPONDING"], 1)
        self.assertEqual(summary.count_by_plan_status["WATCH_PLAN"], 1)
        self.assertEqual(summary.count_by_rr_hypothesis["RR_GOOD"], 1)
        self.assertEqual(summary.count_by_warning["thin_response"], 1)


if __name__ == "__main__":
    unittest.main()
