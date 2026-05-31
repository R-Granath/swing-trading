# Changelog

Projektlogg for `swing-trading` / Eodwin.

Formatet ar skrivet for att vara lasbart bade for manniskor och framtida kodagenter:

- varje pass har datum, commit, status och sammanfattning
- tekniska andringar listas under stabila rubriker
- privat data beskrivs utan att innehall eller hemligheter inkluderas
- kommandon dokumenteras sa att arbetslaget kan ateruppta fran samma lage

## 2026-05-31 - Pullback trade plan decision table

Commit: pending

Status efter passet:

- dokumentationsandringar, inga kodandringar
- tester ej korda eftersom passet bara ror dokumentation

Byggt:

- Nytt beslutstabellsdokument har lagts till:
  `docs/pullback_trade_plan_decision_table_v1.md`.

Beslut och riktning:

- Tabellen ar en bro mellan `PULLBACK_TRADE_PLAN_V1`-design och framtida
  deterministisk Python-implementation.
- Den beskriver hur scoring-output, setup evolution, MVP-features och enkla
  5-10 dagars OHLCV-observationer preliminart kan bli `plan_status`,
  `setup_class`, `rr_hypothesis`, warnings och kommentar.
- Reglerna halls mjuka for MVP: `WATCH_PLAN` hellre an `NO_PLAN`,
  `LATE_PLAN` hellre an felaktigt `NO_PLAN`, och `READY_PLAN` bara nar caset
  verkar planeringsbart.
- Ingen ny strategi implementerades.
- Ingen scoringlogik, trade-planlogik, entry, stop, target eller position
  sizing andrades.

Rekommenderade nasta steg:

- Granska beslutstabellen manuellt mot charts for `ABB.ST`, `ERIC-B.ST`,
  `INVE-B.ST` och `VOLV-B.ST`.
- Darefter kan forsta kodade prototype byggas med filtereffekt-sammanstallning
  per datum.

## 2026-05-31 - Architecture clarifications

Commit: pending

Status efter passet:

- dokumentationsandringar, inga kodandringar
- tester ej korda eftersom passet bara ror dokumentation

Byggt:

- Nytt arkitekturfortydligande har lagts till:
  `docs/architecture_clarifications_v1.md`.
- `README.md` har uppdaterats latt med lank till arkitekturfortydligandet.

Beslut och riktning:

- README ar fortsatt overgripande source of truth for vision och MVP.
- Pullback v1-flodet fortydligas som separata lager: data/indicators/features,
  scoring, trade-plan/setup evolution, risk/reward-hypotes och senare
  entry/stop/target/position sizing.
- Python ska aga deterministisk ranking, planstatus, risk och reproducerbar
  logik.
- LLM ska anvandas for forklaring, rapportering, mentor/dialog och pedagogiskt
  stod, inte som primar regelmotor.
- Ingen ny strategi implementerades.
- Ingen scoringlogik eller trade-planlogik andrades.

## 2026-05-29 - Pullback scoring and stored strategy scores

Commit: pending

Status efter passet:

- `main` var synkad med `origin/main` vid start
- tester grona: `Ran 43 tests OK`
- senaste EODHD-rad for fyra testtickers hamtades for `2026-05-29`
- Pullback-scores beraknades och sparades i SQLite for alla fyra testtickers

Byggt:

- Ny scoringmodul har lagts till: `app/scoring.py`.
- `PULLBACK_SCORING_V1` har implementerats med blocken trend/prior strength,
  pullback quality/location, resumption evidence och risk/tradability.
- Pullback quality/location har justerats sa faktisk rekyl vager tyngre,
  location inte kan dominera utan rekyl och SMA-avstand behandlas asymmetriskt.
- Nytt CLI-kommando har lagts till: `inspect-pullback-score`.
- Ny SQLite-tabell har lagts till: `strategy_scores`.
- Nya datalagerfunktioner har lagts till for att spara och lasa
  strategiscores.
- Nya CLI-kommandon har lagts till:
  - `score-strategies`
  - `show-strategy-scores`
  - `show-top-setups`
- Tester har lagts till for scoringmodellen, CLI-flodet och persistent
  strategy scores.

Beslut och riktning:

- Features sparas inte i databasen i detta steg. De beraknas i arbetsminne fran
  prisdata och indikatorer.
- Scoringresultat sparas separat per ticker, datum, strategi och modellversion.
- Scoring ar fortsatt kandidat- och prioriteringsmotor, inte faktisk
  trade-plan.
