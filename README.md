# Swing Trading

Projekt för att stegvis bygga Eodwin: en end-of-day swing-tradingagent för marknadsdata, strategier, dagliga tips, trade-planering, journalföring, uppföljning och utbildning.

## Vision

Eodwin är en komplett end-of-day swing-tradingplattform som kombinerar systematisk screening, trade-planering, daglig uppföljning, journalföring, portföljtänk och mentorskap.

Målet är att hjälpa användare att lära sig och praktisera swing trading på ett strukturerat sätt. Eodwin ska kunna användas av projektägaren, familj, utvalda kollaboratörer och på längre sikt möjligtvis vänner eller kunder/prenumeranter.

Eodwin ska inte genomföra köp, säljordrar eller annan orderplacering. All handel sker manuellt i användarens externa tradingplattform. Eodwin fungerar som beslutsstöd, analysverktyg, planeringsstöd, uppföljare och mentor.

## Grundprinciper

- Eodwin bygger på end-of-day-data.
- Tips och analyser tas fram efter börsstängning.
- Användaren tar själv slutligt beslut.
- Användaren placerar själv order manuellt i extern tradingplattform.
- Eodwin ska vara konkret men inte exekvera handel.
- Privat data, API-nycklar, databaser och användarjournaler ska inte commitas till GitHub.
- Funktionalitet ska byggas stegvis och kunna testas i liten skala.

## Första Målgrupp

Eodwin ska från tidig version stödja flera användare, men i en kontrollerad liten krets.

Första fasen riktar sig till:

- projektägaren
- utvalda kollaboratörer
- eventuellt familjemedlemmar eller nära testanvändare

Detta innebär att applikationen bör tänka multi-user från början, men utan att bygga tung publik SaaS-funktionalitet, prenumerationshantering eller betalflöden i första fasen.

## Huvudfunktioner

### Datahämtning

Eodwin ska dagligen hämta end-of-day-data från eodhd.com för ett definierat tickeruniversum.

I uppstarten kan tickeruniversumet bestå av cirka 100 utvalda tickers.

Hämtad data ska sparas lokalt i databas så att den kan återanvändas av olika funktioner utan onödiga nya API-anrop.

### Indikatorer och Beräkningar

Utifrån sparad marknadsdata ska Eodwin automatiskt beräkna nödvändiga medelvärden och indikatorer.

Dagliga beräknade värden ska sparas i databas för snabb exekvering och kontroll mot strategier utan att samma beräkningar behöver göras om vid varje kontroll.

Exempel på beräkningar:

- glidande medelvärden
- trendmått
- avstånd till medelvärden
- volatilitet
- risknivåer
- strategi-specifika triggernivåer

Exakta indikatorer bestäms senare utifrån strategierna.

### Strategikunskapsbas

Eodwin ska ha en kunskapsbas med fördefinierade swing-tradingstrategier.

Varje strategi bör beskriva:

- grundidé
- marknadsläge där strategin passar
- kriterier för giltig setup
- entry trigger
- stop-loss-logik
- target- eller exitlogik
- risk/reward-principer
- poängsättning
- toleranser, exempelvis entry tolerance
- pedagogisk förklaring för användaren

Strategierna ska kunna användas både av strategimotorn och av mentor-/utbildningsdelen.

### Daglig Screening och Poängsättning

Eodwin ska varje dag, efter att ny EOD-data hämtats, mappa varje ticker mot tillgängliga strategier.

För varje ticker/strategi ska Eodwin bedöma om det finns en giltig setup och sätta en score.

De tickers som uppfyller kraven på giltig setup ska sorteras i poängordning.

Exempel:

```text
ABB.ST
Strategi: Pullback
Score: 9/10
Status: Setup giltig, inväntar stop-buy trigger
```

### Dagens Tips

Dagens tips ska vara konkreta trade-kandidater, inte bara utbildande observationer.

Tipsen ska bygga på stängd börs och gälla som orderplan inför nästa handelsdag.

Ett tips bör kunna innehålla:

