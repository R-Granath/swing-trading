# Pullback Trade Plan v1

Detta dokument beskriver forsta konceptuella designen for
`PULLBACK_TRADE_PLAN_V1`.

Trade-planen ar ett separat lager ovanpa `PULLBACK_SCORING_V1`. Den ska inte
ersatta scoring och inte skapa en ny strategi. Den ska hjalpa Eodwin att forsta
om en Pullback-kandidat ar planeringsbar, var i pullback-processen setupen
befinner sig och om caset ser tidigt, moget, sent eller ogiltigt ut.

Detta dokument specificerar inte exakta entry-, stop-loss-, target- eller
position-sizing-regler. Ingen kod ska byggas fran detta steg innan
beslutstabellerna har granskats manuellt.

## Strategi-id

```text
PULLBACK_TRADE_PLAN_V1
```

## Relation till scoring

`PULLBACK_SCORING_V1` svarar pa:

```text
Hur val passar denna ticker just nu som pullback-kandidat?
```

`PULLBACK_TRADE_PLAN_V1` ska svara pa:

```text
Om detta ar en relevant pullback-kandidat, var i processen befinner sig setupen
och ar den rimlig att planera manuellt?
```

Viktiga regler:

- scoring rankar kandidater
- trade-plan tolkar kandidatens planeringslage
- trade-plan far anvanda scoringresultat som input
- trade-plan far inte andra heat
- trade-plan ska kunna returnera `NO_PLAN` trots hog heat
- trade-plan ska inte bli Momentum, Breakout eller Early Trend

## MVP-avgransning

Tillaten input:

- senaste OHLCV-rader
- sparade indicators: `sma20`, `sma50`, `sma200`, `atr14`, `atr14_pct`
- MVP-features fran `docs/feature_definitions_v1.md`
- sparat resultat fran `PULLBACK_SCORING_V1`

Inte tillatet i v1:

- nya indikatorer
- RSI, MACD, Bollinger Bands eller candlestick-pattern libraries
- nya strategi-features utanfor Pullback MVP
- entry-trigger, stop-loss, target eller position sizing
- ML, statistik eller optimering

Trade-planen far daremot gora enkla deterministiska observationer over de
senaste 5-10 dagarna baserat pa redan tillgangliga OHLCV-rader och MVP-features.
Dessa observationer ar inte nya indikatorer. De ar en smal setup-evolution
tolkning for planering.

## Varfor setup evolution behovs

En dags score ar en snapshot. Pullback-processen ar en sekvens:

```text
trend -> rekyl -> stabilisering -> respons -> eventuell continuation
```

Tva tickers kan ha liknande heat men vara i olika delar av processen:

- rekylen pagar fortfarande
- saljarna tappar kraft
- kopare har borjat komma tillbaka
- caset bryter redan upp
- caset ar overstrackt och sent
- pullbacktesen har misslyckats

Trade-planen ska darfor ha ett separat och smalt begrepp:

```text
setup_evolution
```

Detta ska hjalpa `plan_status`, `setup_class`, varningar och textmotivering.
Det ska inte ge en ny heat-score.

## Grundprincip for MVP

`setup_evolution` ska i forsta versionen framst vara ett klassificerings- och
motiveringslager. Det ska hjalpa Eodwin att forsta var caset befinner sig i
pullback-processen, inte vara ett aggressivt filter som stoppar nastan alla
setups.

MVP ska inte krava perfekta candles. En pullback kan vara relevant aven nar
responsen inte ar helt bekraftad. Darfor galler:

- endast `FAILED` och tydligt `RR_BAD` ska vara hart negativa i MVP
- `PULLING_BACK` ska normalt overleva som `WATCH_PLAN`, inte `NO_PLAN`
- `STABILIZING` ska normalt overleva som `WATCH_PLAN`, inte `NO_PLAN`
- `RESPONDING` kan bli `READY_PLAN` om scoring, pullback-location och
  preliminar risk/reward ar rimliga
- `BREAKING_OUT` ska granskas efter kontext, inte automatiskt klassas som for
  sent
- `EXTENDED` ar en varning om Pullback-entryzon och risk/reward, inte ett
  omdome om att aktien ar dalig