- Entry, stop-buy, stop-loss, target, risk/reward och position sizing ska byggas
  senare som separat strategilager.
- Forsta sparade strategin ar endast `PULLBACK_SCORING_V1`.

Dataeffekt lokalt:

- `daily-update` hamtade 4 nya rader totalt fran EODHD.
- Varje testticker hade efter uppdatering 252 prisrader i SQLite.
- `score-strategies` sparade 1008 strategy-score-rader.
- Topplista for `2026-05-29`:
  - `ERIC-B.ST` `PULLBACK_SCORING_V1` 95 `HOT`
  - `ABB.ST` `PULLBACK_SCORING_V1` 81 `HOT`
  - `INVE-B.ST` `PULLBACK_SCORING_V1` 78 `CANDIDATE`
  - `VOLV-B.ST` `PULLBACK_SCORING_V1` 63 `WATCH`

Viktiga kommandon:

```powershell
.\.venv\Scripts\python.exe -m app.cli daily-update
.\.venv\Scripts\python.exe -m app.cli inspect-pullback-score ERIC-B.ST --rows 1
.\.venv\Scripts\python.exe -m app.cli score-strategies
.\.venv\Scripts\python.exe -m app.cli show-top-setups --date 2026-05-29 --limit 10
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Rekommenderade nasta steg:

- Granska de fyra Pullback-casen visuellt mot chart for att validera scoringens
  beteende.
- Dokumentera en kort Pullback scoring review for `2026-05-29`.
- Borja drefter designa forsta faktiska Pullback-strategin som separat lager
  fran scoring.

## 2026-05-28 - Pullback MVP feature layer

Commit: `a65544a Add pullback MVP feature layer`

Status efter passet:

- `main` var synkad med `origin/main` vid start
- tester grona: `Ran 33 tests OK`
- lokal SQLite uppdaterad med senaste EODHD-data for fyra testtickers
- `atr14` och `atr14_pct` beraknades och sparades i SQLite

Byggt:

- Nytt dokument har lagts till: `docs/feature_definitions_v1.md`.
- Dokumentet begransar forsta Pullback v1-implementationen till 15 MVP-features
  och markerar ovriga features som `defined_but_deferred`.
- `atr14` och `atr14_pct` har lagts till i indikatorlagret.
- `show-indicators` och `show-stored-indicators` visar nu `atr14` och
  `atr14_pct`.
- Nytt CLI-kommando har lagts till: `inspect-market`.
- Nytt featurelager har lagts till: `app/features.py`.
- Nytt CLI-kommando har lagts till: `inspect-features`.
- Nytt reviewdokument har lagts till:
  `docs/pullback_mvp_review_2026-05-28.md`.

Beslut och riktning:

- Pullback v1 MVP ska fortsatt vara smal.
- Ingen scoring kodades i detta pass.
- Ingen entry-, stop-loss-, target- eller position sizing-logik kodades.
- Featurelagret innehaller endast MVP-subsetet fran
  `docs/feature_definitions_v1.md`.
- CLI-baserad sanity review anvands som praktisk ersattning for manuell
  chartgranskning i detta lage.

Dataeffekt lokalt:

- `daily-update` hamtade 8 nya rader totalt fran EODHD.
- Varje testticker hade efter uppdatering 251 prisrader i SQLite.
- For varje ticker sparades 960 indikatorvarden.
- Granskade tickers:
  - `ABB.ST`
  - `ERIC-B.ST`
  - `INVE-B.ST`
  - `VOLV-B.ST`

Viktiga kommandon:

```powershell
.\.venv\Scripts\python.exe -m app.cli daily-update
.\.venv\Scripts\python.exe -m app.cli inspect-market ABB.ST --rows 5
.\.venv\Scripts\python.exe -m app.cli inspect-features ABB.ST --rows 5
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Rekommenderade nasta steg:

- Formulera och implementera forsta smala `PULLBACK_SCORING_V1`.
- Scoring ska endast anvanda MVP-features fran
  `docs/feature_definitions_v1.md`.
- Folj blocken i `docs/pullback_scoring_spec_v1.md`:
  trend/prior strength, pullback quality/location, resumption evidence och
  risk/tradability.
- Fortsatt ingen entry, stop-loss, target, position sizing eller ny strategi.

## 2026-05-26 - Pullback scoring spec

Commit: `071909e Document pullback scoring spec`

Status efter passet:

- dokumentationsandringar, inga kodandringar
- tester ej korda eftersom passet bara ror dokumentation

Byggt:

- Ny strategispecifikation har lagts till: `docs/pullback_scoring_spec_v1.md`.
- `docs/README.md` har uppdaterats med pullback-specen i lasordningen.
- `docs/strategy_development_method_v1.md` har skarpts sa strategy scoring
  maste bygga pa evidence map, karnlogik och beroenden innan poangtabeller.

Beslut och riktning:

- Pullback v1 definieras som en long-only trendfoljande rekylstrategi.
- Specen beskriver ideal setup, heat 100, nar caset inte langre ar en pullback,
  evidenslage, data gates, beroenden, featurebehov och forklaringsdrivare.
- Metoden sager nu tydligare att LLM inte ska hitta pa slutliga vikter eller
  trosklar utan litteratur-/teoriforankrad prioritering.
- Pullback-score ska byggas sekventiellt: trend/prior strength, pullback
  quality/location, resumption evidence och risk/tradability.
- Datakvalitet ar en teknisk gate och ska inte ge heat-poang.
- Volym far tydligare roll i resumption evidence an enskilda candles.
- Candle-logik ska vara mjuk: 1-3 grona candles kan visa respons, medan 4+
  grona candles kan minska pullback-fit och flytta caset mot Momentum.
- V1 ska undvika generella heat caps; svaga beroenden ska ge lagre score genom
  blockmodellen.
- Framtida backtest ska kalibrera trendmatt, SMA/ATR-location, volymbekraftelse,
  rekyldjup, candlepoang och heat-trosklar.

Rekommenderade nasta steg:

- Skapa `docs/feature_definitions_v1.md`.
- Lagg till ATR14 och ATR14_pct i indikatorlagret.
- Bygg featurefunktioner for trend/prior strength, pullback location,
  resumption evidence och risk/tradability.
- Implementera `PULLBACK_SCORING_V1` med beroenden och poangdrivare.

## 2026-05-26 - Strategy scoring method docs

Commit: `825671c Document strategy scoring method`

Status efter passet:

- dokumentationsandringar, inga kodandringar
- tester ej korda eftersom passet bara ror dokumentation

Byggt:

- Ny docs-indexfil har lagts till: `docs/README.md`.
- Nytt metodikdokument har lagts till: `docs/strategy_development_method_v1.md`.
- Nytt scoringdokument har lagts till: `docs/strategy_scoring_v1.md`.
- `README.md` lankar nu till de viktiga design- och scoringdokumenten.

Beslut och riktning:

- Strategier ska byggas med en tydlig metod: tradingide, litteraturcheck,
  featuredefinitioner, scoringhypotes, manuell granskning, kodad modell,
  backtest, kalibrering och senare live-/journalutfall.
- LLM ska anvandas for struktur, oversattning och kodstod, men inte som ensam
  sanningskalla for tradingedge.
- Litteratur ska anvandas som rimlighetscheck, inte som facit.
- Backtest ska senare anvandas for att kalibrera vikter och trosklar, men med
  forsiktighet mot overanpassning.
- Scoringmodeller ska versioneras sa framtida kandidater och trades kan kopplas
  till den modellversion som skapade signalen.

Rekommenderade nasta steg:

- Skapa `docs/pullback_scoring_spec_v1.md`.
- Definiera ideal pullback, heat 100, poangkurvor, hard stops och observationer.
- Efter pullback-specen: borja koda featurelager och forsta enkla pullback-score.

## 2026-05-26 - SQLite price inspection

Commit: `1583010 Add SQLite price inspection command`

Status efter passet:

- tester grona: `Ran 21 tests OK`
- lokal privat SQLite uppdaterad fran befintliga CSV-priser

Byggt:

- Nytt CLI-kommando har lagts till: `show-db-prices`.
- Kommandot visar prisdata direkt fran SQLite-tabellen `prices`.
- CLI-test har lagts till for bade befintliga SQLite-priser och saknade rader.

Dataeffekt lokalt:

- `sync-prices-db` kordes for aktiva testtickers.
- `ABB.ST`, `ERIC-B.ST`, `INVE-B.ST` och `VOLV-B.ST` synkades med 248 prisrader vardera.

Viktiga kommandon:

