import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.market_data import (
    calculate_and_store_indicators,
    load_db_prices,
    load_indicator_values,
    register_default_indicators,
    sync_csv_prices_to_db,
)
from app.price_store import PRICE_COLUMNS, price_path


def write_price_csv(symbol: str, eod_dir: Path, rows: list[dict]) -> None:
    eod_dir.mkdir(parents=True, exist_ok=True)
    with price_path(symbol, eod_dir).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PRICE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def price_row(day: int, close: int) -> dict:
    return {
        "date": f"2026-01-{day:02d}",
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "adjusted_close": close,
        "volume": 1000,
        "source": "eodhd",
        "fetched_at": "2026-01-31T00:00:00+00:00",
    }


class MarketDataTest(unittest.TestCase):
    def test_sync_csv_prices_to_db(self):
        with tempfile.TemporaryDirectory() as directory:
            base_path = Path(directory)
            database_path = base_path / "eodwin.sqlite"
            eod_dir = base_path / "eod"
            write_price_csv("ABB.ST", eod_dir, [price_row(1, 10), price_row(2, 11)])

            synced_rows = sync_csv_prices_to_db("ABB.ST", eod_dir, database_path)

            self.assertEqual(synced_rows, 2)
            prices = load_db_prices("ABB.ST", database_path)
            self.assertEqual([row["date"] for row in prices], ["2026-01-01", "2026-01-02"])
            self.assertEqual(prices[-1]["adjusted_close"], 11)

    def test_register_default_indicators(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "eodwin.sqlite"

            register_default_indicators(database_path)

            connection = sqlite3.connect(database_path)
            try:
                names = [
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM indicator_definitions ORDER BY name"
                    )
                ]
            finally:
                connection.close()
            self.assertEqual(names, ["atr14", "atr14_pct", "sma20", "sma200", "sma50"])

    def test_calculate_and_store_indicators(self):
        with tempfile.TemporaryDirectory() as directory:
            base_path = Path(directory)
            database_path = base_path / "eodwin.sqlite"
            eod_dir = base_path / "eod"
            write_price_csv("ABB.ST", eod_dir, [price_row(day, day) for day in range(1, 31)])
            sync_csv_prices_to_db("ABB.ST", eod_dir, database_path)

            stored_values = calculate_and_store_indicators("ABB.ST", database_path)

            self.assertEqual(stored_values, 43)
            indicator_rows = load_indicator_values("ABB.ST", database_path, rows=1)
            self.assertEqual(
                indicator_rows,
                [{"date": "2026-01-30", "atr14": "1.0000", "atr14_pct": "3.3333", "sma20": "20.5000"}],
            )


if __name__ == "__main__":
    unittest.main()
