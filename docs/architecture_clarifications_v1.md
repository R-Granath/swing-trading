# Architecture Clarifications v1

Detta dokument fortydligar arkitekturgranser som vuxit fram under Pullback
v1-arbetet. Det ersatter inte README och ska inte skapa en ny parallell vision.

## Relation till README

`README.md` ar fortsatt overgripande source of truth for Eodwins vision och
MVP-riktning: end-of-day swingtradingagent, deterministisk screening,
trade-planering, journal, uppfoljning, mentor/LLM-stod, manuell orderlaggning
och ingen automatisk exekvering.

Detta dokument ar smalare. Det fangar lagerordningen och ansvarsforskjutningen
som blivit tydligare under Pullback v1.

## Pipeline

Eodwins strategi- och planeringsflode ska byggas i lager:

```text
datahamtning
-> indikatorer
-> features
-> scoring
-> trade-plan
-> setup_evolution baserat pa senaste 5-10 candles
-> preliminar risk/reward-hypotes
-> senare entry/stop/target/position sizing
-> rapport/e-mail/UI/LLM-dialog
```

Pullback v1 har gjort separationen sarskilt viktig:

- `PULLBACK_SCORING_V1` rankar kandidater.
- `PULLBACK_TRADE_PLAN_V1` ska senare tolka planbarhet, setup-process och
  preliminar risk/reward.
- Entry, stop, target och position sizing ska komma efter planstatus,
  setup_evolution och risk/reward-hypotes, inte blandas in i scoring.

## Python och LLM

Princip:

```text
Python = deterministisk berakning, ranking, planstatus, risk och reproducerbar logik
LLM = forklaring, sammanfattning, rapportering, mentor/dialog och pedagogiskt stod
```

LLM ska inte vara primar regelmotor. LLM ska inte sjalv besluta att nagot ar
`HOT`, `READY_PLAN`, `RR_GOOD`, `FAILED` eller liknande. Sadana
klassificeringar ska komma fran Python och vara reproducerbara.

LLM kan daremot forklara varfor Python gav ett visst resultat, sammanfatta
dagens kandidater, hjalpa anvandaren att forsta risk och bidra med mentorstod.

## Dagligt e-mail

Dagligt e-mail bor pa sikt baseras pa bade `PULLBACK_SCORING_V1` och framtida
`PULLBACK_TRADE_PLAN_V1`, inte bara hogsta score.

Ett utskick kan exempelvis innehalla:

- `READY_PLAN`-kandidater
- starka `WATCH_PLAN`-kandidater
- `LATE_PLAN` eller skipped med kort motivering
- hog score men svag planbarhet som caution/skipped

Det gor att en ticker med hog heat men svag trade-plan inte automatiskt blir
dagens basta tips.

## Setup evolution

`setup_evolution` ar en viktig Pullback v1-komponent. Den anvander senaste
5-10 OHLCV/candles och MVP-features for att forsta var caset befinner sig i
pullback-processen.

I MVP ska `setup_evolution` vara ett klassificerings- och motiveringslager, inte
ett aggressivt filter. `PULLING_BACK` och `STABILIZING` ska normalt kunna leva
vidare som `WATCH_PLAN`; endast `FAILED` och tydligt dalig risk/reward ska vara
hart negativa.

## Changelog-roll

`CHANGELOG.md` ska anvandas for detaljerade arbetspass, kommandon, testlage,
lokal dataeffekt och exakt vad som byggdes.

Detta dokument ska bara fanga arkitekturprinciper som bor styra fortsatt design
och implementation.
