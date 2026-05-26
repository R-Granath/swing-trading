# Strategy Development Method v1

Detta dokument beskriver hur Eodwin ska bygga, utvardera och forfina
strategier. Syftet ar att skapa en metod som ar praktisk i MVP, men som ocksa
kan vaxa nar backtest, mer data och journalutfall finns pa plats.

Grundprincipen ar enkel:

```text
tradingide -> teori/litteraturcheck -> featuredefinitioner -> scoringhypotes
-> manuell granskning -> kodad modell -> backtest -> kalibrering -> live/journal
```

LLM, litteratur och backtest har olika roller. Ingen av dem ska ensam bestamma
strategin.

## Mal

Metoden ska hjalpa Eodwin att:

- oversatta trader-sprak till kodbara regler
- skilja mellan harda krav, mjuka poang och forklarande observationer
- undvika att enskilda tumregler blir dogmer
- dokumentera varfor en strategi ser ut som den gor
- gora scoringmodeller testbara och versionerade
- forfina modeller med historiska data utan att overanpassa dem

## Kunskapskallor

### LLM

LLM far anvandas for att:

- strukturera strategiideer
- foresla features som kan mata strategins logik
- oversatta uttryck som "nara SMA20" till matematiska hypoteser
- identifiera risker, specialfall och saknade definitioner
- skriva forklarande kommentarer och anvandartexter
- hjalpa till att jamfora strategiideer med kand teknisk analys

LLM ska inte anvandas som ensam sanningskalla for tradingedge. Om modellen
foreslar en regel ska den behandlas som en hypotes, inte som facit.

### Litteratur och etablerad teknisk analys

Litteratur och etablerad marknadsteori ska anvandas som rimlighetscheck.
Sarskilt relevant ar forskning om:

- trendfoljning
- momentum
- moving-average-regler
- trading range breakouts
- teknisk monsterigenkanning
- data-snooping och falska positiva resultat

Litteraturen ska hjalpa oss att valja startpunkter och undvika uppenbart svaga
antaganden. Den ska inte ersatta testning pa Eodwins egen data, marknad och
tidshorisont.

Exempel pa referenspunkter:

