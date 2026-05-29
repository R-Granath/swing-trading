from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


PULLBACK_STRATEGY_ID = "PULLBACK_SCORING_V1"

PULLBACK_SCORE_COLUMNS = [
    "date",
    "strategy",
    "heat",
    "status",
    "trend_score",
    "pullback_score",
    "resumption_score",
    "risk_score",
    "comment",
    "warnings",
]

_REQUIRED_FEATURES = [
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
    "atr14_pct",
    "range_vs_atr14",
    "gap_pct",
]


@dataclass(frozen=True)
class PullbackScore:
    date: str
    strategy: str
    heat: int | None
    status: str
    trend_score: int
    pullback_score: int
    resumption_score: int
    risk_score: int
    positive_drivers: tuple[str, ...]
    negative_drivers: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def comment(self) -> str:
        drivers = [*self.positive_drivers[:3], *self.negative_drivers[:2]]
        if not drivers:
            return ""
        return ", ".join(drivers)

    def as_row(self) -> dict:
        return {
            "date": self.date,
            "strategy": self.strategy,
            "heat": "" if self.heat is None else str(self.heat),
            "status": self.status,
            "trend_score": str(self.trend_score),
            "pullback_score": str(self.pullback_score),
            "resumption_score": str(self.resumption_score),
            "risk_score": str(self.risk_score),
            "comment": self.comment,
            "warnings": ", ".join(self.warnings),
        }


def score_pullback_features(feature_row: dict) -> PullbackScore:
    date = feature_row.get("date", "")
    validation_warnings = _validate_feature_row(feature_row)
    if validation_warnings:
        return PullbackScore(
            date=date,
            strategy=PULLBACK_STRATEGY_ID,
            heat=None,
            status="NO_SCORE",
            trend_score=0,
            pullback_score=0,
            resumption_score=0,
            risk_score=0,
            positive_drivers=(),
            negative_drivers=("invalid data",),
            warnings=tuple(validation_warnings),
        )

    values = {key: _decimal(feature_row.get(key)) for key in _REQUIRED_FEATURES if key != "is_green_candle"}
    volume_vs_avg20 = _decimal(feature_row.get("volume_vs_avg20"))
    is_green_candle = feature_row.get("is_green_candle") == "true"

    positives: list[str] = []
    negatives: list[str] = []
    warnings: list[str] = []
    if volume_vs_avg20 is None:
        warnings.append("volume_missing")
        negatives.append("missing volume confirmation")

    trend_score = _score_trend(values, positives, negatives)
    pullback_score = _score_pullback(values, positives, negatives)
    resumption_score = _score_resumption(values, volume_vs_avg20, is_green_candle, positives, negatives)
    risk_score = _score_risk(values, volume_vs_avg20, positives, negatives)

    heat = trend_score + pullback_score + resumption_score + risk_score
    return PullbackScore(
        date=date,
        strategy=PULLBACK_STRATEGY_ID,
        heat=heat,
        status=_status_for_heat(heat),
        trend_score=trend_score,
        pullback_score=pullback_score,
        resumption_score=resumption_score,
        risk_score=risk_score,
        positive_drivers=tuple(positives),
        negative_drivers=tuple(negatives),
        warnings=tuple(warnings),
    )


def score_pullback_feature_rows(feature_rows: list[dict]) -> list[PullbackScore]:
    return [score_pullback_features(row) for row in feature_rows]


