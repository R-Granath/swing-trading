from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.scoring import PULLBACK_STRATEGY_ID


PULLBACK_TRADE_PLAN_ID = "PULLBACK_TRADE_PLAN_V1"

PULLBACK_TRADE_PLAN_COLUMNS = [
    "date",
    "strategy",
    "source_scoring_model",
    "source_heat",
    "source_status",
    "plan_status",
    "setup_class",
    "setup_evolution",
    "rr_hypothesis",
    "comment",
    "warnings",
]


@dataclass(frozen=True)
class PullbackTradePlan:
    date: str
    strategy: str
    source_scoring_model: str
    source_heat: int | None
    source_status: str
    plan_status: str
    setup_class: str
    setup_evolution: str
    rr_hypothesis: str
    warnings: tuple[str, ...]
    comment: str

    def as_row(self) -> dict:
        return {
            "date": self.date,
            "strategy": self.strategy,
            "source_scoring_model": self.source_scoring_model,
            "source_heat": "" if self.source_heat is None else str(self.source_heat),
            "source_status": self.source_status,
            "plan_status": self.plan_status,
            "setup_class": self.setup_class,
            "setup_evolution": self.setup_evolution,
            "rr_hypothesis": self.rr_hypothesis,
            "comment": self.comment,
            "warnings": ", ".join(self.warnings),
        }


@dataclass(frozen=True)
class PullbackTradePlanSummary:
    date: str
    total_pullback_candidates: int
    count_by_setup_evolution: dict[str, int]
    count_by_plan_status: dict[str, int]
    count_by_rr_hypothesis: dict[str, int]
    count_by_warning: dict[str, int]


@dataclass(frozen=True)
class _EvolutionObservations:
    green_count_5d: int
    red_count_5d: int
    strong_close_count_5d: int
    weak_close_count_5d: int
    average_range_vs_atr14_5d: Decimal | None
    max_range_vs_atr14_5d: Decimal | None
    up_volume_response: bool
    thin_response: bool
    down_volume_risk: bool
    volume_missing: bool
    local_high_10d: Decimal
    local_low_10d: Decimal
    close_vs_local_high_10d_pct: Decimal
    close_vs_local_low_10d_pct: Decimal
    distance_to_sma20_atr_delta_3d: Decimal | None
    distance_to_sma50_atr_delta_3d: Decimal | None
    current_day_response: bool
    weak_current_response: bool
    low_volume_response: bool
    days_since_local_low_10d: int
    green_count_after_local_low: int
    strong_close_count_after_local_low: int
    days_near_ma_zone_10d: int
    days_clearly_above_sma20_10d: int
    max_distance_to_sma20_atr_10d: Decimal | None
    already_bounced_from_pullback_low: bool
    stale_near_ma_zone: bool
    not_clean_pullback_sequence: bool


def build_pullback_trade_plan(
    score_row: dict,
    market_rows: list[dict],
    feature_rows: list[dict],
) -> PullbackTradePlan:
    date = score_row.get("date", "")
    source_strategy = score_row.get("strategy_id") or score_row.get("strategy") or PULLBACK_STRATEGY_ID
    source_heat = _optional_int(score_row.get("heat"))
    source_status = score_row.get("status", "")

    if source_status == "NO_SCORE" or source_heat is None:
        return _plan(
            date=date,
            source_strategy=source_strategy,
            source_heat=source_heat,
            source_status=source_status,
            plan_status="NO_PLAN",
            setup_class="DEEP_PULLBACK",
            setup_evolution="FAILED",
            rr_hypothesis="RR_UNCLEAR",
            warnings=("insufficient_trade_plan_data",),
            comment="No Pullback plan; scoring data is not sufficient for trade-plan review.",
        )

    row_index = _index_for_date(feature_rows, date)
    if row_index is None or row_index >= len(market_rows):
        return _insufficient_data_plan(date, source_strategy, source_heat, source_status)

    current_features = feature_rows[row_index]
    if row_index < 9 or _missing_required_trade_plan_features(current_features):
        return _insufficient_data_plan(date, source_strategy, source_heat, source_status)

    observations = _observe_evolution(market_rows, feature_rows, row_index)
    if observations is None:
        return _insufficient_data_plan(date, source_strategy, source_heat, source_status)

    warnings = _warnings(score_row, current_features, observations)
    setup_evolution = _classify_setup_evolution(current_features, observations)
    setup_class = _classify_setup_class(score_row, current_features, setup_evolution)
    rr_hypothesis = _classify_rr_hypothesis(current_features, observations, setup_evolution, warnings)
    plan_status = _classify_plan_status(score_row, setup_evolution, setup_class, rr_hypothesis, warnings)

    return _plan(
        date=date,
        source_strategy=source_strategy,
        source_heat=source_heat,
        source_status=source_status,
        plan_status=plan_status,
        setup_class=setup_class,
        setup_evolution=setup_evolution,
        rr_hypothesis=rr_hypothesis,
        warnings=tuple(warnings),
        comment=_comment(plan_status, setup_evolution, rr_hypothesis),
    )


