import unittest

from app.indicators import calculate_atr, calculate_indicators, calculate_sma


def price_row(day: int, close: int) -> dict:
    return {
        "date": f"2026-01-{day:02d}",
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "adjusted_close": close,
    }


class IndicatorsTest(unittest.TestCase):
    def test_calculate_sma(self):
        rows = [price_row(day, day) for day in range(1, 6)]

        results = calculate_sma(rows, 3)

        self.assertEqual(
            results,
            [
                {"date": "2026-01-01", "sma3": ""},
                {"date": "2026-01-02", "sma3": ""},
                {"date": "2026-01-03", "sma3": "2.0000"},
                {"date": "2026-01-04", "sma3": "3.0000"},
                {"date": "2026-01-05", "sma3": "4.0000"},
            ],
        )

    def test_calculate_sma_sorts_rows_by_date(self):
        rows = [price_row(3, 3), price_row(1, 1), price_row(2, 2)]

        results = calculate_sma(rows, 2)

        self.assertEqual([row["date"] for row in results], ["2026-01-01", "2026-01-02", "2026-01-03"])
        self.assertEqual(results[-1]["sma2"], "2.5000")

    def test_calculate_indicators_returns_multiple_sma_windows(self):
        rows = [price_row(day, day) for day in range(1, 6)]

        results = calculate_indicators(rows, sma_windows=(2, 3), atr_window=2)

        self.assertEqual(
            results[-1],
            {
                "date": "2026-01-05",
                "sma2": "4.5000",
                "sma3": "4.0000",
                "atr2": "1.0000",
                "atr2_pct": "20.0000",
            },
        )

    def test_calculate_sma_rejects_invalid_window(self):
        with self.assertRaises(ValueError):
            calculate_sma([], 0)

    def test_calculate_atr(self):
        rows = [
            {
                "date": "2026-01-01",
                "high": "10",
                "low": "8",
                "close": "9",
            },
            {
                "date": "2026-01-02",
                "high": "12",
                "low": "9",
                "close": "11",
            },
            {
                "date": "2026-01-03",
                "high": "13",
                "low": "10",
                "close": "12",
            },
        ]

        results = calculate_atr(rows, 2)

        self.assertEqual(
            results,
            [
                {"date": "2026-01-01", "atr2": ""},
                {"date": "2026-01-02", "atr2": ""},
                {"date": "2026-01-03", "atr2": "3.0000"},
            ],
        )

    def test_calculate_atr_sorts_rows_by_date(self):
        rows = [price_row(3, 3), price_row(1, 1), price_row(2, 2)]

        results = calculate_atr(rows, 2)

        self.assertEqual([row["date"] for row in results], ["2026-01-01", "2026-01-02", "2026-01-03"])
        self.assertEqual(results[-1]["atr2"], "1.0000")

    def test_calculate_atr_rejects_invalid_window(self):
        with self.assertRaises(ValueError):
            calculate_atr([], 0)


if __name__ == "__main__":
    unittest.main()
