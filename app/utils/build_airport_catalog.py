"""Rebuild app/data/global_airports.json from open data sources."""

import json
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "global_airports.json"


def main() -> None:
    with urllib.request.urlopen(
        "https://raw.githubusercontent.com/mwgg/Airports/master/airports.json", timeout=120
    ) as r:
        airports = json.load(r)
    with urllib.request.urlopen(
        "https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.json",
        timeout=60,
    ) as r:
        countries = json.load(r)
    code_to_name = {c["alpha-2"]: c["name"] for c in countries}

    records = []
    for _icao, ap in airports.items():
        iata = (ap.get("iata") or "").strip().upper()
        if not iata or len(iata) != 3 or iata == "N/A":
            continue
        lat, lon = ap.get("lat"), ap.get("lon")
        if lat is None or lon is None:
            continue
        cc = (ap.get("country") or "").upper()
        records.append(
            {
                "iata": iata,
                "name": (ap.get("name") or "").strip(),
                "city": (ap.get("city") or "").strip(),
                "country_code": cc,
                "country": code_to_name.get(cc, cc),
                "lat": round(float(lat), 6),
                "lng": round(float(lon), 6),
            }
        )

    records.sort(key=lambda x: (x["country"], x["city"], x["iata"]))
    OUT.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(records)} airports to {OUT}")


if __name__ == "__main__":
    main()
