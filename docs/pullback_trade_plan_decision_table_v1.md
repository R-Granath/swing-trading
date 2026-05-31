# Pullback Trade Plan Decision Table v1

Detta dokument ar ett forsta kvalitativt forslag till beslutstabell for
framtida `PULLBACK_TRADE_PLAN_V1`.

Syftet ar att oversatta trade-plan-konceptet till deterministiska regler som
senare kan kodas i Python. Dokumentet ar fortfarande design, inte
implementation.

## Syfte

Beslutstabellen beskriver hur Eodwin preliminart ska ga fran:

```text
PULLBACK_SCORING_V1
+ setup_evolution
+ 5-10 dagars OHLCV-observationer
+ MVP-features
```

till:

```text
plan_status
setup_class
rr_hypothesis
warnings
comment
```

Malet ar att skapa en bro mellan dokumentation och framtida kod. Tabellen ska
vara enkel nog att granska manuellt pa charts innan den implementeras.

## Scope

Detta steg ar tillatet:

- kvalitativa beslutstabeller
- deterministiska heuristiker for framtida Python
- mjuka regler for planstatus, setupklass och RR-hypotes
- warnings och korta kommentarer
- filtereffekt som senare kan matas per datum

Out of scope:

- ingen Python-kod
- ingen ny strategi
- ingen andring av scoringlogik
- ingen entry-trigger
- ingen stop-loss
- ingen target
- ingen betsize eller position sizing
- ingen orderlogik
- ingen ML, statistik eller optimering

## Tillatna inputs

### Scoring-output

Fran `PULLBACK_SCORING_V1`:

```text
total_score
heat/status
trend_score
pullback_score
resumption_score
risk_score
```

### Setup evolution

Fran framtida setup-evolution-lager:

```text
PULLING_BACK
STABILIZING
RESPONDING
BREAKING_OUT
EXTENDED
FAILED
```

### MVP-features

Fran `docs/feature_definitions_v1.md`:

```text
pullback_depth_20d_pct
distance_to_sma20_atr
distance_to_sma50_atr
close_position_in_range
is_green_candle
volume_vs_avg20
atr14_pct
range_vs_atr14
gap_pct
```

Andra MVP-features far anvandas om de redan finns definierade for Pullback v1,
men tabellen ska inte introducera nya indikatorer.

### 5-10 dagars OHLCV-observationer

Enkla observationer fran `docs/pullback_trade_plan_v1.md`:

```text
green_count_5d
red_count_5d
strong_close_count_5d
weak_close_count_5d
average_range_vs_atr14_5d
max_range_vs_atr14_5d
up_volume_response
thin_response
down_volume_risk
local_high_10d
local_low_10d
close_vs_local_high_10d_pct
close_vs_local_low_10d_pct
distance_to_sma20_atr_delta_3d
distance_to_sma50_atr_delta_3d
```

Dessa ar observationer av befintlig data, inte nya strategier.

## Outputs

### plan_status

```text
NO_PLAN
WATCH_PLAN
READY_PLAN
LATE_PLAN
INVALID_PLAN
```

### setup_class

```text
SMA20_PULLBACK
SMA50_PULLBACK
SHALLOW_PULLBACK
DEEP_PULLBACK
MOMENTUM_HANDOFF
```

### rr_hypothesis

```text
RR_GOOD
RR_MEDIOCRE
RR_UNCLEAR
RR_BAD
```

### warnings

Korta deterministiska varningar, till exempel:

```text
volume_missing_for_evolution
thin_response
down_volume_risk
extended_from_pullback_zone
possible_momentum_handoff
weak_planability_despite_high_score
range_or_gap_risk
failed_local_structure
```

### comment

Kort deterministisk motivering. Kommentaren ska forklara planstatus, inte
forsoka skriva en full tradinganalys.

## Beslutsordning

Beslut ska ske i en fast ordning sa att framtida kod blir reproducerbar:

```text
1. Data- och score-gates
2. Hard negatives
3. setup_evolution
4. setup_class
5. rr_hypothesis
6. plan_status
7. warnings
8. comment
```

### 1. Data- och score-gates

Om `PULLBACK_SCORING_V1` ar `NO_SCORE` eller nodvandiga OHLCV-/feature-rader
saknas for evolution, ska trade-planen normalt bli:

```text
plan_status = NO_PLAN
rr_hypothesis = RR_UNCLEAR
warning = insufficient_trade_plan_data
```

