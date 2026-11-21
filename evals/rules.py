"""Deterministic RSVP and song baseline.

Spanish and English keyword / number-word rules. Song requests use
'X de Y' and 'X by Y' (title then artist) and 'Y - X' (artist then title).
Anything else is ambiguous. Vague requests are not given a guessed title.
"""

from __future__ import annotations

import json
import re
import time
import unicodedata
from typing import Any

_NUMBER_WORDS = {
    "cero": 0,
    "zero": 0,
    "un": 1,
    "uno": 1,
    "una": 1,
    "one": 1,
    "dos": 2,
    "two": 2,
    "tres": 3,
    "three": 3,
    "cuatro": 4,
    "four": 4,
    "cinco": 5,
    "five": 5,
    "seis": 6,
    "six": 6,
    "siete": 7,
    "seven": 7,
    "ocho": 8,
    "eight": 8,
    "nueve": 9,
    "nine": 9,
    "diez": 10,
    "ten": 10,
    "once": 11,
    "eleven": 11,
    "doce": 12,
    "twelve": 12,
    "trece": 13,
    "thirteen": 13,
    "catorce": 14,
    "fourteen": 14,
    "quince": 15,
    "fifteen": 15,
}
_NUMBER_TOKEN = "|".join(sorted(_NUMBER_WORDS, key=len, reverse=True))
_NUMBER = rf"(?:\d+|{_NUMBER_TOKEN})"

_HARD_NO = re.compile(
    r"\b("
    r"no puedo|no podemos|no podre|no podremos|no voy|no vamos|"
    r"no ire|no iremos|no asisto|no asistimos|no puede ir|no pueden ir|"
    r"no va a poder|no van a poder|no se puede|"
    r"can't|cannot|won't|will not|not coming|unable to|we can't|i can't"
    r")\b"
)
_YES = re.compile(
    r"\b("
    r"vamos|voy|asistiremos|estaremos|llegaremos|confirmad[oa]|confirmo|"
    r"yes|yeah|yep|count us in|i'm coming|im coming|i am coming|"
    r"we'll be there|we will be there|si vamos|si voy|claro que si"
    r")\b"
)
_MAYBE = re.compile(
    r"\b("
    r"tal vez|quiza|quizas|puede ser|a lo mejor|maybe|perhaps|not sure|"
    r"no se|depende|ahi vemos|ya veremos|we'll see|we will see"
    r")\b"
)
_PARTY = re.compile(
    rf"\b(?:vamos|somos|seremos|asistiremos|estaremos|party of|we are|we're)\s+({_NUMBER})\b"
)
_PARTY_TRAIL = re.compile(rf"\b({_NUMBER})\s+(?:personas|people|adultos|adults|invitados|guests)\b")
_SOLO = re.compile(r"\b(?:solo yo|solamente yo|just me|only me|nada mas yo)\b")
_KIDS_ZERO = re.compile(r"\b(?:sin|no)\s+(?:ninos|ninas|hijos|hijas|kids|children)\b")
_KIDS_NUM = re.compile(
    rf"\b({_NUMBER})\s+(?:ninos|ninas|hijos|hijas|kids|children|cipotes|chiquitos|bebes)\b"
)
_KIDS_ONE = re.compile(
    r"\b(?:mi\s+(?:hijo|hija|nena|cipote)|my\s+(?:son|daughter|kid)|"
    r"(?:un|una|a)\s+(?:nino|nina|hijo|hija|kid|child|cipote|nena|bebe|chiquito))\b"
)
_RIDE_YES = re.compile(
    r"\b(?:ocup\w*\s+(?:un\s+)?(?:ride|raite|transporte)|necesit\w*\s+(?:un\s+)?(?:ride|raite|transporte|aventon)|"
    r"aventon|raite|que nos lleven|nos pueden llevar|needs? a ride|pick us up)\b"
)
_RIDE_NO = re.compile(
    r"\b(?:tenemos (?:carro|auto)|llevamos carro|we have a car|we'll drive|we will drive|"
    r"manejamos|no necesit\w*\s+ride|no ocupamos ride|no need a ride)\b"
)
_VEGAN = re.compile(r"\bvegan[oa]s?\b")
_VEGETARIAN = re.compile(r"\bvegetari\w*\b")
_GLUTEN = re.compile(r"\b(?:sin gluten|gluten[\s-]?free|celiac[oa]?)\b")
_KIDS_MENU = re.compile(r"\b(?:menu infantil|menu de ninos|kids menu|kids meal|comida de ninos)\b")
_ALLERGY = re.compile(
    r"\b(?:alergic\w*|alergia|allergic)\s+(?:al|a|to)\s+([a-z ]+?)(?=,|\.| y | and |$)"
)
_PARTIAL = re.compile(
    r"\b(?:ni idea|no te lo firme|los demas|el resto|no han contestado|"
    r"no te prometo|de ultimo|todavia no del todo)\b"
)
_ARTICLES = {"la", "el", "los", "las", "the", "una", "un", "the one"}
_SONG_PREFIX = re.compile(
    r"^(?:please play|play|ponme|ponnos|pon|quiero(?: escuchar)?|reproduce)\s+",
    re.IGNORECASE,
)
_SONG_SUFFIX = re.compile(r"\s+(?:por favor|please|que siempre ponen)$", re.IGNORECASE)
_DASH = re.compile(r"\s+[-–—]\s+")
_ENERGY = (
    ("dance", re.compile(r"\b(?:upbeat|bailable|para bailar|bailar|high energy|dance|movid[ao]s?|alta|alegre|merengue|salsa|cumbia)\b")),
    ("slow", re.compile(r"\b(?:slow|lenta|tranquil\w*|chill|bajita|low energy|romantic[ao]?|balada|vals|love song|cancion de amor)\b")),
    ("medium", re.compile(r"\b(?:medium|intermedia)\b")),
)


def fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    without = "".join(char for char in normalized if not unicodedata.combining(char))
    return without.replace("’", "'").casefold()


def _parse_number(token: str) -> int | None:
    if token.isdigit():
        return int(token)
    return _NUMBER_WORDS.get(token)


def _has_yes(folded: str) -> bool:
    for match in _YES.finditer(folded):
        prefix = folded[: match.start()]
        if re.search(r"\bno\s+$", prefix):
            continue
        return True
    stripped = folded.strip()
    if re.fullmatch(r"si[.!]?", stripped):
        return True
    if re.match(r"^si\s*[,.]", stripped):
        return True
    return False


def _meals(folded: str) -> list[str]:
    tags: list[str] = []
    if _VEGAN.search(folded):
        tags.append("vegan")
    if _VEGETARIAN.search(folded):
        tags.append("vegetarian")
    if _GLUTEN.search(folded):
        tags.append("gluten_free")
    if _KIDS_MENU.search(folded):
        tags.append("kids_menu")
    for match in _ALLERGY.finditer(folded):
        allergen = re.sub(r"^(?:la|el|los|las|the)\s+", "", match.group(1).strip())
        allergen = allergen.strip().replace(" ", "_")
        if allergen:
            tags.append(f"allergy:{allergen}")
    return sorted(set(tags))


def _kids(folded: str) -> int | None:
    if _KIDS_ZERO.search(folded):
        return 0
    numbered = _KIDS_NUM.search(folded)
    if numbered:
        return _parse_number(numbered.group(1))
    if _KIDS_ONE.search(folded):
        return 1
    return None


def _party(folded: str) -> int | None:
    match = _PARTY.search(folded) or _PARTY_TRAIL.search(folded)
    if match:
        return _parse_number(match.group(1))
    if _SOLO.search(folded):
        return 1
    return None


def _ride(folded: str) -> tuple[bool | None, bool]:
    """Return needs_ride and whether the reply mentioned transport.

    Unstated transport is null, matching the labeled pack. False is only
    for an explicit decline.
    """
    positive = _RIDE_YES.search(folded) is not None
    negative = _RIDE_NO.search(folded) is not None
    if negative:
        return False, True
    if positive:
        return True, True
    return None, False


def _rsvp_confidence(
    attending: str | None,
    ambiguous: bool,
    party_size: int | None,
    meals: list[str],
    kids_count: int | None,
    ride_explicit: bool,
) -> float:
    if ambiguous:
        return 0.55
    score = 0.75
    if attending == "yes" and party_size is not None:
        score += 0.10
    if meals or kids_count is not None or ride_explicit:
        score += 0.05
    return round(min(score, 0.99), 2)


