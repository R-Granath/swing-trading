# Pullback Scoring Spec v1

Detta dokument beskriver forsta specifikationen for Eodwins long-only
pullback-scoring.

Specen foljer `docs/strategy_development_method_v1.md` och ska anvandas som
underlag nar Pullback v1 senare kodas i Python. Den beskriver hur en ticker ska
rankas mot pullback-strategin. Den beskriver inte hela trade-strategin.

## Strategi-id

```text
PULLBACK_SCORING_V1
```

## Scoring kontra full strategi

Pullback-scoring svarar pa fragan:

```text
Hur val passar denna ticker just nu som pullback-kandidat?
```

Den fulla strategin kommer senare att beskriva:

- entry-logik
- stop-loss
- target
- risk/reward
- position sizing
- hur target kan justeras vid mycket starka forhallanden
- hur en aktiv trade ska foljas upp

Scoring ska alltsa inte forsoka losa hela trade-planen. Den ska rangordna
kandidater sa att Eodwin och anvandaren kan fokusera pa de mest relevanta
setuperna.

## Teoretisk utgangspunkt

En bra pullback ar inte summan av losa indikatorer. Den ar en sekvens:

```text
1. Det fanns tydlig styrka innan rekylen.
2. Priset rekylerar mot ett rimligt omrade.
3. Rekylen skadar inte huvudtrenden.
4. Kopare borjar komma tillbaka.
5. Risk och tradability ar rimliga.
```

Pullback v1 ska darfor byggas runt beroenden mellan block, inte runt fristaende
bonuspoang.

## Evidence map

Denna tabell visar hur olika delar av modellen forankras.

