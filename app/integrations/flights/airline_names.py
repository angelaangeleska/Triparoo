"""Resolve IATA airline codes to carrier names."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.integrations.flights.airlines import CODE_TO_NAME

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "airline_codes.json"


@lru_cache(maxsize=1)
def _load_codes() -> dict[str, str]:
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return dict(CODE_TO_NAME)


def airline_name(code: str, operating_code: str | None = None) -> str:
    codes = _load_codes()
    code = (code or "").upper()
    if code in codes:
        return codes[code]
    if operating_code and operating_code.upper() in codes:
        return codes[operating_code.upper()]
    if code in CODE_TO_NAME:
        return CODE_TO_NAME[code]
    return code