Om score finns men 5-10 dagars evolutiondata ar ofullstandig, kan caset
fortfarande visas som `WATCH_PLAN` om scoring ar stark och databrister ar
begransade. Detta ska markeras med warning.

### 2. Hard negatives

I MVP ska bara tva saker vara hart negativa:

```text
setup_evolution = FAILED
rr_hypothesis = RR_BAD
```

`FAILED` lutar mot `INVALID_PLAN`.
Tydligt `RR_BAD` lutar mot `NO_PLAN`, `LATE_PLAN` eller `INVALID_PLAN` beroende
pa orsak.

### 3. setup_evolution

`setup_evolution` beskriver var caset befinner sig i pullback-processen. Det ar
inte en aggressiv filterregel.

MVP-princip:

```text
WATCH_PLAN hellre an NO_PLAN
LATE_PLAN hellre an felaktigt NO_PLAN
READY_PLAN endast nar setupen faktiskt verkar planeringsbar
```

## Beslutstabell: setup_evolution -> plan_status

| setup_evolution | Normal plan_status | Kan uppgraderas nar | Kan nedgraderas nar |
| --- | --- | --- | --- |
| `PULLING_BACK` | `WATCH_PLAN` | Scoring ar stark och pullback-location ar bra, men respons saknas annu | `FAILED`-tecken, tydlig trend damage eller `RR_BAD` |
| `STABILIZING` | `WATCH_PLAN` | Scoring ar stark, lokalt low haller och RR verkar kunna bli bra | Otydlig struktur, svag score eller tydlig distributionsvarning |
| `RESPONDING` | `READY_PLAN` eller `WATCH_PLAN` | Score, location, range/gap och RR ar rimliga | Respons ar tunn, location ar svag eller RR ar oklar |
| `BREAKING_OUT` | `READY_PLAN` eller `LATE_PLAN` | Forsta tydliga utbrottsdagen fran tajt 5-10 dagars struktur, nara pullbackzon, definierbar invalidation och `RR_GOOD` | Flera starka grona dagar, langt fran SMA20/SMA50-zon eller `RR_MEDIOCRE`/`RR_BAD` |
| `EXTENDED` | `LATE_PLAN` eller `WATCH_PLAN` | Caset ar starkt men Pullback-RR ar inte tydligt dalig | Priset ar langt fran pullbackzonen och invalidation skulle bli for langt bort |
| `FAILED` | `INVALID_PLAN` | Normalt inte i MVP | Alltid hart negativt for Pullback v1 |

Viktigt: `PULLING_BACK` och `STABILIZING` ska normalt inte bli `NO_PLAN` bara
for att respons saknas. De ska vanligen behallas som `WATCH_PLAN`.

## Beslutstabell: setup_evolution + score breakdown -> setup_class

| Villkor | setup_class | Kommentar |
| --- | --- | --- |
| Pullback depth ar grund, priset ar nara SMA20-zon, trend_score ar stark och evolution ar `STABILIZING` eller `RESPONDING` | `SMA20_PULLBACK` | Snabbare trendpullback som kan bli planeringsbar vid respons |
| Pullback depth ar djupare, priset ar nara SMA50-zon, trend_score ar konstruktiv och evolution inte ar `FAILED` | `SMA50_PULLBACK` | Djupare men fortfarande Pullback-specifik setup |
| total_score ar hog men pullback_score ar modest, pullback_depth_20d_pct ar grund och evolution ar `PULLING_BACK`, `STABILIZING` eller tidig `BREAKING_OUT` | `SHALLOW_PULLBACK` | Kan vara tidig pullback eller momentum-handoff; kraver RR-granskning |
| pullback_depth_20d_pct ar djup, distance_to_sma50_atr ar svag eller trend damage syns, men evolution inte ar `FAILED` | `DEEP_PULLBACK` | Ska oftast vara `WATCH_PLAN` tills skadebilden klarnar |
| evolution ar `BREAKING_OUT` eller `EXTENDED` och priset har lamnat pullbackzonen | `MOMENTUM_HANDOFF` | Inte nodvandigtvis dalig aktie, men Pullback v1 kan vara fel planeringsram |

Score breakdown ska anvandas som kontext:

- stark `trend_score` kravs for att `READY_PLAN` ska vara rimligt
- `pullback_score` ska visa att det faktiskt finns en pullback, inte bara
  stark trend
- `resumption_score` hjalper `RESPONDING`, men ska inte ensam radda svag trend
- `risk_score` ska kunna stoppa eller varna nar range/gap/ATR gor planen
  opraktisk

## Beslutstabell: preliminar rr_hypothesis