def build_pullback_trade_plans(
    score_rows: list[dict],
    market_rows_by_symbol: dict[str, list[dict]],
    feature_rows_by_symbol: dict[str, list[dict]],
) -> list[dict]:
    plans = []
    for score_row in score_rows:
        symbol = score_row["symbol"]
        plan = build_pullback_trade_plan(
            score_row,
            market_rows_by_symbol.get(symbol, []),
            feature_rows_by_symbol.get(symbol, []),
        )
        plans.append({"symbol": symbol, **plan.as_row()})
    return plans


def summarize_pullback_trade_plans(date: str, plan_rows: list[dict]) -> PullbackTradePlanSummary:
    setup_evolution = Counter(row["setup_evolution"] for row in plan_rows)
    plan_status = Counter(row["plan_status"] for row in plan_rows)
    rr_hypothesis = Counter(row["rr_hypothesis"] for row in plan_rows)
    warning_counts: Counter[str] = Counter()
    for row in plan_rows:
        warnings = row.get("warnings", "")
        if isinstance(warnings, str):
            values = [warning.strip() for warning in warnings.split(",") if warning.strip()]
        else:
            values = list(warnings)
        warning_counts.update(values)

    return PullbackTradePlanSummary(
        date=date,
        total_pullback_candidates=len(plan_rows),
        count_by_setup_evolution=dict(sorted(setup_evolution.items())),
        count_by_plan_status=dict(sorted(plan_status.items())),
        count_by_rr_hypothesis=dict(sorted(rr_hypothesis.items())),
        count_by_warning=dict(sorted(warning_counts.items())),
    )


def _insufficient_data_plan(
    date: str,
    source_strategy: str,
    source_heat: int | None,
    source_status: str,
) -> PullbackTradePlan:
    return _plan(
        date=date,
        source_strategy=source_strategy,
        source_heat=source_heat,
        source_status=source_status,
        plan_status="NO_PLAN",
        setup_class="SHALLOW_PULLBACK",
        setup_evolution="PULLING_BACK",
        rr_hypothesis="RR_UNCLEAR",
        warnings=("insufficient_trade_plan_data",),
        comment="No Pullback plan; current data is not sufficient for setup evolution.",
    )


def _plan(
    date: str,
    source_strategy: str,
    source_heat: int | None,
    source_status: str,
    plan_status: str,
    setup_class: str,
    setup_evolution: str,
    rr_hypothesis: str,
    warnings: tuple[str, ...],
    comment: str,
) -> PullbackTradePlan:
    return PullbackTradePlan(
        date=date,
        strategy=PULLBACK_TRADE_PLAN_ID,
        source_scoring_model=source_strategy,
        source_heat=source_heat,
        source_status=source_status,
        plan_status=plan_status,
        setup_class=setup_class,
        setup_evolution=setup_evolution,
        rr_hypothesis=rr_hypothesis,
        warnings=warnings,
        comment=comment,
    )