Trade-planen ska alltsa forklara processlage och risk/reward-hypotes innan den
avstar. Om caset inte ar trasigt och inte har tydligt dalig risk/reward ska
MVP hellre luta mot `WATCH_PLAN` an `NO_PLAN`.

## Setup evolution-klasser

Forsta klassificering:

```text
PULLING_BACK
STABILIZING
RESPONDING
BREAKING_OUT
EXTENDED
FAILED
```

### PULLING_BACK

Rekylen pagar fortfarande.

Typisk bild:

- flera av de senaste 5 dagarna ar roda eller stanger svagt
- close ligger lagre an for nagra dagar sedan
- pullback_depth_20d_pct blir mer negativ
- distance_to_sma20_atr eller distance_to_sma50_atr ror sig nedat
- close_position_in_range ar ofta lag eller blandad
- volym pa nedgang kan vara normal eller hog

Planimplikation:

```text
Ofta WATCH_PLAN. Caset kan vara intressant, men trade-planen ska vanta pa
stabilisering eller respons.
```

### STABILIZING

Rekylen verkar bromsa in, men koparna har inte tydligt tagit over.

Typisk bild:

- senaste 3-5 dagarna visar mindre falltakt
- ranges krymper eller blir mer normala relativt ATR
- close_position_in_range forbattras fran svaga nivaer men ar inte stark varje
  dag
- lokalt 5-10 dagars low haller eller testas utan tydlig breakdown
- distance_to_sma20_atr eller distance_to_sma50_atr planar ut
- volymen ar inte tydlig distributionsvarning

Planimplikation:

```text
Ofta WATCH_PLAN. Kan bli READY_PLAN senare om kopare visar tydligare respons
och riskpunkten verkar definierbar.
```

### RESPONDING

Kopare har borjat komma tillbaka efter rekyl.

Typisk bild:

- senaste dagen eller senaste 2-3 dagarna har starkare close_position_in_range
- minst en tydlig gron candle efter rekyl
- close har borjat rora sig upp fran lokalt 5-10 dagars low
- distance_to_sma20_atr eller distance_to_sma50_atr ror sig upp fran
  pullbackzonen
- volym_vs_avg20 ar normal till stark pa responsdag
- dagens range ar inte kaotiskt stor relativt ATR

Planimplikation:

```text
Kan vara READY_PLAN om score, trend och pullback location ocksa ar bra. Kan
vara WATCH_PLAN om responsen ar tidig men inte tillrackligt tydlig.
```

### BREAKING_OUT

Setupen haller pa att lamna pullbackfasen och ga mot continuation eller
breakout.

Typisk bild:

- close nar eller tar ut senaste 5-10 dagars local high
- pullback_depth_20d_pct ror sig nara 0
- priset ar inte langre nara SMA20/SMA50-pullbackzonen
- volymrespons kan vara stark
- senaste candle stanger starkt i dagsrangen

Planimplikation:

```text
Inte automatiskt sent. Om detta ar forsta utbrottsdagen fran en tajt 5-10
dagars struktur, priset fortfarande ar nara pullbackzonen, invalidation verkar
definierbar och RR-hypotesen ar cirka 3:1 eller battre, kan det stoda
READY_PLAN. Om caset redan har flera starka grona dagar efter respons och
stop/invalidation hamnar langt bort, lutar det mot LATE_PLAN.
```

### EXTENDED

Responsen har sprungit for langt for att ge ren pullback-plan.

Typisk bild:

- flera starka grona candles efter rekylen
- close ligger tydligt over SMA20/SMA50-zonen i ATR-termer
- pullback_depth_20d_pct ar nara 0 eller positivt om ny high ar satt
- avstandet till rimlig invalidation skulle bli stort
- risk/reward-hypotesen blir svagare eftersom entryzonen ar borta

Planimplikation:

```text
Varning om att Pullback-entryzonen kan vara borta. Caset kan fortfarande vara
en bra aktie eller passa en annan strategi, men for Pullback v1 blir
risk/reward ofta svagare. Lutar mot LATE_PLAN nar stop/invalidation hamnar for
langt bort, men ar inte automatiskt NO_PLAN.
```

### FAILED

Pullbacktesen ar skadad eller ogiltig.

Typisk bild:

