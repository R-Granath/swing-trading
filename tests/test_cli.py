import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from app.cli import BACKFILL_TOLERANCE_DAYS, DEFAULT_HISTORY_DAYS, resolve_from_date
from app.price_store import save_prices


class CliTest(unittest.TestCase):
    def test_resolve_from_date_uses_requested_date(self):
        with tempfile.TemporaryDirectory() as directory:
            eod_dir = Path(directory)

            self.assertEqual(
                resolve_from_date("ABB.ST", "2026-01-15", eod_dir),
                date(2026, 1, 15),
            )

    def test_resolve_from_date_continues_after_latest_stored_date_when_history_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            eod_dir = Path(directory)
            save_prices(
                "ABB.ST",
                [
                    {
                        "date": "2025-05-01",
                        "open": 8,
                        "high": 9,
                        "low": 7,
                        "close": 8,
                        "adjusted_close": 8,
                        "volume": 800,
                    },
                    {
                        "date": "2026-01-15",
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

            self.assertEqual(resolve_from_date("ABB.ST", None, eod_dir), date(2026, 1, 16))

    def test_resolve_from_date_backfills_one_year_when_no_data_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            eod_dir = Path(directory)

            self.assertEqual(
                resolve_from_date("ABB.ST", None, eod_dir),
                date.today() - timedelta(days=DEFAULT_HISTORY_DAYS),
            )

    def test_resolve_from_date_backfills_one_year_when_history_is_too_short(self):
        with tempfile.TemporaryDirectory() as directory:
            eod_dir = Path(directory)
            save_prices(
                "ABB.ST",
                [
                    {
                        "date": date.today().isoformat(),
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

            self.assertEqual(
                resolve_from_date("ABB.ST", None, eod_dir),
                date.today() - timedelta(days=DEFAULT_HISTORY_DAYS),
            )

    def test_resolve_from_date_accepts_small_gap_after_history_start(self):
        with tempfile.TemporaryDirectory() as directory:
            eod_dir = Path(directory)
            history_start_date = date.today() - timedelta(days=DEFAULT_HISTORY_DAYS)
            latest_stored_date = date.today() - timedelta(days=1)
            save_prices(
                "ABB.ST",
                [
                    {
                        "date": (history_start_date + timedelta(days=1)).isoformat(),
                        "open": 8,
                        "high": 9,
                        "low": 7,
                        "close": 8,
                        "adjusted_close": 8,
                        "volume": 800,
                    },
                    {
                        "date": latest_stored_date.isoformat(),
                        "open": 9,
                        "high": 10,
                        "low": 8,
                        "close": 10,
                        "adjusted_close": 10,
                        "volume": 900,
                    },
                ],
                eod_dir,
            )

            self.assertEqual(resolve_from_date("ABB.ST", None, eod_dir), date.today())

    def test_resolve_from_date_backfills_when_gap_exceeds_tolerance(self):
        with tempfile.TemporaryDirectory() as directory:
            eod_dir = Path(directory)
            history_start_date = date.today() - timedelta(days=DEFAULT_HISTORY_DAYS)
            save_prices(
                "ABB.ST",
                [
                    {
                        "date": (history_start_date + timedelta(days=BACKFILL_TOLERANCE_DAYS + 1)).isoformat(),
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

            self.assertEqual(resolve_from_date("ABB.ST", None, eod_dir), history_start_date)

    def test_resolve_from_date_does_not_return_future_date(self):
        with tempfile.TemporaryDirectory() as directory:
            eod_dir = Path(directory)
            save_prices(
                "ABB.ST",
                [
                    {
                        "date": (date.today() - timedelta(days=DEFAULT_HISTORY_DAYS + 1)).isoformat(),
                        "open": 8,
                        "high": 9,
                        "low": 7,
                        "close": 8,
                        "adjusted_close": 8,
                        "volume": 800,
                    },
                    {
                        "date": date.today().isoformat(),
                        "open": 9,
                        "high": 10,
                        "low": 8,
                        "close": 10,
                        "adjusted_close": 10,
                        "volume": 900,
                    },
                ],
                eod_dir,
            )

            self.assertEqual(resolve_from_date("ABB.ST", None, eod_dir), date.today())


if __name__ == "__main__":
    unittest.main()