def _observe_evolution(
    market_rows: list[dict],
    feature_rows: list[dict],
    row_index: int,
) -> _EvolutionObservations | None:
    current_market = market_rows[row_index]
    close = _decimal(current_market.get("close"))
    if close is None:
        return None

    latest_5_market = market_rows[row_index - 4 : row_index + 1]
    latest_5_features = feature_rows[row_index - 4 : row_index + 1]
    latest_10_market = market_rows[row_index - 9 : row_index + 1]

    highs = [_decimal(row.get("high")) for row in latest_10_market]
    lows = [_decimal(row.get("low")) for row in latest_10_market]
    if any(value is None for value in highs + lows):
        return None

    local_high = max(value for value in highs if value is not None)
    local_low = min(value for value in lows if value is not None)
    local_low_index = next(
        index
        for index, value in enumerate(lows)
        if value == local_low
    )
    days_since_local_low = len(latest_10_market) - 1 - local_low_index
    ranges = [_decimal(row.get("range_vs_atr14")) for row in latest_5_features]
    available_ranges = [value for value in ranges if value is not None]

    volume_values = [_decimal(row.get("volume_vs_avg20")) for row in latest_5_features]
    volume_missing = any(value is None for value in volume_values)

    green_count = 0
    red_count = 0
    strong_close_count = 0
    weak_close_count = 0
    up_volume_response = False
    thin_response = False
    down_volume_risk = False
    current_day_response = False
    weak_current_response = False
    low_volume_response = False

    for offset, (market_row, feature_row, volume) in enumerate(zip(latest_5_market, latest_5_features, volume_values)):
        open_price = _decimal(market_row.get("open"))
        row_close = _decimal(market_row.get("close"))
        close_position = _decimal(feature_row.get("close_position_in_range"))
        if open_price is None or row_close is None:
            return None
        is_green = row_close > open_price
        is_red = row_close < open_price
        green_count += 1 if is_green else 0
        red_count += 1 if is_red else 0
        strong_close_count += 1 if close_position is not None and close_position >= Decimal("0.65") else 0
        weak_close_count += 1 if close_position is not None and close_position <= Decimal("0.35") else 0
        up_volume_response = up_volume_response or (is_green and volume is not None and volume >= Decimal("1.1"))
        is_current_day = offset == len(latest_5_market) - 1
        thin_response = thin_response or (
            is_current_day
            and is_green
            and close_position is not None
            and close_position >= Decimal("0.65")
            and volume is not None
            and volume < Decimal("0.8")
        )
        down_volume_risk = down_volume_risk or (
            is_red
            and volume is not None
            and volume >= Decimal("1.1")
            and close_position is not None
            and close_position <= Decimal("0.35")
        )
        if is_current_day:
            current_day_response = (
                is_green
                and close_position is not None
                and close_position >= Decimal("0.5")
                and volume is not None
                and volume >= Decimal("0.8")
            )
            weak_current_response = (
                is_red
                or close_position is None
                or close_position < Decimal("0.5")
            )
            low_volume_response = (
                is_green
                and close_position is not None
                and close_position >= Decimal("0.5")
                and volume is not None
                and volume < Decimal("0.8")
            )

    distance_sma20 = _decimal(feature_rows[row_index].get("distance_to_sma20_atr"))
    distance_sma50 = _decimal(feature_rows[row_index].get("distance_to_sma50_atr"))
    previous_distance_sma20 = _decimal(feature_rows[row_index - 3].get("distance_to_sma20_atr"))
    previous_distance_sma50 = _decimal(feature_rows[row_index - 3].get("distance_to_sma50_atr"))
    latest_10_features = feature_rows[row_index - 9 : row_index + 1]
    features_after_local_low = latest_10_features[local_low_index + 1 :]
    market_after_local_low = latest_10_market[local_low_index + 1 :]
    green_count_after_local_low = 0
    strong_close_count_after_local_low = 0
    for market_row, feature_row in zip(market_after_local_low, features_after_local_low):
        open_price = _decimal(market_row.get("open"))
        row_close = _decimal(market_row.get("close"))
        close_position = _decimal(feature_row.get("close_position_in_range"))
        if open_price is None or row_close is None:
            return None
        green_count_after_local_low += 1 if row_close > open_price else 0
        strong_close_count_after_local_low += 1 if close_position is not None and close_position >= Decimal("0.65") else 0

    days_near_ma_zone = 0
    days_clearly_above_sma20 = 0
    distance_sma20_values = []
    for feature_row in latest_10_features:
        row_distance_sma20 = _decimal(feature_row.get("distance_to_sma20_atr"))
        row_distance_sma50 = _decimal(feature_row.get("distance_to_sma50_atr"))
        if row_distance_sma20 is not None:
            distance_sma20_values.append(row_distance_sma20)
        if row_distance_sma20 is not None and row_distance_sma20 >= Decimal("1.25"):
            days_clearly_above_sma20 += 1
        if (
            row_distance_sma20 is not None
            and abs(row_distance_sma20) <= Decimal("1")
        ) or (
            row_distance_sma50 is not None
            and abs(row_distance_sma50) <= Decimal("1")
        ):
            days_near_ma_zone += 1

    return _EvolutionObservations(
        green_count_5d=green_count,
        red_count_5d=red_count,
        strong_close_count_5d=strong_close_count,
        weak_close_count_5d=weak_close_count,
        average_range_vs_atr14_5d=sum(available_ranges) / Decimal(len(available_ranges)) if available_ranges else None,
        max_range_vs_atr14_5d=max(available_ranges) if available_ranges else None,
        up_volume_response=up_volume_response,
        thin_response=thin_response,
        down_volume_risk=down_volume_risk,
        volume_missing=volume_missing,
        local_high_10d=local_high,
        local_low_10d=local_low,
        close_vs_local_high_10d_pct=_pct_distance(close, local_high) or Decimal("0"),
        close_vs_local_low_10d_pct=_pct_distance(close, local_low) or Decimal("0"),
        distance_to_sma20_atr_delta_3d=_delta(distance_sma20, previous_distance_sma20),
        distance_to_sma50_atr_delta_3d=_delta(distance_sma50, previous_distance_sma50),
        current_day_response=current_day_response,
        weak_current_response=weak_current_response,
        low_volume_response=low_volume_response,
        days_since_local_low_10d=days_since_local_low,
        green_count_after_local_low=green_count_after_local_low,
        strong_close_count_after_local_low=strong_close_count_after_local_low,
        days_near_ma_zone_10d=days_near_ma_zone,
        days_clearly_above_sma20_10d=days_clearly_above_sma20,
        max_distance_to_sma20_atr_10d=max(distance_sma20_values) if distance_sma20_values else None,
        already_bounced_from_pullback_low=(
            days_since_local_low >= 2
            and green_count_after_local_low >= 2
            and weak_current_response
        ),
        stale_near_ma_zone=days_near_ma_zone >= 7 and weak_current_response,
        not_clean_pullback_sequence=(
            days_clearly_above_sma20 < 2
            and days_near_ma_zone >= 6
        ),
    )


