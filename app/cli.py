from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from app.config import get_settings
from app.eodhd_client import fetch_eod
from app.features import PULLBACK_MVP_FEATURE_COLUMNS, calculate_pullback_mvp_features
from app.indicators import DEFAULT_ATR_WINDOW, DEFAULT_SMA_WINDOWS, calculate_indicators
from app.market_data import (
    calculate_and_store_indicators,
    load_db_prices,
    load_indicator_values,
    load_strategy_scores,
    load_top_strategy_scores,
    register_default_indicators,
    save_strategy_scores,
    sync_csv_prices_to_db,
)
from app.price_store import PRICE_COLUMNS, earliest_price_date, latest_price_date, load_prices, save_prices
from app.review import (
    PULLBACK_TRADE_PLAN_REVIEW_COLUMNS,
    build_pullback_trade_plan_review_rows,
    filter_limit_review_rows,
)
from app.scoring import PULLBACK_SCORE_COLUMNS, PULLBACK_STRATEGY_ID, score_pullback_feature_rows
from app.tickers import Ticker, init_db, list_tickers, upsert_ticker
from app.trade_plan import (
    PULLBACK_TRADE_PLAN_COLUMNS,
    build_pullback_trade_plan,
    build_pullback_trade_plans,
    summarize_pullback_trade_plans,
)