- close bryter tydligt under lokalt 5-10 dagars low
- close ligger langt under SMA50-zonen eller trendstrukturen forsvagas
- pullback_depth_20d_pct blir djup med trend damage
- ranges expanderar nedat
- close_position_in_range ar svag under flera dagar
- responsforsok misslyckas snabbt

Planimplikation:

```text
INVALID_PLAN eller NO_PLAN. Setupen ska inte planeras som Pullback v1.
```

## Deterministiska observationer over 5-10 dagar

Detta ar inte nya indikatorer. Det ar en liten uppsattning enkla observationer
som beraknas fran befintliga rader och MVP-features nar trade-planen skapas.

### Candle-sekvens

Berakna over senaste 5 dagar:

```text
green_count_5d = antal dagar dar close > open
red_count_5d   = antal dagar dar close < open
strong_close_count_5d = antal dagar dar close_position_in_range >= 0.65
weak_close_count_5d   = antal dagar dar close_position_in_range <= 0.35
```

Tolkning:

- fler roda och svaga closes lutar mot `PULLING_BACK` eller `FAILED`
- blandad sekvens med farre svaga closes lutar mot `STABILIZING`
- 1-3 starka grona closes efter rekyl lutar mot `RESPONDING`
- for manga starka grona dagar efter rekyl kan luta mot `EXTENDED`

Detta anvander candle-data men inte candlestickmonster.

### Range contraction och expansion

Berakna over senaste 5 dagar:

```text
range_vs_atr14_today
average_range_vs_atr14_5d
max_range_vs_atr14_5d
```

Tolkning:

- fallande eller normaliserad range efter rekyl lutar mot `STABILIZING`
- normal range med stark close lutar mot `RESPONDING`
- stor nedatrange med svag close lutar mot `FAILED`
- extrem uprange efter flera grona dagar kan luta mot `EXTENDED`

Ingen ny range-indikator skapas; detta anvander befintlig `range_vs_atr14`.

### Volymrespons

Berakna over senaste 5 dagar:

```text
up_volume_response = gron dag med volume_vs_avg20 >= 1.1
thin_response      = gron dag med volume_vs_avg20 < 0.8
down_volume_risk   = rod dag med volume_vs_avg20 >= 1.1 och svag close
```

Tolkning:

- gron respons pa normal/hog volym stoder `RESPONDING`
- tunn studs lutar mot `STABILIZING` eller svag `RESPONDING`
- hog volym pa svag rod dag lutar mot `PULLING_BACK` eller `FAILED`

Om volym saknas ska evolution fortfarande kunna klassificeras, men med varning:

```text
volume_missing_for_evolution
```

### Lokal 5-10 dagars struktur

Berakna fran OHLC:

```text
local_high_10d = hogsta high senaste 10 handelsdagar
local_low_10d  = lagsta low senaste 10 handelsdagar
close_vs_local_high_10d_pct
close_vs_local_low_10d_pct
```

Tolkning:

- close nara local low och svaga candles lutar mot `PULLING_BACK`
- local low testas men haller, med battre closes, lutar mot `STABILIZING`
- close ror sig upp fran local low med stark close lutar mot `RESPONDING`
- close nara eller over local high lutar mot `BREAKING_OUT`
- close under local low med svag range/close lutar mot `FAILED`

Detta ar lokal struktur, inte breakout-strategi. Den anvands bara for att se
var pullbacken befinner sig.

### Forandring i SMA-avstand

Jamfor dagens MVP-features med 3-5 handelsdagar bakat:

```text
distance_to_sma20_atr_delta_3d
distance_to_sma50_atr_delta_3d
distance_to_sma20_atr_delta_5d
distance_to_sma50_atr_delta_5d
```

Tolkning:

- avstand ror sig nedat mot SMA20/SMA50: `PULLING_BACK`
- avstand planar ut nara SMA20/SMA50: `STABILIZING`
- avstand ror sig upp fran zonen: `RESPONDING`
- avstand ror sig snabbt upp och priset ar nara local high: `EXTENDED` eller
  `BREAKING_OUT`
- avstand ror sig langt under SMA50 med svag close: `FAILED`

Detta skapar inte nya trendindikatorer. Det ar en kort historisk jamforelse av
redan definierade MVP-features.

## Enkel klassificeringsordning

Evolution ska klassificeras i en tydlig ordning, sa att utfall blir
deterministiskt.

