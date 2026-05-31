# Pullback Scoring Checkpoint 2026-05-29

Detta ar en kort checkpoint av forsta sparade `PULLBACK_SCORING_V1`-resultatet
efter `daily-update` och `score-strategies` for 2026-05-29.

Checkpointen ar inte en trade-plan och inte en koprekommendation. Syftet ar att
se om dagens toppar beter sig rimligt relativt `docs/pullback_scoring_spec_v1.md`
och `docs/feature_definitions_v1.md`.

## Underlag

CLI-kommandon:

```powershell
.\.venv\Scripts\python.exe -m app.cli show-top-setups --date 2026-05-29 --limit 20
.\.venv\Scripts\python.exe -m app.cli inspect-pullback-score <TICKER> --rows 1
.\.venv\Scripts\python.exe -m app.cli inspect-features <TICKER> --rows 1
```

Resultatet inneholl 1008 sparade Pullback-score-rader.

## Topplista

```text
Ticker      Strategy              Heat  Status
ERIC-B.ST   PULLBACK_SCORING_V1   95    HOT
ABB.ST      PULLBACK_SCORING_V1   81    HOT
INVE-B.ST   PULLBACK_SCORING_V1   78    CANDIDATE
VOLV-B.ST   PULLBACK_SCORING_V1   63    WATCH
```

## Scorebreakdown

```text
Ticker      Trend  Pullback  Resumption  Risk  Heat  Status
ERIC-B.ST   40     25        20          10    95    HOT
ABB.ST      40     13        18          10    81    HOT
INVE-B.ST   35     13        20          10    78    CANDIDATE
VOLV-B.ST   24     13        16          10    63    WATCH
```

## Snabb tolkning

`ERIC-B.ST` ar dagens renaste Pullback-case i modellen. Den har maximal trend,
tydlig faktisk rekyl fran 20D-high, stark dagsstangning, hog volym relativt
20D-snitt och normal riskbild. Detta matchar specens ideal om stark trend,
kontrollerad rekyl och aterkommande kopare.

`ABB.ST` far HOT framst genom mycket stark trend och stark respons, men
pullback-delen ar betydligt svagare. Rekylen ar bara cirka -2.2 procent fran
20D-high. Det ar rimligt att den blir hogt rankad som kandidat, men den bor
granskas visuellt for att avgora om den ar en verklig pullback eller redan mer
momentum/continuation.

`INVE-B.ST` liknar ABB i scoreprofil men med svagare trendblock. Den far mycket
resumption evidence pa stark close och hog volym, medan rekylen fortfarande ar
grund. CANDIDATE verkar rimligare an HOT eftersom prior strength inte ar lika
tydlig.

`VOLV-B.ST` fungerar som kontrollcase. Responsen ar stark, men trend/prior
strength ar svagare och `return_60d_pct` ar negativ. WATCH ar darfor rimligt:
en gron responsdag far inte ensam gora caset till en stark Pullback.

## Sanity slutsats

Resultatet verkar principiellt rimligt for MVP:

- stark trend + faktisk rekyl + respons lyfter ERIC-B tydligt
- stark trend utan djupare rekyl kan fortfarande rankas hogt, men inte via
  pullbackblocket
- svagare prior strength haller VOLV-B nere trots bra respons
- riskblocket ar inte drivande, vilket passar specens roll for risk/tradability

Viktig observationspunkt for nasta manuella granskning:

```text
ABB.ST och INVE-B.ST bor granskas som mojliga grunda pullbacks eller
momentum-handoff, eftersom deras pullback_score bara ar 13 medan resumption
och trend driver total heat.
```

Inga nya features foreslas i denna checkpoint.
