# Pullback Theory Basis v1

Detta dokument ar en teoribrygga for Eodwins Pullback v1. Syftet ar att
minska risken att scoring och trade-plan blir en samling lokala filter som
uppfinns efter varje review-case.

Dokumentet andrar ingen kod. Det forklarar:

- vilken pullback-teori projektet faktiskt anvander idag
- vilka delar som har starkare externt stod
- vilka delar som ar praktiska MVP-proxies eller lokala hypoteser
- vilka gap som finns mellan chartlogik och nuvarande kod
- hur review-cases ska anvandas utan att overanpassa modellen

## Nuvarande Pullback v1-teori

Pullback v1 ar en long-only trendfoljande rekylmodell.

Den nuvarande teorin ar:

```text
stark tidigare trend
-> kontrollerad rekyl
-> nara rimlig MA-/supportzon
-> huvudtrenden ar inte skadad
-> kopare borjar komma tillbaka
-> risk/tradability ar rimlig
```

Det betyder att Pullback v1 inte forsoker kopa billigt i allman mening. Den
forsoker hitta en aktie som redan visat styrka, dar en rekyl skapat ett
potentiellt battre planeringslage utan att den positiva trenden brutits.

## Arbetsdefinition: clean pullback

En clean pullback i Eodwin betyder:

- aktien hade tydlig styrka innan rekylen
- priset gjorde en identifierbar rekyl fran en relevant high eller range-high
- rekylen skedde mot ett rimligt omrade, exempelvis stigande SMA20/SMA50 eller
  annat lokalt stodomrade
- rekylen var tillracklig for att inte vara chase, men inte sa djup att den
  ser ut som trendbrott
- responsen kom relativt tidigt efter pullback-low eller efter test av zonen
- dagens struktur ger fortfarande en rimlig manuell planeringsfraga
- caset har inte redan blivit momentum, breakout, repair phase eller stale
  sideways-lage

Detta ar en chartlogisk definition. Kodens uppgift ar att approximera den
deterministiskt, inte att lata en enskild feature latsas vara hela charten.

## Referensramar

Pullback v1 ar inte en direkt implementation av en enskild bok eller trader.
Den ar en praktisk syntes av tre nara beslaktade ideer.

### Trend/momentum som karnedge

Projektets starkaste teoretiska ankare ar bredare trend- och momentumstod.
Detta ar redan dokumenterat i `strategy_development_method_v1.md` och
`pullback_scoring_spec_v1.md`.

Relevanta referenser i projektet:

- Jegadeesh och Titman (1993), momentum i aktier:
  https://ideas.repec.org/a/bla/jfinan/v48y1993i1p65-91.html
- Moskowitz, Ooi och Pedersen, time-series momentum:
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2089463
- Hurst, Ooi och Pedersen, trend following over lang historik:
  https://www.aqr.com/insights/research/journal-article/a-century-of-evidence-on-trend-following-investing

Implication for Eodwin:

```text
Trend/prior strength ar core. Utan tidigare styrka finns ingen Pullback v1.
```

### Klassisk teknisk trendfas och MA-struktur

Stan Weinsteins stage analysis ar en relevant praktisk referensram for att
tanka i trendfaser, MA, relativ styrka, volym, breakouts och pullbacks. Google
Books listar `Stage 2 advance`, `relative strength`, `pullback`, `uptrend` och
`volume` bland bokens centrala index-/amnesord:

https://books.google.com/books/about/Stan_Weinstein_s_Secrets_For_Profiting_i.html?id=RTB_yclEGqQC

Implication for Eodwin:

```text
MA-struktur ar en trendproxy, inte magi. Pullback v1 ska helst agera i en
konstruktiv advance/regim, inte i topping, repair eller fallande fas.
```

### Ledarskap, tajt struktur och att inte jaga for sent

Mark Minervinis SEPA/Trend Template/VCP-ramverk ar relevant som praktisk
tradingreferens for att filtrera pa stark trend forst och sedan soka
konstruktiv chartstruktur. En offentlig sammanfattning av Trend Template
beskriver starka trender, tighta konsolideringar/VCP, volym och att undvika
erratic/excessive volatility:

https://www.chartmill.com/documentation/stock-screener/technical-analysis-trading-strategies/496-Mark-Minervini-Trend-Template-A-Step-by-Step-Guide-for-Beginners

