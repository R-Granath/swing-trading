import unittest

from app.features import PULLBACK_MVP_FEATURE_COLUMNS, calculate_pullback_mvp_features


def market_row(day: int) -> dict:
    return {
        "date": f"2026-03-{day:02d}",
        "open": 100 + day,
        "high": 102 + day,
        "low": 98 + day,
        "close": 101 + day,
        "volume": 1000 + day * 10,
        "sma20": 99 + day,
        "sma50": 95 + day,
        "sma200": 80 + day,
        "atr14": 4,
        "atr14_pct": 4,
    }


class FeaturesTest(unittest.TestCase):
    def test_calculate_pullback_mvp_features_returns_only_mvp_columns(self):
        rows = [market_row(day) for day in range(1, 62)]

        results = calculate_pullback_mvp_features(rows)

        self.assertEqual(sorted(results[-1].keys()), sorted(["date", *PULLBACK_MVP_FEATURE_COLUMNS]))

    def test_calculate_trend_features(self):
        rows = [market_row(day) for day in range(1, 62)]

        result = calculate_pullback_mvp_features(rows)[-1]

        self.assertEqual(result["close_vs_sma50_pct"], "3.8462")
        self.assertEqual(result["close_vs_sma200_pct"], "14.8936")
        self.assertEqual(result["sma50_vs_sma200_pct"], "10.6383")
        self.assertEqual(result["sma50_slope_10d"], "6.8493")
        self.assertEqual(result["return_60d_pct"], "58.8235")

    def test_calculate_pullback_location_features(self):
        rows = [market_row(day) for day in range(1, 62)]

        result = calculate_pullback_mvp_features(rows)[-1]

        self.assertEqual(result["rolling_high_20d"], "163.0000")
        self.assertEqual(result["pullback_depth_20d_pct"], "-0.6135")
        self.assertEqual(result["distance_to_sma20_atr"], "0.5000")
        self.assertEqual(result["distance_to_sma50_atr"], "1.5000")

    def test_calculate_resumption_features(self):
        rows = [market_row(day) for day in range(1, 62)]

        result = calculate_pullback_mvp_features(rows)[-1]

        self.assertEqual(result["close_position_in_range"], "0.7500")
        self.assertEqual(result["is_green_candle"], "true")
        self.assertEqual(result["volume_vs_avg20"], "1.0627")

    def test_calculate_risk_features(self):
        rows = [market_row(day) for day in range(1, 62)]

        result = calculate_pullback_mvp_features(rows)[-1]

        self.assertEqual(result["atr14_pct"], "4.0000")
        self.assertEqual(result["range_vs_atr14"], "1.0000")
        self.assertEqual(result["gap_pct"], "0.0000")

    def test_missing_lookback_features_are_blank(self):
        rows = [market_row(day) for day in range(1, 10)]

        result = calculate_pullback_mvp_features(rows)[-1]

        self.assertEqual(result["sma50_slope_10d"], "")
        self.assertEqual(result["return_60d_pct"], "")
        self.assertEqual(result["rolling_high_20d"], "")
        self.assertEqual(result["pullback_depth_20d_pct"], "")
        self.assertEqual(result["volume_vs_avg20"], "")


if __name__ == "__main__":
    unittest.main()