def _classify_setup_evolution(feature_row: dict, observations: _EvolutionObservations) -> str:
    depth = _decimal(feature_row.get("pullback_depth_20d_pct")) or Decimal("0")
    distance_sma20 = _decimal(feature_row.get("distance_to_sma20_atr")) or Decimal("0")
    distance_sma50 = _decimal(feature_row.get("distance_to_sma50_atr")) or Decimal("0")
    close_position = _decimal(feature_row.get("close_position_in_range")) or Decimal("0.5")
    range_today = _decimal(feature_row.get("range_vs_atr14")) or Decimal("1")

    if (
        observations.close_vs_local_low_10d_pct <= Decimal("0.25")
        and observations.weak_close_count_5d >= 3
        and (range_today >= Decimal("1.5") or observations.down_volume_risk)
    ) or (depth <= Decimal("-15") and distance_sma50 < Decimal("-1") and close_position <= Decimal("0.35")):
        return "FAILED"
    if (
        observations.green_count_5d >= 3
        and observations.strong_close_count_5d >= 3
        and depth >= Decimal("-1.5")
        and distance_sma20 > Decimal("1.5")
    ):
        return "EXTENDED"
    if observations.close_vs_local_high_10d_pct >= Decimal("-1") and close_position >= Decimal("0.65"):
        return "BREAKING_OUT"
    if (
        observations.green_count_5d >= 1
        and observations.strong_close_count_5d >= 1
        and observations.close_vs_local_low_10d_pct >= Decimal("2")
        and (observations.up_volume_response or not observations.volume_missing)
    ):
        return "RESPONDING"
    if (
        observations.weak_close_count_5d <= 2
        and observations.close_vs_local_low_10d_pct <= Decimal("4")
        and observations.average_range_vs_atr14_5d is not None
        and observations.average_range_vs_atr14_5d <= Decimal("1.5")
    ):
        return "STABILIZING"
    return "PULLING_BACK"


