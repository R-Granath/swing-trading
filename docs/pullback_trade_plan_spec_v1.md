# Pullback Trade Plan Spec v1

Detta dokument borjar designen av `PULLBACK_TRADE_PLAN_V1` som ett separat
lager ovanpa `PULLBACK_SCORING_V1`.

Dokumentet specificerar strategiavsikt, ansvar, gransningar och MVP-granser.
Det specificerar inte exakta entry-, stop-loss-, target- eller
position-sizing-regler. Dessa ska inte kodas innan trade-plan-strategin ar
forankrad och manuellt granskad.

## Strategi-id

```text
PULLBACK_TRADE_PLAN_V1
```

## Relation till scoring

`PULLBACK_SCORING_V1` svarar pa:

```text
Hur val passar denna ticker just nu som pullback-kandidat?
```

`PULLBACK_TRADE_PLAN_V1` ska senare svara pa:

```text
Om detta ar en relevant pullback-kandidat, hur kan en manuell swing-trade
planeras pa ett disciplinerat och riskkontrollerat satt?
```

Scoring och trade-plan ska vara separata:

- scoring rankar kandidater
- trade-plan beskriver vad som skulle behova handas for att en trade ska bli
  praktiskt handlingsbar
- trade-plan far anvanda scoringresultat som input, men far inte andra heat
- trade-plan ska kunna saga `NO_PLAN` aven nar score ar hog
- trade-plan ska inte skapa en ny strategi eller konkurrera med Momentum,
  Breakout eller Early Trend

## MVP-roll

I MVP ska Pullback trade-plan vara en planeringshjalp for manuell review, inte
en automatisk ordermotor.

Den ska senare kunna producera:

- planstatus
- setupklass
- trigger-ide
- invalidation/stop-ide
- target-ide
- risk/reward-vy
- position sizing-underlag
- korta kommentarer och varningar

I detta designsteg definieras bara vad dessa begrepp betyder och nar de far
komma in.

## Strategisk utgangspunkt

En Pullback trade-plan ska bara beskriva en long-only swing-trade dar:

```text
1. En etablerad positiv trend redan finns.
2. Priset har rekylerat fran en relevant high eller tidigare stark fas.
3. Rekylen verkar kontrollerad snarare an trendbrytande.
4. Kopare visar tidig eller tydlig aterkomst.
5. Riskpunkten gar att definiera utan orimligt stor stop.
6. Entry ska inte jaga priset om setupen redan overgatt till momentum.
```

Trade-planen ska alltsa inte ta alla hogt rankade kandidater. Den ska filtrera
fram vilka kandidater som ar mojliga att planera.

## Designprinciper

### 1. Plan fore prisnivaer

Forst ska modellen beskriva vilken typ av pullback-plan som ar aktuell.
Exakta nivaer far komma senare.

Exempel pa planfraga:

```text
Ar detta en tidig SMA20-respons, en djupare SMA50-respons, eller en setup som
redan ar for sen for ren pullback?
```

### 2. Ingen entry utan invalidation

En framtida trigger far inte foreslas om modellen inte ocksa kan beskriva vad
som skulle visa att setupen har fel.

Det betyder att trigger och stop/invalidation hor ihop som ett par.

### 3. Risk/reward fore position sizing

Position sizing ska inte designas forran planens riskpunkt och rimliga
target-hypotes ar definierade.

### 4. Plan kan avsta

En bra scoringkandidat kan fortfarande fa `NO_PLAN` om:

- setupen ar for grund for att ge rimlig riskpunkt
- responsen har redan sprungit ivag
- risk/reward ser orimlig ut
- datan racker for scoring men inte for planering
- caset passar battre som Momentum eller Breakout

## Planstatus

Forsta statusmodell:

```text
NO_PLAN       Ingen trade-plan ska skapas.
WATCH_PLAN    Kandidaten ar intressant men behover trigger/respons.
READY_PLAN    Setupen ar tillrackligt definierad for manuell trade-review.
LATE_PLAN     Setupen ar relevant men entryzonen kan vara borta.
INVALID_PLAN  Pullbacktesen ar tekniskt skadad eller ogiltig.
```

Status ska inte betyda orderrekommendation. `READY_PLAN` betyder bara att
setupen ar tillrackligt strukturerad for manuell granskning.

## Setupklasser

Forsta MVP-taxonomi:

```text
SMA20_PULLBACK       Snabbare trend, grundare rekyl nara SMA20.
SMA50_PULLBACK       Djupare men konstruktiv rekyl nara SMA50.
SHALLOW_PULLBACK     Stark kandidat men rekyl kan vara for grund.
DEEP_PULLBACK        Rekylen ar djup och kraver extra skadegranskning.
MOMENTUM_HANDOFF     Pullbackplan bor avsta; annan strategi kan passa battre.
```

Detta ar klassificering, inte en ny scoringmodell.

## Inputkontrakt

MVP ska utga fran samma databas som scoring, men initialt kan trade-planen
beraknas i arbetsminne.

Tillaten input i forsta designen:

- OHLCV-rader
- sparade indicators
- MVP-features fran `docs/feature_definitions_v1.md`
- sparat `PULLBACK_SCORING_V1`-resultat

Trade-planen far inte introducera nya indikatorer eller deferred features i
forsta versionen.

## Outputkontrakt

Framtida output bor vara deterministisk och sparbar:

```text
date
symbol
strategy_id
source_scoring_model
source_heat
plan_status
setup_class
trigger_note
invalidation_note
target_note
risk_reward_note
position_size_note
warnings
comment
```

I forsta kodsteg kan flera av notfalten vara tomma eller textuella, men
kontraktet ska tydligt visa att trade-plan och scoring ar olika lager.

## MVP-avgransning for nasta steg

Nasta steg ska inte koda entry, stop, target eller position sizing.

Nasta steg bor i stallet specificera:

1. Vilka scoring-/featurevillkor som gor att en kandidat far planeras.
2. Hur `setup_class` bestams utan nya features.
3. Nar trade-planen ska returnera `NO_PLAN`, `WATCH_PLAN`, `READY_PLAN`,
   `LATE_PLAN` eller `INVALID_PLAN`.
4. Vilka manuella chart-review-fragor som maste besvaras innan prisnivaer
   kodas.

## Manuella granskningsfragor

Innan nivaer kodas ska minst dessa fragor granskas pa riktiga charts:

- Ser `SMA20_PULLBACK` och `SMA50_PULLBACK` ut som olika handlingsbara setupper?
- Nar ar en grund pullback for grund for att ge rimlig riskpunkt?
- Nar har en responsdag gjort entry for sen?
- Vilka typer av pullback-cases bor fa `WATCH_PLAN` snarare an `READY_PLAN`?
- Vilka kandidater med hog heat bor fa `NO_PLAN` pa grund av momentum-handoff?
- Finns det vanliga fall dar score ar bra men stop/invalidation skulle hamna
  orimligt langt bort?

## Rekommenderat nasta designsteg

Skapa en smal beslutstabell for planstatus och setupklass med enbart befintliga
MVP-features.

Forsta tabellen ska vara kvalitativ och granskas manuellt innan kod:

```text
input:  source_heat, trend_score, pullback_score, resumption_score,
        pullback_depth_20d_pct, distance_to_sma20_atr, distance_to_sma50_atr,
        close_position_in_range, volume_vs_avg20, atr14_pct, range_vs_atr14

output: plan_status, setup_class, warnings
```

Forst nar denna tabell kanns rimlig ska `trigger_note`, `invalidation_note`,
`target_note`, `risk_reward_note` och `position_size_note` specificeras.
