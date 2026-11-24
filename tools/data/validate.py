#!/usr/bin/env python3
"""Validate the Boda Lista synthetic data pack.

Stdlib plus optional rapidfuzz. If rapidfuzz is not installed, leak
checks fall back to difflib and print a warning.
"""

from __future__ import annotations

import difflib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"

MEAL_TAGS = {"vegetarian", "vegan", "gluten_free", "kids_menu"}
ALLERGY_RE = re.compile(r"^allergy:[a-z][a-z0-9_]{0,31}$")
ATTENDING = {"yes", "no", "maybe"}
SPLITS = {"dev", "test", "stress"}
LANGS = {"es", "en"}
ENERGY = {"slow", "medium", "dance"}
EMAIL_RE = re.compile(r"^[^@]+@([a-z0-9.-]*example\.com)$", re.I)
PHONE_RE = re.compile(r"(555[\d\- ]{4,}|5550|5551|5555|\+503 555)")

errors: list[str] = []
warnings: list[str] = []

SCHEMA_PATH = DATA / "schema.json"
UNKNOWN_ANSWER = "No tengo esa información, pregúntale a los novios"
UNKNOWN_ANSWER_EN = "I don't have that information, ask the couple"
UNKNOWN_BY_LANG = {"es": UNKNOWN_ANSWER, "en": UNKNOWN_ANSWER_EN}
LEAK_REPORT_PATH = DATA / "leak_report.json"
LEAK_THRESHOLD = 90

# Generated files checked for schema, split, and test-set leaks.
GENERATED_FILES = (
    {
        "name": "rsvp_dev_generated.jsonl",
        "task": "rsvp",
        "schema": "rsvp",
        "split": "dev",
        "count": 1500,
        "langs": {"es": 1200, "en": 300},
        "id_prefix": "dev-",
    },
    {
        "name": "rsvp_stress.jsonl",
        "task": "rsvp",
        "schema": "rsvp",
        "split": "stress",
        "count": 500,
        "langs": {"es": 400, "en": 100},
        "id_prefix": "stress-",
    },
    {
        "name": "song_dev_generated.jsonl",
        "task": "song",
        "schema": "song",
        "split": "dev",
        "count": 60,
        "langs": {"es": 48, "en": 12},
        "ambiguous": 15,
        "id_prefix": "dev-",
    },
    {
        "name": "guest_question_dev_generated.jsonl",
        "task": "guest_question",
        "schema": "guest_question",
        "split": "dev",
        "count": 120,
        "langs": {"es": 90, "en": 30},
        "out_of_scope": 40,
        "id_prefix": "dev-",
    },
)

LEAK_ENGINE = "rapidfuzz"
_fuzz_ratio = None


def _init_leak_engine() -> None:
    global LEAK_ENGINE, _fuzz_ratio
    try:
        from rapidfuzz import fuzz
    except ImportError:
        LEAK_ENGINE = "difflib"
        _fuzz_ratio = None
        print(
            "WARNING: rapidfuzz is not installed; falling back to "
            "difflib.SequenceMatcher for leak checks."
        )
        return
    LEAK_ENGINE = "rapidfuzz"
    _fuzz_ratio = fuzz.ratio


_init_leak_engine()


def normalize_text(text: str) -> str:
    """Lowercase and collapse whitespace, including ends."""
    return " ".join(text.lower().split())


def similarity(left: str, right: str) -> float:
    """Return a 0–100 ratio. rapidfuzz fuzz.ratio, or difflib if it is missing."""
    if _fuzz_ratio is not None:
        return float(_fuzz_ratio(left, right))
    return difflib.SequenceMatcher(None, left, right).ratio() * 100.0


def difflib_similarity(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, left, right).ratio() * 100.0


def length_bound(left: str, right: str) -> float:
    """Upper bound shared by fuzz.ratio and SequenceMatcher.ratio, on 0–100."""
    left_len = len(left)
    right_len = len(right)
    if left_len == 0 or right_len == 0:
        return 0.0
    return 200.0 * min(left_len, right_len) / (left_len + right_len)


