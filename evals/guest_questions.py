"""Score guest-question predictions. No model calls.

Fact labels are the locked rule. Token-F1 remains available as the
``legacy_*`` helpers and is still reported next to the fact metrics.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from typing import Any

# Refusal phrases. Source of truth: src/features/qa/qaRequest.js
# (UNKNOWN_ANSWER and UNKNOWN_ANSWER_EN). Python does not import that module.
# evals/tests/test_fact_score.py fails if these strings drift.
UNKNOWN_ANSWER = "No tengo esa información, pregúntale a los novios"
UNKNOWN_ANSWER_EN = "I don't have that information, ask the couple"
TOKEN_F1_MIN = 0.6
_NUMBER_OR_TIME = re.compile(r"\d{1,2}:\d{2}|\d+(?:am|pm)?")
_TOKEN = re.compile(r"\d{1,2}:\d{2}|\d+(?:am|pm)?|[a-z0-9]+")
_TIME_RE = re.compile(
    r"(?<!\d)(\d{1,2}):(\d{2})(?:\s*([ap])\.?\s*m\.?)?(?!\d)",
    re.IGNORECASE,
)
_INT_RE = re.compile(r"(?<!\d)(\d+)(?!\d)")
_WORD_RE = re.compile(r"[a-z0-9']+")
_LEADING_YES = re.compile(r"^(?:si|yes)\b")
_LEADING_NO = re.compile(r"^no\b")
_CLEAR_NEGATION = re.compile(r"\b(?:do not|don't|dont|no se puede|no estacionar)\b")

# Stopwords that belong to one language. Shared tokens such as "a" are omitted
# so they cannot tip the ratio.
_ES_STOP = frozenset(
    {
        "el",
        "la",
        "los",
        "las",
        "de",
        "del",
        "al",
        "en",
        "y",
        "o",
        "que",
        "es",
        "por",
        "con",
        "un",
        "una",
        "para",
        "su",
        "se",
        "lo",
        "como",
        "esta",
        "este",
        "esa",
        "ese",
        "son",
        "hay",
        "porque",
        "cuando",
        "donde",
        "desde",
        "hasta",
        "entre",
        "sobre",
        "sin",
        "pero",
        "muy",
        "ya",
        "unos",
        "unas",
        "le",
        "les",
        "te",
    }
)
_EN_STOP = frozenset(
    {
        "the",
        "of",
        "to",
        "in",
        "on",
        "at",
        "for",
        "and",
        "is",
        "it",
        "its",
        "it's",
        "be",
        "are",
        "was",
        "were",
        "with",
        "from",
        "by",
        "that",
        "this",
        "do",
        "not",
        "don't",
        "dont",
        "an",
        "or",
        "as",
        "if",
        "but",
        "we",
        "you",
        "your",
        "our",
        "they",
        "their",
        "have",
        "has",
        "there",
    }
)


def exact_match(prediction: str, gold: str) -> bool:
    """Return whether a guest-question answer matches its gold string."""
    return prediction.strip() == gold.strip()


def normalize(text: str | None) -> str:
    """Lowercase, strip accents, collapse whitespace, and strip edge punctuation."""
    if not text:
        return ""
    folded = unicodedata.normalize("NFKD", text)
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    folded = folded.casefold().strip()
    folded = re.sub(r"\s+", " ", folded)
    folded = re.sub(r"^[\s\"'`.,;:!?¡¿]+", "", folded)
    folded = re.sub(r"[\s\"'`.,;:!?¡¿]+$", "", folded)
    return folded.strip()


normalize_answer = normalize


def is_unknown_answer(gold: str) -> bool:
    return is_refusal(gold)


def is_refusal(text: str | None) -> bool:
    """True when the answer is the Spanish or the English locked refusal."""
    return refusal_language(text) is not None


def refusal_language(text: str | None) -> str | None:
    """Language of a refusal phrase, or None when the answer is not a refusal."""
    norm = normalize(text)
    if norm == normalize(UNKNOWN_ANSWER):
        return "es"
    if norm == normalize(UNKNOWN_ANSWER_EN):
        return "en"
    return None


def tokens(text: str | None) -> list[str]:
    return _TOKEN.findall(normalize(text))


def number_time_tokens(text: str | None) -> list[str]:
    return [token for token in tokens(text) if _NUMBER_OR_TIME.fullmatch(token)]


def legacy_token_f1(prediction: str | None, gold: str | None) -> float:
    predicted = tokens(prediction)
    expected = tokens(gold)
    if not predicted and not expected:
        return 1.0
    if not predicted or not expected:
        return 0.0
    overlap = sum((Counter(predicted) & Counter(expected)).values())
    precision = overlap / len(predicted)
    recall = overlap / len(expected)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


token_f1 = legacy_token_f1


def legacy_facts_match(prediction: str | None, gold: str | None) -> bool:
    if legacy_token_f1(prediction, gold) < TOKEN_F1_MIN:
        return False
    predicted = set(tokens(prediction))
    return all(token in predicted for token in number_time_tokens(gold))


facts_match = legacy_facts_match


def _object_from_raw(raw: str) -> dict[str, Any] | None:
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def answer_text(prediction: dict[str, Any] | None) -> str:
    if not prediction:
        return ""
    output = prediction.get("output")
    if isinstance(output, dict):
        for key in ("answer", "text"):
            value = output.get(key)
            if isinstance(value, str) and value.strip():
                return value
    raw = prediction.get("raw")
    if isinstance(raw, str):
        parsed = _object_from_raw(raw)
        if parsed and isinstance(parsed.get("answer"), str) and parsed["answer"].strip():
            return parsed["answer"]
        return raw
    return ""


def answer_confidence(prediction: dict[str, Any] | None) -> float | None:
    if not prediction:
        return None
    output = prediction.get("output") if isinstance(prediction.get("output"), dict) else {}
    raw = prediction.get("raw")
    parsed = _object_from_raw(raw) if isinstance(raw, str) else None
    candidates = [
        output.get("confidence") if output else None,
        parsed.get("confidence") if parsed else None,
        prediction.get("confidence"),
    ]
    for value in candidates:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        number = float(value)
        if 0.0 <= number <= 1.0:
            return number
    return None


def legacy_is_in_scope_correct(gold: dict[str, Any], prediction_text: str) -> bool:
    if gold.get("out_of_scope"):
        return False
    return (not is_refusal(prediction_text)) and legacy_facts_match(prediction_text, gold.get("answer"))


is_in_scope_correct = legacy_is_in_scope_correct


def legacy_is_hallucination(gold: dict[str, Any], prediction_text: str) -> bool:
    """Token-F1 hallucination. Non-refusals that fail the legacy overlap check."""
    if is_refusal(prediction_text):
        return False
    if gold.get("out_of_scope"):
        return True
    return not legacy_facts_match(prediction_text, gold.get("answer"))


is_hallucination = legacy_is_hallucination


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _canonical_clock(hour: int, minute: int, meridian: str | None) -> str | None:
    if minute > 59:
        return None
    if meridian is None:
        if hour > 23:
            return None
    else:
        mark = meridian.casefold()
        if hour > 12:
            return None
        if mark == "a":
            if hour == 12:
                hour = 0
        elif mark == "p":
            if hour < 12:
                hour += 12
        else:
            return None
    return f"{hour:02d}:{minute:02d}"


def canonical_quantities(text: str | None) -> tuple[list[str], list[str]]:
    """Return canonical HH:MM times and plain integer strings, in order.

    ``1:15 a.m.``, ``01:15`` and ``1:15`` all become ``01:15``. A p.m. hour
    below 12 gains 12 hours. Integers keep their digit spelling.
    """
    if not text:
        return [], []
    folded = unicodedata.normalize("NFKD", text)
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    folded = folded.casefold()
    times: list[str] = []
    masked = list(folded)
    for match in _TIME_RE.finditer(folded):
        canon = _canonical_clock(int(match.group(1)), int(match.group(2)), match.group(3))
        if canon is None:
            continue
        times.append(canon)
        for index in range(match.start(), match.end()):
            masked[index] = " "
    integers = _INT_RE.findall("".join(masked))
    return _unique(times), _unique(integers)


def answer_polarity(text: str | None) -> str | None:
    """Leading polarity as ``yes`` or ``no``.

    Sí / Si / Yes are ``yes``. A leading No, or a clear negation such as
    ``no se puede``, ``no estacionar``, or ``do not``, is ``no``.
    """
    norm = normalize(text)
    if not norm:
        return None
    if _LEADING_YES.match(norm):
        return "yes"
    if _LEADING_NO.match(norm):
        return "no"
    if _CLEAR_NEGATION.search(norm):
        return "no"
    return None


def derive_facts(answer: str | None) -> list[str]:
    """Times, integers, and a leading polarity, when ``gold_facts`` is absent."""
    facts: list[str] = []
    polarity = answer_polarity(answer)
    if polarity:
        facts.append(polarity)
    times, numbers = canonical_quantities(answer)
    facts.extend(times)
    facts.extend(numbers)
    return facts


def row_facts(gold: dict[str, Any]) -> list[str]:
    raw = gold.get("gold_facts")
    if isinstance(raw, list):
        return [str(item).strip() for item in raw]
    return derive_facts(gold.get("answer"))


def _clock_fact(text: str) -> str | None:
    times, numbers = canonical_quantities(text)
    if len(times) != 1 or numbers:
        return None
    residual = normalize(_TIME_RE.sub(" ", text))
    residual = re.sub(r"\b[ap]\s*m\b", "", residual).strip()
    if residual:
        return None
    return times[0]


def fact_spec(fact: str) -> tuple[str, str]:
    """Classify one gold fact as polarity, time, number, or text."""
    text = str(fact).strip()
    norm = normalize(text)
    if norm in {"yes", "no"}:
        return ("polarity", norm)
    clock = _clock_fact(text)
    if clock is not None:
        return ("time", clock)
    times, numbers = canonical_quantities(text)
    if len(numbers) == 1 and not times and norm == numbers[0]:
        return ("number", numbers[0])
    return ("text", norm)


def _fact_present(kind: str, value: str, prediction: str) -> bool:
    if kind == "polarity":
        return answer_polarity(prediction) == value
    if kind == "time":
        times, _numbers = canonical_quantities(prediction)
        return value in times
    if kind == "number":
        _times, numbers = canonical_quantities(prediction)
        return value in numbers
    if not value:
        return False
    return value in normalize(prediction)


def _gold_polarity(facts: list[str]) -> str | None:
    for fact in facts:
        kind, value = fact_spec(fact)
        if kind == "polarity":
            return value
    return None


def _polarity_contradicts(prediction: str, facts: list[str]) -> bool:
    expected = _gold_polarity(facts)
    if expected is None:
        return False
    got = answer_polarity(prediction)
    return got is not None and got != expected


def _unsupported_quantity(prediction: str, gold: dict[str, Any], facts: list[str]) -> bool:
    pred_times, pred_numbers = canonical_quantities(prediction)
    allowed_times: set[str] = set()
    allowed_numbers: set[str] = set()
    sources = [str(gold.get("answer") or "")]
    sources.extend(facts)
    for source in sources:
        times, numbers = canonical_quantities(source)
        allowed_times.update(times)
        allowed_numbers.update(numbers)
    if any(item not in allowed_times for item in pred_times):
        return True
    return any(item not in allowed_numbers for item in pred_numbers)


def fact_label(gold: dict[str, Any], prediction_text: str | None) -> str:
    """Return correct, hallucination, abstain, wrong_fact, or incomplete.

    ``wrong_fact`` and out-of-scope ``hallucination`` are the fact-based
    hallucinations. ``abstain`` and ``incomplete`` are not.
    """
    text = prediction_text or ""
    if gold.get("out_of_scope"):
        return "correct" if is_refusal(text) else "hallucination"
    if is_refusal(text):
        return "abstain"
    facts = row_facts(gold)
    if _unsupported_quantity(text, gold, facts) or _polarity_contradicts(text, facts):
        return "wrong_fact"
    if all(_fact_present(*fact_spec(fact), text) for fact in facts):
        return "correct"
    return "incomplete"


def is_fact_hallucination(gold: dict[str, Any], prediction_text: str | None) -> bool:
    return fact_label(gold, prediction_text) in {"wrong_fact", "hallucination"}


def wedding_info_path():
    """Info sheet the eval loader already resolves from the repo root."""
    from evals.loader import REPO_ROOT

    return REPO_ROOT / "data" / "wedding_info.json"


@lru_cache(maxsize=1)
def proper_noun_tokens() -> frozenset[str]:
    """Tokens of venue and place names on the wedding info sheet."""
    path = wedding_info_path()
    if not path.exists():
        return frozenset()
    info = json.loads(path.read_text(encoding="utf-8"))
    names: list[str] = []
    venue = info.get("venue") if isinstance(info.get("venue"), dict) else {}
    for key in ("name", "ceremony_area", "reception_area"):
        value = venue.get(key)
        if isinstance(value, str):
            names.append(value)
    for item in info.get("schedule") or []:
        if isinstance(item, dict) and isinstance(item.get("place"), str):
            names.append(item["place"])
    tokens: set[str] = set()
    for name in names:
        tokens.update(_WORD_RE.findall(normalize(name)))
    return frozenset(tokens)


def _content_tokens(text: str | None) -> list[str]:
    words = _WORD_RE.findall(normalize(text))
    places = proper_noun_tokens()
    return [word for word in words if word not in places and not word.isdigit()]


def detect_answer_language(text: str | None) -> str | None:
    """Stopword-ratio language of an answer, ignoring venue and place names."""
    words = _content_tokens(text)
    if not words:
        return None
    spanish = sum(word in _ES_STOP for word in words)
    english = sum(word in _EN_STOP for word in words)
    if spanish == english:
        return None
    return "es" if spanish > english else "en"


def language_mismatch(answer: str | None, lang: str | None) -> bool:
    """True when the answer language differs from the row's question ``lang``.

    The gold text is not consulted. A refusal in the other language is a
    mismatch and is still a refusal.
    """
    if lang not in {"en", "es"}:
        return False
    detected = refusal_language(answer)
    if detected is None:
        detected = detect_answer_language(answer)
    return detected is not None and detected != lang


def _f_score(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None:
        return None
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _rates(pairs: list[tuple[dict[str, Any], str]]) -> dict[str, Any]:
    out_of_scope = [(gold, text) for gold, text in pairs if gold.get("out_of_scope")]
    in_scope = [(gold, text) for gold, text in pairs if not gold.get("out_of_scope")]
    true_positive = sum(1 for _gold, text in out_of_scope if is_refusal(text))
    false_positive = sum(1 for _gold, text in in_scope if is_refusal(text))
    false_negative = len(out_of_scope) - true_positive
    precision = _rate(true_positive, true_positive + false_positive)
    recall = _rate(true_positive, true_positive + false_negative)
    labels = [(gold, text, fact_label(gold, text)) for gold, text in pairs]
    fact_correct = sum(1 for gold, _text, label in labels if not gold.get("out_of_scope") and label == "correct")
    wrong = sum(1 for _gold, _text, label in labels if label in {"wrong_fact", "hallucination"})
    incomplete = sum(1 for _gold, _text, label in labels if label == "incomplete")
    abstain = sum(1 for _gold, _text, label in labels if label == "abstain")
    comparable = [(gold, text) for gold, text in in_scope if not is_refusal(text)]
    mismatches = sum(1 for gold, text in comparable if language_mismatch(text, gold.get("lang")))
    legacy_correct = sum(1 for gold, text in in_scope if legacy_is_in_scope_correct(gold, text))
    legacy_hallucinations = sum(1 for gold, text in pairs if legacy_is_hallucination(gold, text))
    token_scores = [legacy_token_f1(text, gold.get("answer")) for gold, text in pairs]
    n = len(pairs)
    n_in_scope = len(in_scope)
    return {
        "n": n,
        "n_out_of_scope": len(out_of_scope),
        "n_in_scope": n_in_scope,
        "n_refusal": sum(1 for _gold, text in pairs if is_refusal(text)),
        "n_fact_correct": fact_correct,
        "fact_correct_rate": _rate(fact_correct, n_in_scope),
        "n_wrong_fact": wrong,
        "n_hallucination": wrong,
        "wrong_fact_rate": _rate(wrong, n),
        "hallucination_rate": _rate(wrong, n),
        "n_incomplete": incomplete,
        "incomplete_rate": _rate(incomplete, n),
        "n_abstain": abstain,
        "abstain_rate": _rate(abstain, n),
        "refusal_precision": precision,
        "refusal_recall": recall,
        "refusal_f1": _f_score(precision, recall),
        "lang_mismatch_count": mismatches,
        "lang_mismatch_rate": _rate(mismatches, len(comparable)),
        "legacy_token_f1": (sum(token_scores) / len(token_scores)) if token_scores else None,
        "legacy_in_scope_correctness": _rate(legacy_correct, n_in_scope),
        "in_scope_correctness": _rate(legacy_correct, n_in_scope),
        "legacy_n_hallucination": legacy_hallucinations,
        "legacy_hallucination_rate": _rate(legacy_hallucinations, n),
    }


def format_guest_metric_line(summary: dict[str, Any] | None) -> str | None:
    """One line for the score and threshold CLIs. Empty when nothing was scored."""
    if not isinstance(summary, dict) or not summary.get("n"):
        return None
    return (
        "guest_question "
        f"n={summary.get('n')} "
        f"fact_correct_rate={summary.get('fact_correct_rate')} "
        f"hallucination_rate={summary.get('hallucination_rate')} "
        f"incomplete_rate={summary.get('incomplete_rate')} "
        f"abstain_rate={summary.get('abstain_rate')} "
        f"lang_mismatch_rate={summary.get('lang_mismatch_rate')} "
        f"legacy_token_f1={summary.get('legacy_token_f1')}"
    )


def score_guest_questions(
    golds: list[dict[str, Any]],
    predictions: list[dict[str, Any]] | dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Score provided predictions. This does not call a model."""
    by_id = predictions if isinstance(predictions, dict) else {row["id"]: row for row in predictions}
    pairs = [(gold, answer_text(by_id.get(gold["id"]))) for gold in golds]
    summary = _rates(pairs)
    grouped: dict[str, list[tuple[dict[str, Any], str]]] = {}
    for gold, text in pairs:
        grouped.setdefault(gold.get("split") or "unk", []).append((gold, text))
    summary["by_split"] = {split: _rates(rows) for split, rows in sorted(grouped.items())}
    return summary
