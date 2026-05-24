import tempfile
import unittest
from pathlib import Path

from app.tickers import Ticker, list_tickers, upsert_ticker


class TickerTest(unittest.TestCase):
    def test_upsert_and_list_ticker(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "eodwin.sqlite"

            upsert_ticker(
                Ticker(
                    symbol="abb.st",
                    name="ABB Ltd",
                    market="Sweden",
                    exchange_code="ST",
                    currency="SEK",
                ),
                database_path,
            )

            tickers = list_tickers(database_path)
            self.assertEqual(len(tickers), 1)
            self.assertEqual(tickers[0]["symbol"], "ABB.ST")
            self.assertEqual(tickers[0]["name"], "ABB Ltd")

    def test_upsert_updates_existing_ticker(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "eodwin.sqlite"

            upsert_ticker(Ticker(symbol="AAPL.US", name="Old"), database_path)
            upsert_ticker(Ticker(symbol="AAPL.US", name="Apple Inc", currency="USD"), database_path)

            tickers = list_tickers(database_path)
            self.assertEqual(len(tickers), 1)
            self.assertEqual(tickers[0]["name"], "Apple Inc")
            self.assertEqual(tickers[0]["currency"], "USD")


if __name__ == "__main__":
    unittest.main()