def leak_stats(rows: list[dict], test_rows: list[dict], test_ids: set[str]) -> dict:
    """Count id collisions and same-task text leaks. Track the max ratio."""
    test_norms = [
        normalize_text(row["text"])
        for row in test_rows
        if isinstance(row.get("text"), str)
    ]
    text_leaks = 0
    id_leaks = 0
    max_sim = 0.0
    for row in rows:
        if row.get("id") in test_ids:
            id_leaks += 1
        norm = normalize_text(row["text"]) if isinstance(row.get("text"), str) else ""
        row_hit = False
        for other in test_norms:
            bound = length_bound(norm, other)
            if bound < LEAK_THRESHOLD and bound <= max_sim:
                continue
            score = similarity(norm, other)
            if score > max_sim:
                max_sim = score
            if score >= LEAK_THRESHOLD:
                row_hit = True
        if row_hit:
            text_leaks += 1
    return {
        "rows": len(rows),
        "text_leaks": text_leaks,
        "id_leaks": id_leaks,
        "max_similarity": round(max_sim, 2),
    }


def _is_type(instance, typ: str) -> bool:
    if typ == "null":
        return instance is None
    if typ == "boolean":
        return isinstance(instance, bool)
    if typ == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if typ == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if typ == "string":
        return isinstance(instance, str)
    if typ == "array":
        return isinstance(instance, list)
    if typ == "object":
        return isinstance(instance, dict)
    return False


def _resolve(schema: dict, root: dict) -> dict:
    ref = schema.get("$ref")
    if not ref:
        return schema
    if not ref.startswith("#/$defs/"):
        raise ValueError(f"unsupported $ref: {ref}")
    name = ref.split("/")[-1]
    return root["$defs"][name]


