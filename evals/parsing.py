"""Robust JSON object extraction for model outputs.

Invalid JSON and outputs that miss the task schema are both errors.
The scorer reports them as invalid_json.
"""

from __future__ import annotations

import json
import re
from typing import Any


class InvalidModelOutput(ValueError):
    """The model text is not a usable JSON object for this task."""


_FENCE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL | re.IGNORECASE)


def parse_json_object(text: str | None) -> dict[str, Any]:
    """Pull the first JSON object out of raw model text."""
    if text is None or not str(text).strip():
        raise InvalidModelOutput("empty model output")
    raw = str(text).strip()
    fenced = _FENCE.search(raw)
    if fenced:
        candidate = fenced.group(1)
    else:
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end <= start:
            raise InvalidModelOutput("no JSON object")
        candidate = raw[start : end + 1]
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise InvalidModelOutput(f"invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise InvalidModelOutput("JSON value is not an object")
    return value


def _int_or_null(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise InvalidModelOutput(f"{field} must be an integer or null")
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lower() in {"", "null", "none"}:
            return None
        if not re.fullmatch(r"-?\d+", stripped):
            raise InvalidModelOutput(f"{field} must be an integer or null")
        value = int(stripped)
    if isinstance(value, float):
        if not value.is_integer():
            raise InvalidModelOutput(f"{field} must be an integer or null")
        value = int(value)
    if value < 0:
        raise InvalidModelOutput(f"{field} must be >= 0")
    return int(value)


def _bool_or_null(value: Any, field: str) -> bool | None:
    if value is None:
        return None
    return _bool_field(value, field)


def _bool_field(value: Any, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    raise InvalidModelOutput(f"{field} must be a boolean")


def _confidence(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise InvalidModelOutput("confidence must be a number in [0, 1]")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise InvalidModelOutput("confidence must be a number in [0, 1]") from exc
    if number < 0 or number > 1:
        raise InvalidModelOutput("confidence must be a number in [0, 1]")
    return number


def _optional_str(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidModelOutput(f"{field} must be a string or null")
    stripped = value.strip()
    return stripped or None


def normalize_output(task: str, obj: dict[str, Any]) -> dict[str, Any]:
    """Coerce a parsed object into the shared output schema.

    Raises InvalidModelOutput when a required field is missing or mistyped.
    """
    if task == "rsvp":
        if "ambiguous" not in obj or "needs_ride" not in obj:
            raise InvalidModelOutput("rsvp output is missing required fields")
        if "meal_restrictions" not in obj:
            raise InvalidModelOutput("rsvp output is missing meal_restrictions")
        attending = obj.get("attending")
        if isinstance(attending, str):
            attending = attending.strip().lower()
        if attending not in {None, "yes", "no", "maybe"}:
            raise InvalidModelOutput("attending must be yes, no, maybe, or null")
        meals = obj.get("meal_restrictions")
        if not isinstance(meals, list) or not all(isinstance(item, str) for item in meals):
            raise InvalidModelOutput("meal_restrictions must be a list of strings")
        return {
            "attending": attending,
            "party_size": _int_or_null(obj.get("party_size"), "party_size"),
            "meal_restrictions": meals,
            "kids_count": _int_or_null(obj.get("kids_count"), "kids_count"),
            "needs_ride": _bool_or_null(obj.get("needs_ride"), "needs_ride"),
            "ambiguous": _bool_field(obj.get("ambiguous"), "ambiguous"),
            "confidence": _confidence(obj.get("confidence")),
        }
    if task == "song":
        if "ambiguous" not in obj:
            raise InvalidModelOutput("song output is missing ambiguous")
        for field in ("title", "artist", "energy"):
            if field not in obj:
                raise InvalidModelOutput(f"song output is missing {field}")
        return {
            "title": _optional_str(obj.get("title"), "title"),
            "artist": _optional_str(obj.get("artist"), "artist"),
            "energy": _optional_str(obj.get("energy"), "energy"),
            "ambiguous": _bool_field(obj.get("ambiguous"), "ambiguous"),
            "confidence": _confidence(obj.get("confidence")),
        }
    raise InvalidModelOutput(f"unknown task {task}")


def resolve_prediction(task: str, prediction: dict[str, Any] | None) -> tuple[dict[str, Any] | None, str | None, float | None, float | None]:
    """Return output, error, latency_ms, confidence.

    error is 'invalid_json' when the raw text or output object cannot be used.
    """
    if prediction is None:
        return None, "missing_prediction", None, None
    latency = prediction.get("latency_ms")
    top_conf = prediction.get("confidence")
    raw = prediction.get("raw")
    try:
        if isinstance(raw, str) and raw.strip():
            parsed = parse_json_object(raw)
        elif isinstance(prediction.get("output"), dict):
            parsed = prediction["output"]
        else:
            raise InvalidModelOutput("no output")
        output = normalize_output(task, parsed)
    except InvalidModelOutput:
        return None, "invalid_json", latency, top_conf if isinstance(top_conf, (int, float)) else None
    confidence = output.get("confidence")
    if confidence is None and isinstance(top_conf, (int, float)) and not isinstance(top_conf, bool):
        confidence = float(top_conf)
        output = dict(output)
        output["confidence"] = confidence
    return output, None, latency, confidence
