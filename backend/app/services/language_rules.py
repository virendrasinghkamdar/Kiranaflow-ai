"""Kirana Hinglish / Hindi / English understanding rules.

The LLM never writes to the database. This layer only normalizes speech
into English catalog terms and unit-aware quantities.
"""

import re

# Spoken / misspelled product words → catalog search terms
SYNONYMS = {
    "aata": "atta",
    "aatta": "atta",
    "aataa": "atta",
    "gehun": "atta",
    "gehu": "atta",
    "wheat": "atta",
    "flour": "atta",
    "doodh": "milk",
    "dudh": "milk",
    "tel": "oil",
    "tail": "oil",
    "namak": "salt",
    "namak": "salt",
    "cheeni": "sugar",
    "chini": "sugar",
    "shakkar": "sugar",
    "chawal": "rice",
    "chaawal": "rice",
    "daal": "dal",
    "daal": "dal",
    "sabun": "soap",
    "chai": "tea",
    "patti": "tea",
    "makhan": "butter",
    "dahi": "curd",
    "paneer": "paneer",
    "namkeen": "namkeen",
    "biscuit": "biscuit",
    "biskut": "biscuit",
    "noodles": "noodles",
    "maggie": "maggi",
    "aashirwad": "aashirvaad",
    "ashirvad": "aashirvaad",
    "ashirwad": "aashirvaad",
    "patanjli": "patanjali",
    "fortune": "fortune",
}

UNIT_ALIASES = {
    "kilo": "kg",
    "keelo": "kg",
    "kilos": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "kg": "kg",
    "litre": "l",
    "liter": "l",
    "litres": "l",
    "liters": "l",
    "ltr": "l",
    "packet": "pack",
    "packets": "pack",
    "packt": "pack",
    "pack": "pack",
    "packs": "pack",
    "pkt": "pack",
    "pcs": "pack",
    "piece": "pack",
    "pieces": "pack",
    "bottle": "bottle",
    "bottles": "bottle",
    "gm": "g",
}

GENERIC_PRODUCTS = {
    "atta", "oil", "milk", "rice", "dal", "salt", "sugar", "tea",
    "soap", "noodles", "biscuit", "bread", "ghee", "curd", "paneer",
    "namkeen", "shampoo", "detergent",
}

REPEAT_PHRASES = (
    "repeat last", "repeat order", "last order", "same as last",
    "pichla order", "pichhla", "pichla wala", "wahi wala",
    "wahi order", "dobara bhej", "same order", "phir se wahi",
)

NUMBER_WORDS = {
    "ek": 1, "एक": 1, "one": 1,
    "do": 2, "दो": 2, "two": 2,
    "teen": 3, "तीन": 3, "three": 3,
    "char": 4, "चार": 4, "four": 4,
    "paanch": 5, "panch": 5, "पांच": 5, "five": 5,
    "cheh": 6, "chhe": 6, "छह": 6, "six": 6,
    "saat": 7, "सात": 7, "seven": 7,
    "aath": 8, "आठ": 8, "eight": 8,
    "nau": 9, "नौ": 9, "nine": 9,
    "das": 10, "दस": 10, "ten": 10,
}


def canonicalize_text(text: str) -> str:
    t = (text or "").lower().strip()
    t = t.replace("aashirwad", "aashirvaad").replace("ashirvad", "aashirvaad")
    for src, dst in SYNONYMS.items():
        t = re.sub(rf"\b{re.escape(src)}\b", dst, t)
    return t


def is_repeat_request(message: str) -> bool:
    t = (message or "").lower()
    return any(p in t for p in REPEAT_PHRASES)


def is_generic_query(query: str) -> bool:
    tokens = canonicalize_text(query).split()
    return len(tokens) == 1 and tokens[0] in GENERIC_PRODUCTS


def extract_qty_unit_product(segment: str) -> tuple:
    """
    Parse '2 kilo aata' → (2, 'kg', 'atta')
    Parse 'do packet maggi' → (2, 'pack', 'maggi')
    """
    segment = canonicalize_text(segment)
    if not segment:
        return 1, "", ""

    unit_alt = "|".join(re.escape(k) for k in sorted(UNIT_ALIASES.keys(), key=len, reverse=True))
    num_words = "|".join(re.escape(k) for k in sorted(NUMBER_WORDS.keys(), key=len, reverse=True))

    match = re.match(rf"^(\d+)\s+(?:({unit_alt})\s+)?(.+)$", segment)
    if match:
        qty = int(match.group(1))
        unit = UNIT_ALIASES.get((match.group(2) or "").strip(), "")
        product = (match.group(3) or "").strip()
        return max(1, qty), unit, product

    match = re.match(rf"^(\d+)\s*({unit_alt})\s+(.+)$", segment)
    if match:
        qty = int(match.group(1))
        unit = UNIT_ALIASES.get((match.group(2) or "").strip(), "")
        product = (match.group(3) or "").strip()
        return max(1, qty), unit, product

    match = re.match(rf"^({num_words})\s+(?:({unit_alt})\s+)?(.+)$", segment)
    if match:
        qty = NUMBER_WORDS[match.group(1)]
        unit = UNIT_ALIASES.get((match.group(2) or "").strip(), "")
        product = (match.group(3) or "").strip()
        return max(1, qty), unit, product

    match = re.match(r"^(.+?)\s+(\d+)$", segment)
    if match:
        return max(1, int(match.group(2))), "", match.group(1).strip()

    return 1, "", segment


def matches_are_ambiguous(query: str, scored: list) -> bool:
    """True when the operator should ask the customer to pick a brand."""
    if not scored or len(scored) < 2:
        return False
    top = scored[0]["score"]
    close = [s for s in scored if s["score"] >= max(0.72, top - 0.15)]
    brands = {getattr(s["product"], "brand", "") for s in close}
    if is_generic_query(query) and len(close) >= 2:
        return True
    if len(close) >= 2 and len(brands) >= 2 and top < 0.97:
        return True
    return False
