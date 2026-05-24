from __future__ import annotations

import json
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen


EODHD_BASE_URL = "https://eodhd.com/api/eod"


def fetch_eod(symbol: str, api_key: str, from_date: date | None = None) -> list[dict]:
    params = {
        "api_token": api_key,
        "fmt": "json",
        "period": "d",
    }
    if from_date:
        params["from"] = from_date.isoformat()

    url = f"{EODHD_BASE_URL}/{symbol.upper()}?{urlencode(params)}"
    with urlopen(url, timeout=30) as response:
        payload = response.read().decode("utf-8")

    data = json.loads(payload)
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(data["error"])
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected response from EODHD for {symbol}: {data}")
    return data