- ticker
- strategi
- score
- senaste stängningskurs
- setup-status
- föreslagen stop-buy trigger
- preliminär stop-loss
- preliminär target
- risk/reward
- kort motivering
- eventuell varning om gap-, volatilitet- eller likviditetsrisk

Exempel:

```text
ABB.ST
Strategi: Pullback
Score: 9/10
Senaste close: 123.40
Föreslagen stop-buy: 124.10
Initial stop-loss: 119.80
Target: 134.00
Risk/reward: 2.3
Kommentar: Stark trend, pullback mot relevant medelvärde och giltig setup enligt strategin.
```

Tipsen är konkreta men ska betraktas som beslutsstöd. Användaren ansvarar själv för order och slutligt beslut.

### E-postutskick

Efter daglig screening ska Eodwin kunna skicka ut dagens högst rankade kandidater via e-post.

I första versionen bör utskick kunna gå till en liten kontrollerad lista av mottagare.

Antalet kandidater per utskick kan exempelvis vara 3-9 bäst rankade per dag.

På längre sikt kan antal tips eller innehåll möjligtvis styras av användarens roll eller prenumerationsnivå.

### Trade-planering

När användaren väljer en kandidat ska Eodwin kunna hjälpa till att skapa en konkret trade-plan.

Eftersom order normalt placeras innan nästa börsöppning ska Eodwin utgå från senaste stängningskurs och strategins triggerlogik.

Vanligt scenario:

- setup är giltig enligt senaste EOD-data
- Eodwin föreslår en stop-buy-trigger något över relevant triggernivå
- användaren lägger själv en manuell stop-buy-order i extern tradingplattform
- ordern triggas eller triggas inte under nästa handelsdag

Trade-planen kan innehålla:

- ticker
- strategi
- setup score
- senaste close
- föreslagen stop-buy
- initial stop-loss
- target
- risk per aktie
- användarens riskprocent
- föreslagen position size
- planstatus

### Trade-livscykel

Eodwin ska kunna följa en trade genom flera statusar:

```text
Candidate
Setup är giltig enligt EOD-screening.

Planned order
Användaren har valt kandidaten och skapat en plan.

Pending order
Användaren har lagt manuell stop-buy-order i extern tradingplattform, men ordern är ännu inte fylld.

Active trade
Ordern har fyllts. Användaren registrerar faktisk entry, antal, initial stop-loss och eventuell target.

Closed trade
Användaren registrerar exit, exitpris, datum och kommentar.
```

Eodwin vet inte automatiskt om användaren lagt order eller om ordern blivit fylld. Detta behöver användaren registrera manuellt.

### Registrering av Faktisk Entry

När en order fylls ska användaren registrera faktisk köpkurs och antal aktier.

Eodwin ska använda detta för att:

- jämföra faktisk entry mot planerad eller teoretisk entry
- bedöma om entry ligger inom strategins tolerans
- beräkna verklig risk
- kontrollera position size
- hjälpa användaren tolka situationen med tillgänglig data
- skapa bättre journal- och lärandedata över tid

Exempel på uppföljning:

```text
Faktisk entry var 0.35% över planerad trigger.
Det ligger inom toleransen för strategin Pullback.
Din verkliga risk blev 0.92% av portföljen, baserat på entry 124.50, stop-loss 119.80 och 46 aktier.
Setupen är fortfarande giltig enligt senaste EOD-data. Behåll stop enligt plan.
```

### Risk och Position Size

Eodwin ska ha 1% risk per trade som standard.

Användaren ska kunna ange en egen riskprofil, exempelvis 0,5% per trade i stället för standardvärdet.

Riskprofilen används för att beräkna föreslagen position size.

Mentor- och utbildningsmodulen ska kunna diskutera konsekvenser av olika risknivåer, exempelvis:

- lägre risk per trade
- högre risk per trade
- drawdown
- volatilitet i portföljen
- förväntad långsiktig utveckling
- psykologisk belastning

I första versionen kan riskprofilen vara en enkel användarinställning. Senare kan risk eventuellt variera per strategi.