Forsta prioritet ar skydd, men klassificeringen ska inte i sig vara ett hart
filter:

```text
1. FAILED
2. EXTENDED
3. BREAKING_OUT
4. RESPONDING
5. STABILIZING
6. PULLING_BACK
```

Praktisk tolkning:

- om setupen ar skadad ska den inte kallas stabil och kan bli `INVALID_PLAN`
- om setupen har tydligt `RR_BAD` ska planen kunna avsta
- om setupen ar overstrackt ska den flaggas, men inte automatiskt avfardas som
  dalig aktie
- om priset bryter upp ur pullbackzonen ska kontext avgora mellan
  `READY_PLAN` och `LATE_PLAN`
- om inget av ovanstaende galler men rekylen pagar ska den normalt bli
  `PULLING_BACK` och overleva som `WATCH_PLAN`

## Preliminar beslutstabell

Detta ar en kvalitativ startpunkt for manuell granskning, inte slutlig kod.

```text
Evolution      Typisk planstatus     Typisk setup_class
FAILED         INVALID_PLAN/NO_PLAN  DEEP_PULLBACK eller MOMENTUM_HANDOFF
EXTENDED       LATE_PLAN/WATCH_PLAN  MOMENTUM_HANDOFF eller SHALLOW_PULLBACK
BREAKING_OUT   READY_PLAN/LATE_PLAN  SMA20_PULLBACK, SHALLOW_PULLBACK eller MOMENTUM_HANDOFF
RESPONDING     READY_PLAN/WATCH_PLAN SMA20_PULLBACK eller SMA50_PULLBACK
STABILIZING    WATCH_PLAN            SMA20_PULLBACK eller SMA50_PULLBACK
PULLING_BACK   WATCH_PLAN            SMA20_PULLBACK, SMA50_PULLBACK eller DEEP_PULLBACK
```

Tabellen ar medvetet mjuk. Den ska hjalpa forklaring och prioritering, inte
minska kandidatlistan aggressivt i forsta versionen.

## Koppling till plan_status

### WATCH_PLAN

Passar nar:

- score ar relevant men evolution ar `PULLING_BACK` eller `STABILIZING`
- evolution ar `EXTENDED` men caset inte ar trasigt och RR inte ar tydligt
  dalig
- responsen ar tidig men inte tillrackligt tydlig
- risk/reward-hypotesen kan bli bra, men invalidation eller target ar inte
  tillrackligt tydlig

Exempelmotivering:

```text
Pullback still developing; sellers may be slowing, but buyer response is not
confirmed enough for READY_PLAN.
```

### READY_PLAN

Passar nar:

- scoring ar stark nog for Pullback
- evolution ar `RESPONDING`
- setup_class ar `SMA20_PULLBACK` eller `SMA50_PULLBACK`
- range/gap-risk ar normal
- preliminar risk/reward-hypotes ser ut att kunna bli cirka 3:1 eller battre

`READY_PLAN` kan ocksa passa nar evolution ar `BREAKING_OUT`, om:

- det ar forsta tydliga utbrottsdagen fran en tajt 5-10 dagars struktur
- priset fortfarande ar nara pullbackzonen
- invalidation verkar definierbar utan orimligt avstand
- preliminar RR-hypotes ar cirka 3:1 eller battre

Exempelmotivering:

```text
Buyers responding from pullback zone; local invalidation appears close enough
relative to prior high/continuation target for manual review.
```

`READY_PLAN` ar inte en orderrekommendation. Det betyder att setupen ar
tillrackligt strukturerad for manuell trade-review.

### LATE_PLAN

Passar nar:

- evolution ar `EXTENDED`
- evolution ar `BREAKING_OUT` efter flera starka grona dagar, snarare an
  forsta utbrottsdagen fran tajt struktur
- priset har lamnat pullbackzonen tydligt
- riskpunkten skulle ligga for langt bort
- risk/reward-hypotesen lutar mot cirka 2:1 eller samre

Exempelmotivering:

```text
Pullback response may already have moved into momentum; possible target remains,
but invalidation is now too far away for a clean Pullback plan.
```

### INVALID_PLAN

Passar nar:

- evolution ar `FAILED`
- local low bryts med svag close eller stor nedatrange
- trend damage syns i Pullback-score eller features
- setupen inte langre ar en kontrollerad rekyl