def _schema_errors(instance, schema, root: dict, path: str) -> list[str]:
    found: list[str] = []
    schema = _resolve(schema, root) if isinstance(schema, dict) and "$ref" in schema else schema
    if schema is True:
        return found
    if schema is False:
        return [f"{path}: not allowed"]
    if not isinstance(schema, dict):
        return [f"{path}: invalid schema"]

    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is_type(instance, typ) for typ in types):
            found.append(f"{path}: expected type {types}, got {type(instance).__name__}")
            return found

    if "const" in schema and instance != schema["const"]:
        found.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")

    if "enum" in schema and instance not in schema["enum"]:
        found.append(f"{path}: {instance!r} not in enum {schema['enum']!r}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            found.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            found.append(f"{path}: longer than maxLength {schema['maxLength']}")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            found.append(f"{path}: does not match pattern {schema['pattern']!r}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            found.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            found.append(f"{path}: above maximum {schema['maximum']}")

    if isinstance(instance, list) and "items" in schema:
        if "minItems" in schema and len(instance) < schema["minItems"]:
            found.append(f"{path}: fewer than minItems {schema['minItems']}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            found.append(f"{path}: more than maxItems {schema['maxItems']}")
        item_schema = schema["items"]
        for i, item in enumerate(instance):
            found.extend(_schema_errors(item, item_schema, root, f"{path}[{i}]"))

    if isinstance(instance, dict) and ("properties" in schema or "required" in schema or "additionalProperties" in schema):
        required = schema.get("required") or []
        for key in required:
            if key not in instance:
                found.append(f"{path}: missing required field {key!r}")
        props = schema.get("properties") or {}
        addl = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in props:
                found.extend(_schema_errors(value, props[key], root, f"{path}.{key}"))
            elif addl is False:
                found.append(f"{path}: unexpected field {key!r}")
            elif isinstance(addl, dict):
                found.extend(_schema_errors(value, addl, root, f"{path}.{key}"))

    if "if" in schema:
        if_errs = _schema_errors(instance, schema["if"], root, path)
        if not if_errs and "then" in schema:
            found.extend(_schema_errors(instance, schema["then"], root, path))
        if if_errs and "else" in schema:
            found.extend(_schema_errors(instance, schema["else"], root, path))

    if "allOf" in schema and isinstance(schema["allOf"], list):
        for sub in schema["allOf"]:
            found.extend(_schema_errors(instance, sub, root, path))

    return found


SCHEMA_ROOT: dict | None = None


def load_schema() -> dict | None:
    global SCHEMA_ROOT
    if not SCHEMA_PATH.is_file():
        err("missing file: data/schema.json")
        return None
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"schema.json: invalid JSON ({e})")
        return None
    if "$defs" not in schema:
        err("schema.json: missing $defs")
        return None
    for name in ("rsvp", "song", "guest_question", "wedding_info"):
        if name not in schema["$defs"]:
            err(f"schema.json: missing $defs.{name}")
    print("schema.json: loaded ($defs: rsvp, song, guest_question, wedding_info)")
    SCHEMA_ROOT = schema
    return schema


def check_against_schema(instance, schema_root: dict, def_name: str, where: str) -> None:
    if not schema_root:
        return
    definition = schema_root["$defs"][def_name]
    for message in _schema_errors(instance, definition, schema_root, where):
        err(f"schema/{def_name}: {message}")



def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        err(f"missing file: {path.relative_to(ROOT)}")
        return []
    rows = []
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                err(f"{path.name}:{i}: invalid JSON ({e})")
                continue
            if not isinstance(obj, dict):
                err(f"{path.name}:{i}: row is not an object")
                continue
            rows.append(obj)
    return rows


def load_json(path: Path):
    if not path.is_file():
        err(f"missing file: {path.relative_to(ROOT)}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"{path.name}: invalid JSON ({e})")
        return None


def require_keys(row: dict, keys: list[str], where: str) -> None:
    for k in keys:
        if k not in row:
            err(f"{where}: missing field {k!r}")


def check_common(row: dict, where: str, task: str) -> None:
    require_keys(row, ["id", "split", "task", "text", "lang"], where)
    if row.get("task") != task:
        err(f"{where}: task must be {task!r}, got {row.get('task')!r}")
    if row.get("split") not in SPLITS:
        err(f"{where}: split must be one of {sorted(SPLITS)}, got {row.get('split')!r}")
    if row.get("lang") not in LANGS:
        err(f"{where}: lang must be es|en, got {row.get('lang')!r}")
    text = row.get("text")
    if not isinstance(text, str) or not text.strip():
        err(f"{where}: text must be a non-empty string")
    rid = row.get("id")
    if not isinstance(rid, str) or not rid.strip():
        err(f"{where}: id must be a non-empty string")


def check_meals(meals, where: str) -> None:
    if not isinstance(meals, list):
        err(f"{where}: meal_restrictions must be a list")
        return
    for tag in meals:
        if not isinstance(tag, str):
            err(f"{where}: meal_restrictions tag is not a string: {tag!r}")
        elif tag in MEAL_TAGS or ALLERGY_RE.match(tag):
            continue
        else:
            err(
                f"{where}: invalid meal_restrictions tag {tag!r} "
                "(use vegetarian, vegan, gluten_free, kids_menu, or allergy:<x>)"
            )


def check_rsvp_row(row: dict, where: str) -> None:
    check_common(row, where, "rsvp")
    require_keys(row, ["attending", "party_size", "meal_restrictions"], where)
    if row.get("attending") not in ATTENDING:
        err(f"{where}: attending must be yes|no|maybe, got {row.get('attending')!r}")
    ps = row.get("party_size")
    if ps is not None and (not isinstance(ps, int) or isinstance(ps, bool) or ps < 1):
        err(f"{where}: party_size must be a positive int or null, got {ps!r}")
    check_meals(row.get("meal_restrictions"), where)
    if "ambiguous" in row and not isinstance(row.get("ambiguous"), bool):
        err(f"{where}: ambiguous must be bool")
    if "kids_count" in row:
        kc = row["kids_count"]
        if kc is not None and (not isinstance(kc, int) or isinstance(kc, bool) or kc < 0):
            err(f"{where}: kids_count must be a non-negative int or null")
    if "needs_ride" in row:
        nr = row["needs_ride"]
        if nr is not None and not isinstance(nr, bool):
            err(f"{where}: needs_ride must be bool or null")
    if "household_id" in row and row["household_id"] is not None:
        if not isinstance(row["household_id"], str) or not row["household_id"]:
            err(f"{where}: household_id must be a string")


def check_song_row(row: dict, where: str) -> None:
    check_common(row, where, "song")
    require_keys(row, ["title", "artist", "ambiguous"], where)
    amb = row.get("ambiguous")
    if not isinstance(amb, bool):
        err(f"{where}: ambiguous must be bool")
        return
    title, artist = row.get("title"), row.get("artist")
    if amb:
        if title is not None:
            err(f"{where}: ambiguous song must have title=null, got {title!r}")
        if artist is not None and not isinstance(artist, str):
            err(f"{where}: artist must be a string or null")
        if isinstance(artist, str) and not artist.strip():
            err(f"{where}: artist string must be non-empty or null")
    else:
        if not isinstance(title, str) or not title.strip():
            err(f"{where}: clear song must have a non-empty title")
        if not isinstance(artist, str) or not artist.strip():
            err(f"{where}: clear song must have a non-empty artist")
    if "energy" in row:
        en = row["energy"]
        if en is not None and en not in ENERGY:
            err(f"{where}: energy must be slow|medium|dance or null, got {en!r}")


def unique_ids(rows: list[dict], label: str) -> set[str]:
    ids = []
    for i, row in enumerate(rows, 1):
        if isinstance(row.get("id"), str):
            ids.append(row["id"])
    dup = [k for k, v in Counter(ids).items() if v > 1]
    if dup:
        err(f"{label}: duplicate ids: {dup[:8]}{'...' if len(dup) > 8 else ''}")
    return set(ids)


def unique_texts(rows: list[dict], label: str) -> set[str]:
    texts = [r.get("text") for r in rows if isinstance(r.get("text"), str)]
    dup = [k for k, v in Counter(texts).items() if v > 1]
    if dup:
        err(f"{label}: duplicate texts ({len(dup)}): {dup[:3]!r}")
    return set(texts)


def print_dist(title: str, counter: Counter, total: int) -> None:
    print(f"  {title}:")
    for k, n in sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0]))):
        pct = (100.0 * n / total) if total else 0
        print(f"    {k}: {n} ({pct:.1f}%)")


