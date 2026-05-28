# Feature Definitions v1

Detta dokument definierar den smala featuremangd som far anvandas for forsta
implementationen av Pullback v1.

Malet ar inte en bred featurekatalog. Malet ar en begriplig och manuellt
verifierbar MVP:

```text
data -> indicators -> features -> pullback score -> manuell chart review
-> enkel backtest -> iteration
```

Dokumentet foljer `docs/pullback_scoring_spec_v1.md`, men begransar forsta
implementationen till ett mindre subset. Alla andra features som finns namnda i
strategidokumenten ska betraktas som `defined_but_deferred` tills de aktivt tas
in efter manuell granskning eller backtest.

## Arkitekturregel

### Indicators

Indicators ar neutrala berakningar fran prisdata. De ska inte innehalla
tradinglogik, score eller strategiavvagningar.

Pullback v1 MVP far anvanda dessa indicators:

- `sma20`
- `sma50`
- `sma200`
- `atr14`
- `atr14_pct`

Forsta tekniska indikatorsteget ar endast:

```text
atr14
atr14_pct
```

### Features

Features ar deterministiska tolkningar av data och indicators.

Features ska vara:

- enkla att forsta
- manuellt verifierbara pa chart
- fria fran score, vikter och status
- begransade till Pullback v1 MVP

Ingen feature far byggas "for sakerhets skull".

### Scoring

Scoring anvander features for ranking.

Scoring far:

- vaga features
- ge status
- skapa ranking
- generera `HOT`, `WATCH` och `LOW`

Scoring far inte introducera nya implicita features. Ingen scoringkod far bero
pa deferred features.

## Pullback v1 MVP feature subset

Detta ar den enda featuremangd som far kodas initialt.

## Trend / Prior Strength

Syfte:

```text
Ar detta ratt marknad for en pullback?
```

### 1. close_vs_sma50_pct

```text
(close - sma50) / sma50 * 100
```

Mater:

```text
Pris relativt mellantrend
```

### 2. close_vs_sma200_pct

```text
(close - sma200) / sma200 * 100
```

Mater:

```text
Langsiktig trendregim
```

### 3. sma50_vs_sma200_pct

```text
(sma50 - sma200) / sma200 * 100
```

Mater:

```text
Trendstruktur
```

### 4. sma50_slope_10d

```text
(sma50_today - sma50_10d_ago) / sma50_10d_ago * 100
```

Mater:

```text
Om mellantrenden lutar uppat
```

### 5. return_60d_pct

```text
(close - close_60d_ago) / close_60d_ago * 100
```

Mater:

```text
Tidigare styrka / momentum-proxy
```

## Pullback Quality / Location

Syfte:

```text
Ar detta faktiskt en konstruktiv rekyl?
```

### 6. rolling_high_20d

```text
highest high over latest 20 trading days
```

Mater:

```text
Referenspunkt for pullback depth
```

### 7. pullback_depth_20d_pct

```text
(close - rolling_high_20d) / rolling_high_20d * 100
```

Mater:

```text
Hur langt aktien rekylerat
```

### 8. distance_to_sma20_atr

```text
(close - sma20) / atr14
```

Mater:

```text
Location nara snabb trend
```

### 9. distance_to_sma50_atr

```text
(close - sma50) / atr14
```

Mater:

```text
Djupare men fortfarande konstruktiv rekyl
```

## Resumption Evidence

Syfte:

```text
Kommer koparna tillbaka?
```

### 10. close_position_in_range

```text
(close - low) / (high - low)
```

Mater:

```text
Styrka i dagens close
```

### 11. is_green_candle

```text
close > open
```

Mater:

```text
Enkel positiv dagsriktning
```

Regel:

```text
En gron candle far aldrig radda en svag trend.
```

### 12. volume_vs_avg20

```text
volume / volume_avg20
```

Mater:

```text
Deltagande pa responsdagen
```

`volume_avg20` ar ett hjalpberaknat rullande snitt for denna feature. Det ska
inte behandlas som en egen scoringfeature i Pullback v1 MVP.

## Risk / Tradability

Syfte:

```text
Ar setupen praktiskt tradable?
```

### 13. atr14_pct

```text
atr14 / close * 100
```

Mater:

```text
Volatilitetsniva
```

### 14. range_vs_atr14

```text
(high - low) / atr14
```

Mater:

```text
Om dagens rorelse ar extrem
```

### 15. gap_pct

```text
(open - previous_close) / previous_close * 100
```

Mater:

```text
Gap-risk
```

## Data gates

Data gates kors fore featureberakning och scoring.

Ge `NO_SCORE` eller teknisk datavarning nar nagon nodvandig input saknas eller
ar ogiltig.

Hard gates:

- prisrad saknas for scoringdatum
- `open`, `high`, `low` eller `close` saknas
- `high <= low`
- `open`, `high`, `low` eller `close` ar negativt eller noll
- `sma20`, `sma50` eller `sma200` saknas
- `atr14` saknas eller ar `<= 0`
- nodvandig historik saknas for 10D, 20D eller 60D-lookback
- `previous_close` saknas nar `gap_pct` ska beraknas

Soft warnings:

- `volume` saknas
- `volume_avg20` kan inte beraknas
- `volume_vs_avg20` saknas

Saknad volym ska inte stoppa scoring, men resumption evidence blir mindre
saker.

## Deferred features

Foljande features ar inte del av forsta implementationen, aven om de namns i
andra dokument:

- `close_vs_sma20_pct`
- `sma20_vs_sma50_pct`
- `sma20_slope_5d`
- `sma200_slope_20d`
- `return_20d_pct`
- `body_pct_of_range`
- `consecutive_green_candles`
- `up_day_volume_vs_avg20`
- `down_day_volume_vs_avg20`
- `range_pct`
- 52-week-high-features
- RSI
- MACD
- Bollinger Bands
- breda candlestickmonster
- breakout-features
- momentum-strategifeatures

Status:

```text
defined_but_deferred
```

Ingen scoringkod far bero pa dessa features i Pullback v1 MVP.

## Hard constraints

Foljande ska inte byggas i detta steg:

- nya features utanfor MVP-subsetet
- nya indikatorer utanfor `atr14` och `atr14_pct`
- RSI
- MACD
- Bollinger Bands
- candlestick-pattern libraries
- breakout-logik
- momentum-strategi
- entry-trigger
- stop-loss-logik
- target-logik
- position sizing

## Implementation order

### Step 1

Implementera endast:

```text
atr14
atr14_pct
```

i indikatorlagret.

### Step 2

Implementera endast MVP-feature subset i detta dokument.

### Step 3

Kor manuell chart review pa riktiga tickers.

### Step 4

Forst darefter:

```text
PULLBACK_SCORING_V1
```

Ingen ytterligare scope-expansion innan detta fungerar.