Exempelmotivering:

```text
Pullback thesis damaged; price failed below local support and no clean
invalidation/continuation structure remains.
```

### NO_PLAN

Passar nar:

- scoring ar for lag for Pullback-plan
- data saknas for setup evolution
- caset passar tydligt battre som annan strategi och Pullback-RR ar svag
- setupen ar for kaotisk for rimlig plan
- risk/reward-hypotesen ar tydligt `RR_BAD`

`NO_PLAN` ska anvandas forsiktigt i MVP. `PULLING_BACK` och `STABILIZING` ska
normalt inte bli `NO_PLAN` bara for att responsen saknas; de ska hellre bli
`WATCH_PLAN`.

Exempelmotivering:

```text
No Pullback trade plan; current structure does not offer a clean pullback
process or acceptable preliminary risk/reward.
```

## Koppling till setup_class

Evolution ska forfina, inte ersatta, setup_class.

```text
SMA20_PULLBACK
```

Passar nar pullbacken ar grund till normal, priset ar nara SMA20-zonen i
ATR-termer och evolution ar `STABILIZING` eller `RESPONDING`.

```text
SMA50_PULLBACK
```

Passar nar rekylen ar djupare men fortfarande konstruktiv, priset ar nara
SMA50-zonen i ATR-termer och evolution inte ar `FAILED`.

```text
SHALLOW_PULLBACK
```

Passar nar scoring ar stark men faktisk rekyl ar grund. Evolution avgor om den
ar tidig watch, sen continuation eller momentum-handoff.

```text
DEEP_PULLBACK
```

Passar nar rekylen ar djup och kraver extra skadegranskning. `STABILIZING` kan
ge WATCH_PLAN, men `FAILED` ger INVALID_PLAN.

```text
MOMENTUM_HANDOFF
```

Passar nar evolution ar `BREAKING_OUT` eller `EXTENDED`, eller nar Pullback
inte langre ar basta beskrivning av caset.

`MOMENTUM_HANDOFF` betyder inte att caset ar daligt. Det betyder att Pullback
v1 kanske inte langre ar basta planeringsramen, sarskilt om RR for Pullback har
forsamrats.

## Preliminar risk/reward-hypotes

Trade-plan v1 ska inte rakna exakt entry, stop eller target i detta steg.
Den ska daremot kunna uttrycka en preliminar risk/reward-hypotes for att
forklara planstatus.

Grundide:

```text
rimlig risk = avstand till lokal invalidation eller pullbackzon
rimlig reward = avstand till tidigare high eller fortsatt trend/continuation
```

I MVP ska detta vara textuell och grov:

```text
RR_GOOD       Setupen verkar kunna erbjuda cirka 3:1 eller battre.
RR_MEDIOCRE   Setupen verkar snarare erbjuda cirka 2:1 eller samre.
RR_UNCLEAR    Datan/processen racker inte for rimlig hypotes.
RR_BAD        Invalidation ar for langt bort eller target ar for nara.
```

### RR_GOOD

Typisk kombination:

- evolution ar `RESPONDING`
- evolution ar forsta konstruktiva `BREAKING_OUT` fran tajt 5-10 dagars
  struktur
- priset ar fortfarande nara rimlig SMA20/SMA50-pullbackzon
- local low eller pullbackzon verkar ge nara invalidation
- tidigare 20D-high eller local high ligger tillrackligt langt bort
- range/gap-risk ar normal

Planimplikation:

```text
Kan stoda READY_PLAN for manuell review.
```

### RR_MEDIOCRE

Typisk kombination:

- evolution ar `STABILIZING`, `BREAKING_OUT` eller tidig `EXTENDED`
- target-hypotes finns, men priset har redan rort sig en bit
- invalidation skulle hamna relativt langt bort
- setupen kan vara intressant men inte ren nog

Planimplikation:

```text
Lutar mot WATCH_PLAN eller LATE_PLAN.
```

### RR_BAD

Typisk kombination:

- evolution ar `FAILED`
- evolution ar tydligt `EXTENDED` efter flera starka grona dagar
- priset ar langt fran rimlig invalidation
- tidigare high ligger for nara for att motivera risken
- range/gap-risk gor planeringen opraktisk

Planimplikation:

```text
Lutar mot NO_PLAN, LATE_PLAN eller INVALID_PLAN.
```