DEFAULT_HISTORY_DAYS = 365
BACKFILL_TOLERANCE_DAYS = 7
DEFAULT_INDICATOR_COLUMNS = (
    [f"sma{window}" for window in DEFAULT_SMA_WINDOWS]
    + [f"atr{DEFAULT_ATR_WINDOW}", f"atr{DEFAULT_ATR_WINDOW}_pct"]
)


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

    inspect_market = subparsers.add_parser(
        "inspect-market",
        help="Show SQLite price rows together with stored indicators for one ticker",
    )
    inspect_market.add_argument("symbol", help="EODHD symbol, for example ABB.ST or AAPL.US")
    inspect_market.add_argument("--rows", type=int, default=10, help="Number of latest rows to show")

    inspect_features = subparsers.add_parser(
        "inspect-features",
        help="Show Pullback v1 MVP features for one ticker",
    )
    inspect_features.add_argument("symbol", help="EODHD symbol, for example ABB.ST or AAPL.US")
    inspect_features.add_argument("--rows", type=int, default=10, help="Number of latest rows to show")

    inspect_pullback_score = subparsers.add_parser(
        "inspect-pullback-score",
        help="Show Pullback v1 scoring for one ticker",
    )
    inspect_pullback_score.add_argument("symbol", help="EODHD symbol, for example ABB.ST or AAPL.US")
    inspect_pullback_score.add_argument("--rows", type=int, default=10, help="Number of latest rows to show")

    inspect_pullback_trade_plan = subparsers.add_parser(
        "inspect-pullback-trade-plan",
        help="Show Pullback trade-plan v1 rows for one ticker",
    )
    inspect_pullback_trade_plan.add_argument("symbol", help="EODHD symbol, for example ABB.ST or AAPL.US")
    inspect_pullback_trade_plan.add_argument("--rows", type=int, default=10, help="Number of latest rows to show")

    score_strategies = subparsers.add_parser(
        "score-strategies",
        help="Calculate and store strategy scores in SQLite",
    )
    score_strategies.add_argument(
        "symbol",
        nargs="?",
        help="Optional ticker. If omitted, score all active tickers.",
    )

    show_strategy_scores = subparsers.add_parser(
        "show-strategy-scores",
        help="Show stored strategy scores for one date",
    )
    show_strategy_scores.add_argument("--date", help="Score date in YYYY-MM-DD format. Defaults to latest stored date.")

    show_top_setups = subparsers.add_parser(
        "show-top-setups",
        help="Show highest stored strategy scores for one date",
    )
    show_top_setups.add_argument("--date", help="Score date in YYYY-MM-DD format. Defaults to latest stored date.")
    show_top_setups.add_argument("--limit", type=int, default=20, help="Maximum number of rows to show")

    summarize_pullback_trade_plans_command = subparsers.add_parser(
        "summarize-pullback-trade-plans",
        help="Summarize Pullback trade-plan v1 filter effect for one stored score date",
    )
    summarize_pullback_trade_plans_command.add_argument(
        "--date",
        help="Score date in YYYY-MM-DD format. Defaults to latest stored date.",
    )

    review_pullback_trade_plans = subparsers.add_parser(
        "review-pullback-trade-plans",
        help="Review historical Pullback scores, features, and trade-plan classifications",
    )
    review_pullback_trade_plans.add_argument("--from-date", help="Start date in YYYY-MM-DD format")
    review_pullback_trade_plans.add_argument("--to-date", help="End date in YYYY-MM-DD format")
    review_pullback_trade_plans.add_argument("--symbol", help="Optional ticker. Defaults to all active tickers.")
    review_pullback_trade_plans.add_argument("--min-heat", type=int, help="Minimum Pullback heat")
    review_pullback_trade_plans.add_argument("--plan-status", help="Filter by plan status, for example WATCH_PLAN")
    review_pullback_trade_plans.add_argument("--setup-class", help="Filter by setup class, for example SHALLOW_PULLBACK")
    review_pullback_trade_plans.add_argument("--setup-evolution", help="Filter by setup evolution, for example RESPONDING")
    review_pullback_trade_plans.add_argument("--limit", type=int, default=50, help="Maximum number of rows to show")

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
        visible_columns = ["date"] + DEFAULT_INDICATOR_COLUMNS
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

        visible_columns = ["date"] + DEFAULT_INDICATOR_COLUMNS
        print("\t".join(visible_columns))
        for row in indicator_rows:
            print("\t".join(row.get(column, "") for column in visible_columns))
        return 0

    if args.command == "inspect-market":
        price_rows = load_db_prices(args.symbol, settings.database_path)
        if not price_rows:
            print(f"No SQLite prices found for {args.symbol.upper()}. Run sync-prices-db first.")
            return 0

        selected_price_rows = price_rows[-args.rows :]
        indicator_rows = {
            row["date"]: row
            for row in load_indicator_values(args.symbol, settings.database_path, args.rows)
        }
        visible_columns = [
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            *DEFAULT_INDICATOR_COLUMNS,
        ]
        print("\t".join(visible_columns))
        for price_row in selected_price_rows:
            indicator_row = indicator_rows.get(price_row["date"], {})
            output_row = {
                **{column: _format_optional_value(price_row.get(column)) for column in visible_columns},
                **{column: indicator_row.get(column, "") for column in DEFAULT_INDICATOR_COLUMNS},
            }
            print("\t".join(output_row.get(column, "") for column in visible_columns))
        return 0

    if args.command == "inspect-features":
        market_rows = _load_market_rows_with_indicators(args.symbol, settings.database_path)
        if not market_rows:
            print(f"No SQLite prices found for {args.symbol.upper()}. Run sync-prices-db first.")
            return 0

        feature_rows = calculate_pullback_mvp_features(market_rows)
        visible_columns = ["date"] + PULLBACK_MVP_FEATURE_COLUMNS
        print("\t".join(visible_columns))
        for row in feature_rows[-args.rows :]:
            print("\t".join(row.get(column, "") for column in visible_columns))
        return 0

    if args.command == "inspect-pullback-score":
        market_rows = _load_market_rows_with_indicators(args.symbol, settings.database_path)
        if not market_rows:
            print(f"No SQLite prices found for {args.symbol.upper()}. Run sync-prices-db first.")
            return 0

        feature_rows = calculate_pullback_mvp_features(market_rows)
        score_rows = [score.as_row() for score in score_pullback_feature_rows(feature_rows)]
        print("\t".join(PULLBACK_SCORE_COLUMNS))
        for row in score_rows[-args.rows :]:
            print("\t".join(row.get(column, "") for column in PULLBACK_SCORE_COLUMNS))
        return 0

    if args.command == "inspect-pullback-trade-plan":
        market_rows = _load_market_rows_with_indicators(args.symbol, settings.database_path)
        if not market_rows:
            print(f"No SQLite prices found for {args.symbol.upper()}. Run sync-prices-db first.")
            return 0

        feature_rows = calculate_pullback_mvp_features(market_rows)
        score_rows = [_strategy_score_storage_row(args.symbol, score) for score in score_pullback_feature_rows(feature_rows)]
        plan_rows = [
            build_pullback_trade_plan(score_row, market_rows, feature_rows).as_row()
            for score_row in score_rows
        ]
        print("\t".join(PULLBACK_TRADE_PLAN_COLUMNS))
        for row in plan_rows[-args.rows :]:
            print("\t".join(row.get(column, "") for column in PULLBACK_TRADE_PLAN_COLUMNS))
        return 0

    if args.command == "score-strategies":
        symbols = [args.symbol.upper()] if args.symbol else [ticker["symbol"] for ticker in list_tickers(settings.database_path)]
        total_saved = 0
        for symbol in symbols:
            market_rows = _load_market_rows_with_indicators(symbol, settings.database_path)
            if not market_rows:
                print(f"{symbol}: no SQLite prices found. Run sync-prices-db first.")
                continue

            feature_rows = calculate_pullback_mvp_features(market_rows)
            scores = score_pullback_feature_rows(feature_rows)
            saved = save_strategy_scores(
                [_strategy_score_storage_row(symbol, score) for score in scores],
                settings.database_path,
            )
            total_saved += saved
            latest_score = scores[-1]
            heat = "" if latest_score.heat is None else str(latest_score.heat)
            print(f"{symbol}: stored {saved} {PULLBACK_STRATEGY_ID} scores, latest {latest_score.date} {heat} {latest_score.status}")
        print(f"Strategy scoring complete: stored {total_saved} scores")
        return 0

    if args.command == "show-strategy-scores":
        rows = load_strategy_scores(settings.database_path, score_date=args.date)
        if not rows:
            print("No stored strategy scores found. Run score-strategies first.")
            return 0
        _print_strategy_score_rows(rows)
        return 0

    if args.command == "show-top-setups":
        rows = load_top_strategy_scores(settings.database_path, score_date=args.date, limit=args.limit)
        if not rows:
            print("No stored scored setups found. Run score-strategies first.")
            return 0
        _print_strategy_score_rows(rows)
        return 0

    if args.command == "summarize-pullback-trade-plans":
        score_rows = load_strategy_scores(settings.database_path, score_date=args.date)
        if not score_rows:
            print("No stored strategy scores found. Run score-strategies first.")
            return 0

        pullback_score_rows = [row for row in score_rows if row["strategy_id"] == PULLBACK_STRATEGY_ID]
        market_rows_by_symbol = {}
        feature_rows_by_symbol = {}
        for score_row in pullback_score_rows:
            symbol = score_row["symbol"]
            if symbol in market_rows_by_symbol:
                continue
            market_rows = _load_market_rows_with_indicators(symbol, settings.database_path)
            market_rows_by_symbol[symbol] = market_rows
            feature_rows_by_symbol[symbol] = calculate_pullback_mvp_features(market_rows) if market_rows else []

        plan_rows = build_pullback_trade_plans(pullback_score_rows, market_rows_by_symbol, feature_rows_by_symbol)
        summary_date = args.date or score_rows[0]["date"]
        _print_pullback_trade_plan_summary(summarize_pullback_trade_plans(summary_date, plan_rows))
        return 0

    if args.command == "review-pullback-trade-plans":
        symbols = [args.symbol.upper()] if args.symbol else [ticker["symbol"] for ticker in list_tickers(settings.database_path)]
        review_rows = []
        for symbol in symbols:
            market_rows = _load_market_rows_with_indicators(symbol, settings.database_path)
            if not market_rows:
                continue
            review_rows.extend(
                build_pullback_trade_plan_review_rows(
                    symbol,
                    market_rows,
                    from_date=args.from_date,
                    to_date=args.to_date,
                    min_heat=args.min_heat,
                    plan_status=args.plan_status,
                    setup_class=args.setup_class,
                    setup_evolution=args.setup_evolution,
                )
            )

        _print_review_rows(filter_limit_review_rows(review_rows, args.limit))
        return 0

    return 1


