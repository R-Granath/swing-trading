from __future__ import annotations

from app.features import calculate_pullback_mvp_features
from app.scoring import PULLBACK_STRATEGY_ID, score_pullback_feature_rows
from app.trade_plan import build_pullback_trade_plan


PULLBACK_TRADE_PLAN_REVIEW_COLUMNS = [
    "date",
    "symbol",
    "heat",
    "status",
    "trend_score",
    "pullback_score",
    "resumption_score",
    "risk_score",
    "plan_status",
    "setup_class",
    "setup_evolution",
    "rr_hypothesis",
    "score_comment",
    "plan_comment",
    "score_warnings",
    "plan_warnings",
    "pullback_depth_20d_pct",
    "distance_to_sma20_atr",
    "distance_to_sma50_atr",
    "close_position_in_range",
    "volume_vs_avg20",
    "range_vs_atr14",
    "gap_pct",
]


def build_pullback_trade_plan_review_rows(
    symbol: str,
    market_rows: list[dict],
    *,
    from_date: str | None = None,
    to_date: str | None = None,
    min_heat: int | None = None,
    plan_status: str | None = None,
    setup_class: str | None = None,
    setup_evolution: str | None = None,
) -> list[dict]:
    feature_rows = calculate_pullback_mvp_features(market_rows)
    score_rows = [
        _strategy_score_storage_row(symbol, score)
        for score in score_pullback_feature_rows(feature_rows)
    ]

    review_rows = []
    for score_row, feature_row in zip(score_rows, feature_rows):
        row_date = score_row["date"]
        if from_date and row_date < from_date:
            continue
        if to_date and row_date > to_date:
            continue
        if min_heat is not None and (score_row["heat"] is None or score_row["heat"] < min_heat):
            continue

        plan = build_pullback_trade_plan(score_row, market_rows, feature_rows)
        if plan_status and plan.plan_status != plan_status:
            continue
        if setup_class and plan.setup_class != setup_class:
            continue
        if setup_evolution and plan.setup_evolution != setup_evolution:
            continue

        review_rows.append(
            {
                "date": row_date,
                "symbol": symbol.upper(),
                "heat": "" if score_row["heat"] is None else str(score_row["heat"]),
                "status": score_row["status"],
                "trend_score": str(score_row["trend_score"]),
                "pullback_score": str(score_row["pullback_score"]),
                "resumption_score": str(score_row["resumption_score"]),
                "risk_score": str(score_row["risk_score"]),
                "plan_status": plan.plan_status,
                "setup_class": plan.setup_class,
                "setup_evolution": plan.setup_evolution,
                "rr_hypothesis": plan.rr_hypothesis,
                "score_comment": score_row["comment"],
                "plan_comment": plan.comment,
                "score_warnings": ", ".join(score_row["warnings"]),
                "plan_warnings": ", ".join(plan.warnings),
                "pullback_depth_20d_pct": feature_row.get("pullback_depth_20d_pct", ""),
                "distance_to_sma20_atr": feature_row.get("distance_to_sma20_atr", ""),
                "distance_to_sma50_atr": feature_row.get("distance_to_sma50_atr", ""),
                "close_position_in_range": feature_row.get("close_position_in_range", ""),
                "volume_vs_avg20": feature_row.get("volume_vs_avg20", ""),
                "range_vs_atr14": feature_row.get("range_vs_atr14", ""),
                "gap_pct": feature_row.get("gap_pct", ""),
            }
        )
    return review_rows


def filter_limit_review_rows(rows: list[dict], limit: int | None = None) -> list[dict]:
    sorted_rows = sorted(
        rows,
        key=lambda row: (row["date"], _heat_sort_value(row["heat"]), row["symbol"]),
        reverse=True,
    )
    if limit is None:
        return sorted_rows
    return sorted_rows[:limit]


def _strategy_score_storage_row(symbol: str, score) -> dict:
    return {
        "symbol": symbol.upper(),
        "date": score.date,
        "strategy_id": PULLBACK_STRATEGY_ID,
        "model_version": PULLBACK_STRATEGY_ID,
        "heat": score.heat,
        "status": score.status,
        "trend_score": score.trend_score,
        "pullback_score": score.pullback_score,
        "resumption_score": score.resumption_score,
        "risk_score": score.risk_score,
        "comment": score.comment,
        "positive_drivers": list(score.positive_drivers),
        "negative_drivers": list(score.negative_drivers),
        "warnings": list(score.warnings),
    }


def _heat_sort_value(value: str) -> int:
    if value == "":
        return -1
    return int(value)