### Daglig Uppföljning

För aktiva trades ska Eodwin dagligen kunna analysera senaste EOD-data och hjälpa användaren att följa planen.

Uppföljningen kan innehålla:

- aktuell kurs mot entry
- aktuell kurs mot stop-loss
- aktuell kurs mot target
- om setupen fortfarande är tekniskt sund
- om strategins exitvillkor närmar sig
- om stop-loss bör ligga kvar eller justeras enligt strategi
- om användaren avviker från plan
- pedagogisk förklaring av situationen

Eodwin ska inte automatiskt ändra order eller placera exitorder. Användaren gör allt manuellt.

### Journalföring

Eodwin ska hjälpa användaren att bokföra trades och lärdomar.

Journalen bör kunna innehålla:

- planerade trades
- lagda men ej fyllda ordrar
- aktiva trades
- avslutade trades
- entry och exit
- antal aktier
- risk
- resultat
- strategi
- score vid entry
- kommentarer
- användarens reflektioner
- Eodwins feedback

På längre sikt kan journalen användas för att identifiera mönster i användarens beteende och resultat.

### Mentor och Utbildning

Eodwin ska fungera som mentor och lärare i swing trading.

Användaren ska kunna diskutera:

- strategier
- risk
- position sizing
- portföljtänk
- pågående trades
- avslutade trades
- misstag och lärdomar
- grundläggande och avancerade swing-tradingkoncept

Mentorn ska utgå från Eodwins kunskapsbas, användarens trades och aktuell marknadsdata där det är relevant.

### UI

Eodwin ska ha ett UI där användare kan:

- se dagens tips
- filtrera eller sortera kandidater
- öppna en kandidat
- skapa trade-plan
- registrera pending order
- registrera faktisk entry och antal
- följa aktiva trades
- stänga trades
- läsa journal
- diskutera med agenten
- hantera sin riskprofil

Administratörer och kollaboratörer kan senare få extra vyer för strategier, tickeruniversum, backtester och systemstatus.

### Backtestning och Strategiutveckling

Administratörer och särskilda kollaboratörer ska kunna göra backtestning för att finjustera och optimera fördefinierade strategier.

Backtestning är en viktig del av visionen, men kräver mer designarbete.

Eodwin bör på sikt kunna hjälpa till med:

- historisk strategiutvärdering
- parameterjustering
- jämförelse mellan strategier
- risk/reward-analys
- drawdown-analys
- win rate
- expectancy
- känslighetsanalys
- LLM-stödd tolkning av testresultat

Det är ännu en öppen fråga exakt hur backtestmodulen ska byggas.

## Användarroller

Första tänkbara roller:

```text
Admin
Kan ändra tickeruniversum, strategier, användare, scheman och systeminställningar.

Collaborator
Kan använda systemet, testa funktioner, skapa egna trade-planer, logga trades och eventuellt bidra med feedback på strategier.

Subscriber/User
Kan se tips, skapa planer, följa trades, journalföra och använda mentor.
```

I första fasen behövs troligen bara enkel rollhantering: admin och kollaboratör/användare.

## Preliminär Verktygs- och Applikationslista

Detta är en tidig lista över verktyg och komponenter som sannolikt kommer behövas. Den är inte ett slutligt teknikbeslut.

### Utvecklingsmiljö

- Python som huvudspråk för datahämtning, strategi- och analyslogik.
- Lokal Python-miljö i `.venv/`.
- Git för versionshantering.
- GitHub för kodlagring, issues och eventuell projektplanering.

### Datakällor

- eodhd.com för end-of-day-marknadsdata.
- Eventuella kompletterande nyhets- eller fundamentadatakällor i senare fas.

### Databas och Lagring

- Lokal databas för tidig utveckling och privat testdata.
- Separat hantering av privat data under `data/private/`.
- Framtida produktionsdatabas för flera användare om applikationen växer.

### Backend och Batchjobb

