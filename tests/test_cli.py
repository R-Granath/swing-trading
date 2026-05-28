import io
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from app.cli import BACKFILL_TOLERANCE_DAYS, DEFAULT_HISTORY_DAYS, main, resolve_from_date
from app.config import Settings
from app.market_data import sync_csv_prices_to_db
from app.market_data import calculate_and_store_indicators
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

    def test_show_db_prices_prints_latest_sqlite_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            base_path = Path(directory)
            eod_dir = base_path / "eod"
            database_path = base_path / "eodwin.sqlite"
            save_prices(
                "ABB.ST",
                [
                    {
                        "date": "2026-01-01",
                        "open": 8,
                        "high": 9,
                        "low": 7,
                        "close": 8,
                        "adjusted_close": 8,
                        "volume": 800,
                    },
                    {
                        "date": "2026-01-02",
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
            sync_csv_prices_to_db("ABB.ST", eod_dir, database_path)

            output = io.StringIO()
            with (
                patch("app.cli.get_settings", return_value=Settings(database_path=database_path, eod_dir=eod_dir)),
                patch("sys.argv", ["app.cli", "show-db-prices", "ABB.ST", "--rows", "1"]),
                redirect_stdout(output),
            ):
                exit_code = main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                output.getvalue().splitlines(),
                [
                    "date\topen\thigh\tlow\tclose\tadjusted_close\tvolume",
                    "2026-01-02\t9.0\t10.0\t8.0\t10.0\t10.0\t900",
                ],
            )

    def test_show_db_prices_handles_missing_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            base_path = Path(directory)
            eod_dir = base_path / "eod"
            database_path = base_path / "eodwin.sqlite"

            output = io.StringIO()
            with (
                patch("app.cli.get_settings", return_value=Settings(database_path=database_path, eod_dir=eod_dir)),
                patch("sys.argv", ["app.cli", "show-db-prices", "ABB.ST"]),
                redirect_stdout(output),
            ):
                exit_code = main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(output.getvalue(), "No SQLite prices found for ABB.ST. Run sync-prices-db first.\n")

    def test_show_stored_indicators_prints_atr_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            base_path = Path(directory)
            eod_dir = base_path / "eod"
            database_path = base_path / "eodwin.sqlite"
            save_prices(
                "ABB.ST",
                [
                    {
                        "date": f"2026-01-{day:02d}",
                        "open": day,
                        "high": day,
                        "low": day,
                        "close": day,
                        "adjusted_close": day,
                        "volume": 1000,
                    }
                    for day in range(1, 31)
                ],
                eod_dir,
            )
            sync_csv_prices_to_db("ABB.ST", eod_dir, database_path)
            calculate_and_store_indicators("ABB.ST", database_path)

            output = io.StringIO()
            with (
                patch("app.cli.get_settings", return_value=Settings(database_path=database_path, eod_dir=eod_dir)),
                patch("sys.argv", ["app.cli", "show-stored-indicators", "ABB.ST", "--rows", "1"]),
                redirect_stdout(output),
            ):
                exit_code = main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                output.getvalue().splitlines(),
                [
                    "date\tsma20\tsma50\tsma200\tatr14\tatr14_pct",
                    "2026-01-30\t20.5000\t\t\t1.0000\t3.3333",
                ],
            )

    def test_inspect_market_prints_price_and_indicator_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            base_path = Path(directory)
            eod_dir = base_path / "eod"
            database_path = base_path / "eodwin.sqlite"
            save_prices(
                "ABB.ST",
                [
                    {
                        "date": f"2026-01-{day:02d}",
                        "open": day,
                        "high": day,
                        "low": day,
                        "close": day,
                        "adjusted_close": day,
                        "volume": 1000,
                    }
                    for day in range(1, 31)
                ],
                eod_dir,
            )
            sync_csv_prices_to_db("ABB.ST", eod_dir, database_path)
            calculate_and_store_indicators("ABB.ST", database_path)

            output = io.StringIO()
            with (
                patch("app.cli.get_settings", return_value=Settings(database_path=database_path, eod_dir=eod_dir)),
                patch("sys.argv", ["app.cli", "inspect-market", "ABB.ST", "--rows", "1"]),
                redirect_stdout(output),
            ):
                exit_code = main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                output.getvalue().splitlines(),
                [
                    "date\topen\thigh\tlow\tclose\tvolume\tsma20\tsma50\tsma200\tatr14\tatr14_pct",
                    "2026-01-30\t30.0\t30.0\t30.0\t30.0\t1000\t20.5000\t\t\t1.0000\t3.3333",
                ],
            )

    def test_inspect_features_prints_pullback_mvp_features(self):
        with tempfile.TemporaryDirectory() as directory:
            base_path = Path(directory)
            eod_dir = base_path / "eod"
            database_path = base_path / "eodwin.sqlite"
            save_prices(
                "ABB.ST",
                [
                    {
                        "date": f"2026-01-{day:02d}",
                        "open": day,
                        "high": day,
                        "low": day,
                        "close": day,
                        "adjusted_close": day,
                        "volume": 1000,
                    }
                    for day in range(1, 31)
                ],
                eod_dir,
            )
            sync_csv_prices_to_db("ABB.ST", eod_dir, database_path)
            calculate_and_store_indicators("ABB.ST", database_path)

            output = io.StringIO()
            with (
                patch("app.cli.get_settings", return_value=Settings(database_path=database_path, eod_dir=eod_dir)),
                patch("sys.argv", ["app.cli", "inspect-features", "ABB.ST", "--rows", "1"]),
                redirect_stdout(output),
            ):
                exit_code = main()

            self.assertEqual(exit_code, 0)
            lines = output.getvalue().splitlines()
            self.assertEqual(exit_code, 0)
            self.assertTrue(lines[0].startswith("date\tclose_vs_sma50_pct"))
            self.assertIn("distance_to_sma20_atr", lines[0])
            self.assertIn("atr14_pct", lines[0])
            self.assertTrue(lines[1].startswith("2026-01-30\t"))


if __name__ == "__main__":
    unittest.main()
