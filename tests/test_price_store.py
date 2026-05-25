import tempfile
import unittest
from pathlib import Path

from app.price_store import earliest_price_date, latest_price_date, load_prices, price_path, save_prices


class PriceStoreTest(unittest.TestCase):
    def test_save_and_load_prices(self):
        with tempfile.TemporaryDirectory() as directory:
            eod_dir = Path(directory)
            rows = [
                {
                    "date": "2026-01-02",
                    "open": 10,
                    "high": 12,
                    "low": 9,
                    "close": 11,
                    "adjusted_close": 11,
                    "volume": 1000,
                },
                {
                    "date": "2026-01-01",
                    "open": 9,
                    "high": 10,
                    "low": 8,
                    "close": 10,
                    "adjusted_close": 10,
                    "volume": 900,
                },
            ]

            path = save_prices("abb.st", rows, eod_dir)

            self.assertEqual(path, price_path("ABB.ST", eod_dir))
            loaded = load_prices("ABB.ST", eod_dir)
            self.assertEqual([row["date"] for row in loaded], ["2026-01-01", "2026-01-02"])
            self.assertEqual(loaded[0]["source"], "eodhd")

    def test_save_prices_merges_with_existing_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            eod_dir = Path(directory)
            save_prices(
                "ABB.ST",
                [
                    {
                        "date": "2026-01-01",
                        "open": 9,
                        "high": 10,
                        "low": 8,
                        "close": 10,
                        "adjusted_close": 10,
                        "volume": 900,
                    }
                ],
                eod_dir,
            )

            save_prices(
                "ABB.ST",
                [
                    {
                        "date": "2026-01-02",
                        "open": 10,
                        "high": 12,
                        "low": 9,
                        "close": 11,
                        "adjusted_close": 11,
                        "volume": 1000,
                    }
                ],
                eod_dir,
            )

            loaded = load_prices("ABB.ST", eod_dir)
            self.assertEqual([row["date"] for row in loaded], ["2026-01-01", "2026-01-02"])

    def test_price_date_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            eod_dir = Path(directory)
            save_prices(
                "ABB.ST",
                [
                    {
                        "date": "2026-01-01",
                        "open": 9,
                        "high": 10,
                        "low": 8,
                        "close": 10,
                        "adjusted_close": 10,
                        "volume": 900,
                    }
                ],
                eod_dir,
            )

            self.assertEqual(latest_price_date("ABB.ST", eod_dir).isoformat(), "2026-01-01")
            self.assertEqual(earliest_price_date("ABB.ST", eod_dir).isoformat(), "2026-01-01")


if __name__ == "__main__":
    unittest.main()