def validate_rsvps() -> list[dict]:
    path = DATA / "rsvp_replies.jsonl"
    rows = load_jsonl(path)
    print(f"rsvp_replies.jsonl: {len(rows)} rows")
    if len(rows) != 300:
        err(f"rsvp_replies.jsonl: expected 300 rows, got {len(rows)}")
    for i, row in enumerate(rows, 1):
        check_rsvp_row(row, f"rsvp_replies.jsonl:{i}")
        if row.get("split") != "test":
            err(f"rsvp_replies.jsonl:{i}: hand-checked RSVPs must have split='test', got {row.get('split')!r}")
    unique_ids(rows, "rsvp_replies.jsonl")
    unique_texts(rows, "rsvp_replies.jsonl")

    if rows:
        n = len(rows)
        lang = Counter(r.get("lang") for r in rows)
        att = Counter(r.get("attending") for r in rows)
        amb = Counter(bool(r.get("ambiguous")) for r in rows)
        size_stated = sum(1 for r in rows if r.get("party_size") is not None)
        meals = sum(1 for r in rows if r.get("meal_restrictions"))
        print_dist("lang", lang, n)
        print_dist("attending", att, n)
        print_dist("ambiguous", Counter({"true" if k else "false": v for k, v in amb.items()}), n)
        print(f"  party_size stated: {size_stated} / {n}")
        print(f"  with meal_restrictions: {meals} / {n}")
        meal_tags = Counter()
        for r in rows:
            for t in r.get("meal_restrictions") or []:
                key = "allergy:*" if isinstance(t, str) and t.startswith("allergy:") else t
                meal_tags[key] += 1
        if meal_tags:
            print_dist("meal_restriction tags", meal_tags, meals)

        # Stratification: language x ambiguity
        if lang.get("es", 0) < 200:
            err(f"rsvp test set should be majority Spanish; es={lang.get('es', 0)}")
        if lang.get("en", 0) < 50:
            err(f"rsvp test set must be stratified by language; en={lang.get('en', 0)} (need >= 50)")
        if amb.get(True, 0) < 50:
            err(f"rsvp test set must be stratified by ambiguity; ambiguous={amb.get(True, 0)} (need >= 50)")
        for lang_code in ("es", "en"):
            subset = [r for r in rows if r.get("lang") == lang_code]
            n_amb = sum(1 for r in subset if r.get("ambiguous") is True)
            if subset and n_amb < 8:
                err(f"rsvp test set: lang={lang_code} has only {n_amb} ambiguous rows (need >= 8)")
        for value in ("yes", "no", "maybe"):
            if att.get(value, 0) < 20:
                err(f"rsvp test set: attending={value} has only {att.get(value, 0)} rows (need >= 20)")
    return rows


