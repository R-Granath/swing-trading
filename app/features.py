from __future__ import annotations

from decimal import Decimal, InvalidOperation


PULLBACK_MVP_FEATURE_COLUMNS = [
    "close_vs_sma50_pct",
    "close_vs_sma200_pct",
    "sma50_vs_sma200_pct",
    "sma50_slope_10d",
    "return_60d_pct",
    "rolling_high_20d",
    "pullback_depth_20d_pct",
    "distance_to_sma20_atr",
    "distance_to_sma50_atr",
    "close_position_in_range",
    "is_green_candle",
    "volume_vs_avg20",
    "atr14_pct",
    "range_vs_atr14",
    "gap_pct",
]


def calculate_pullback_mvp_features(rows: list[dict]) -> list[dict]:
    sorted_rows = sorted(rows, key=lambda row: row["date"])
    results: list[dict] = []

    for index, row in enumerate(sorted_rows):
        features = {column: "" for column in PULLBACK_MVP_FEATURE_COLUMNS}
        features["date"] = row["date"]

        close = _optional_decimal(row.get("close"))
        open_price = _optional_decimal(row.get("open"))
        high = _optional_decimal(row.get("high"))
        low = _optional_decimal(row.get("low"))
        volume = _optional_decimal(row.get("volume"))
        sma20 = _optional_decimal(row.get("sma20"))
        sma50 = _optional_decimal(row.get("sma50"))
        sma200 = _optional_decimal(row.get("sma200"))
        atr14 = _optional_decimal(row.get("atr14"))
        atr14_pct = _optional_decimal(row.get("atr14_pct"))

        features["close_vs_sma50_pct"] = _format_decimal(_pct_distance(close, sma50))
        features["close_vs_sma200_pct"] = _format_decimal(_pct_distance(close, sma200))
        features["sma50_vs_sma200_pct"] = _format_decimal(_pct_distance(sma50, sma200))
        features["atr14_pct"] = _format_decimal(atr14_pct)

        if index >= 10:
            previous_sma50 = _optional_decimal(sorted_rows[index - 10].get("sma50"))
            features["sma50_slope_10d"] = _format_decimal(_pct_distance(sma50, previous_sma50))

        if index >= 60:
            close_60d_ago = _optional_decimal(sorted_rows[index - 60].get("close"))
            features["return_60d_pct"] = _format_decimal(_pct_distance(close, close_60d_ago))

        if index >= 19:
            highs = [_optional_decimal(item.get("high")) for item in sorted_rows[index - 19 : index + 1]]
            if all(value is not None for value in highs):
                rolling_high = max(value for value in highs if value is not None)
                features["rolling_high_20d"] = _format_decimal(rolling_high)
                features["pullback_depth_20d_pct"] = _format_decimal(_pct_distance(close, rolling_high))

        features["distance_to_sma20_atr"] = _format_decimal(_atr_distance(close, sma20, atr14))
        features["distance_to_sma50_atr"] = _format_decimal(_atr_distance(close, sma50, atr14))

        if close is not None and high is not None and low is not None and high > low:
            features["close_position_in_range"] = _format_decimal((close - low) / (high - low))
            features["range_vs_atr14"] = _format_decimal(_safe_divide(high - low, atr14))

        if close is not None and open_price is not None:
            features["is_green_candle"] = str(close > open_price).lower()

        if index >= 19 and volume is not None:
            volumes = [_optional_decimal(item.get("volume")) for item in sorted_rows[index - 19 : index + 1]]
            if all(value is not None for value in volumes):
                volume_avg20 = sum(value for value in volumes if value is not None) / Decimal(20)
                features["volume_vs_avg20"] = _format_decimal(_safe_divide(volume, volume_avg20))

        if index >= 1:
            previous_close = _optional_decimal(sorted_rows[index - 1].get("close"))
            features["gap_pct"] = _format_decimal(_pct_distance(open_price, previous_close))

        results.append(features)

    return results


def _pct_distance(value: Decimal | None, reference: Decimal | None) -> Decimal | None:
    if value is None or reference is None or reference <= 0:
        return None
    return (value - reference) / reference * Decimal(100)


def _atr_distance(value: Decimal | None, reference: Decimal | None, atr: Decimal | None) -> Decimal | None:
    if value is None or reference is None or atr is None or atr <= 0:
        return None
    return (value - reference) / atr


def _safe_divide(value: Decimal | None, reference: Decimal | None) -> Decimal | None:
    if value is None or reference is None or reference <= 0:
        return None
    return value / reference


def _optional_decimal(value) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"Invalid numeric value: {value}") from exc


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return ""
    return f"{value.quantize(Decimal('0.0001'))}"
