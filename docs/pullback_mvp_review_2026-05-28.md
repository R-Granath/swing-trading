# Pullback MVP Review 2026-05-28

Detta ar en forsta CLI-baserad sanity review av Pullback v1 MVP-features.

Syftet ar att kontrollera om featurevarden verkar rimliga innan
`PULLBACK_SCORING_V1` byggs. Detta ar inte en trade-plan, inte en
koprekommendation och inte en scoringmodell.

Underlaget kommer fran:

```powershell
.\.venv\Scripts\python.exe -m app.cli inspect-market <TICKER> --rows 5
.\.venv\Scripts\python.exe -m app.cli inspect-features <TICKER> --rows 5
```

Granskade tickers:

- `ABB.ST`
- `ERIC-B.ST`
- `INVE-B.ST`
- `VOLV-B.ST`

## Overgripande sanity check

Featurelagret verkar tekniskt komplett for de senaste raderna:

- alla 15 MVP-features fylls for de fyra tickers
- SMA20/SMA50/SMA200 finns
- ATR14 och ATR14_pct finns
- 20D-high, pullback depth, ATR-avstand och volymrelationer beraknas
- inga uppenbara tomma varden i senaste raderna

Det viktiga i detta steg ar inte om nagon ticker ar "bast". Det viktiga ar om
features beskriver olika marknadslagen pa ett begripligt satt.

## ABB.ST

Senaste granskningsdatum: `2026-05-28`

Viktiga featurevarden:

```text
close_vs_sma50_pct        12.2119
close_vs_sma200_pct       33.6969
sma50_vs_sma200_pct       19.1468
sma50_slope_10d            4.7061
return_60d_pct            16.9749
pullback_depth_20d_pct    -2.3937
distance_to_sma20_atr      0.7774
distance_to_sma50_atr      4.7384
close_position_in_range    0.5882
is_green_candle            true
volume_vs_avg20            0.7039
atr14_pct                  2.2967
range_vs_atr14             0.7501
gap_pct                   -0.1824
```

Tolkning:

- Trend/prior strength ser stark ut.
- Priset ligger tydligt over SMA50 och SMA200.
- SMA50 lutar upp och ligger tydligt over SMA200.
- Pullback depth runt `-2.4%` tyder pa faktisk rekyl, men inte djup rekyl.
- Priset ligger relativt nara SMA20 i ATR-termer.
- Volymen ar under 20D-snitt pa senaste grona dag, sa resumption evidence ar
  inte stark via volym.

Sanity slutsats:

`ABB.ST` ser ut som en rimlig kandidat for att testa Pullback-featurelogiken:
stark trend, viss rekyl, nara SMA20, men inte tydlig volymbekraftelse.

## ERIC-B.ST

Senaste granskningsdatum: `2026-05-28`

Viktiga featurevarden:

```text
close_vs_sma50_pct         7.1086
close_vs_sma200_pct       28.1062
sma50_vs_sma200_pct       19.6040
sma50_slope_10d            3.4756
return_60d_pct            13.8211
pullback_depth_20d_pct    -6.6301
distance_to_sma20_atr      0.7022
distance_to_sma50_atr      2.2798
close_position_in_range    0.1754
is_green_candle            false
volume_vs_avg20            0.9122
atr14_pct                  2.9112
range_vs_atr14             0.8227
gap_pct                   -0.2887
```

Tolkning:

- Trendbilden ar fortfarande positiv.
- Rekylen ar djupare an ABB, runt `-6.6%` fran 20D-high.
- Priset ar fortfarande over SMA50, men svagare candle-respons syns i
  `close_position_in_range`.
- Senaste dagen ar rod och stanger langt ner i dagsrangen.
- ATR_pct ar hogre an ABB och INVE-B, men inte extrem i detta lilla urval.

Sanity slutsats:

`ERIC-B.ST` ar ett bra testfall for "bra trend men svag/djupare rekyl". Den bor
inte behandlas likadant som ABB nar scoring senare byggs. Features fangar detta
rimligt genom djupare pullback och svag close-position.

## INVE-B.ST

Senaste granskningsdatum: `2026-05-28`

Viktiga featurevarden:

```text
close_vs_sma50_pct         3.8228
close_vs_sma200_pct       14.8316
sma50_vs_sma200_pct       10.6035
sma50_slope_10d            1.1807
return_60d_pct             0.0397
pullback_depth_20d_pct    -2.5654
distance_to_sma20_atr      0.9558
distance_to_sma50_atr      2.1826
close_position_in_range    0.3733
is_green_candle            false
volume_vs_avg20            0.8418
atr14_pct                  1.6870
range_vs_atr14             0.5882
gap_pct                   -0.9916
```

Tolkning:

- Trendstruktur ar positiv men svagare an ABB och ERIC-B.
- `return_60d_pct` ar nastan neutral.
- Pullback depth ar modest, runt `-2.6%`.
- Priset ligger over SMA50/SMA200 men inte med samma styrka.
- Senaste candle ger svag resumption evidence.
- Volatiliteten ser lugnare ut.

Sanity slutsats:

`INVE-B.ST` ar ett bra testfall for mildare trend och lagre volatilitet. Den kan
vara konstruktiv, men featurebilden sager inte "stark prior strength" pa samma
satt som ABB.

## VOLV-B.ST

Senaste granskningsdatum: `2026-05-28`

Viktiga featurevarden:

```text
close_vs_sma50_pct         3.6904
close_vs_sma200_pct       11.3989
sma50_vs_sma200_pct        7.4342
sma50_slope_10d           -0.1535
return_60d_pct            -8.0728
pullback_depth_20d_pct    -3.4339
distance_to_sma20_atr      0.6584
distance_to_sma50_atr      1.8065
close_position_in_range    0.7736
is_green_candle            true
volume_vs_avg20            0.8920
atr14_pct                  1.9701
range_vs_atr14             0.8318
gap_pct                   -0.9533
```

Tolkning:

- Priset ligger over SMA50 och SMA200, men prior strength ar svag.
- `return_60d_pct` ar negativ.
- `sma50_slope_10d` ar fortfarande svagt negativ.
- Senaste candle ser starkare ut via close-position och green candle.
- Detta ar exakt den typ av case dar en gron candle inte far radda svagare
  trend.

Sanity slutsats:

`VOLV-B.ST` ar ett viktigt kontrollcase. Featurelagret visar bade positiv
senaste candle och svagare trend/prior strength. Det passar Pullback-specens
beroendeprincip: resumption evidence ska inte ensam skapa en stark pullback.

## Slutsats for MVP

Featurelagret verkar tillrackligt begripligt for att ga vidare till en forsta
enkel Pullback-scoringhypotes.

Viktiga observationer:

- ABB och ERIC-B visar starkare trend/prior strength an INVE-B och VOLV-B.
- ERIC-B visar hur en djupare rekyl med svag close-position kan skiljas fran en
  grundare pullback.
- INVE-B visar mildare trend och lugnare volatilitet.
- VOLV-B visar varfor positiv candle-respons inte ska overtrumfa svagare trend.

Inga nya features foreslas i detta steg.

## Nasta steg

Nasta steg ar att formulera och koda en forsta smal `PULLBACK_SCORING_V1` som
endast anvander MVP-features fran `docs/feature_definitions_v1.md`.

Scoring ska fortsatt folja blocken i `docs/pullback_scoring_spec_v1.md`:

```text
Trend / prior strength          0-40
Pullback quality / location     0-30
Resumption evidence             0-20
Risk / tradability              0-10
```

Ingen entry, stop-loss, target, position sizing eller ny strategi ska byggas i
nasta steg.