def validate_songs(households: set[str]) -> list[dict]:
    path = DATA / "song_requests.jsonl"
    if not path.exists():
        warn("song_requests.jsonl not found (optional until written)")
        return []
    rows = load_jsonl(path)
    print(f"song_requests.jsonl: {len(rows)} rows")
    if len(rows) != 60:
        err(f"song_requests.jsonl: expected 60 rows, got {len(rows)}")
    n_amb = 0
    for i, row in enumerate(rows, 1):
        check_song_row(row, f"song_requests.jsonl:{i}")
        if SCHEMA_ROOT:
            check_against_schema(row, SCHEMA_ROOT, "song", f"song_requests.jsonl:{i}")
        if row.get("split") != "test":
            err(f"song_requests.jsonl:{i}: hand-checked songs must have split='test', got {row.get('split')!r}")
        if row.get("ambiguous") is True:
            n_amb += 1
        hid = row.get("household_id")
        if households and hid and hid not in households:
            err(f"song_requests.jsonl:{i}: household_id {hid!r} not in guests/households")
    unique_ids(rows, "song_requests.jsonl")
    unique_texts(rows, "song_requests.jsonl")
    if rows:
        n = len(rows)
        print_dist("lang", Counter(r.get("lang") for r in rows), n)
        print_dist("ambiguous", Counter("true" if r.get("ambiguous") else "false" for r in rows), n)
        print_dist("energy", Counter(r.get("energy") for r in rows), n)
        if n_amb != 15:
            err(f"song_requests.jsonl: expected 15 ambiguous rows, got {n_amb}")
        langs = Counter(r.get("lang") for r in rows)
        if langs.get("en", 0) < 8 or langs.get("es", 0) < 30:
            err(f"song_requests.jsonl: language mix too thin: {dict(langs)}")
    return rows


def validate_guests() -> tuple[set[str], list[dict]]:
    path = DATA / "guests.jsonl"
    if not path.exists():
        warn("guests.jsonl not found")
        return set(), []
    rows = load_jsonl(path)
    print(f"guests.jsonl: {len(rows)} rows")
    if len(rows) != 150:
        err(f"guests.jsonl: expected 150 rows, got {len(rows)}")
    households = set()
    blocked = re.compile(r"\b(moran|ramirez|garc[ií]a)\b", re.I)
    for i, row in enumerate(rows, 1):
        require_keys(row, ["guest_id", "household_id", "first_name", "last_name"], f"guests.jsonl:{i}")
        hid = row.get("household_id")
        if isinstance(hid, str):
            households.add(hid)
        name = f"{row.get('first_name', '')} {row.get('last_name', '')}"
        if blocked.search(name):
            err(f"guests.jsonl:{i}: blocked real-family surname in {name!r}")
    unique_ids([{"id": r.get("guest_id")} for r in rows], "guests.jsonl")
    print(f"  households: {len(households)}")
    return households, rows


def validate_info() -> None:
    obj = load_json(DATA / "wedding_info.json")
    md = DATA / "info_sheet.md"
    if not md.is_file():
        err("missing file: data/info_sheet.md")
    if not isinstance(obj, dict):
        return
    print("wedding_info.json: present")
    if SCHEMA_ROOT and isinstance(obj, dict):
        check_against_schema(obj, SCHEMA_ROOT, "wedding_info", "wedding_info.json")
    if obj.get("synthetic") is not True:
        err("wedding_info.json: must set synthetic=true")
    for key in ("couple", "schedule", "venue", "dress_code", "parking", "gifts", "contacts"):
        if key not in obj:
            err(f"wedding_info.json: missing key {key!r}")
    contacts = obj.get("contacts") or []
    if not isinstance(contacts, list) or len(contacts) < 1:
        err("wedding_info.json: contacts must be a non-empty list")
    else:
        for i, c in enumerate(contacts):
            email = c.get("email") if isinstance(c, dict) else None
            phone = c.get("phone") if isinstance(c, dict) else None
            if email and not EMAIL_RE.search(str(email)):
                err(f"wedding_info.json contacts[{i}]: email must use example.com, got {email!r}")
            if phone and not PHONE_RE.search(str(phone)):
                err(f"wedding_info.json contacts[{i}]: phone must be a 555-style fake number, got {phone!r}")
    if md.is_file():
        text = md.read_text(encoding="utf-8")
        print(f"info_sheet.md: {len(text.splitlines())} lines")
        if "synthetic" not in text.lower() and "ficticio" not in text.lower() and "fictional" not in text.lower():
            err("info_sheet.md: must be clearly marked synthetic/fictional")


