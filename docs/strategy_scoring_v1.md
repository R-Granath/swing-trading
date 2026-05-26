# Strategy Scoring v1

Detta dokument beskriver forsta riktningen for Eodwins nya strategiscreening.
Syftet ar att ga fran hard routing till mjukare scoring, dar varje ticker kan
bedomas mot flera long-only-strategier och rankas efter hur val setupen passar.

Dokumentet ar ett designunderlag, inte ett facit. Regler, vikter och features
ska justeras nar vi ser verkliga kandidater, backtester och anvandarfeedback.

Arbetssattet for att bygga och forfina strategier beskrivs i
`docs/strategy_development_method_v1.md`.

## Varfor mjuk scoring

Eodwin ska separera data, features, scoring och presentation:

```text
data -> features -> scoring -> presentation
```

Det gor modellen lattare att testa, forklara och forbattra over tid.

Tidigare designarbete visade samtidigt att for hard routing riskerar att dolja
intressanta nara-kandidater. En modell som bara godkanner exakt matchande setups
kan bli for tyst, sarskilt i en tidig MVP dar vi fortfarande lar oss hur
strategierna beter sig pa riktiga EOD-data.

Darfor ska MVP anvanda mjuk scoring:

- varje ticker bedoms mot flera strategier
- varje ticker far heat per strategi
- hogst heat blir `BestStrategy`
- topp 2-3 strategier kan visas som alternativ
- nara kandidater kan visas som `WATCH` i stallet for att forsvinna

Pa sa satt kan systemet rangordna starka kandidater och samtidigt ge anvandaren
mer nyanserad information.

Hard stop ska anvandas sparsamt och bara nar det skyddar modellen:

- for lite eller trasig data
- saknade nyckelpriser eller indikatorer
- extrem volatilitet eller uppenbar gap-/riskavvikelse
- likviditetsproblem nar volymdata finns

## MVP-strategier

Forsta versionen ar long-only. Korta strategier ingar inte i MVP eftersom de ar
svare att handla praktiskt pa anvandarens tillgangliga plattformar.

Prioriterad ordning:

1. Pullback i upptrend
2. Momentum / continuation
3. Breakout
4. Volatility compression
5. Early trend

Senare eller forsiktigare:

6. Mean reversion
7. Gap

Alla strategier ska ge en heat-score mellan 0 och 100. En ticker kan darfor ha
flera relevanta strategier samtidigt, till exempel `PULLBACK 82` och
`MOMENTUM 71`.

## Gemensamt featurelager

Strategierna ska bestalla features i stallet for att vi bygger alla indikatorer
i blindo. Samtidigt behovs ett litet gemensamt featurelager som kan anvandas av
flera strategier.

Basfeatures:

- `close`
- `volume`
- `sma20`
- `sma50`
- `sma200`
- `atr14`
- `atr14_pct`

Relationer:

- `close_vs_sma20_pct`
- `close_vs_sma50_pct`
- `close_vs_sma200_pct`
- `sma20_vs_sma50_pct`
- `sma50_vs_sma200_pct`

Indikatorrorelse over tid:

- `sma20_slope_5d`
- `sma50_slope_10d`
- `sma200_slope_20d`
- `atr14_pct_change_5d`
- `sma20_vs_sma50_pct_change_5d`
- `sma50_vs_sma200_pct_change_20d`

Range och candle:

- `range_pct`
- `close_position_in_range`
- `body_pct_of_range`
- `range_vs_atr14`

Event och struktur senare:

- `breakout_20d`
- `range_position_20d`
- `volume_vs_avg20`
- `gap_pct`

Den stora forbattringen jamfort med den gamla agenten ar att indikatorer sparas
dag for dag i SQLite. Det gor att Eodwin kan analysera riktning och acceleration
i indikatorer, inte bara dagens absoluta varde.

## SMA200 som regimfilter

SMA200 ska anvandas som ett langsiktigt trend- och regimfilter. Det ska paverka
scoring och riskklass, men inte alltid vara ett hart entrykrav.

Exempel:

- pris over SMA200 ger plus for trendfoljande strategier
- SMA50 over SMA200 ger plus for etablerad upptrend
- fallande SMA200 kan dra ner heat eller hoja risk
- pris langt under SMA200 kan vara hard stop for vissa trendstrategier
- mean reversion kan senare fa annan logik

## Heat-modell

Forsta generella komponentmodell:

```text
Trend/regim         0-25
Setup-form          0-25
Risk/volatilitet    0-20
Timing/candle       0-15
Volym/bekraftelse   0-10
Datakvalitet        0-5
```

Varje strategi far egna vikter och tolkningar av komponenterna. Summan ska bli
0-100 och bor vara latt att forklara i output.

Rekommenderade statusnivaer:

```text
80-100  HOT
65-79   CANDIDATE
50-64   WATCH
0-49    LOW
```

Status ar bara en presentationshjalp. Sortering sker pa heat.

## Pullback heat

Pullback ska hitta aktier i upptrend som rekylerat kontrollerat mot relevanta
medelvarden.

Positiva signaler:

- close over SMA200
- SMA50 over SMA200
- SMA20 och SMA50 lutar upp
- close ligger nara SMA20 eller SMA50
- close ar inte for langt under SMA50
- ATR14_pct ar normal for aktien
- senaste candle stanger starkt i sin dagsrange

