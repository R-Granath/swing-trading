# Swing Trading

Projekt for att stegvis bygga verktyg for marknadsdata, strategier, loggning och analys.

## Python-miljo

Projektet har en egen lokal Python-miljo i `.venv/`.

Aktivera miljon i PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Kontrollera Python-version:

```powershell
python --version
```

## Nuvarande struktur

```text
app/
tests/
data/private/
```

- `app/`: plats for programmets kod.
- `tests/`: plats for tester som kontrollerar att koden fungerar.
- `data/private/`: lokal privat data som inte ska laddas upp till GitHub.

## Framtida riktning

Projektet kan senare utokas med:

- marknadsdata
- tradingjournal
- strategitester
- risk- och portfoljanalys
- rapporter