def validate_vendors() -> None:
    path = DATA / "vendor_quotes.jsonl"
    if not path.exists():
        warn("vendor_quotes.jsonl not found")
        return
    rows = load_jsonl(path)
    print(f"vendor_quotes.jsonl: {len(rows)} rows")
    if len(rows) < 5:
        err(f"vendor_quotes.jsonl: expected at least 5 quotes, got {len(rows)}")
    for i, row in enumerate(rows, 1):
        require_keys(
            row,
            ["id", "vendor_type", "vendor_name", "amount_usd"],
            f"vendor_quotes.jsonl:{i}",
        )


def validate_questions() -> list[dict]:
    path = DATA / "guest_questions.jsonl"
    if not path.exists():
        warn("guest_questions.jsonl not found (optional)")
        return []
    rows = load_jsonl(path)
    print(f"guest_questions.jsonl: {len(rows)} rows")
    if len(rows) < 30:
        err(f"guest_questions.jsonl: expected at least 30 questions, got {len(rows)}")
    unknown = 0
    for i, row in enumerate(rows, 1):
        require_keys(row, ["id", "split", "task", "text", "lang", "answer", "out_of_scope"], f"guest_questions.jsonl:{i}")
        if SCHEMA_ROOT:
            check_against_schema(row, SCHEMA_ROOT, "guest_question", f"guest_questions.jsonl:{i}")
        if row.get("lang") not in LANGS:
            err(f"guest_questions.jsonl:{i}: lang must be es|en")
        if row.get("split") != "test":
            err(f"guest_questions.jsonl:{i}: hand-checked questions must have split='test'")
        if row.get("out_of_scope") is True:
            unknown += 1
            if row.get("answer") != UNKNOWN_ANSWER:
                err(
                    f"guest_questions.jsonl:{i}: out-of-scope answer must be exactly "
                    f"{UNKNOWN_ANSWER!r}, got {row.get('answer')!r}"
                )
        elif row.get("answer") == UNKNOWN_ANSWER:
            err(f"guest_questions.jsonl:{i}: in-scope row uses the out-of-scope phrase")
    if rows and unknown < 5:
        err(f"guest_questions.jsonl: need at least 5 out-of-scope answers, got {unknown}")
    unique_ids(rows, "guest_questions.jsonl")
    unique_texts(rows, "guest_questions.jsonl")
    print(f"  out-of-scope answers: {unknown}")
    print_dist("lang", Counter(r.get("lang") for r in rows), len(rows) or 1)
    return rows


def _check_guest_answer(row: dict, where: str) -> None:
    """Out-of-scope gold must be the refusal for the row's language."""
    expected = UNKNOWN_BY_LANG.get(row.get("lang"))
    if row.get("out_of_scope") is True:
        if expected is None or row.get("answer") != expected:
            err(
                f"{where}: out-of-scope answer for lang {row.get('lang')!r} must be exactly "
                f"{expected!r}, got {row.get('answer')!r}"
            )
    elif row.get("answer") in UNKNOWN_BY_LANG.values():
        err(f"{where}: in-scope row uses an out-of-scope phrase")