Implication for Eodwin:

```text
Forst trendkvalitet, sedan struktur/timing. Hog score far inte automatiskt
betyda planbarhet om priset redan ar for sent eller strukturen ar rorig.
```

### Buy points fran baser/konsolidering och riskdisciplin

William O'Neils CAN SLIM ar inte en ren pullbackmodell, men den ar relevant for
tva principer: ledande aktier ska kopas vid definierbara buy points nar de
kommer ur baser/konsolidering, och risk ska kapas disciplinerat. En offentlig
sammanfattning beskriver buy points fran price consolidation areas/bases och
loss cutting runt 7-8 procent:

https://en.wikipedia.org/wiki/CAN_SLIM

Implication for Eodwin:

```text
Trade-plan ska krava ett definierbart lage. Att en aktie ar stark eller har
hog heat racker inte for READY_PLAN.
```

## Evidence map for Pullback v1

| Princip | Roll | Stod | Eodwin-proxy idag | Kommentar |
| --- | --- | --- | --- | --- |
| Tidigare styrka/trend | core | starkare empiriskt stod via momentum/trend | `return_60d_pct`, `close_vs_sma200_pct`, `sma50_vs_sma200_pct`, `sma50_slope_10d` | Bor dominera scoring. |
| Konstruktiv MA-/regimstruktur | core/secondary | praktisk teknisk analys, indirekt empiriskt stod | SMA50/SMA200-relation, close over/under SMA50/SMA200 | MA ar proxy for trend/regim, inte garanti. |
| Faktisk rekyl fran relevant high | core | rimlig chartlogik, svagare exakt evidens | `rolling_high_20d`, `pullback_depth_20d_pct` | Storsta gapet: 20D-high ar inte samma sak som swing-high/pullback-start. |
| Location nara zon | secondary/core for setup | praktisk teknisk analys | `distance_to_sma20_atr`, `distance_to_sma50_atr` | Bra proxy, men maste tolkas ihop med sekvensen. |
| Tidig respons fran zon | timing/trade-plan | praktisk tradinglogik | `close_position_in_range`, `is_green_candle`, `volume_vs_avg20`, 5-10D observationer | Viktigt for READY_PLAN, men svagare som ensam edge. |
| Volymbekraftelse | timing/confirmation | rimligt stod, volym kan bara information | `volume_vs_avg20` | Borde senare jamfora responsvolym mot nedgangsvolym. |
| Undvik sent/extended lage | trade-plan/risk | praktisk tradinglogik | `setup_evolution`, distance to MA, green counts, local high/low | Nuvarande proxy ar ofullstandig. |
| Risk/tradability | risk | risklogik, inte core edge | `atr14_pct`, `range_vs_atr14`, `gap_pct` | Ska justera eller varna, inte definiera strategin. |

## Gap mellan teori och kod

### 1. Pullback-ben saknas

Teorin sager att vi vill se:

```text
relevant swing-high eller range-high
-> rekylben
-> test av zon
-> tidig respons
```

Nuvarande kod anvander:

```text
rolling_high_20d
pullback_depth_20d_pct
senaste 5-10 dagars observationer
```

Detta ar en MVP-proxy. Den kan lata aldre highs spoka och ge hog
pullback-score aven nar aktuell sekvens inte ar en clean pullback.

Konsekvens:

```text
Ett battre swing-high/pullback-leg-ankare ar troligen viktigare an fler sma
specialfilter.
```

### 2. Fresh response ar inte tydligt definierad

Teorin sager att READY_PLAN ska handla om planbarhet nu. En aktie kan rimligen
dyka upp flera dagar i rad, men varje READY ska fortfarande vara kopplad till
en farsk och planbar respons, inte bara ett gammalt pullback-case som fortfarande
har hog score.

Nuvarande kod har:

- `days_since_local_low_10d`
- `green_count_after_local_low`
- `already_bounced_from_pullback_low`
- `stale_near_ma_zone`
- `not_clean_pullback_sequence`

Men den saknar en tydlig modell for:

```text
forsta responsdag i aktuell pullback-sekvens
antal dagar sedan forsta respons
vad som nollstaller sekvensen
```

Konsekvens:

```text
Freshness bor designas efter pullback-ben/logik, inte som ett isolerat nytt
filter for ett enskilt Ericsson-case.
```

### 3. Strategihandoff ar ofardig