### RR_UNCLEAR

Typisk kombination:

- for lite 5-10 dagars data
- volym saknas och candlebilden ar blandad
- local high/low ger ingen tydlig struktur
- score ar relevant men setupens process ar otydlig

Planimplikation:

```text
Lutar mot WATCH_PLAN eller NO_PLAN beroende pa scoringstyrka.
```

## Outputkontrakt

Framtida output bor vara deterministisk och sparbar:

```text
date
symbol
strategy_id
source_scoring_model
source_heat
source_status
plan_status
setup_class
setup_evolution
rr_hypothesis
evolution_comment
risk_reward_note
warnings
comment
```

Senare kan detta utokas med:

```text
trigger_note
invalidation_note
target_note
position_size_note
```

Dessa senare falt ska inte specificeras i detalj forran setup evolution och
planstatus har granskats manuellt.

## Exempel pa deterministiska kommentarer

```text
PULLING_BACK:
Pullback still developing; recent candles remain weak and price is moving
toward the MA support zone.

STABILIZING:
Pullback is stabilizing near the support zone; sellers appear to be losing
pressure, but buyer response is not yet confirmed.

RESPONDING:
Buyers are responding from the pullback zone with stronger closes and acceptable
range/volume behavior.

BREAKING_OUT:
Price is pressing back toward the local high; if this is the first move out of
a tight pullback structure and RR remains good, it can still support READY_PLAN.

EXTENDED:
Response may have moved far from the pullback zone; this is a warning about
Pullback RR, not proof that the stock is bad.

FAILED:
Pullback thesis is damaged by weak closes and break below local support.
```

## Manuell granskningsplan

Innan kodning ska denna design granskas pa ett litet urval:

- en tydlig `PULLING_BACK`
- en tydlig `STABILIZING`
- en tydlig `RESPONDING`
- en ticker som ar `BREAKING_OUT`
- en `EXTENDED` kandidat som scoring fortfarande gillar
- en `FAILED` kandidat med trend damage

Fragor att besvara:

- Skiljer evolution-klasserna faktiskt olika steg i pullback-processen?
- Ger `RESPONDING` battre trade-plan-lage an `PULLING_BACK`?
- Fanger `EXTENDED` de case dar heat ar hog men entryzonen ar borta?
- Ar `FAILED` tillrackligt forsiktig utan att bli ett hardt stop for allt?
- Hjalper RR-hypotesen till att forklara `READY_PLAN` kontra `LATE_PLAN`?

## Filtereffekt i forsta implementationen

Forsta implementationen ska mata hur harda reglerna blir innan de skarps.

Efter varje korning bor Eodwin kunna visa en enkel sammanstallning per datum:

```text
date
total_pullback_candidates
count_by_setup_evolution
count_by_plan_status
count_by_rr_hypothesis
```

Syftet ar att upptacka om `PULLBACK_TRADE_PLAN_V1` filtrerar bort for manga
setups for tidigt.

Exempel pa kontrollfragor:

- Blir nastan alla kandidater `NO_PLAN`?
- Blir `PULLING_BACK` och `STABILIZING` normalt kvar som `WATCH_PLAN`?
- Blir `BREAKING_OUT` alltid `LATE_PLAN`, aven nar det bara ar forsta
  utbrottsdagen fran tajt struktur?
- Blir `EXTENDED` en automatisk dom, i stallet for en RR-varning?
- Ar `READY_PLAN` sa strikt att den nastan aldrig uppstar?

Om sammanstallningen visar att modellen ar for hard ska trosklar och
beslutstabeller justeras innan entry, stop, target eller position sizing
specificeras.

## Rekommenderat nasta steg

Nasta steg ar att skapa en kvalitativ beslutstabell for:

```text
input:  PULLBACK_SCORING_V1 breakdown
        senaste 5-10 dagars OHLCV
        senaste 5-10 dagars MVP-features

output: setup_evolution
        plan_status
        setup_class
        rr_hypothesis
        warnings
```

Forst efter manuell chart review ska detta kodas. Entry, stop, target och
position sizing ska fortfarande vanta.

Forsta kodade versionen ska ocksa innehalla sammanstallningen av filtereffekt
per datum. Den ska anvandas som sanity check innan reglerna skarps.