def _classify_setup_class(score_row: dict, feature_row: dict, setup_evolution: str) -> str:
    depth = _decimal(feature_row.get("pullback_depth_20d_pct")) or Decimal("0")
    distance_sma20 = abs(_decimal(feature_row.get("distance_to_sma20_atr")) or Decimal("99"))
    distance_sma50 = abs(_decimal(feature_row.get("distance_to_sma50_atr")) or Decimal("99"))
    total_score = _optional_int(score_row.get("heat")) or 0
    trend_score = _optional_int(score_row.get("trend_score")) or 0
    pullback_score = _optional_int(score_row.get("pullback_score")) or 0

    if setup_evolution in ("BREAKING_OUT", "EXTENDED") and distance_sma20 > Decimal("1.5"):
        return "MOMENTUM_HANDOFF"
    if depth <= Decimal("-12") or (distance_sma50 > Decimal("2") and depth <= Decimal("-8")):
        return "DEEP_PULLBACK"
    if total_score >= 65 and pullback_score <= 13 and depth >= Decimal("-3"):
        return "SHALLOW_PULLBACK"
    if distance_sma50 <= Decimal("1") and depth <= Decimal("-5") and setup_evolution != "FAILED":
        return "SMA50_PULLBACK"
    if distance_sma20 <= Decimal("1") and trend_score >= 25 and setup_evolution in ("STABILIZING", "RESPONDING", "BREAKING_OUT"):
        return "SMA20_PULLBACK"
    return "SMA20_PULLBACK" if distance_sma20 <= distance_sma50 else "SMA50_PULLBACK"


def _classify_rr_hypothesis(
    feature_row: dict,
    observations: _EvolutionObservations,
    setup_evolution: str,
    warnings: list[str],
) -> str:
    depth = _decimal(feature_row.get("pullback_depth_20d_pct")) or Decimal("0")
    distance_sma20 = _decimal(feature_row.get("distance_to_sma20_atr")) or Decimal("0")
    range_today = _decimal(feature_row.get("range_vs_atr14")) or Decimal("1")

    if setup_evolution == "FAILED":
        return "RR_BAD"
    if setup_evolution == "EXTENDED" and observations.green_count_5d >= 4 and distance_sma20 > Decimal("2"):
        return "RR_BAD"
    if "range_or_gap_risk" in warnings and range_today > Decimal("2.25"):
        return "RR_BAD"
    if (
        setup_evolution in ("RESPONDING", "BREAKING_OUT")
        and abs(distance_sma20) <= Decimal("1.25")
        and observations.close_vs_local_high_10d_pct <= Decimal("0")
        and range_today <= Decimal("1.75")
        and depth <= Decimal("-1")
    ):
        return "RR_GOOD"
    if setup_evolution in ("STABILIZING", "BREAKING_OUT", "EXTENDED"):
        return "RR_MEDIOCRE"
    return "RR_UNCLEAR"


def _classify_plan_status(
    score_row: dict,
    setup_evolution: str,
    setup_class: str,
    rr_hypothesis: str,
    warnings: list[str],
) -> str:
    total_score = _optional_int(score_row.get("heat")) or 0
    trend_score = _optional_int(score_row.get("trend_score")) or 0

    if setup_evolution == "FAILED":
        return "INVALID_PLAN"
    if rr_hypothesis == "RR_BAD":
        return "LATE_PLAN" if setup_evolution == "EXTENDED" else "NO_PLAN"
    if any(
        warning in warnings
        for warning in (
            "weak_current_response",
            "low_volume_response",
            "already_bounced_from_pullback_low",
            "stale_near_ma_zone",
            "not_clean_pullback_sequence",
        )
    ):
        return "WATCH_PLAN"
    if setup_evolution == "RESPONDING":
        if (
            total_score >= 65
            and trend_score >= 25
            and setup_class in ("SMA20_PULLBACK", "SMA50_PULLBACK")
            and rr_hypothesis == "RR_GOOD"
            and "thin_response" not in warnings
        ):
            return "READY_PLAN"
        return "WATCH_PLAN"
    if setup_evolution == "BREAKING_OUT":
        if (
            total_score >= 65
            and trend_score >= 25
            and setup_class in ("SMA20_PULLBACK", "SMA50_PULLBACK")
            and rr_hypothesis == "RR_GOOD"
        ):
            return "READY_PLAN"
        return "LATE_PLAN" if setup_class == "MOMENTUM_HANDOFF" else "WATCH_PLAN"
    if setup_evolution == "EXTENDED":
        return "LATE_PLAN" if setup_class == "MOMENTUM_HANDOFF" else "WATCH_PLAN"
    return "WATCH_PLAN"


