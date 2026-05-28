from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal, InvalidOperation


DEFAULT_SMA_WINDOWS = (20, 50, 200)
DEFAULT_ATR_WINDOW = 14


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


def calculate_atr(rows: list[dict], window: int = DEFAULT_ATR_WINDOW) -> list[dict]:
    if window < 1:
        raise ValueError("window must be at least 1")

    sorted_rows = sorted(rows, key=lambda row: row["date"])
    true_ranges: list[Decimal] = []
    results: list[dict] = []
    previous_close: Decimal | None = None

    for row in sorted_rows:
        high = _decimal_value(row.get("high"))
        low = _decimal_value(row.get("low"))
        close = _decimal_value(row.get("close"))

        if previous_close is None:
            value = None
        else:
            true_range = max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close),
            )
            true_ranges.append(true_range)
            if len(true_ranges) < window:
                value = None
            else:
                value = sum(true_ranges[-window:]) / Decimal(window)

        results.append({"date": row["date"], f"atr{window}": _format_decimal(value)})
        previous_close = close

    return results


def calculate_indicators(
    rows: list[dict],
    sma_windows: Iterable[int] = DEFAULT_SMA_WINDOWS,
    atr_window: int = DEFAULT_ATR_WINDOW,
) -> list[dict]:
    sorted_rows = sorted(rows, key=lambda row: row["date"])
    results = [{"date": row["date"]} for row in sorted_rows]

    for window in sma_windows:
        sma_rows = calculate_sma(sorted_rows, window)
        for result, sma_row in zip(results, sma_rows, strict=True):
            result[f"sma{window}"] = sma_row[f"sma{window}"]

    atr_rows = calculate_atr(sorted_rows, atr_window)
    for result, atr_row, source_row in zip(results, atr_rows, sorted_rows, strict=True):
        atr_name = f"atr{atr_window}"
        atr_value = atr_row[atr_name]
        result[atr_name] = atr_value
        if atr_value == "":
            result[f"{atr_name}_pct"] = ""
            continue
        close = _decimal_value(source_row.get("close"))
        if close <= 0:
            raise ValueError(f"Invalid close value for ATR pct: {close}")
        atr_pct = Decimal(atr_value) / close * Decimal(100)
        result[f"{atr_name}_pct"] = _format_decimal(atr_pct)

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
