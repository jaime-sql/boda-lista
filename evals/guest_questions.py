"""Score guest-question predictions. No model calls.

A prediction is a refusal when its normalized text matches the locked phrase.
Normalization lowercases, strips accents, and drops leading and trailing
punctuation. In-scope answers are correct when they are not refusals, their
token F1 against the gold answer is at least 0.6, and every number or time
token in the gold answer appears in the prediction. A hallucination is any
non-refusal that fails that check, including an answer to an out-of-scope
question.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from typing import Any

UNKNOWN_ANSWER = "No tengo esa información, pregúntale a los novios"
TOKEN_F1_MIN = 0.6
_NUMBER_OR_TIME = re.compile(r"\d{1,2}:\d{2}|\d+(?:am|pm)?")
_TOKEN = re.compile(r"\d{1,2}:\d{2}|\d+(?:am|pm)?|[a-z0-9]+")


def exact_match(prediction: str, gold: str) -> bool:
    """Return whether a guest-question answer matches its gold string."""
    return prediction.strip() == gold.strip()


def is_unknown_answer(gold: str) -> bool:
    return normalize_answer(gold) == normalize_answer(UNKNOWN_ANSWER)


def normalize_answer(text: str | None) -> str:
    if not text:
        return ""
    folded = unicodedata.normalize("NFKD", text)
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    folded = folded.casefold().strip()
    folded = re.sub(r"\s+", " ", folded)
    folded = re.sub(r"^[\s\"'`.,;:!?¡¿]+", "", folded)
    folded = re.sub(r"[\s\"'`.,;:!?¡¿]+$", "", folded)
    return folded.strip()


def is_refusal(text: str | None) -> bool:
    return normalize_answer(text) == normalize_answer(UNKNOWN_ANSWER)


def tokens(text: str | None) -> list[str]:
    return _TOKEN.findall(normalize_answer(text))


def number_time_tokens(text: str | None) -> list[str]:
    return [token for token in tokens(text) if _NUMBER_OR_TIME.fullmatch(token)]


def token_f1(prediction: str | None, gold: str | None) -> float:
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


def facts_match(prediction: str | None, gold: str | None) -> bool:
    if token_f1(prediction, gold) < TOKEN_F1_MIN:
        return False
    predicted = set(tokens(prediction))
    return all(token in predicted for token in number_time_tokens(gold))


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


def is_in_scope_correct(gold: dict[str, Any], prediction_text: str) -> bool:
    if gold.get("out_of_scope"):
        return False
    return (not is_refusal(prediction_text)) and facts_match(prediction_text, gold.get("answer"))


def is_hallucination(gold: dict[str, Any], prediction_text: str) -> bool:
    """Non-refusals that fail correctness, in scope or out of scope."""
    if is_refusal(prediction_text):
        return False
    if gold.get("out_of_scope"):
        return True
    return not facts_match(prediction_text, gold.get("answer"))


def _rates(pairs: list[tuple[dict[str, Any], str]]) -> dict[str, Any]:
    out_of_scope = [(gold, text) for gold, text in pairs if gold.get("out_of_scope")]
    in_scope = [(gold, text) for gold, text in pairs if not gold.get("out_of_scope")]
    true_positive = sum(1 for _gold, text in out_of_scope if is_refusal(text))
    false_positive = sum(1 for _gold, text in in_scope if is_refusal(text))
    false_negative = len(out_of_scope) - true_positive
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else None
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else None
    if precision is None or recall is None or precision + recall == 0:
        f1 = None if precision is None or recall is None else 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    correct = sum(1 for gold, text in in_scope if is_in_scope_correct(gold, text))
    hallucinations = sum(1 for gold, text in pairs if is_hallucination(gold, text))
    n = len(pairs)
    return {
        "n": n,
        "n_out_of_scope": len(out_of_scope),
        "n_in_scope": len(in_scope),
        "n_refusal": sum(1 for _gold, text in pairs if is_refusal(text)),
        "n_hallucination": hallucinations,
        "refusal_precision": precision,
        "refusal_recall": recall,
        "refusal_f1": f1,
        "in_scope_correctness": (correct / len(in_scope)) if in_scope else None,
        "hallucination_rate": (hallucinations / n) if n else None,
    }


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
