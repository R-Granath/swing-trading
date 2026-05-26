# Strategy Development Method v1

Detta dokument beskriver hur Eodwin ska bygga, utvardera och forfina
strategier. Syftet ar att skapa en metod som ar praktisk i MVP, men som ocksa
kan vaxa nar backtest, mer data och journalutfall finns pa plats.

Grundprincipen ar enkel:

```text
tradingide -> teori/evidence map -> ideal setup -> karnforhallanden
-> featuredefinitioner -> scoringhypotes -> manuell granskning
-> kodad modell -> backtest -> kalibrering -> live/journal
```

LLM, litteratur och backtest har olika roller. Ingen av dem ska ensam bestamma
strategin.

En viktig princip ar att scoring inte ska borja med en tabell dar poang delas
ut jamnt mellan indikatorer. Strategin ska forst beskriva vilka forhallanden
som verkligen driver setupen, hur starkt de ar forankrade i teori/litteratur
och vilken roll de ska ha i modellen.

## Mal

Metoden ska hjalpa Eodwin att:

- oversatta trader-sprak till kodbara regler
- skilja mellan harda krav, mjuka poang och forklarande observationer
- undvika att enskilda tumregler blir dogmer
- dokumentera varfor en strategi ser ut som den gor
- gora scoringmodeller testbara och versionerade
- vikta viktiga forhallanden hogre an svaga timingdetaljer
- skilja mellan litteraturforankrade karnantaganden och lokala hypoteser
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
- hjalpa till att bygga en evidence map for varje strategi

LLM ska inte anvandas som ensam sanningskalla for tradingedge. Om modellen
foreslar en regel ska den behandlas som en hypotes, inte som facit.

LLM ska inte sjalv hitta pa slutliga vikter, trosklar eller poangtabeller.
Innan poang satts ska modellen kunna forklara:

- vilket marknadsfenomen regeln forsoker fanga
- om regeln ar karnlogik, timing, riskjustering, observation eller data gate
- vilket stod regeln har i litteratur, etablerad teknisk analys eller lokal
  hypotes
- varfor regeln fortjanar hog eller lag vikt

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

Litteraturens viktigaste roll ar att styra prioritering. Det som har bredare
stod, till exempel trend/momentum, kan fa vara karnkomponent. Det som har
svagare stod, till exempel enskilda candlestick-monster, ska normalt vara
timing eller observation snarare an huvuddelen av score.

Exempel pa referenspunkter:

- [Jegadeesh och Titman (1993)](https://ideas.repec.org/a/bla/jfinan/v48y1993i1p65-91.html):
  momentum i aktier
- [Moskowitz, Ooi och Pedersen](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2089463):
  time-series momentum over flera marknader
- [Hurst, Ooi och Pedersen](https://www.aqr.com/insights/research/journal-article/a-century-of-evidence-on-trend-following-investing):
  lang historik for trendfoljning
- [Brock, Lakonishok och LeBaron (1992)](https://ideas.repec.org/a/bla/jfinan/v47y1992i5p1731-64.html):
  moving-average- och trading-range-regler
- [Lo, Mamaysky och Wang (2000)](https://ideas.repec.org/a/bla/jfinan/v55y2000i4p1705-1765.html):
  algoritmisk teknisk monsterigenkanning
- [Blume, Easley och O'Hara (1994)](https://ideas.repec.org/a/bla/jfinan/v49y1994i1p153-81.html):
  volym som informationsbarare i teknisk analys
- [Gervais, Kaniel och Mingelgrin (2001)](https://scholars.duke.edu/publication/773086):
  hog volym och efterfoljande avkastning
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

### 1. Beskriv strategi och avgransning

Borja med att tydligt saga vad dokumentet beskriver.

Exempel:

- scoring: hur val en ticker passar en strategi just nu
- full strategi: entry, stop-loss, target, risk/reward och trade-uppfoljning

Scoring ska rangordna kandidater. Den ska inte forsoka losa hela trade-planen.
Entry, stop, target och position sizing kan bygga vidare pa scoring, men ska
beskrivas i separata strategi- eller trade-plan-dokument.

### 2. Beskriv ideal setup

Borja med att beskriva hur en perfekt setup ser ut i marknadstermer.

Exempel for pullback:

- etablerad upptrend
- kontrollerad rekyl mot relevant medelvarde eller stod
- trendnivan haller
- volatiliteten ar rimlig
- kopare borjar komma tillbaka
- caset ar inte redan overstrackt

Detta steg ska vara begripligt for en manniska.

### 3. Bygg evidence map

Innan poang satts ska varje strategi ha en evidence map.

En evidence map ska for varje regel eller feature beskriva:

- vilket marknadsfenomen regeln forsoker fanga
- vilken roll regeln har i strategin
- vilket stod regeln har
- om regeln ar karnlogik, sekundar logik, timing, riskjustering, observation
  eller data gate

Exempel pa rolltyper:

```text
core              stor vikt; utan detta finns inte strategin
secondary         relevant, men inte strategins huvudedge
timing            hjalper entry-/bevakningslage, men ska inte bara score
risk/tradability  justerar ranking och praktisk anvandbarhet
observation       visas eller forklaras men styr inte score tungt
data gate         styr om scoring kan goras; ger inte heat-poang
local hypothesis  rimlig ide som maste granskas lokalt
```

Detta steg ska hindra att LLM eller manniskan delar ut poang till indikatorer
bara for att de finns.

### 4. Dela upp i strategiska block

Bryt ner strategin i block utifran vad som faktiskt driver setupen.

Block ska inte vara likviktade av vana. Viktningen ska folja strategins logik
och evidenslaget.

Exempel:

- trend/prior strength
- setup quality/location
- resumption eller trigger evidence
- risk/tradability

Datakvalitet ska normalt inte vara ett scoringblock. Det ar en gate.

Exempel for Pullback v1:

```text
Trend / prior strength          0-40
Pullback quality / location     0-30
Resumption evidence             0-20
Risk / tradability              0-10
```

Har far trend och pullback quality storst vikt eftersom det ar strategins
karnmekanik. Candles far inte stor vikt ensamma eftersom rena candlestick-regler
har svagare stod och latt blir brus utan kontext.

Komponenterna ska forklara varfor heat blir hogt eller lagt.

### 5. Definiera beroenden innan poang

Innan exakta poangkurvor skrivs ska strategin beskriva beroenden mellan block.

Exempel for Pullback:

```text
Trend -> Pullback location -> Resumption -> Risk/tradability
```

Det betyder:

- en stark candle ska inte kunna gora en svag trend till en bra pullback
- en stark trend utan rekyl ska passa Momentum battre an Pullback
- en bra rekyl utan aterkomst kan vara WATCH, men normalt inte HOT
- risk/tradability ska justera ranking, inte definiera edgen

Bra beroenden minskar behovet av konstgjorda heat caps. Om en setup saknar
viktiga karnforhallanden ska den fa lagre heat genom modellen.

### 6. Definiera features

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

Features ska inte automatiskt fa poang. Forst ska de kopplas till roll i
evidence map och strategiskt block.

### 7. Bestam gate, score, timing, risk eller observation

Inte alla regler ska vara grindar.

Data gate ska anvandas for:

- saknad eller trasig data
- for kort historik
- ogiltig OHLC-data
- saknade features som strategin maste ha for scoring

Core score ska anvandas for:

- forhallanden som definierar strategins edge
- exempelvis trend/prior strength i trendfoljande strategier

Mjuk poang ska anvandas for:

- setup quality
- location
- resumption evidence
- volatilitet
- volym
- grad av overstrackning

Risk/tradability ska anvandas for:

- volatilitet
- gap
- range
- likviditet
- praktisk handelbarhet

Observation ska anvandas for:

- saker som ar intressanta men osakra
- tidiga signaler som inte ska styra heat tungt
- forklaringar till anvandaren

Hard stop ska anvandas sparsamt. I scoringmodeller ska hard stop framst betyda
att scoring inte kan goras tekniskt eller att input ar uppenbart ogiltig.

### 8. Formulera heat 100

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

Heat 100-definitionen ska skrivas innan exakta poangtabeller. Den ska forklara
vilka forhallanden som verkligen ar viktiga.

### 9. Formulera strategi-handoff

Varje strategi ska beskriva nar en annan strategi bor ranka hogre.

Exempel:

- Pullback utan rekyl kan vara Momentum.
- Pullback som bryter 20D-high pa stark volym kan vara Breakout.
- Svag men forbattrande trend kan vara Early Trend.

Detta gor att Eodwin kan lata basta strategi vinna i stallet for att tvinga
varje strategi att losa alla lagen med egna caps.

### 10. Formulera poangkurvor

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

Poangkurvor ska inte skapas innan evidence map, blockviktning och beroenden ar
tydliga. Annars riskerar modellen att se exakt ut utan att vara forankrad.

### 11. Koda deterministiskt

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

### 12. Granska kandidater

Forsta kodade versionen ska granskas pa riktiga EOD-data.

Vi ska sarskilt titta pa:

- toppkandidater per strategi
- kandidater runt `WATCH`/`CANDIDATE`-gransen
- aktier som far hog heat av fel anledning
- aktier som visuellt ser intressanta ut men far lag heat
- om flera strategier konkurrerar pa ett begripligt satt

### 13. Backtesta och kalibrera

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
- falsk precision fran snygga men oforankrade poangtabeller
- LLM-genererade vikter som inte speglar strategi, teori eller litteratur
- for manga parametrar for tidigt
- for harda regler som doljer bra nara-kandidater
- for mjuka regler som ger for manga mediokra kandidater
- candlestick-regler som far for stor tyngd utan stottande kontext
- modeller som ser bra ut i backtest men ar svara att handla manuellt

Darfor ska MVP hellre borja med fa, begripliga och robusta features an manga
smarta specialregler.

En bra scoringmodell ska kannas som marknadslogik uttryckt i kod, inte som en
lista indikatorer som rakat fa poang.

## Praktisk startordning

Rekommenderad ordning for Eodwin:

1. Dokumentera denna generella metod.
2. Skapa `pullback_scoring_spec_v1.md` som forsta strategispecifikation.
3. Skapa evidence map och kontrollera att viktningen foljer karnlogiken.
4. Definiera features som Pullback v1 behover.
5. Granska ett litet manuellt chartbook-urval innan scoring kodas skarpt.
6. Koda features och enkel pullback-scoring.
7. Inspektera kandidater manuellt via CLI.
8. Justera uppenbara missar utan att optimera for hart.
9. Upprepa metoden for Momentum och Breakout.
10. Bygg backtest nar scoringresultat och tradeplanlogik ar stabilare.