RR-hypotesen ar grov och textuell. Den ska inte rakna exakt entry, stop eller
target.

| rr_hypothesis | Typiska villkor | Planimplikation |
| --- | --- | --- |
| `RR_GOOD` | Evolution ar `RESPONDING` eller forsta konstruktiva `BREAKING_OUT`; priset ar fortfarande nara SMA20/SMA50-pullbackzon; lokal invalidation verkar nara; tidigare high/local high ger rimlig reward; range/gap ar normal | Kan stoda `READY_PLAN` |
| `RR_MEDIOCRE` | Target-hypotes finns men priset har rort sig en bit; invalidation verkar relativt langt bort; evolution ar `STABILIZING`, sen `BREAKING_OUT` eller tidig `EXTENDED` | Lutar mot `WATCH_PLAN` eller `LATE_PLAN` |
| `RR_UNCLEAR` | Setup-processen ar otydlig; volume saknas; local high/low ar inte tydlig; score ar relevant men planbarhet ar inte bevisad | Lutar mot `WATCH_PLAN` om score ar relevant |
| `RR_BAD` | Evolution ar `FAILED`; eller tydligt `EXTENDED` efter flera starka grona dagar; priset ar langt fran rimlig invalidation; tidigare high ar for nara; range/gap-risk ar stor | Hart negativt: `NO_PLAN`, `LATE_PLAN` eller `INVALID_PLAN` |

## Warnings-tabell

| Warning | Nar den satts | Effekt |
| --- | --- | --- |
| `insufficient_trade_plan_data` | Saknar nodvandiga 5-10 dagars OHLCV-/feature-rader | `NO_PLAN` eller forsiktigt `WATCH_PLAN` |
| `volume_missing_for_evolution` | `volume_vs_avg20` saknas for viktiga dagar | Gor RR/evolution mindre saker, men stoppar inte ensam |
| `thin_response` | Gron responsdag men `volume_vs_avg20` ar lag | Kan halla `RESPONDING` kvar som `WATCH_PLAN` |
| `down_volume_risk` | Rod/svag dag pa hog relativ volym | Varning for `PULLING_BACK`, `STABILIZING` eller `FAILED` |
| `extended_from_pullback_zone` | Priset har rort sig langt fran SMA20/SMA50-zon efter respons | Lutar mot `LATE_PLAN` eller `RR_MEDIOCRE` |
| `possible_momentum_handoff` | `BREAKING_OUT`/`EXTENDED` och Pullback inte langre basta tolkning | Kan ge `MOMENTUM_HANDOFF` |
| `weak_planability_despite_high_score` | total_score ar hog men pullback_score/RR/evolution ar svag | Visas som caution/skipped i rapport |
| `range_or_gap_risk` | `range_vs_atr14`, `gap_pct` eller risk_score visar opraktisk risk | Kan sanka till `WATCH_PLAN`, `LATE_PLAN` eller `NO_PLAN` |
| `failed_local_structure` | Close bryter local low med svag close/range | Lutar mot `INVALID_PLAN` |

## Kommentarer

Kommentarer ska byggas deterministiskt av status, evolution, RR och warnings.

Exempel:

```text
READY_PLAN:
Buyers responding from pullback zone; preliminary RR appears good and local
structure is still close enough for manual review.

WATCH_PLAN:
Pullback is still developing; setup remains relevant, but buyer response or RR
is not clear enough for READY_PLAN.

LATE_PLAN:
Pullback response may have moved too far from the MA zone; case may be strong,
but Pullback RR is weaker.

INVALID_PLAN:
Pullback thesis is damaged by failed local structure and weak recent closes.

NO_PLAN:
No Pullback plan; current structure does not offer acceptable preliminary
risk/reward or enough plan data.
```

## Hypotetiska cases

### 1. Stark score + RESPONDING + nara SMA20

Input:

```text
total_score: 80+
trend_score: stark
pullback_score: bra
setup_evolution: RESPONDING
distance_to_sma20_atr: nara zon
volume_vs_avg20: normal eller stark
range_vs_atr14: normal
```

Output:

```text
plan_status: READY_PLAN
setup_class: SMA20_PULLBACK
rr_hypothesis: RR_GOOD
warnings: none eller mild volume warning
comment: Buyers responding from pullback zone; preliminary RR appears good.
```

### 2. Stark score + EXTENDED + langt fran SMA20

Input:

```text
total_score: hog
setup_evolution: EXTENDED
distance_to_sma20_atr: langt ovanfor zon
green_count_5d: flera
pullback_depth_20d_pct: nara 0
```

