from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.config import DEFAULT_DATABASE_PATH
from app.indicators import DEFAULT_SMA_WINDOWS, calculate_indicators
from app.price_store import load_prices
from app.tickers import init_db


PRICE_COLUMNS = ("open", "high", "low", "close", "adjusted_close", "volume")


def init_market_data_db(database_path: Path = DEFAULT_DATABASE_PATH) -> None:
    init_db(database_path)
    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS prices (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                adjusted_close REAL,
                volume INTEGER,
                source TEXT NOT NULL DEFAULT 'eodhd',
                fetched_at TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (symbol, date)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS indicator_definitions (
                name TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                parameters TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS indicator_values (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                indicator_name TEXT NOT NULL,
                value REAL,
                calculated_at TEXT NOT NULL,
                PRIMARY KEY (symbol, date, indicator_name),
                FOREIGN KEY (indicator_name) REFERENCES indicator_definitions(name)
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def register_default_indicators(database_path: Path = DEFAULT_DATABASE_PATH) -> None:
    init_market_data_db(database_path)
    for window in DEFAULT_SMA_WINDOWS:
        upsert_indicator_definition(
            name=f"sma{window}",
            indicator_type="sma",
            parameters={"window": window, "price_column": "adjusted_close"},
            database_path=database_path,
        )


def upsert_indicator_definition(
    name: str,
    indicator_type: str,
    parameters: dict,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> None:
    now = datetime.now(UTC).isoformat()
    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            INSERT INTO indicator_definitions (name, type, parameters, active, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                type = excluded.type,
                parameters = excluded.parameters,
                active = excluded.active,
                updated_at = excluded.updated_at
            """,
            (name.lower(), indicator_type, json.dumps(parameters, sort_keys=True), now, now),
        )
        connection.commit()
    finally:
        connection.close()


def sync_csv_prices_to_db(
    symbol: str,
    eod_dir: Path,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> int:
    init_market_data_db(database_path)
    rows = load_prices(symbol, eod_dir)
    now = datetime.now(UTC).isoformat()
    connection = sqlite3.connect(database_path)
    try:
        connection.executemany(
            """
            INSERT INTO prices (
                symbol, date, open, high, low, close, adjusted_close, volume, source, fetched_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, date) DO UPDATE SET
                open = excluded.open,
                high = excluded.high,
                low = excluded.low,
                close = excluded.close,
                adjusted_close = excluded.adjusted_close,
                volume = excluded.volume,
                source = excluded.source,
                fetched_at = excluded.fetched_at,
                updated_at = excluded.updated_at
            """,
            [
                (
                    symbol.upper(),
                    row["date"],
                    _optional_float(row.get("open")),
                    _optional_float(row.get("high")),
                    _optional_float(row.get("low")),
                    _optional_float(row.get("close")),
                    _optional_float(row.get("adjusted_close")),
                    _optional_int(row.get("volume")),
                    row.get("source") or "eodhd",
                    row.get("fetched_at"),
                    now,
                )
                for row in rows
            ],
        )
        connection.commit()
        return len(rows)
    finally:
        connection.close()


def load_db_prices(symbol: str, database_path: Path = DEFAULT_DATABASE_PATH) -> list[dict]:
    init_market_data_db(database_path)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT date, open, high, low, close, adjusted_close, volume, source, fetched_at
            FROM prices
            WHERE symbol = ?
            ORDER BY date
            """,
            (symbol.upper(),),
        )
        return [dict(row) for row in rows]
    finally:
        connection.close()


def calculate_and_store_indicators(
    symbol: str,
    database_path: Path = DEFAULT_DATABASE_PATH,
    sma_windows: Iterable[int] = DEFAULT_SMA_WINDOWS,
) -> int:
    register_default_indicators(database_path)
    price_rows = load_db_prices(symbol, database_path)
    indicator_rows = calculate_indicators(price_rows, sma_windows=sma_windows)
    calculated_at = datetime.now(UTC).isoformat()
    values = []
    for row in indicator_rows:
        for name, value in row.items():
            if name == "date" or value == "":
                continue
            values.append((symbol.upper(), row["date"], name, float(Decimal(value)), calculated_at))

    connection = sqlite3.connect(database_path)
    try:
        connection.executemany(
            """
            INSERT INTO indicator_values (symbol, date, indicator_name, value, calculated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(symbol, date, indicator_name) DO UPDATE SET
                value = excluded.value,
                calculated_at = excluded.calculated_at
            """,
            values,
        )
        connection.commit()
        return len(values)
    finally:
        connection.close()


def load_indicator_values(
    symbol: str,
    database_path: Path = DEFAULT_DATABASE_PATH,
    rows: int = 10,
) -> list[dict]:
    init_market_data_db(database_path)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        dates = [
            row["date"]
            for row in connection.execute(
                """
                SELECT DISTINCT date
                FROM indicator_values
                WHERE symbol = ?
                ORDER BY date DESC
                LIMIT ?
                """,
                (symbol.upper(), rows),
            )
        ]
        if not dates:
            return []
        placeholders = ",".join("?" for _ in dates)
        value_rows = connection.execute(
            f"""
            SELECT date, indicator_name, value
            FROM indicator_values
            WHERE symbol = ? AND date IN ({placeholders})
            ORDER BY date, indicator_name
            """,
            (symbol.upper(), *dates),
        )
        by_date = {date: {"date": date} for date in sorted(dates)}
        for row in value_rows:
            by_date[row["date"]][row["indicator_name"]] = f"{row['value']:.4f}"
        return list(by_date.values())
    finally:
        connection.close()


def _optional_float(value) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _optional_int(value) -> int | None:
    if value in (None, ""):
        return None
    return int(value)
