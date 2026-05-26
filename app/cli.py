from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from app.config import get_settings
from app.eodhd_client import fetch_eod
from app.indicators import DEFAULT_SMA_WINDOWS, calculate_indicators
from app.market_data import (
    calculate_and_store_indicators,
    load_db_prices,
    load_indicator_values,
    register_default_indicators,
    sync_csv_prices_to_db,
)
from app.price_store import PRICE_COLUMNS, earliest_price_date, latest_price_date, load_prices, save_prices
from app.tickers import Ticker, init_db, list_tickers, upsert_ticker


DEFAULT_HISTORY_DAYS = 365
BACKFILL_TOLERANCE_DAYS = 7


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Eodwin local data tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Create the local SQLite database")

    add_ticker = subparsers.add_parser("add-ticker", help="Add or update a ticker in the universe")
    add_ticker.add_argument("symbol", help="EODHD symbol, for example ABB.ST or AAPL.US")
    add_ticker.add_argument("--name")
    add_ticker.add_argument("--market")
    add_ticker.add_argument("--exchange-code")
    add_ticker.add_argument("--currency")

    subparsers.add_parser("list-tickers", help="List active tickers")

    fetch = subparsers.add_parser("fetch", help="Fetch and store EOD prices for one ticker")
    fetch.add_argument("symbol", help="EODHD symbol, for example ABB.ST or AAPL.US")
    fetch.add_argument("--from-date", help="Start date in YYYY-MM-DD format")

    fetch_all = subparsers.add_parser("fetch-all", help="Fetch and store EOD prices for all active tickers")
    fetch_all.add_argument("--from-date", help="Start date in YYYY-MM-DD format")

    show_prices = subparsers.add_parser("show-prices", help="Show stored EOD prices for one ticker")
    show_prices.add_argument("symbol", help="EODHD symbol, for example ABB.ST or AAPL.US")
    show_prices.add_argument("--rows", type=int, default=10, help="Number of latest rows to show")

    show_db_prices = subparsers.add_parser("show-db-prices", help="Show SQLite EOD prices for one ticker")
    show_db_prices.add_argument("symbol", help="EODHD symbol, for example ABB.ST or AAPL.US")
    show_db_prices.add_argument("--rows", type=int, default=10, help="Number of latest rows to show")

    show_indicators = subparsers.add_parser("show-indicators", help="Show calculated indicators for one ticker")
    show_indicators.add_argument("symbol", help="EODHD symbol, for example ABB.ST or AAPL.US")
    show_indicators.add_argument("--rows", type=int, default=10, help="Number of latest rows to show")

    sync_prices = subparsers.add_parser("sync-prices-db", help="Sync CSV prices into SQLite")
    sync_prices.add_argument("symbol", nargs="?", help="Optional ticker. If omitted, sync all active tickers.")

    calculate_indicators_command = subparsers.add_parser(
        "calculate-indicators",
        help="Calculate and store indicator values in SQLite",
    )
    calculate_indicators_command.add_argument(
        "symbol",
        nargs="?",
        help="Optional ticker. If omitted, calculate for all active tickers.",
    )

    show_stored_indicators = subparsers.add_parser(
        "show-stored-indicators",
        help="Show stored SQLite indicator values for one ticker",
    )
    show_stored_indicators.add_argument("symbol", help="EODHD symbol, for example ABB.ST or AAPL.US")
    show_stored_indicators.add_argument("--rows", type=int, default=10, help="Number of latest rows to show")

    daily_update = subparsers.add_parser(
        "daily-update",
        help="Fetch prices, sync them to SQLite, and calculate indicators for active tickers",
    )
    daily_update.add_argument("--from-date", help="Optional start date in YYYY-MM-DD format")

    return parser.parse_args()


def resolve_from_date(symbol: str, requested_from_date: str | None, eod_dir) -> date:
    if requested_from_date:
        return date.fromisoformat(requested_from_date)

    history_start_date = date.today() - timedelta(days=DEFAULT_HISTORY_DAYS)
    earliest_date = earliest_price_date(symbol, eod_dir)
    backfill_deadline = history_start_date + timedelta(days=BACKFILL_TOLERANCE_DAYS)
    if not earliest_date or earliest_date > backfill_deadline:
        return history_start_date

    latest_date = latest_price_date(symbol, eod_dir)
    if latest_date:
        next_date = latest_date + timedelta(days=1)
        return min(next_date, date.today())
    return history_start_date