- Python-script för schemalagd datahämtning.
- Separata jobb för indikatorberäkning, strategiscreening, scoring och e-postutskick.
- Senare möjlighet till API-backend för UI och agentinteraktion.

### Strategi- och Analyslager

- Kodade strategiregler för deterministisk screening.
- Separat kunskapsbas för strategibeskrivningar och pedagogik.
- Backtestverktyg eller egen backtestmodul i senare fas.

### LLM och Agentfunktioner

- LLM för mentor, förklaringar, sammanfattningar, trade-diskussioner och hjälp att tolka resultat.
- LLM ska användas som stödjande lager, inte som ensam källa för strategisignaler.
- Kritiska beräkningar och regler ska vara deterministiska och testbara.

### UI

- Webbaserat gränssnitt för dagens tips, trade-planer, journal, uppföljning och mentorinteraktion.
- Enkel multi-user-modell från början.
- Adminvyer för tickeruniversum, strategier och systemstatus i senare fas.

### E-post och Notiser

- E-postutskick för dagens tips.
- Liten whitelist av mottagare i första versionen.
- Eventuella andra notifieringar i senare fas.

### Testning och Kvalitet

- Automatiska tester för strategi- och riskberäkningar.
- Tester för datahämtning och datavalidering.
- Backtester för strategier.
- Loggning och kontroller för schemalagda jobb.

### Säkerhet

- `.env` för lokala hemligheter.
- API-nycklar ska aldrig commitas.
- Databaser, tradehistorik, e-postlistor och användarjournaler ska hållas utanför Git.
- Tydlig `.gitignore` för privat och genererad data.

## Teknisk Strukturidé

Detta är inte slutliga teknikval, utan en tidig strukturidé.

Eodwin kan byggas i lager:

### Datakärna

Ansvarar för att lagra:

- tickeruniversum
- historisk EOD-data
- indikatorer
- strategiresultat
- dagliga kandidater
- användare
- trade-planer
- trades
- journalanteckningar
- riskprofiler

### Batchflöden

Schemalagda Python-jobb för:

- datahämtning
- datavalidering
- indikatorberäkning
- strategimappning
- scoring
- e-postutskick
- daglig uppföljningsanalys

### Strategimotor

Kodade regler för:

- setup-kriterier
- entry trigger
- stop-loss
- target
- scoring
- toleranser
- strategi-specifik risklogik

### LLM-lager

Används för:

- mentor
- förklaringar
- trade-diskussioner
- sammanfattningar
- pedagogiska texter
- hjälp att tolka journal och backtester
- naturligt språk-gränssnitt mot användaren

LLM ska inte självständigt fatta orderbeslut eller exekvera handel.

### UI/API

Webbaserat gränssnitt och API för:

- dagens tips
- trade-planering
- journal
- uppföljning
- mentorinteraktion
- användarinställningar
- adminfunktioner

### Admin- och Backtestlager

Separata funktioner för:

- strategiutveckling
- parameterjustering
- backtester
- utvärdering
- systemstatus

## Säkerhet och Privat Data

Följande ska inte commitas till GitHub:

- API-nycklar
- `.env`
- databaser
- privat marknadsdata om licens eller policy kräver det
- användarjournaler
- tradehistorik
- personuppgifter
- e-postlistor
- lokala exportfiler

Projektet ska använda `.gitignore` och tydlig struktur för privat data.

## Föreslagen MVP

En rimlig första MVP kan vara:

1. Definiera tickeruniversum.
2. Hämta och spara EOD-data från eodhd.com.
3. Beräkna nödvändiga indikatorer.
4. Implementera 1-2 första strategier.
5. Göra daglig screening och scoring.
6. Bygga ett enkelt lokalt UI för tickeruniversum, senaste data, indikatorer och screeningresultat.
7. Skapa dagens tips som text/rapport.
8. Skicka tips till en liten e-postlista.
9. Låta användaren skapa trade-plan från kandidat.
10. Låta användaren registrera faktisk entry och antal.
11. Följa aktiva trades dagligen med enkel EOD-analys.
12. Logga trades i journal.
13. Ha enkel mentorinteraktion kring kandidat, trade-plan och aktiv trade.

