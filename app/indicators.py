from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal, InvalidOperation


DEFAULT_SMA_WINDOWS = (20, 50, 200)


def calculate_sma(rows: list[dict], window: int, price_column: str = "adjusted_close") -> list[dict]:
    if window < 1:
        raise ValueError("window must be at least 1")

    sorted_rows = sorted(rows, key=lambda row: row["date"])
    values: list[Decimal] = []
    results: list[dict] = []

    for row in sorted_rows:
        price = _decimal_value(row.get(price_column))
        values.append(price)
        if len(values) < window:
            value = None
        else:
            value = sum(values[-window:]) / Decimal(window)
        results.append({"date": row["date"], f"sma{window}": _format_decimal(value)})

    return results


def calculate_indicators(rows: list[dict], sma_windows: Iterable[int] = DEFAULT_SMA_WINDOWS) -> list[dict]:
    sorted_rows = sorted(rows, key=lambda row: row["date"])
    results = [{"date": row["date"]} for row in sorted_rows]

    for window in sma_windows:
        sma_rows = calculate_sma(sorted_rows, window)
        for result, sma_row in zip(results, sma_rows, strict=True):
            result[f"sma{window}"] = sma_row[f"sma{window}"]

    return results


def _decimal_value(value) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"Invalid price value: {value}") from exc


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return ""
    return f"{value.quantize(Decimal('0.0001'))}"