Output:

```text
plan_status: LATE_PLAN
setup_class: MOMENTUM_HANDOFF
rr_hypothesis: RR_MEDIOCRE eller RR_BAD
warnings: extended_from_pullback_zone, possible_momentum_handoff
comment: Strong case, but Pullback entry zone may be gone and RR is weaker.
```

### 3. Bra score + STABILIZING

Input:

```text
total_score: CANDIDATE eller HOT
setup_evolution: STABILIZING
local_low_10d: haller
strong_close_count_5d: blandad
volume_vs_avg20: normal eller saknas
```

Output:

```text
plan_status: WATCH_PLAN
setup_class: SMA20_PULLBACK eller SMA50_PULLBACK
rr_hypothesis: RR_UNCLEAR
warnings: optional volume_missing_for_evolution
comment: Pullback is stabilizing, but buyer response is not confirmed enough.
```

### 4. Hog score + BREAKING_OUT forsta dagen fran tajt struktur

Input:

```text
total_score: hog
setup_evolution: BREAKING_OUT
strong_close_count_5d: forsta tydliga respons/utbrottsdag
average_range_vs_atr14_5d: normal eller kontrakterande
distance_to_sma20_atr: fortfarande rimligt nara
rr_hypothesis: RR_GOOD
```

Output:

```text
plan_status: READY_PLAN
setup_class: SMA20_PULLBACK eller SHALLOW_PULLBACK
rr_hypothesis: RR_GOOD
warnings: none eller possible_momentum_handoff
comment: First move out of tight pullback structure; RR remains good enough for manual review.
```

### 5. FAILED

Input:

```text
setup_evolution: FAILED
close: bryter local_low_10d
close_position_in_range: svag
range_vs_atr14: stor eller negativt expanderande
```

Output:

```text
plan_status: INVALID_PLAN
setup_class: DEEP_PULLBACK eller MOMENTUM_HANDOFF
rr_hypothesis: RR_BAD
warnings: failed_local_structure
comment: Pullback thesis is damaged by failed local structure.
```

### 6. Hog score men svag planbarhet

Input:

```text
total_score: HOT
trend_score: stark
pullback_score: modest
setup_evolution: EXTENDED eller sen BREAKING_OUT
rr_hypothesis: RR_MEDIOCRE
```

Output:

```text
plan_status: LATE_PLAN
setup_class: MOMENTUM_HANDOFF eller SHALLOW_PULLBACK
rr_hypothesis: RR_MEDIOCRE
warnings: weak_planability_despite_high_score
comment: High score, but Pullback planability is weaker because price has moved away from the zone.
```

## Filtereffekt

Framtida kod ska kunna sammanstalla filtereffekt per datum innan reglerna
skarps.

Minimum:

```text
date
total_pullback_candidates
count_by_setup_evolution
count_by_plan_status
count_by_rr_hypothesis
count_by_warning
```

Kontrollfragor:

- Hur manga kandidater blir `READY_PLAN`?
- Hur manga blir `WATCH_PLAN`?
- Hur manga blir `LATE_PLAN`?
- Hur manga blir `INVALID_PLAN` eller `NO_PLAN`?
- Blir `PULLING_BACK` och `STABILIZING` normalt kvar som `WATCH_PLAN`?
- Blir nastan alla hog-score-kandidater stoppade?
- Blir `BREAKING_OUT` alltid sent, aven nar det ar forsta dagen fran tajt
  struktur?

Om filtereffekten blir for hard ska beslutstabellen mjukas upp innan entry,
stop, target eller position sizing designas.

## Manuell review fore kodning

Beslutstabellen ska granskas manuellt mot riktiga charts innan kodning.

Forsta review-urval:

```text
ABB.ST
ERIC-B.ST
INVE-B.ST
VOLV-B.ST
```

Reviewen ska kontrollera:

- om planstatus verkar rimlig mot chart
- om `setup_evolution` forklarar processlaget
- om hog score men svag planbarhet blir tydligt forklart
- om `WATCH_PLAN` anvands tillrackligt ofta for osakra men relevanta cases
- om `READY_PLAN` bara uppstar nar setupen faktiskt verkar planeringsbar

## Rekommenderat nasta steg

Nasta steg efter detta dokument:

```text
manuell review av beslutstabellen mot riktiga charts och darefter forsta
kodade prototype med filtereffekt-sammanstallning
```

Entry, stop, target och position sizing ska fortfarande vanta.