## Öppna Frågor

- Vilka marknader ska tickeruniversumet först omfatta?
- Vilka 2-3 strategier ska implementeras först?
- Ska riskprofil i första versionen bara vara per användare, eller även per strategi?
- Hur ska första UI:t avgränsas?
- Vilken databas ska användas i första versionen?
- Hur ska autentisering lösas för liten grupp kollaboratörer?
- Hur ska e-postutskick göras i första versionen?
- Hur ska backtestmodulen designas?
- Vilken roll ska LLM ha i första fungerande MVP?
- Vilka delar måste fungera helt deterministiskt utan LLM?

## Python-miljö

Projektet har en egen lokal Python-miljö i `.venv/`.

Aktivera miljön i PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Kontrollera Python-version:

```powershell
python --version
```

## Nuvarande Struktur

```text
app/
docs/
tests/
data/private/
```

- `app/`: plats för programmets kod.
- `docs/`: viktiga designbeslut, strategimetodik och scoringdokument.
- `tests/`: plats för tester som kontrollerar att koden fungerar.
- `data/private/`: lokal privat data som inte ska laddas upp till GitHub.

## Viktiga Dokument

Läs `docs/README.md` innan strategi-, scoring-, feature- eller screeninglogik
ändras.

Viktiga dokument:

- `docs/strategy_development_method_v1.md`: metod för hur strategier byggs,
  granskas, backtestas och förfinas.
- `docs/strategy_scoring_v1.md`: första riktningen för mjuk strategy scoring
  och heat per strategi.

## Nuvarande Dataflöde

Första tekniska byggsteget är på plats:

- tickeruniversum sparas i SQLite-databasen `data/private/eodwin.sqlite`
- prisdata sparas som CSV per ticker i `data/private/eod/`
- EODHD-nyckel läses från `.env` via variabeln `EODHD_API_KEY`
- `.env`, SQLite-databasen och hämtad prisdata ska inte commitas

Aktiva testtickers:

```text
ABB.ST
ERIC-B.ST
INVE-B.ST
VOLV-B.ST
```

Användbara kommandon:

```powershell
.\.venv\Scripts\python.exe -m app.cli init-db
.\.venv\Scripts\python.exe -m app.cli list-tickers
.\.venv\Scripts\python.exe -m app.cli fetch-all
.\.venv\Scripts\python.exe -m app.cli fetch-all --from-date 2026-05-01
.\.venv\Scripts\python.exe -m app.cli show-prices ABB.ST --rows 5
.\.venv\Scripts\python.exe -m app.cli show-db-prices ABB.ST --rows 5
.\.venv\Scripts\python.exe -m app.cli show-indicators ABB.ST --rows 5
.\.venv\Scripts\python.exe -m app.cli sync-prices-db
.\.venv\Scripts\python.exe -m app.cli calculate-indicators
.\.venv\Scripts\python.exe -m app.cli show-stored-indicators ABB.ST --rows 5
.\.venv\Scripts\python.exe -m app.cli daily-update
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Om `fetch` eller `fetch-all` körs utan `--from-date` väljer programmet startdatum automatiskt. Om ingen lokal prisdata finns, eller om lokal historik är kortare än cirka ett år, hämtas cirka ett år tillbaka. Om ett års lokal historik redan finns hämtas data från dagen efter senaste sparade datum. Ny hämtad data slås ihop med befintlig CSV-data per datum, så historik inte skrivs bort vid dagliga uppdateringar.

SQLite innehåller tickerregistret, prisdata och indikatorvärden. CSV-filerna finns kvar som enkel filcache och inspektionslager, medan SQLite är systemets datakärna för screening, analys och kommande UI.

## Arbetsprincip

Projektet ska byggas stegvis.

Varje större tekniskt val ska föregås av diskussion och beslut.

När beslut är överenskomna ska de dokumenteras i projektet.

Eodwin ska utvecklas som ett praktiskt verktyg först, och först senare som eventuell publik tjänst.
