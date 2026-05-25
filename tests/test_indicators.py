import unittest

from app.indicators import calculate_indicators, calculate_sma


def price_row(day: int, close: int) -> dict:
    return {
        "date": f"2026-01-{day:02d}",
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

        results = calculate_indicators(rows, sma_windows=(2, 3))

        self.assertEqual(results[-1], {"date": "2026-01-05", "sma2": "4.5000", "sma3": "4.0000"})

    def test_calculate_sma_rejects_invalid_window(self):
        with self.assertRaises(ValueError):
            calculate_sma([], 0)


if __name__ == "__main__":
    unittest.main()
