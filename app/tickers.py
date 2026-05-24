from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.config import DEFAULT_DATABASE_PATH


@dataclass(frozen=True)
class Ticker:
    symbol: str
    name: str | None = None
    market: str | None = None
    exchange_code: str | None = None
    currency: str | None = None
    source: str = "eodhd"
    active: bool = True


def connect(database_path: Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(database_path: Path = DEFAULT_DATABASE_PATH) -> None:
    connection = connect(database_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tickers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                name TEXT,
                market TEXT,
                exchange_code TEXT,
                currency TEXT,
                source TEXT NOT NULL DEFAULT 'eodhd',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def upsert_ticker(ticker: Ticker, database_path: Path = DEFAULT_DATABASE_PATH) -> None:
    init_db(database_path)
    now = datetime.now(UTC).isoformat()
    connection = connect(database_path)
    try:
        connection.execute(
            """
            INSERT INTO tickers (
                symbol, name, market, exchange_code, currency, source, active, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                name = excluded.name,
                market = excluded.market,
                exchange_code = excluded.exchange_code,
                currency = excluded.currency,
                source = excluded.source,
                active = excluded.active,
                updated_at = excluded.updated_at
            """,
            (
                ticker.symbol.upper(),
                ticker.name,
                ticker.market,
                ticker.exchange_code,
                ticker.currency,
                ticker.source,
                1 if ticker.active else 0,
                now,
                now,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def list_tickers(database_path: Path = DEFAULT_DATABASE_PATH, active_only: bool = True) -> list[sqlite3.Row]:
    init_db(database_path)
    query = "SELECT * FROM tickers"
    params: tuple[int, ...] = ()
    if active_only:
        query += " WHERE active = ?"
        params = (1,)
    query += " ORDER BY symbol"
    connection = connect(database_path)
    try:
        return list(connection.execute(query, params))
    finally:
        connection.close()