def _format_optional_value(value) -> str:
    if value is None:
        return ""
    return str(value)


def _load_market_rows_with_indicators(symbol: str, database_path) -> list[dict]:
    price_rows = load_db_prices(symbol, database_path)
    if not price_rows:
        return []

    indicator_rows = {
        row["date"]: row
        for row in load_indicator_values(symbol, database_path, rows=len(price_rows))
    }
    return [
        {
            **price_row,
            **{
                column: indicator_rows.get(price_row["date"], {}).get(column, "")
                for column in DEFAULT_INDICATOR_COLUMNS
            },
        }
        for price_row in price_rows
    ]


def _strategy_score_storage_row(symbol: str, score) -> dict:
    return {
        "symbol": symbol,
        "date": score.date,
        "strategy_id": score.strategy,
        "model_version": score.strategy,
        "heat": score.heat,
        "status": score.status,
        "trend_score": score.trend_score,
        "pullback_score": score.pullback_score,
        "resumption_score": score.resumption_score,
        "risk_score": score.risk_score,
        "comment": score.comment,
        "positive_drivers": list(score.positive_drivers),
        "negative_drivers": list(score.negative_drivers),
        "warnings": list(score.warnings),
    }


def _print_strategy_score_rows(rows: list[dict]) -> None:
    visible_columns = ["date", "symbol", "strategy_id", "heat", "status", "comment", "warnings"]
    print("\t".join(visible_columns))
    for row in rows:
        output_row = {
            **row,
            "heat": "" if row["heat"] is None else str(row["heat"]),
            "warnings": ", ".join(row["warnings"]),
        }
        print("\t".join(str(output_row.get(column, "")) for column in visible_columns))


def _print_pullback_trade_plan_summary(summary) -> None:
    print(f"date\t{summary.date}")
    print(f"total_pullback_candidates\t{summary.total_pullback_candidates}")
    _print_count_block("count_by_setup_evolution", summary.count_by_setup_evolution)
    _print_count_block("count_by_plan_status", summary.count_by_plan_status)
    _print_count_block("count_by_rr_hypothesis", summary.count_by_rr_hypothesis)
    _print_count_block("count_by_warning", summary.count_by_warning)


def _print_count_block(title: str, counts: dict[str, int]) -> None:
    print(title)
    if not counts:
        print("(none)\t0")
        return
    for key, value in counts.items():
        print(f"{key}\t{value}")


def _print_review_rows(rows: list[dict]) -> None:
    print("\t".join(PULLBACK_TRADE_PLAN_REVIEW_COLUMNS))
    for row in rows:
        print("\t".join(row.get(column, "") for column in PULLBACK_TRADE_PLAN_REVIEW_COLUMNS))


if __name__ == "__main__":
    raise SystemExit(main())
