"""Airline reference data for flight offer details."""

AIRLINES: list[tuple[str, str]] = [
    ("Lufthansa", "LH"),
    ("Ryanair", "FR"),
    ("easyJet", "U2"),
    ("Wizz Air", "W6"),
    ("Turkish Airlines", "TK"),
    ("Air France", "AF"),
    ("British Airways", "BA"),
    ("KLM", "KL"),
    ("Swiss", "LX"),
    ("Aegean Airlines", "A3"),
    ("Pegasus Airlines", "PC"),
    ("Qatar Airways", "QR"),
    ("Emirates", "EK"),
    ("Singapore Airlines", "SQ"),
    ("Air Serbia", "JU"),
    ("Edelweiss Air", "WK"),
    ("ITA Airways", "AZ"),
    ("Vueling", "VY"),
    ("Norwegian", "DY"),
    ("TAP Air Portugal", "TP"),
]

CODE_TO_NAME: dict[str, str] = {code: name for name, code in AIRLINES}