def _warnings(score_row: dict, feature_row: dict, observations: _EvolutionObservations) -> list[str]:
    warnings: list[str] = []
    total_score = _optional_int(score_row.get("heat")) or 0
    pullback_score = _optional_int(score_row.get("pullback_score")) or 0
    risk_score = _optional_int(score_row.get("risk_score")) or 0
    distance_sma20 = _decimal(feature_row.get("distance_to_sma20_atr")) or Decimal("0")
    range_today = _decimal(feature_row.get("range_vs_atr14")) or Decimal("1")
    gap_pct = abs(_decimal(feature_row.get("gap_pct")) or Decimal("0"))

    if observations.volume_missing:
        warnings.append("volume_missing_for_evolution")
    if observations.thin_response:
        warnings.append("thin_response")
    if observations.down_volume_risk:
        warnings.append("down_volume_risk")
    if observations.weak_current_response:
        warnings.append("weak_current_response")
    if observations.low_volume_response:
        warnings.append("low_volume_response")
    if observations.already_bounced_from_pullback_low:
        warnings.append("already_bounced_from_pullback_low")
    if observations.stale_near_ma_zone:
        warnings.append("stale_near_ma_zone")
    if observations.not_clean_pullback_sequence:
        warnings.append("not_clean_pullback_sequence")
    if range_today > Decimal("2.25") or gap_pct > Decimal("3") or risk_score <= 3:
        warnings.append("range_or_gap_risk")
    if (
        observations.close_vs_local_low_10d_pct <= Decimal("0.25")
        and observations.weak_close_count_5d >= 3
    ) or (
        _decimal(feature_row.get("pullback_depth_20d_pct")) is not None
        and (_decimal(feature_row.get("pullback_depth_20d_pct")) or Decimal("0")) <= Decimal("-15")
        and observations.weak_close_count_5d >= 3
    ):
        warnings.append("failed_local_structure")
    if observations.green_count_5d >= 3 and distance_sma20 > Decimal("1.5"):
        warnings.append("extended_from_pullback_zone")
    if observations.close_vs_local_high_10d_pct >= Decimal("-1") and distance_sma20 > Decimal("1.5"):
        warnings.append("possible_momentum_handoff")
    if total_score >= 80 and pullback_score <= 13:
        warnings.append("weak_planability_despite_high_score")
    return warnings


def _comment(plan_status: str, setup_evolution: str, rr_hypothesis: str) -> str:
    if plan_status == "READY_PLAN":
        return "Buyers responding from pullback zone; preliminary RR appears good enough for manual review."
    if plan_status == "WATCH_PLAN":
        if setup_evolution == "STABILIZING":
            return "Pullback is stabilizing, but buyer response is not confirmed enough for READY_PLAN."
        return "Pullback is still developing; setup remains relevant, but planability is not clear enough."
    if plan_status == "LATE_PLAN":
        return "Pullback response may have moved too far from the MA zone; Pullback RR is weaker."
    if plan_status == "INVALID_PLAN":
        return "Pullback thesis is damaged by failed local structure and weak recent closes."
    if rr_hypothesis == "RR_BAD":
        return "No Pullback plan; preliminary risk/reward is not acceptable for this setup."
    return "No Pullback plan; current structure does not offer enough plan data."


def _missing_required_trade_plan_features(feature_row: dict) -> bool:
    required = [
        "pullback_depth_20d_pct",
        "distance_to_sma20_atr",
        "distance_to_sma50_atr",
        "close_position_in_range",
        "is_green_candle",
        "atr14_pct",
        "range_vs_atr14",
        "gap_pct",
    ]
    return any(feature_row.get(column) in (None, "") for column in required)


def _index_for_date(rows: list[dict], date: str) -> int | None:
    for index, row in enumerate(rows):
        if row.get("date") == date:
            return index
    return None


def _pct_distance(value: Decimal | None, reference: Decimal | None) -> Decimal | None:
    if value is None or reference is None or reference <= 0:
        return None
    return (value - reference) / reference * Decimal(100)


def _delta(value: Decimal | None, previous_value: Decimal | None) -> Decimal | None:
    if value is None or previous_value is None:
        return None
    return value - previous_value


def _optional_int(value) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _decimal(value) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"invalid numeric value {value}") from exc