def _score_trend(values: dict[str, Decimal], positives: list[str], negatives: list[str]) -> int:
    close_vs_sma200 = values["close_vs_sma200_pct"]
    sma50_vs_sma200 = values["sma50_vs_sma200_pct"]
    sma50_slope = values["sma50_slope_10d"]
    return_60d = values["return_60d_pct"]

    regime = _band_score(close_vs_sma200, [(Decimal("10"), 9), (Decimal("3"), 7), (Decimal("0"), 4)])
    if sma50_slope >= Decimal("0"):
        regime += 2
    if sma50_vs_sma200 >= Decimal("0"):
        regime += 1
    regime = min(regime, 12)

    ma_structure = _band_score(
        sma50_vs_sma200,
        [(Decimal("8"), 10), (Decimal("3"), 8), (Decimal("0"), 6), (Decimal("-2"), 3)],
    )
    prior_strength = _band_score(
        return_60d,
        [(Decimal("15"), 10), (Decimal("8"), 8), (Decimal("3"), 5), (Decimal("0"), 2)],
    )
    slope = _band_score(
        sma50_slope,
        [(Decimal("1"), 8), (Decimal("0.25"), 6), (Decimal("0"), 4), (Decimal("-0.5"), 2)],
    )

    score = regime + ma_structure + prior_strength + slope
    if score >= 30:
        positives.append("strong prior trend")
    elif score <= 15:
        negatives.append("weak prior trend")
    if ma_structure >= 8:
        positives.append("constructive MA structure")
    return score


def _score_pullback(values: dict[str, Decimal], positives: list[str], negatives: list[str]) -> int:
    depth = values["pullback_depth_20d_pct"]
    distance_sma20 = values["distance_to_sma20_atr"]
    distance_sma50 = values["distance_to_sma50_atr"]
    close_vs_sma50 = values["close_vs_sma50_pct"]
    sma50_vs_sma200 = values["sma50_vs_sma200_pct"]

    if depth >= Decimal("-1"):
        actual_pullback = 0
        location_cap = 2
        damage_cap = 3
        negatives.append("no actual pullback")
        negatives.append("possible momentum handoff")
    elif depth >= Decimal("-3"):
        actual_pullback = 4
        location_cap = 5
        damage_cap = 4
    elif depth >= Decimal("-8"):
        actual_pullback = 15
        location_cap = 10
        damage_cap = 5
        positives.append("controlled pullback from recent high")
    elif depth >= Decimal("-12"):
        actual_pullback = 12
        location_cap = 10
        damage_cap = 5
        positives.append("controlled pullback from recent high")
    elif depth >= Decimal("-18"):
        actual_pullback = 4
        location_cap = 6
        damage_cap = 3
        negatives.append("deep pullback with trend damage")
    else:
        actual_pullback = 0
        location_cap = 3
        damage_cap = 2
        negatives.append("deep pullback with trend damage")

    sma20_location = _score_sma20_pullback_location(distance_sma20)
    sma50_location = _score_sma50_pullback_location(distance_sma50)
    location = min(max(sma20_location, sma50_location), location_cap)
    if location >= 8 and sma20_location >= sma50_location and actual_pullback >= 12:
        positives.append("near rising SMA20")
    elif location >= 8 and actual_pullback >= 12:
        positives.append("near SMA50 support zone")

    damage = min(
        _band_score(
            close_vs_sma50,
            [(Decimal("1"), 5), (Decimal("0"), 4), (Decimal("-2.5"), 3), (Decimal("-5"), 1)],
        ),
        damage_cap,
    )
    if close_vs_sma50 < Decimal("-5") or sma50_vs_sma200 < Decimal("-2"):
        negatives.append("deep pullback with trend damage")

    return actual_pullback + location + damage


def _score_resumption(
    values: dict[str, Decimal],
    volume_vs_avg20: Decimal | None,
    is_green_candle: bool,
    positives: list[str],
    negatives: list[str],
) -> int:
    close_position = values["close_position_in_range"]
    price_response = _band_score(
        close_position,
        [(Decimal("0.8"), 7), (Decimal("0.65"), 5), (Decimal("0.5"), 3), (Decimal("0.35"), 1)],
    )
    if price_response >= 5:
        positives.append("strong close in daily range")
    elif price_response <= 1:
        negatives.append("weak close in range")

    if volume_vs_avg20 is None:
        volume = 1
    elif is_green_candle:
        volume = _band_score(
            volume_vs_avg20,
            [(Decimal("1.5"), 8), (Decimal("1.1"), 6), (Decimal("0.8"), 4), (Decimal("0"), 2)],
        )
    else:
        volume = _band_score(volume_vs_avg20, [(Decimal("1.1"), 3), (Decimal("0.8"), 2), (Decimal("0"), 1)])
    if volume >= 6:
        positives.append("buyers returning on volume")
    elif volume_vs_avg20 is not None and volume <= 2:
        negatives.append("response lacks volume")

    candle = 5 if is_green_candle else 0
    return price_response + volume + candle


