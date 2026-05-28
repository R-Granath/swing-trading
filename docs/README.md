# Eodwin Docs Index

Denna mapp samlar viktiga designbeslut och arbetsmetoder for Eodwin.
Dokumenten ska lasas innan strategi-, scoring-, feature- eller screeninglogik
andras.

## Lasordning

1. `strategy_development_method_v1.md`
2. `strategy_scoring_v1.md`
3. `pullback_scoring_spec_v1.md`
4. `feature_definitions_v1.md`
5. Framtida strategispecifikationer, till exempel `momentum_scoring_spec_v1.md`

## Dokument

### `strategy_development_method_v1.md`

Beskriver hur Eodwin ska bygga strategier med hjalp av:

- LLM som struktur- och oversattningsstod
- litteratur som rimlighetscheck
- evidence map innan poang och trosklar
- viktning efter karnlogik och evidenslage
- manuell granskning i MVP
- backtest for senare kalibrering
- journal/live-utfall for praktisk verklighetskontroll

Detta dokument satter arbetssattet. Det ska anvandas innan nya strategi-specar
skrivs eller scoringregler kodas.

### `strategy_scoring_v1.md`

Beskriver den forsta scoringriktningen:

- mjuk heat per strategi i stallet for hard routing
- long-only MVP-strategier
- gemensamt featurelager
- statusnivaer som `HOT`, `CANDIDATE`, `WATCH` och `LOW`
- SMA200 som regimfilter
- hur scoringmodellen kan versioneras och forfinas

Detta dokument beskriver modellens riktning. Det ar inte en exakt kodspec for
enskilda strategier.

### `pullback_scoring_spec_v1.md`

Beskriver forsta strategispecifikationen for Pullback:

- ideal setup och heat 100-definition
- nar caset inte langre ar en pullback
- komponentviktning for Pullback v1
- data gates och beroenden
- featurebehov och startformler
- resumption evidence med prisrespons, volym och candles
- nar pullback-heat bor flytta mot Momentum eller Breakout
- testfall och oppna fragor for manuell granskning/backtest

Detta dokument ar en kodnara scoringhypotes. Trosklarna ska granskas manuellt
och senare kalibreras med backtest.

### `feature_definitions_v1.md`

Definierar det smala Pullback v1 MVP-subsetet som far kodas forst:

- separation mellan indicators, features och scoring
- endast `atr14` och `atr14_pct` som nasta indikatorsteg
- 15 tillatna MVP-features for Pullback v1
- data gates och soft warnings
- deferred features som inte far anvandas i forsta scoringkoden
- implementation order fram till manuell chart review och senare scoring

### `pullback_mvp_review_2026-05-28.md`

Dokumenterar forsta CLI-baserade sanity review av Pullback v1 MVP-features for
`ABB.ST`, `ERIC-B.ST`, `INVE-B.ST` och `VOLV-B.ST`.

Syftet ar att kontrollera om featurevarden verkar rimliga innan scoring byggs.
Det ar inte en trade-plan och inte en scoringmodell.

## Framtida dokument

Planerade dokument:

- `momentum_scoring_spec_v1.md`
- `backtest_method_v1.md`

Strategispecifikationer ska beskriva ideal setup, heat 100, features,
poangkurvor, hard stops och vilka saker som bara ska vara observationer.