```powershell
.\.venv\Scripts\python.exe -m app.cli sync-prices-db
.\.venv\Scripts\python.exe -m app.cli show-db-prices ABB.ST --rows 5
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## 2026-05-25 - Daily market data and indicator pipeline

Commit: `d1d379b Add daily market data and indicator pipeline`

Status efter passet:

- `main` synkad med `origin/main`
- tester grona: `Ran 19 tests OK`
- lokal privat SQLite och CSV-data uppdaterad for fyra testtickers

Byggt:

- Automatisk backfill/pafyllning av EOD-data.
- CSV-prisdata slas ihop per datum sa historik inte skrivs bort vid korta dagliga hamtningar.
- Ett samlat dagligt kommando har lagts till: `daily-update`.
- Prisdata kan synkas fran CSV till SQLite-tabellen `prices`.
- Indikator-definitioner sparas i SQLite-tabellen `indicator_definitions`.
- Indikatorvarden sparas dag for dag i SQLite-tabellen `indicator_values`.
- Forsta indikatorlagret har lagts till med SMA20, SMA50 och SMA200.

Dataeffekt lokalt:

- Ett ars EOD-data hamtades for:
  - `ABB.ST`
  - `ERIC-B.ST`
  - `INVE-B.ST`
  - `VOLV-B.ST`
- Varje ticker hade efter backfill 248 prisrader fran cirka `2025-05-26` till `2026-05-25`.
- SMA20, SMA50 och SMA200 beraknades och sparades i SQLite.

Databaslage:

- SQLite-fil: `data/private/eodwin.sqlite`
- Tabeller:
  - `tickers`
  - `prices`
  - `indicator_definitions`
  - `indicator_values`
- Privat data ar fortsatt ignorerad av Git.

Viktiga kommandon:

```powershell
.\.venv\Scripts\python.exe -m app.cli daily-update
.\.venv\Scripts\python.exe -m app.cli show-prices ABB.ST --rows 5
.\.venv\Scripts\python.exe -m app.cli show-indicators ABB.ST --rows 5
.\.venv\Scripts\python.exe -m app.cli sync-prices-db
.\.venv\Scripts\python.exe -m app.cli calculate-indicators
.\.venv\Scripts\python.exe -m app.cli show-stored-indicators ABB.ST --rows 5
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Noteringar:

- `daily-update` ar manuell i uppbyggnadsfasen.
- Automatiserad daglig korning ska aktiveras senare nar flodet ar mer moget.
- Om det gar flera dagar mellan manuella korningar ska programmet fylla pa fran senaste sparade datum.
- En 7-dagars tolerans finns for att undvika onodig ettars-backfill nar forsta handelsdag ligger efter exakt kalenderdatum.

Rekommenderade nasta steg:

- Lagg till ett kommando for att visa prisdata direkt fran SQLite, till exempel `show-db-prices`.
- Lagg till fler indikatorer, troligen RSI14 och ATR14.
- Efter RSI/ATR: borja med forsta enkla screeningregel, till exempel `close > SMA50 > SMA200`.

## 2026-05-24 - Initial EOD data pipeline

Commit: `ca974b4 Add initial EOD data pipeline`

Status efter passet:

- `main` synkad med `origin/main`
- tester grona
- forsta lokala dataflodet for Eodwin fungerade

Byggt:

- SQLite borjade anvandas for tickeruniversum.
- Lokal SQLite-fil definierades som `data/private/eodwin.sqlite`.
- EOD-prisdata sparades som CSV per ticker under `data/private/eod/`.
- `.env` flyttades till projektroten och ignoreras av Git.
- `.env.example` lades till som mall.
- Batchhamtning fungerade for alla aktiva tickers.
- Enkel terminalvisning av prisdata lades till.

Tickeruniversum:

- `ABB.ST`
- `ERIC-B.ST`
- `INVE-B.ST`
- `VOLV-B.ST`

Viktiga kommandon:

```powershell
.\.venv\Scripts\python.exe -m app.cli list-tickers
.\.venv\Scripts\python.exe -m app.cli fetch-all --from-date 2026-05-20
.\.venv\Scripts\python.exe -m app.cli show-prices ABB.ST --rows 5
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Databeslut vid detta lage:

- SQLite inneholl tickeruniversumet.
- Prisdata lag som CSV per ticker for enkel inspektion.
- Fragor lamnades oppna kring om priser och indikatorer senare skulle flyttas in i SQLite.

## 2026-05-24 - Vision and MVP plan

Commit: `4f06fac Document Eodwin vision and MVP plan`

Byggt:

- Projektets vision, MVP-riktning och huvudfunktioner dokumenterades i `README.md`.
- Grundprinciper for end-of-day swing-trading, beslutsstod, risk, journal, mentor, UI, backtest och sakerhet formulerades.

## 2026-05-24 - Project initialization

Commit: `cb9edf6 Initialize swing trading project`

Byggt:

- Forsta projektstrukturen skapades.
- Git-repo initierades for `swing-trading`.