def _score_risk(
    values: dict[str, Decimal],
    volume_vs_avg20: Decimal | None,
    positives: list[str],
    negatives: list[str],
) -> int:
    atr14_pct = values["atr14_pct"]
    range_vs_atr14 = values["range_vs_atr14"]
    gap_pct = abs(values["gap_pct"])

    volatility = 4 if Decimal("1") <= atr14_pct <= Decimal("6") else 3 if atr14_pct <= Decimal("10") else 1
    range_gap = 0
    range_gap += Decimal("1.5") if range_vs_atr14 <= Decimal("1.5") else Decimal("0.75") if range_vs_atr14 <= Decimal("2.25") else Decimal("0")
    range_gap += Decimal("1.5") if gap_pct <= Decimal("1.5") else Decimal("0.75") if gap_pct <= Decimal("3") else Decimal("0")
    liquidity = 2 if volume_vs_avg20 is None else _band_score(volume_vs_avg20, [(Decimal("0.8"), 3), (Decimal("0.4"), 2), (Decimal("0"), 1)])

    if volatility == 4:
        positives.append("normal ATR")
    elif volatility <= 1:
        negatives.append("unusual ATR")
    if range_vs_atr14 > Decimal("2.25") or gap_pct > Decimal("3"):
        negatives.append("range or gap risk")

    return volatility + int(range_gap) + liquidity


def _validate_feature_row(feature_row: dict) -> list[str]:
    warnings: list[str] = []
    for feature in _REQUIRED_FEATURES:
        if feature_row.get(feature) in (None, ""):
            warnings.append(f"missing {feature}")

    if warnings:
        return warnings

    try:
        values = {key: _decimal(feature_row.get(key)) for key in _REQUIRED_FEATURES if key != "is_green_candle"}
    except ValueError as exc:
        return [str(exc)]

    if feature_row.get("is_green_candle") not in ("true", "false"):
        warnings.append("invalid is_green_candle")
    if values["rolling_high_20d"] <= 0:
        warnings.append("invalid rolling_high_20d")
    if not Decimal("0") <= values["close_position_in_range"] <= Decimal("1"):
        warnings.append("invalid close_position_in_range")
    if values["atr14_pct"] <= 0:
        warnings.append("invalid atr14_pct")
    if values["range_vs_atr14"] <= 0:
        warnings.append("invalid range_vs_atr14")
    return warnings


def _decimal(value) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"invalid numeric value {value}") from exc


def _band_score(value: Decimal, bands: list[tuple[Decimal, int]]) -> int:
    for threshold, score in bands:
        if value >= threshold:
            return score
    return 0


def _distance_score(value: Decimal, bands: list[tuple[Decimal, int]]) -> int:
    for threshold, score in bands:
        if value <= threshold:
            return score
    return 0


def _score_sma20_pullback_location(distance: Decimal) -> int:
    if Decimal("0") <= distance <= Decimal("0.75"):
        return 10
    if Decimal("-0.5") <= distance < Decimal("0"):
        return 6
    if Decimal("0.75") < distance <= Decimal("1.5"):
        return 5
    if Decimal("-1") <= distance < Decimal("-0.5"):
        return 2
    if Decimal("1.5") < distance <= Decimal("2"):
        return 2
    return 0


def _score_sma50_pullback_location(distance: Decimal) -> int:
    if Decimal("0") <= distance <= Decimal("1"):
        return 8
    if Decimal("-0.5") <= distance < Decimal("0"):
        return 4
    if Decimal("1") < distance <= Decimal("2"):
        return 5
    if Decimal("-1") <= distance < Decimal("-0.5"):
        return 1
    return 0


def _status_for_heat(heat: int) -> str:
    if heat >= 80:
        return "HOT"
    if heat >= 65:
        return "CANDIDATE"
    if heat >= 50:
        return "WATCH"
    return "LOW"