def main() -> int:
    args = parse_args()
    settings = get_settings()

    if args.command == "init-db":
        init_db(settings.database_path)
        print(f"Initialized {settings.database_path}")
        return 0

    if args.command == "add-ticker":
        upsert_ticker(
            Ticker(
                symbol=args.symbol,
                name=args.name,
                market=args.market,
                exchange_code=args.exchange_code,
                currency=args.currency,
            ),
            settings.database_path,
        )
        print(f"Saved ticker {args.symbol.upper()}")
        return 0

    if args.command == "list-tickers":
        for row in list_tickers(settings.database_path):
            print(
                "\t".join(
                    [
                        row["symbol"],
                        row["name"] or "",
                        row["market"] or "",
                        row["currency"] or "",
                    ]
                )
            )
        return 0

    if args.command == "fetch":
        if not settings.eodhd_api_key:
            print("Missing EODHD_API_KEY. Add it to .env in the project root.", file=sys.stderr)
            return 1
        from_date = resolve_from_date(args.symbol, args.from_date, settings.eod_dir)
        rows = fetch_eod(args.symbol, settings.eodhd_api_key, from_date)
        path = save_prices(args.symbol, rows, settings.eod_dir)
        print(f"Fetched {len(rows)} rows from {from_date.isoformat()}. Updated {path}")
        return 0

    if args.command == "fetch-all":
        if not settings.eodhd_api_key:
            print("Missing EODHD_API_KEY. Add it to .env in the project root.", file=sys.stderr)
            return 1
        tickers = list_tickers(settings.database_path)
        if not tickers:
            print("No active tickers found.")
            return 0
        failures = 0
        for ticker in tickers:
            symbol = ticker["symbol"]
            try:
                from_date = resolve_from_date(symbol, args.from_date, settings.eod_dir)
                rows = fetch_eod(symbol, settings.eodhd_api_key, from_date)
                path = save_prices(symbol, rows, settings.eod_dir)
                print(f"{symbol}: fetched {len(rows)} rows from {from_date.isoformat()}. Updated {path}")
            except Exception as exc:
                failures += 1
                print(f"{symbol}: fetch failed: {exc}", file=sys.stderr)
        return 1 if failures else 0

    if args.command == "daily-update":
        if not settings.eodhd_api_key:
            print("Missing EODHD_API_KEY. Add it to .env in the project root.", file=sys.stderr)
            return 1
        tickers = list_tickers(settings.database_path)
        if not tickers:
            print("No active tickers found.")
            return 0

        register_default_indicators(settings.database_path)
        failures = 0
        total_fetched_rows = 0
        total_synced_rows = 0
        total_indicator_values = 0
        for ticker in tickers:
            symbol = ticker["symbol"]
            try:
                from_date = resolve_from_date(symbol, args.from_date, settings.eod_dir)
                fetched_rows = fetch_eod(symbol, settings.eodhd_api_key, from_date)
                save_prices(symbol, fetched_rows, settings.eod_dir)
                synced_rows = sync_csv_prices_to_db(symbol, settings.eod_dir, settings.database_path)
                indicator_values = calculate_and_store_indicators(symbol, settings.database_path)
                total_fetched_rows += len(fetched_rows)
                total_synced_rows += synced_rows
                total_indicator_values += indicator_values
                print(
                    f"{symbol}: fetched {len(fetched_rows)} rows from {from_date.isoformat()}, "
                    f"synced {synced_rows} prices, stored {indicator_values} indicators"
                )
            except Exception as exc:
                failures += 1
                print(f"{symbol}: daily update failed: {exc}", file=sys.stderr)

        print(
            f"Daily update complete: fetched {total_fetched_rows} rows, "
            f"synced {total_synced_rows} prices, stored {total_indicator_values} indicators, "
            f"failures {failures}"
        )
        return 1 if failures else 0

    if args.command == "show-prices":
        rows = load_prices(args.symbol, settings.eod_dir)
        if not rows:
            print(f"No stored prices found for {args.symbol.upper()}. Run fetch first.")
            return 0

        visible_columns = PRICE_COLUMNS[:7]
        selected_rows = rows[-args.rows :]
        print("\t".join(visible_columns))
        for row in selected_rows:
            print("\t".join(row.get(column, "") for column in visible_columns))
        return 0

    if args.command == "show-db-prices":
        rows = load_db_prices(args.symbol, settings.database_path)
        if not rows:
            print(f"No SQLite prices found for {args.symbol.upper()}. Run sync-prices-db first.")
            return 0

        visible_columns = ["date", "open", "high", "low", "close", "adjusted_close", "volume"]
        selected_rows = rows[-args.rows :]
        print("\t".join(visible_columns))
        for row in selected_rows:
            print("\t".join(_format_optional_value(row.get(column)) for column in visible_columns))
        return 0

    if args.command == "show-indicators":
        rows = load_prices(args.symbol, settings.eod_dir)
        if not rows:
            print(f"No stored prices found for {args.symbol.upper()}. Run fetch first.")
            return 0

        indicator_rows = calculate_indicators(rows)
        visible_columns = ["date"] + [f"sma{window}" for window in DEFAULT_SMA_WINDOWS]
        selected_rows = indicator_rows[-args.rows :]
        print("\t".join(visible_columns))
        for row in selected_rows:
            print("\t".join(row.get(column, "") for column in visible_columns))
        return 0

    if args.command == "sync-prices-db":
        symbols = [args.symbol.upper()] if args.symbol else [ticker["symbol"] for ticker in list_tickers(settings.database_path)]
        for symbol in symbols:
            synced_rows = sync_csv_prices_to_db(symbol, settings.eod_dir, settings.database_path)
            print(f"{symbol}: synced {synced_rows} price rows into SQLite")
        return 0

    if args.command == "calculate-indicators":
        register_default_indicators(settings.database_path)
        symbols = [args.symbol.upper()] if args.symbol else [ticker["symbol"] for ticker in list_tickers(settings.database_path)]
        for symbol in symbols:
            stored_values = calculate_and_store_indicators(symbol, settings.database_path)
            print(f"{symbol}: stored {stored_values} indicator values in SQLite")
        return 0

    if args.command == "show-stored-indicators":
        indicator_rows = load_indicator_values(args.symbol, settings.database_path, args.rows)
        if not indicator_rows:
            print(f"No stored indicators found for {args.symbol.upper()}. Run calculate-indicators first.")
            return 0

        visible_columns = ["date"] + [f"sma{window}" for window in DEFAULT_SMA_WINDOWS]
        print("\t".join(visible_columns))
        for row in indicator_rows:
            print("\t".join(row.get(column, "") for column in visible_columns))
        return 0

    return 1


def _format_optional_value(value) -> str:
    if value is None:
        return ""
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