def extract_rsvp(text: str, lang: str | None = None) -> dict[str, Any]:
    del lang  # language is a hint for the model backends; rules are bilingual
    folded = fold(text)
    hard_no = _HARD_NO.search(folded) is not None
    maybe = _MAYBE.search(folded) is not None
    yes = _has_yes(folded)
    partial = _PARTIAL.search(folded) is not None
    if hard_no and yes:
        # Contradictory replies stay unresolved. The gold schema still requires
        # an attending value, so the baseline uses maybe and flags ambiguous.
        attending = "maybe"
        ambiguous = True
    elif hard_no:
        attending = "no"
        ambiguous = False
    elif maybe:
        attending = "maybe"
        ambiguous = False
    elif yes:
        attending = "yes"
        ambiguous = False
    else:
        attending = "maybe"
        ambiguous = True
    if partial and not (hard_no and yes):
        ambiguous = True
    party_size = None if attending == "no" or (hard_no and yes) else _party(folded)
    meals = _meals(folded)
    kids_count = _kids(folded)
    needs_ride, ride_explicit = _ride(folded)
    confidence = _rsvp_confidence(attending, ambiguous, party_size, meals, kids_count, ride_explicit)
    return {
        "attending": attending,
        "party_size": party_size,
        "meal_restrictions": meals,
        "kids_count": kids_count,
        "needs_ride": needs_ride,
        "ambiguous": ambiguous,
        "confidence": confidence,
    }


def _clean_song_text(text: str) -> str:
    cleaned = text.strip().strip("\"'")
    cleaned = _SONG_PREFIX.sub("", cleaned)
    changed = True
    while changed:
        updated = _SONG_SUFFIX.sub("", cleaned)
        changed = updated != cleaned
        cleaned = updated
    return cleaned.strip()


def _article_only(value: str) -> bool:
    return fold(value) in _ARTICLES


def _energy(folded: str) -> str | None:
    for label, pattern in _ENERGY:
        if pattern.search(folded):
            return label
    return None


def _song_confidence(ambiguous: bool, title: str | None, artist: str | None) -> float:
    if not ambiguous and title and artist:
        return 0.92
    if ambiguous and not title:
        return 0.80 if artist else 0.70
    return 0.45


def extract_song(text: str, lang: str | None = None) -> dict[str, Any]:
    del lang
    cleaned = _clean_song_text(text)
    title: str | None = None
    artist: str | None = None
    ambiguous = True
    dashed = _DASH.split(cleaned, maxsplit=1)
    if len(dashed) == 2 and dashed[0].strip() and dashed[1].strip():
        artist, title = dashed[0].strip(), dashed[1].strip()
        ambiguous = _article_only(title) or _article_only(artist)
    else:
        by_match = re.search(r"^(.+?)\s+by\s+(.+)$", cleaned, flags=re.IGNORECASE)
        de_match = re.search(r"^(.+?)\s+de\s+(.+)$", cleaned, flags=re.IGNORECASE)
        match = by_match or de_match
        if match:
            left, right = match.group(1).strip(), match.group(2).strip()
            if _article_only(left):
                artist = right
                title = None
                ambiguous = True
            else:
                title, artist = left, right
                ambiguous = False
    if ambiguous:
        title = None
    energy = _energy(fold(text))
    return {
        "title": title,
        "artist": artist,
        "energy": energy,
        "ambiguous": ambiguous,
        "confidence": _song_confidence(ambiguous, title, artist),
    }


def extract(task: str, text: str, lang: str | None = None) -> dict[str, Any]:
    if task == "rsvp":
        return extract_rsvp(text, lang)
    if task == "song":
        return extract_song(text, lang)
    raise ValueError(f"rules backend has no extractor for task {task!r}")


def predict_item(item: dict[str, Any]) -> dict[str, Any]:
    """Score one row from its text only. Gold fields on the row are ignored."""
    started = time.perf_counter()
    output = extract(item["task"], item["text"], item.get("lang"))
    latency_ms = (time.perf_counter() - started) * 1000.0
    return {
        "id": item["id"],
        "task": item["task"],
        "split": item.get("split"),
        "lang": item.get("lang"),
        "ok": True,
        "error": None,
        "confidence": output["confidence"],
        "latency_ms": latency_ms,
        "output": output,
        "raw": json.dumps(output, ensure_ascii=False),
    }


def predict_all(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [predict_item(item) for item in items]