Negativa signaler:

- priset ar overstrackt ovanfor SMA20/SMA50
- extrem ATR14_pct
- stort negativt gap
- close langt under SMA50
- fallande SMA50 eller tydligt svag regim

## Momentum heat

Momentum ska hitta aktier dar trend och prisrorelse redan ar starka, men utan
att aktien ar sa overstrackt att risken blir orimlig.

Positiva signaler:

- close over SMA20, SMA50 och SMA200
- SMA20 over SMA50 over SMA200
- SMA20 och SMA50 lutar upp
- close nara senaste hogre range
- volym over normalt snitt nar volymfeature finns
- candle stanger i ovre delen av dagsrangen

Negativa signaler:

- avstand till SMA20/SMA50 ar extremt
- ATR14_pct sticker ivag
- flera svaga candles efter uppgang
- trendregimen ar oklar

## Breakout heat

Breakout ska hitta aktier som bryter eller ligger nara ett viktigt intervall.

Positiva signaler:

- close nara eller over 20D-high
- hog `range_position_20d`
- volym over snitt nar volymfeature finns
- candle stanger nara high
- ATR14_pct ar hanterbar
- langsiktig trend ar positiv eller neutral

Negativa signaler:

- breakout sker med kaotisk range
- stangning svagt i dagsrangen
- priset ar mycket overstrackt
- ingen volymbekraftelse nar volymdata finns

## Volatility compression heat

Volatility compression ska hitta aktier dar volatiliteten faller medan priset
haller sig i ett konstruktivt lage.

Positiva signaler:

- ATR14_pct faller
- daily range krymper
- close haller sig over SMA50/SMA200
- SMA20 och SMA50 konvergerar eller planar positivt
- ingen tydlig failure-candle
- ingen stor gap-risk

Negativa signaler:

- kompression sker under fallande SMA200
- close tappar viktiga medelvarden
- ATR14_pct stiger snabbt
- range expanderar nedat

## Early trend heat

Early trend ska hitta tidiga trendforsok innan de blivit fullt etablerade.

Positiva signaler:

- close atertar SMA20 eller SMA50
- SMA20 borjar luta upp
- avstandet mellan SMA20 och SMA50 forbattras
- SMA50 planar ut eller borjar stiga
- close_position_in_range ar stark
- ATR14_pct ar inte extrem

Negativa signaler:

- priset ar fortfarande langt under SMA200
- SMA50 och SMA200 faller tydligt
- uppgangen drivs av en ensam extrem candle
- risk/reward blir dalig pa grund av stor range

## Output i MVP

Screeningoutput ska visa hogsta strategin och minst en alternativ strategi nar
det ar relevant.

Exempel:

```text
Ticker      BestStrategy   Heat   NextBest       Comment
ABB.ST      PULLBACK       82     MOMENTUM 71    Uptrend, near SMA20, normal ATR
VOLV-B.ST   BREAKOUT       76     EARLY_TREND 65 Breaking 20D range with volume support
```

Kommentarer ska vara korta och deterministiskt byggda av de viktigaste
poangdrivarna. LLM kan senare anvandas for pedagogisk forklaring, men sjalva
scoringen ska vara deterministisk och testbar.

## Modellens livscykel

Strategy Scoring v1 ar en forsta praktisk modell, inte en slutgiltig sanning.
Den ska vara enkel nog att forsta, testa och inspektera pa riktiga EOD-data.

I MVP satts vikter och trosklar manuellt utifran strategiide, teknisk logik och
visuell granskning av kandidater. Nar backtestmodulen finns pa plats ska samma
modell kunna forfinas med historiska resultat.

Backtester kan senare anvandas for att:

- justera viktningen mellan trend, setup, volatilitet, candle och volym
- identifiera vilka features som faktiskt hjalper per strategi
- hitta rimliga heat-trosklar for `HOT`, `CANDIDATE` och `WATCH`
- jamfora strategiresultat over olika marknadsregimer
- upptacka regler som ar for harda, for svaga eller overanpassade

Scoringmodellen bor darfor versioneras. En framtida kandidat eller trade ska
kunna kopplas till vilken scoringversion som anvandes nar signalen skapades.

Praktiskt kan detta senare innebara att screeningresultat sparar exempelvis:

- `scoring_model_version`
- `strategy_id`
- `heat`
- `status`
- viktigaste positiva och negativa poangdrivare
- vilka featurevarden som anvandes vid scoringtillfallet

## Nasta kodsteg

Rimlig teknisk ordning:

1. Lagg till `ATR14` och `ATR14_pct` i indikatorlagret.
2. Bygg ett featurelager ovanpa priser och sparade indikatorer.
3. Implementera relationsfeatures for SMA20/SMA50/SMA200.
4. Lagg till slope-features baserade pa dagliga indikatorvarden i SQLite.
5. Skapa forsta screeningmodellen for `PULLBACK` och `MOMENTUM`.
6. Lagg till CLI-kommando for att visa screeningresultat.

Forsta kodversionen kan vara enkel. Det viktiga ar att den producerar en
rankad lista med `BestStrategy`, `heat`, status och kort anledning, sa att vi
kan inspektera om modellen beter sig rimligt pa riktiga EOD-data.