Teorin sager att Pullback ska forlora mot Momentum, Breakout eller Volatility
Compression nar charten inte langre ar en ren rekyl.

Nuvarande kod har bara Pullback scoring och Pullback trade-plan. Darmed maste
Pullback-lagret sjalvt satta warnings som `possible_momentum_handoff` eller
`SHALLOW_PULLBACK`, men det finns ingen konkurrerande strategi som faktiskt kan
ta over.

Konsekvens:

```text
En del "felaktiga" Pullback-cases kan egentligen vara ratt cases for framtida
Momentum/Breakout/Volatility Compression.
```

### 4. Volymmodellen ar grund

Teorin sager att volym ska hjalpa oss forsta deltagande. Nuvarande kod jamfor
oftast dagens volym mot 20D-snitt.

Senare kan battre volymfragor vara:

- ar responsvolym hogre an rekylens roddagsvolym?
- torkar volymen upp under rekylen?
- kommer volym in nar priset atertar zon?

Detta ska inte byggas forst, men det ar ett dokumenterat gap.

## Review-labels

Manuell review ska inte bara saga "bra" eller "dalig". Den ska satta stabila
etiketter som senare kan anvandas for att testa om koden ror sig i ratt
riktning.

Foreslagna labels:

```text
clean_pullback
early_response
acceptable_followup_ready
late_same_sequence
stale_near_ma
shallow_momentum
volatility_compression
repair_phase_or_old_high_anchor
failed_or_damaged
```

Preliminar anvandning pa diskuterade cases:

| Case | Preliminar label | Kommentar |
| --- | --- | --- |
| ERIC-B.ST 2026-05-29 | `clean_pullback`, `early_response` | Bedomdes okulart rimlig READY_PLAN. |
| INVE-B.ST 2026-04-30 | `clean_pullback` eller `acceptable_followup_ready` | Rimlig men inte perfekt READY_PLAN. |
| VOLV-B.ST 2026-06-02 | `volatility_compression` eller annan strategi | Inte ren Pullback v1. |
| INVE-B.ST 2026-05-07 | `late_same_sequence` | Redan studsat, aktuell dag svag/rod. |
| ERIC-B.ST 2026-04-23 | `stale_near_ma` | Sideways/stale nara MA, inte clean pullback. |
| ABB.ST 2026-04-02 | `not_clean_pullback`, `low_volume_response` | Lag volym och inte clean sekvens. |
| ABB.ST 2026-03-25 | `repair_phase_or_old_high_anchor` | Aldre high/reparationsfas, inte clean pullback. |
| ERIC-B.ST 2026-03-23 | `clean_pullback`, `early_response` | Ser mer clean ut an ERIC-B.ST 2026-04-23. |
| ERIC-B.ST 2026-03-27 | `acceptable_followup_ready` eller `late_same_sequence` | Oppet reviewbeslut. |
| ERIC-B.ST 2026-03-30 | `acceptable_followup_ready` eller `late_same_sequence` | Oppet reviewbeslut. |
| ERIC-B.ST 2026-04-01 | `late_same_sequence`? | Anvandaren tycker den ser mindre clean ut an 2026-03-23 trots liknande score. |

## Designprinciper innan nasta kodandring

Innan fler trade-plan-filter kodas ska nasta andring kunna svara pa:

1. Vilken teoriprincip approximera regeln?
2. Ar principen core, secondary, timing, risk eller lokal hypotes?
3. Vilket chartfenomen forsoker regeln fanga?
4. Varfor loser inte befintliga features detta?
5. Vilka review-cases ska regeln hjalpa?
6. Vilka review-cases far regeln inte forstora?
7. Ar regeln en tillfallig proxy eller ett steg mot ett battre pullback-ben?

## Rekommenderad nasta ordning

1. Satt review-labels pa kvarvarande READY_PLAN utan kodandring.
2. Bestam om ERIC-B.ST 2026-03-27, 2026-03-30 och 2026-04-01 ar
   `acceptable_followup_ready` eller `late_same_sequence`.
3. Designa sedan en kodbar proxy for ett pullback-ben eller fresh response.
4. Implementera minsta nodvandiga trade-plan-andring.
5. Kor review-kommandot igen och jamfor label-effekt.

Entry, stop, target och position sizing ska fortfarande vanta tills
READY_PLAN betyder ratt sak.
