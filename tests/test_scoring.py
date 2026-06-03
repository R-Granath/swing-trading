import unittest

from app.scoring import PULLBACK_STRATEGY_ID, score_pullback_features


def feature_row(**overrides) -> dict:
    row = {
        "date": "2026-05-28",
        "close_vs_sma50_pct": "2.0000",
        "close_vs_sma200_pct": "18.0000",
        "sma50_vs_sma200_pct": "10.0000",
        "sma50_slope_10d": "1.2000",
        "return_60d_pct": "20.0000",
        "rolling_high_20d": "100.0000",
        "pullback_depth_20d_pct": "-5.0000",
        "distance_to_sma20_atr": "0.3000",
        "distance_to_sma50_atr": "1.2000",
        "close_position_in_range": "0.8500",
        "is_green_candle": "true",
        "volume_vs_avg20": "1.4000",
        "atr14_pct": "3.0000",
        "range_vs_atr14": "1.0000",
        "gap_pct": "0.5000",
    }
    row.update(overrides)
    return row


class PullbackScoringTest(unittest.TestCase):
    def test_strong_trend_controlled_pullback_and_volume_response_scores_hot(self):
        score = score_pullback_features(feature_row())

        self.assertEqual(score.strategy, PULLBACK_STRATEGY_ID)
        self.assertEqual(score.heat, 98)
        self.assertEqual(score.status, "HOT")
        self.assertEqual(score.trend_score, 40)
        self.assertEqual(score.pullback_score, 30)
        self.assertIn("strong prior trend", score.positive_drivers)
        self.assertIn("controlled pullback from recent high", score.positive_drivers)
        self.assertIn("buyers returning on volume", score.positive_drivers)

    def test_strong_trend_without_actual_pullback_does_not_score_hot(self):
        score = score_pullback_features(
            feature_row(
                pullback_depth_20d_pct="-0.2000",
                distance_to_sma20_atr="3.0000",
                distance_to_sma50_atr="4.0000",
                close_vs_sma50_pct="8.0000",
            )
        )

        self.assertLess(score.heat, 80)
        self.assertEqual(score.status, "CANDIDATE")
        self.assertIn("no actual pullback", score.negative_drivers)

    def test_near_sma_without_actual_pullback_gets_low_pullback_block_score(self):
        score = score_pullback_features(
            feature_row(
                pullback_depth_20d_pct="-0.2000",
                distance_to_sma20_atr="0.2000",
                distance_to_sma50_atr="0.8000",
                close_vs_sma50_pct="2.0000",
            )
        )

        self.assertEqual(score.pullback_score, 5)
        self.assertIn("possible momentum handoff", score.negative_drivers)

    def test_location_scores_above_sma_better_than_clearly_below_sma(self):
        above_score = score_pullback_features(
            feature_row(
                distance_to_sma20_atr="0.4000",
                distance_to_sma50_atr="0.8000",
            )
        )
        below_score = score_pullback_features(
            feature_row(
                distance_to_sma20_atr="-0.8000",
                distance_to_sma50_atr="-0.8000",
            )
        )

        self.assertGreater(above_score.pullback_score, below_score.pullback_score)
        self.assertEqual(above_score.pullback_score, 30)
        self.assertEqual(below_score.pullback_score, 21)

    def test_sma50_location_scores_above_support_better_than_just_below(self):
        above_score = score_pullback_features(
            feature_row(
                distance_to_sma20_atr="2.5000",
                distance_to_sma50_atr="0.3000",
            )
        )
        below_score = score_pullback_features(
            feature_row(
                distance_to_sma20_atr="2.5000",
                distance_to_sma50_atr="-0.3000",
            )
        )

        self.assertEqual(above_score.pullback_score, 28)
        self.assertEqual(below_score.pullback_score, 22)

    def test_weak_trend_with_strong_candle_does_not_become_candidate(self):
        score = score_pullback_features(
            feature_row(
                close_vs_sma200_pct="-10.0000",
                sma50_vs_sma200_pct="-5.0000",
                sma50_slope_10d="-1.0000",
                return_60d_pct="-5.0000",
                close_vs_sma50_pct="-1.0000",
                volume_vs_avg20="1.6000",
            )
        )

        self.assertLess(score.heat, 65)
        self.assertEqual(score.status, "WATCH")
        self.assertIn("weak prior trend", score.negative_drivers)

    def test_missing_required_feature_returns_no_score(self):
        score = score_pullback_features(feature_row(sma50_slope_10d=""))

        self.assertIsNone(score.heat)
        self.assertEqual(score.status, "NO_SCORE")
        self.assertEqual(score.warnings, ("missing sma50_slope_10d",))
        self.assertIn("invalid data", score.negative_drivers)

    def test_missing_volume_keeps_score_but_marks_warning(self):
        score = score_pullback_features(feature_row(volume_vs_avg20=""))

        self.assertIsNotNone(score.heat)
        self.assertIn("volume_missing", score.warnings)
        self.assertIn("missing volume confirmation", score.negative_drivers)


if __name__ == "__main__":
    unittest.main()