def validate_generated(test_rows_by_task: dict[str, list[dict]], test_ids: set[str], households: set[str]) -> None:
    report_files: dict[str, dict] = {}
    for spec in GENERATED_FILES:
        name = spec["name"]
        path = DATA / name
        rows = load_jsonl(path)
        print(f"{name}: {len(rows)} rows")
        for i, row in enumerate(rows, 1):
            where = f"{name}:{i}"
            if spec["task"] == "rsvp":
                check_rsvp_row(row, where)
            elif spec["task"] == "song":
                check_song_row(row, where)
            else:
                check_common(row, where, "guest_question")
                require_keys(row, ["answer", "out_of_scope"], where)
                _check_guest_answer(row, where)
            if SCHEMA_ROOT:
                check_against_schema(row, SCHEMA_ROOT, spec["schema"], where)
            if row.get("split") != spec["split"]:
                err(f"{where}: split must be {spec['split']!r}, got {row.get('split')!r}")
            if row.get("split") == "test":
                err(f"{where}: generated rows must never use split=test")
            rid = row.get("id")
            if isinstance(rid, str) and not rid.startswith(spec["id_prefix"]):
                err(f"{where}: id {rid!r} must start with {spec['id_prefix']!r}")
            hid = row.get("household_id")
            if households and hid and hid not in households:
                err(f"{where}: household_id {hid!r} not in guests/households")
        unique_ids(rows, name)
        unique_texts(rows, name)
        if len(rows) != spec["count"]:
            err(f"{name}: expected {spec['count']} rows, got {len(rows)}")
        if rows:
            langs = Counter(row.get("lang") for row in rows)
            print_dist("lang", langs, len(rows))
            for code, expected in spec.get("langs", {}).items():
                if langs.get(code, 0) != expected:
                    err(f"{name}: lang {code} expected {expected}, got {langs.get(code, 0)}")
        if "ambiguous" in spec:
            n_amb = sum(1 for row in rows if row.get("ambiguous") is True)
            print(f"  ambiguous: {n_amb}")
            if n_amb != spec["ambiguous"]:
                err(f"{name}: expected {spec['ambiguous']} ambiguous rows, got {n_amb}")
        if "out_of_scope" in spec:
            n_oos = sum(1 for row in rows if row.get("out_of_scope") is True)
            print(f"  out-of-scope answers: {n_oos}")
            if n_oos != spec["out_of_scope"]:
                err(f"{name}: expected {spec['out_of_scope']} out-of-scope rows, got {n_oos}")
        stats = leak_stats(rows, test_rows_by_task.get(spec["task"], []), test_ids)
        report_files[name] = stats
        print(
            f"  leaks: text={stats['text_leaks']} id={stats['id_leaks']} "
            f"max_similarity={stats['max_similarity']}"
        )
        if stats["text_leaks"]:
            err(f"{name}: {stats['text_leaks']} text leak(s) at ratio >= {LEAK_THRESHOLD}")
        if stats["id_leaks"]:
            err(f"{name}: {stats['id_leaks']} id collision(s) with the hand-checked test set")

    report = {
        "threshold": LEAK_THRESHOLD,
        "engine": LEAK_ENGINE,
        "files": report_files,
    }
    LEAK_REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"leak_report.json: engine={LEAK_ENGINE} threshold={LEAK_THRESHOLD}")


def main() -> int:
    print(f"Validating {DATA}")
    schema_root = load_schema()
    rsvps = validate_rsvps()
    if schema_root:
        for i, row in enumerate(rsvps, 1):
            check_against_schema(row, schema_root, "rsvp", f"rsvp_replies.jsonl:{i}")
    households, _guests = validate_guests()
    # also accept households from RSVP extra field if guests missing
    if not households:
        households = {r.get("household_id") for r in rsvps if r.get("household_id")}
    songs = validate_songs(households)
    if rsvps:
        rsvp_hhs = {r.get("household_id") for r in rsvps if r.get("household_id")}
        if households and rsvp_hhs - households:
            missing = sorted(rsvp_hhs - households)[:8]
            err(f"rsvp household_id not in guests: {missing}")
    validate_info()
    validate_vendors()
    questions = validate_questions()
    test_ids = {
        row["id"]
        for group in (rsvps, songs, questions)
        for row in group
        if isinstance(row.get("id"), str)
    }
    validate_generated(
        {"rsvp": rsvps, "song": songs, "guest_question": questions},
        test_ids,
        households,
    )

    for w in warnings:
        print(f"WARNING: {w}")
    if errors:
        print(f"\nFAILED with {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nOK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
