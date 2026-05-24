from __future__ import annotations

import argparse
import sys
from datetime import date

from app.config import get_settings
from app.eodhd_client import fetch_eod
from app.price_store import PRICE_COLUMNS, load_prices, save_prices
from app.tickers import Ticker, init_db, list_tickers, upsert_ticker


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

    return parser.parse_args()


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
        from_date = date.fromisoformat(args.from_date) if args.from_date else None
        rows = fetch_eod(args.symbol, settings.eodhd_api_key, from_date)
        path = save_prices(args.symbol, rows, settings.eod_dir)
        print(f"Saved {len(rows)} rows to {path}")
        return 0

    if args.command == "fetch-all":
        if not settings.eodhd_api_key:
            print("Missing EODHD_API_KEY. Add it to .env in the project root.", file=sys.stderr)
            return 1
        from_date = date.fromisoformat(args.from_date) if args.from_date else None
        tickers = list_tickers(settings.database_path)
        if not tickers:
            print("No active tickers found.")
            return 0
        failures = 0
        for ticker in tickers:
            symbol = ticker["symbol"]
            try:
                rows = fetch_eod(symbol, settings.eodhd_api_key, from_date)
                path = save_prices(symbol, rows, settings.eod_dir)
                print(f"{symbol}: saved {len(rows)} rows to {path}")
            except Exception as exc:
                failures += 1
                print(f"{symbol}: fetch failed: {exc}", file=sys.stderr)
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

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