| Del | Roll i Pullback v1 | Evidenslage |
| --- | --- | --- |
| Trend / prior strength | Karnan. Utan tidigare styrka finns ingen trend-pullback. | Starkast stod. Momentum och trendfoljning har bred empirisk litteratur, till exempel [Jegadeesh & Titman 1993](https://ideas.repec.org/a/bla/jfinan/v48y1993i1p65-91.html), [Moskowitz, Ooi & Pedersen](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2089463) och [Hurst, Ooi & Pedersen](https://www.aqr.com/insights/research/journal-article/a-century-of-evidence-on-trend-following-investing). |
| Moving averages / trend filter | Praktisk proxy for trend, regim och dynamiskt stod. | Indirekt stod. Enkla moving-average- och trading-range-regler ar studerade, bland annat [Brock, Lakonishok & LeBaron 1992](https://finance.martinsewell.com/stylized-facts/distribution/BrockLakonishokLeBaron1992.pdf). Exakt SMA20/SMA50-narhet ar daremot en praktisk hypotes. |
| Pullback location | Avgor om priset faktiskt erbjuder en rekyl i stallet for chase. | Blandat/indirekt stod. Nara tidigare high har momentum- och referenspunktsstod, se [George & Hwang 2004](https://www.bauer.uh.edu/TGeorge/papers/gh4-paper.pdf). Exakta rekylband maste valideras lokalt. |
| Volume confirmation | Bekraftar att aterkomsten har deltagande, inte bara en liten candle. | Rimligt stod. Volym innehaller information utover pris enligt [Blume, Easley & O'Hara 1994](https://ideas.repec.org/a/bla/jfinan/v49y1994i1p153-81.html), och hog volym har kopplats till efterfoljande avkastning i [Gervais, Kaniel & Mingelgrin 2001](https://scholars.duke.edu/publication/773086). |
| Candles | Timingform: visar hur priset stanger och om kopare syns i dagsrangen. | Svagare som ensam edge. Candles ska inte vara hela strategin. Rena candlestick-regler har svagare evidens, se [Marshall, Young & Rose 2006](https://ideas.repec.org/a/eee/jbfina/v30y2006i8p2303-2323.html). |
| Volatility / tradability | Skyddar mot kaotiska eller opraktiska setups. | Risklogik snarare an core edge. Volatilitet bor styra risk och ranking, men inte definiera pullback ensam. |
| Data quality | Teknisk gate. | Ingen tradingedge. Ska inte ge heat-poang. |

Konsekvensen ar att trend och pullback-kvalitet ska vaga mest. Candles ska vaga
minst av signalblocken, och bara fa betydelse i ratt kontext.

## Ideal setup

En ideal pullback har foljande egenskaper:

- aktien hade tydlig styrka innan rekylen
- priset ar i langsiktig eller medellang positiv regim
- SMA20/SMA50/SMA200 visar en konstruktiv trendbild
- priset har rekylerat fran en relevant topp eller range-high
- rekylen ar tillracklig for att ge battre entryzon, men inte sa djup att
  trenden ar skadad
- close ligger vid eller nara en rimlig support-/medelvardszon
- kopare borjar aterkomma genom starkare close, reclaim eller positiv respons
- volymen ger stod for responsen, eller atminstone inte tydlig varning
- ATR/range ar rimlig nog for manuell swing-trading
- caset har inte redan overgatt till momentum eller breakout

## Nar det inte langre ar en bra pullback

En ticker ska rankas lagre som Pullback nar:

- det saknas tydlig prior strength
- priset inte har rekylerat, utan bara fortsatt upp
- rekylen ar sa djup att huvudtrenden verkar skadad
- priset har brutit viktiga trendnivaer med svag respons
- aterkomsten saknar volym eller sker med svag close
- flera starka grona dagar redan har tagit bort entryzonen
- aktien passar battre som `MOMENTUM`, `BREAKOUT` eller `EARLY_TREND`

Detta ar inte harda diskvalificeringar. De betyder att Pullback-heat bor bli
lagre eller att en annan strategi bor ranka hogre.

## Heat 100-definition

En pullback nara heat 100 ska se ut ungefar sa har:

- stark trend/prior strength finns redan innan rekylen
- close ar over SMA200 och SMA50/SMA200-bilden ar konstruktiv
- SMA20 och SMA50 lutar upp
- priset har rekylerat fran en relevant high, men inte brutit ned trenden
- rekylen landar nara stigande SMA20/SMA50 eller annat rimligt stodomrade
- avstandet till SMA20/SMA50 ger fortfarande en praktisk entryzon
- responsen visar att kopare kommer tillbaka
- responsen far stod av volym eller tydligt battre prisbeteende
- ATR/range ar rimlig
- caset ar inte redan for sent eller overstrackt

Heat 100 betyder att setupen matchar Pullback mycket val. Det betyder inte att
traden ska tas automatiskt.

## Sekventiell scoringmodell

Pullback v1 ska anvanda fyra scoreblock:

```text
Trend / prior strength          0-40
Pullback quality / location     0-30
Resumption evidence             0-20
Risk / tradability              0-10
```

Summan ar 0-100.

Datakvalitet ar inte ett scoreblock. Saknad eller trasig data ska ge `NO_SCORE`
eller datavarning, inte plus/minuspoang.

## Beroenden

Pullback-score ska byggas sekventiellt:

```text
Trend -> Pullback location -> Resumption -> Risk/tradability
```

Det betyder:

- Resumption evidence ska inte ensam kunna gora en svag trend till en bra
  pullback.
- Candle- eller volymstyrka ska tolkas som mest vardefull nar trend och
  pullback location redan ar bra.
- En stark trend utan rekyl ar inte en pullback; den kan vara Momentum.
- En bra rekyl utan aterkomst kan vara `WATCH`, men ska normalt inte vara `HOT`.
- Dalig risk/tradability ska dra ner ranking, men ar inte karnan i edgen.

V1 ska undvika generella heat caps. Om en setup saknar viktiga beroenden ska den
fa lagre heat genom scoreblocken. Hard stop anvands bara for datafel eller
uppenbart ogiltig input.

## Data gates

Data gates sker fore scoring.

Ge `NO_SCORE` eller teknisk datavarning for:

- saknad prisrad for scoringdatum
- saknad `open`, `high`, `low` eller `close`
- `high <= low`
- negativa priser
- saknade SMA20/SMA50/SMA200 nar trenddelen ska beraknas
- for kort historik for nodvandiga features

Om volym saknas men prisdata ar komplett kan scoring fortfarande goras, men
`volume_missing` ska markeras och resumption evidence blir mindre saker.

## Featurebehov

### Bas

- `open`
- `high`
- `low`
- `close`
- `volume`
- `sma20`
- `sma50`
- `sma200`
- `atr14`
- `atr14_pct`

### Trend och prior strength

```text
close_vs_sma20_pct  = (close - sma20) / sma20 * 100
close_vs_sma50_pct  = (close - sma50) / sma50 * 100
close_vs_sma200_pct = (close - sma200) / sma200 * 100
sma20_vs_sma50_pct  = (sma20 - sma50) / sma50 * 100
sma50_vs_sma200_pct = (sma50 - sma200) / sma200 * 100

sma20_slope_5d      = (sma20_today - sma20_5d_ago) / sma20_5d_ago * 100
sma50_slope_10d     = (sma50_today - sma50_10d_ago) / sma50_10d_ago * 100
sma200_slope_20d    = (sma200_today - sma200_20d_ago) / sma200_20d_ago * 100

return_20d_pct      = (close - close_20d_ago) / close_20d_ago * 100
return_60d_pct      = (close - close_60d_ago) / close_60d_ago * 100
```

`return_60d_pct` ar en MVP-proxy for prior strength. Senare kan 3-12 manaders
momentum eller 52-week-high-narhet laggas till nar historiken ar langre.

### Pullback location

```text
rolling_high_20d        = hogsta high senaste 20 handelsdagar
pullback_depth_20d_pct  = (close - rolling_high_20d) / rolling_high_20d * 100
distance_to_sma20_atr   = (close - sma20) / atr14
distance_to_sma50_atr   = (close - sma50) / atr14
```

ATR-normaliserade avstand ar ofta battre an fasta procentband eftersom olika
aktier har olika normal volatilitet. Procentband kan anvandas som enklare
fallback i MVP.

### Resumption evidence

```text
close_position_in_range      = (close - low) / (high - low)
body_pct_of_range            = abs(close - open) / (high - low)
is_green_candle              = close > open
consecutive_green_candles    = antal sammanhangande grona candles fram till idag
volume_avg20                 = snittvolym senaste 20 handelsdagar
volume_vs_avg20              = volume / volume_avg20
up_day_volume_vs_avg20       = volume_vs_avg20 nar close > open
down_day_volume_vs_avg20     = volume_vs_avg20 nar close < open
```

Senare kan vi lagga till mer exakt volymanalys, till exempel om responsdagens
volym ar hogre an volymen under rekylens rodagar.

### Risk / tradability

```text
range_pct       = (high - low) / close * 100
range_vs_atr14  = (high - low) / atr14
gap_pct         = (open - previous_close) / previous_close * 100
```

## Trend / prior strength, 0-40

Syfte: mata om aktien har tillracklig tidigare styrka for att pullback ens ska
vara ratt strategi.

Delar:

```text
Long-term regime                 0-12
MA structure                     0-10
Prior price strength             0-10
Slope consistency                0-8
```

### Long-term regime, 0-12

Hog poang nar:

- close ar over SMA200
- SMA200 lutar upp eller ar stabil
- close inte bara ar marginellt over en fallande SMA200

### MA structure, 0-10

Hog poang nar:

- SMA20 > SMA50 > SMA200
- eller SMA20 > SMA50 och SMA50/SMA200-bilden tydligt forbattras

### Prior price strength, 0-10

Hog poang nar:

- `return_20d_pct` eller `return_60d_pct` visar positiv styrka fore rekylen
- priset ar relativt nara en relevant high, utan att vara overstrackt

Detta block ska senare forbattras med 3-12 manaders momentum och/eller
52-week-high-narhet nar langre historik finns.

### Slope consistency, 0-8

Hog poang nar:

- SMA20 lutar upp
- SMA50 lutar upp
- SMA200 inte faller tydligt

## Pullback quality / location, 0-30

Syfte: mata om det faktiskt finns en attraktiv rekyl i en konstruktiv trend.

Delar:

```text
Actual pullback from high         0-10
Location near support/MA zone     0-12
Trend damage control             0-8
```

### Actual pullback from high, 0-10

Hog poang nar:

- priset har backat tillrackligt fran 20D-high for att inte vara chase
- rekylen ar inte sa djup att den ser ut som trendbrott

Startintervall att granska manuellt:

```text
pullback_depth_20d_pct runt -3% till -10% ar ofta mest intressant
pullback_depth_20d_pct nara 0% kan vara Momentum/Breakout snarare an Pullback
pullback_depth_20d_pct under -12% kan vara djup rekyl eller trendbrott
```

Intervallen ska inte hardkodas som sanning. De ar startpunkter for visuell
granskning.

### Location near support/MA zone, 0-12

Hog poang nar:

- close ar nara stigande SMA20 i en stark trend
- eller close ar nara SMA50 i en lugnare/mer mogen trend
- avstandet ar rimligt relativt ATR14

Startprincip:

```text
SMA20-zon passar snabbare/starkare trend
SMA50-zon passar djupare men fortfarande konstruktiv pullback
ATR-normaliserat avstand ar battre an exakt procentband
```

### Trend damage control, 0-8

Hog poang nar:

- close inte ligger langt under SMA50
- SMA20/SMA50-bilden inte har brutit ned kraftigt
- rekylen ser kontrollerad ut snarare an panikartad

## Resumption evidence, 0-20

Syfte: mata om kopare borjar komma tillbaka efter rekylen.

Delar:

```text
Price response / reclaim          0-7
Volume confirmation               0-8
Candle sequence                   0-5
```

Volym vager mer an enskilda candles eftersom den ger information om deltagande.
Candles visar form, volym visar om rorelsen har kraft bakom sig.

### Price response / reclaim, 0-7

Hog poang nar:

- close stanger i ovre delen av dagsrangen
- close atertar SMA20/SMA50 efter att ha testat under eller nara
- dagens close visar tydlig forbattrad respons jamfort med rekylens svaga dagar

### Volume confirmation, 0-8

Hog poang nar:

- gron responsdag sker pa volym over 20D-snitt
- volymen pa responsdagen ar hogre an typiska nedgangsdagar i rekylen
- volymen tyder pa deltagande, inte bara tunn studs

Saknad volym ska inte stoppa scoring, men ska gora resumption evidence mindre
saker.

### Candle sequence, 0-5

`consecutive_green_candles` ska vara en liten timingkurva, inte ett krav.

```text
0 grona candles     pullback kan fortfarande paga
1 gron candle       tidig respons
2 grona candles     tydligare respons
3 grona candles     stark bekraftelse men entry kan borja bli senare
4+ grona candles    mer momentum-karaktar, mindre ren pullback
```

Scoring ska inte belona tre grona candles blint. Tre grona candles ar mest
vardefullt om priset fortfarande ligger i rimlig entryzon och inte ar
overstrackt.

## Risk / tradability, 0-10

Syfte: justera ranking for risk och praktisk handelbarhet.

Delar:

```text
Volatility sanity                 0-4
Range/gap sanity                  0-3
Liquidity/tradability             0-3
```

Hog poang nar:

- ATR14_pct ar rimlig for swing-trading
- dagens range inte ar kaotisk relativt ATR14
- gap inte dominerar setupen
- volym/liquidity verkar tillracklig for manuell handel

Risk/tradability ar inte huvudkallan till edge. Den ska hjalpa Eodwin att
ranka ner opraktiska setups.

## Strategihandoff

Pullback-score ska samspela med andra strategier.

Exempel:

- Stark trend men ingen rekyl: `MOMENTUM` bor troligen ranka hogre.
- Pris nara eller over 20D-high med stark volym: `BREAKOUT` bor troligen ranka
  hogre.
- Svag/langsam forbattrande trend efter botten: `EARLY_TREND` kan ranka hogre.
- Djup nedgang under viktig trendstruktur: Pullback bor ranka lagt.

Detta ar en viktig anledning att undvika harda caps. Om Pullback inte ar basta
tolkning ska en annan strategi kunna vinna ranking naturligt.

## Forklaringsdrivare

Scoringfunktionen ska returnera korta positiva och negativa poangdrivare.

Exempel pa positiva drivare:

- `strong prior trend`
- `constructive MA structure`
- `controlled pullback from recent high`
- `near rising SMA20`
- `near SMA50 support zone`
- `buyers returning on volume`
- `strong close in daily range`
- `normal ATR`

Exempel pa negativa drivare:

- `weak prior trend`
- `no actual pullback`
- `deep pullback with trend damage`
- `weak close in range`
- `response lacks volume`
- `extended after several green candles`
- `possible momentum handoff`
- `missing volume confirmation`
- `invalid data`

## Exempeloutput

```text
Ticker      Strategy   Heat   Status      Comment
ABB.ST      PULLBACK   84     HOT         Strong trend, controlled pullback near SMA20, buyers returning on volume
ERIC-B.ST   PULLBACK   69     CANDIDATE   Constructive trend, deeper SMA50 pullback, early response
INVE-B.ST   PULLBACK   56     WATCH       Good trend and location, but resumption not confirmed
VOLV-B.ST   PULLBACK   43     LOW         Strong stock, but no pullback left; possible momentum handoff
```

## Initial statusnivaer

Anvand samma presentationsnivaer som `strategy_scoring_v1.md`:

```text
80-100  HOT
65-79   CANDIDATE
50-64   WATCH
0-49    LOW
```

For Pullback v1 ska `WATCH` vara viktigt. En ticker med stark trend och bra
location men svag resumption kan vara vard att bevaka, aven om den inte ar
`HOT`.

## Testfall for kodning

Nar Pullback v1 kodas bor tester skapas for minst dessa scenarier:

- stark trend + kontrollerad rekyl + volymrespons ger hog heat
- stark trend utan rekyl ger lagre Pullback och borde passa Momentum battre
- svag trend med stark candle far inte hog Pullback-score
- bra trend och location men ingen resumption blir `WATCH`/lag `CANDIDATE`
- respons pa hog volym ger mer resumption evidence an respons pa tunn volym
- 1-3 grona candles kan oka timing, men bara i ratt kontext
- 4+ grona candles efter rekyl minskar Pullback-fit om entryzonen ar borta
- djup rekyl med trend damage rankas lagre
- trasig OHLC-data ger `NO_SCORE`
- saknad volym ger varning och svagare resumption evidence

## Oppna fragor for manuell granskning och senare backtest

Detta ska granskas innan scoring betraktas som stabil:

- Ska prior strength matas med 20D/60D returns, SMA-struktur, 52-week-high eller
  en kombination?
- Ar 20D-high ratt referens for rekyldjup, eller ska 30D/60D ocksa testas?
- Ska location matas med ATR-avstand snarare an procentband?
- Hur stor roll ska SMA20 ha jamfort med SMA50 i svenska large caps?
- Vilken volymdefinition bast fangar att kopare aterkommer?
- Ar hog volym pa responsdagen viktigare an lag volym under rekylen?
- Hur manga grona dagar ar ofta for sent for Pullback?
- Nar ska Pullback forlora mot Momentum eller Breakout i ranking?
- Vilka heat-nivaer ger rimligt antal kandidater i ett universum om cirka 100
  tickers?

## Rekommenderat nasta steg

Efter denna spec:

1. Skapa `docs/feature_definitions_v1.md` for gemensamma featureformler.
2. Lagg till ATR14 och ATR14_pct i indikatorlagret.
3. Bygg featurefunktioner for trend, pullback location, resumption och risk.
4. Granska ett litet manuellt chartbook-urval innan scoring kodas skarpt.
5. Implementera `PULLBACK_SCORING_V1` forst nar featuredefinitionerna ar stabila.