- [Brock, Lakonishok och LeBaron (1992)](https://ideas.repec.org/a/bla/jfinan/v47y1992i5p1731-64.html):
  moving-average- och trading-range-regler
- [Lo, Mamaysky och Wang (2000)](https://ideas.repec.org/a/bla/jfinan/v55y2000i4p1705-1765.html):
  algoritmisk teknisk monsterigenkanning
- [Sullivan, Timmermann och White (1999)](https://ideas.repec.org/a/bla/jfinan/v54y1999i5p1647-1691.html):
  data-snooping i tekniska tradingregler
- [Marshall, Young och Rose (2006)](https://www.sciencedirect.com/science/article/pii/S0378426605002116):
  svagare evidens for rena candlestick-regler

### Manuell granskning

Innan backtest finns ska manuell granskning vara en viktig kontroll. Den ska
inte avgora om en strategi ar lonsam, men den kan upptacka om modellen beter sig
orimligt.

Manuell granskning ska svara pa fragor som:

- ser toppkandidaterna ut som strategin sager?
- missar modellen uppenbart intressanta kandidater?
- far svaga kandidater for hog heat?
- beror heat pa ratt saker?
- ar kommentarerna begripliga och arliga?

### Backtest

Nar backtestmodulen finns ska den anvandas for att kalibrera och ifragasatta
scoringmodeller.

Backtest ska kunna hjalpa till att:

- justera vikter och trosklar
- jamfora alternativa scoringversioner
- mata tradeoff mellan traffsakerhet, antal kandidater och risk
- testa regler i olika marknadsregimer
- identifiera overanpassade eller onodiga features
- avgora om en regel ska vara hard stop, mjuk poang eller bara forklaring

Backtest ska inte anvandas for att blint optimera fram maximal historisk
avkastning. En regel som bara fungerar efter manga parameterforsok ska betraktas
med misstanksamhet.

### Live- och journalutfall

Senare ska Eodwins journal och verkliga anvandarutfall kunna anvandas som extra
feedback. Detta ar sarskilt viktigt eftersom en strategi inte bara ska hitta
tekniska setups, utan ocksa vara praktiskt handelbar for anvandaren.

Live- och journaldata kan hjalpa till att svara pa:

- vilka strategier anvandaren faktiskt kan folja disciplinerat
- vilka setups som ofta ser bra ut men ar svara att handla
- om foreslagna entry-, stop- och targetnivaer ar realistiska
- om vissa signaler leder till for manga falska starter

## Strategins arbetsflode

Varje strategi bor utvecklas i samma ordning.

### 1. Beskriv ideal setup

Borja med att beskriva hur en perfekt setup ser ut i marknadstermer.

Exempel for pullback:

- etablerad upptrend
- kontrollerad rekyl mot relevant medelvarde eller stod
- trendnivan haller
- volatiliteten ar rimlig
- kopare borjar komma tillbaka
- caset ar inte redan overstrackt

Detta steg ska vara begripligt for en manniska.

### 2. Dela upp i komponenter

Bryt ner strategin i komponenter som kan poangsattas.

Exempel:

- trend/regim
- setup-form
- risk/volatilitet
- timing/candle
- volym/bekraftelse
- datakvalitet

Komponenterna ska forklara varfor heat blir hogt eller lagt.

### 3. Definiera features

Varje kvalitativ ide ska oversattas till en eller flera features.

Exempel:

```text
"nara SMA20" -> close_vs_sma20_pct
"lutar upp" -> sma20_slope_5d
"stanger starkt" -> close_position_in_range
"rekyl ar inte panikartad" -> range_vs_atr14 och atr14_pct
```

Featuredefinitioner ska vara stabila, testbara och ateranvandbara mellan
strategier.

### 4. Bestam hard stop, mjuk poang eller observation

Inte alla regler ska vara grindar.

Hard stop ska anvandas for:

- saknad eller trasig data
- for kort historik
- extrem risk som gor caset praktiskt olampligt
- strategi-specifika lage dar setupen uppenbart inte finns

Mjuk poang ska anvandas for:

- trendstyrka
- narhet till medelvarde
- candle-bekraftelse
- volatilitet
- volym
- grad av overstrackning

Observation ska anvandas for:

- saker som ar intressanta men osakra
- tidiga signaler som inte ska styra heat tungt
- forklaringar till anvandaren

### 5. Formulera heat 100

Varje strategi ska ha en tydlig definition av vad som ger nara maximal heat.
Det betyder inte att caset ar garanterat bra, bara att det matchar strategins
egen setup mycket val.

En heat 100-definition ska beskriva:

- marknadsregim
- prisets lage
- rekylens eller breakoutens kvalitet
- risklage
- timing
- eventuell volymbekraftelse
- vad som skulle dra ner heat

### 6. Formulera poangkurvor

Nar mojligt ska scoring vara gradvis, inte binar.

Exempel:

```text
1 gron candle efter rekyl  -> lite timingplus
2 grona candles            -> mer timingplus
3 grona candles            -> stark timingbekraftelse
4+ grona candles           -> mindre pullbackplus, mojlig overstrackning
```

Detta gor att modellen kan visa nara kandidater och samtidigt flytta heat
mellan strategier nar marknadslaget forandras.

### 7. Koda deterministiskt

Nar strategin ar dokumenterad ska Python-koden folja dokumentet sa nara som
mojligt.

Koden ska:

- berakna features deterministiskt
- ge samma heat for samma input
- returnera positiva och negativa poangdrivare
- vara enkel att testa med kontrollerade exempel
- inte anvanda LLM i sjalva scoringbeslutet

LLM kan senare anvandas for forklaring av ett resultat, men heat ska komma fran
testbar kod.

### 8. Granska kandidater

Forsta kodade versionen ska granskas pa riktiga EOD-data.

Vi ska sarskilt titta pa:

- toppkandidater per strategi
- kandidater runt `WATCH`/`CANDIDATE`-gransen
- aktier som far hog heat av fel anledning
- aktier som visuellt ser intressanta ut men far lag heat
- om flera strategier konkurrerar pa ett begripligt satt

### 9. Backtesta och kalibrera

Nar backtest finns ska varje strategi testas med sparad scoringversion.

Backtest ska helst jamfora:

- originalversion mot justerade versioner
- olika heat-trosklar
- olika entry- och exitvarianter
- olika marknadsregimer
- olika tickergrupper

En forbattring ska bedomas pa flera matt, inte bara total avkastning.

Exempel pa matt:

- antal kandidater
- hit rate
- genomsnittlig vinst/forlust
- maximal drawdown
- risk/reward
- expectancy
- tid i trade
- kanslighet for transaktionskostnader

## Versionering

Varje scoringmodell ska ha en tydlig version.

Exempel:

```text
PULLBACK_SCORING_V1
MOMENTUM_SCORING_V1
STRATEGY_SCORING_ENGINE_V1
```

Nar en signal sparas bor den kunna kopplas till:

- scoringmodellens version
- strategi-id
- heat
- status
- featurevarden vid scoringtillfallet
- viktigaste positiva och negativa poangdrivare

Det gor det mojligt att senare forsta varfor en kandidat valdes, aven om
modellen har andrats.

## Forsiktighetsprinciper

Eodwin ska vara praktisk, men inte overmodig.

Viktiga risker:

- overanpassning till historisk data
- for manga parametrar for tidigt
- for harda regler som doljer bra nara-kandidater
- for mjuka regler som ger for manga mediokra kandidater
- candlestick-regler som far for stor tyngd utan stottande kontext
- modeller som ser bra ut i backtest men ar svara att handla manuellt

Darfor ska MVP hellre borja med fa, begripliga och robusta features an manga
smarta specialregler.

## Praktisk startordning

Rekommenderad ordning for Eodwin:

1. Dokumentera denna generella metod.
2. Skapa `pullback_scoring_spec_v1.md` som forsta strategispecifikation.
3. Definiera features som Pullback v1 behover.
4. Koda features och enkel pullback-scoring.
5. Inspektera kandidater manuellt via CLI.
6. Justera uppenbara missar utan att optimera for hart.
7. Upprepa metoden for Momentum och Breakout.
8. Bygg backtest nar scoringresultat och tradeplanlogik ar stabilare.
