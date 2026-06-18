"""Build IATA airline code → name map from OpenFlights data."""

import csv
import json
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "airline_codes.json"
OPENFLIGHTS = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat"


def main() -> None:
    raw = urllib.request.urlopen(OPENFLIGHTS, timeout=60).read().decode("utf-8", errors="replace")
    codes: dict[str, str] = {}
    for row in csv.reader(raw.splitlines()):
        if len(row) < 8:
            continue
        name, iata = row[1], row[3]
        if iata and iata != "\\N" and len(iata) == 2:
            codes[iata.upper()] = name
    OUT.write_text(json.dumps(codes, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(codes)} airline codes to {OUT}")


if __name__ == "__main__":
    main()
