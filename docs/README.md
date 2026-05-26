# Eodwin Docs Index

Denna mapp samlar viktiga designbeslut och arbetsmetoder for Eodwin.
Dokumenten ska lasas innan strategi-, scoring-, feature- eller screeninglogik
andras.

## Lasordning

1. `strategy_development_method_v1.md`
2. `strategy_scoring_v1.md`
3. Framtida strategispecifikationer, till exempel `pullback_scoring_spec_v1.md`

## Dokument

### `strategy_development_method_v1.md`

Beskriver hur Eodwin ska bygga strategier med hjalp av:

- LLM som struktur- och oversattningsstod
- litteratur som rimlighetscheck
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

## Framtida dokument

Planerade dokument:

- `pullback_scoring_spec_v1.md`
- `momentum_scoring_spec_v1.md`
- `feature_definitions_v1.md`
- `backtest_method_v1.md`

Strategispecifikationer ska beskriva ideal setup, heat 100, features,
poangkurvor, hard stops och vilka saker som bara ska vara observationer.
