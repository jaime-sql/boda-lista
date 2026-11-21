"""Score RSVP and song predictions against gold rows.

Field rates use every item of that task. Invalid JSON counts as incorrect
and is also reported on its own. Fuzzy song titles use rapidfuzz
token_sort_ratio after accent-folding; the threshold is FUZZY_THRESHOLD (90).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

from evals.feature_map import TASK_TO_FEATURE
from evals.guest_questions import UNKNOWN_ANSWER
from evals.loader import load_paths
from evals.parsing import resolve_prediction
from evals.pricing import cost_per_thousand

FUZZY_THRESHOLD = 90
ATTENDING_LABELS = ("yes", "no", "maybe")

MEAL_ALIASES = {
    "vegetarian": "vegetarian",
    "vegetariano": "vegetarian",
    "vegetariana": "vegetarian",
    "vegan": "vegan",
    "vegano": "vegan",
    "vegana": "vegan",
    "gluten_free": "gluten_free",
    "glutenfree": "gluten_free",
    "sin_gluten": "gluten_free",
    "kids_menu": "kids_menu",
    "menu_infantil": "kids_menu",
    "kidsmenu": "kids_menu",
}
# Gold energy is slow | medium | dance | null (data/schema.json).
ENERGY_ALIASES = {
    "dance": "dance",
    "high": "dance",
    "alta": "dance",
    "upbeat": "dance",
    "bailable": "dance",
    "alegre": "dance",
    "medium": "medium",
    "media": "medium",
    "intermedia": "medium",
    "slow": "slow",
    "low": "slow",
    "baja": "slow",
    "chill": "slow",
    "lenta": "slow",
    "romantic": "slow",
    "romantica": "slow",
    "balada": "slow",
}


def fold_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without = "".join(char for char in normalized if not unicodedata.combining(char))
    lowered = without.casefold().strip()
    lowered = re.sub(r"[^a-z0-9:<\s_-]", "", lowered)
    lowered = re.sub(r"[\s-]+", "_", lowered)
    return lowered.strip("_")


def canonical_meal(tag: str) -> str:
    folded = fold_label(tag)
    if folded.startswith("allergy:"):
        allergen = folded.split(":", 1)[1]
        allergen = re.sub(r"^(?:la|el|los|las|the)_", "", allergen)
        return f"allergy:{allergen}" if allergen else folded
    return MEAL_ALIASES.get(folded, folded)


def meal_set(tags: list[str] | None) -> set[str]:
    return {canonical_meal(tag) for tag in (tags or []) if str(tag).strip()}


def canonical_energy(value: str | None) -> str | None:
    if value is None:
        return None
    folded = fold_label(value)
    if not folded:
        return None
    return ENERGY_ALIASES.get(folded, folded)


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = unicodedata.normalize("NFKD", value)
    without = "".join(char for char in normalized if not unicodedata.combining(char))
    lowered = without.casefold()
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered or None


def fuzzy_equal(left: str | None, right: str | None, threshold: int = FUZZY_THRESHOLD) -> bool:
    left_norm = normalize_text(left)
    right_norm = normalize_text(right)
    if left_norm is None and right_norm is None:
        return True
    if left_norm is None or right_norm is None:
        return False
    if left_norm == right_norm:
        return True
    return fuzz.token_sort_ratio(left_norm, right_norm) >= threshold


def set_f1(gold: set[str], predicted: set[str]) -> float:
    if not gold and not predicted:
        return 1.0
    true_positive = len(gold & predicted)
    precision = true_positive / len(predicted) if predicted else 0.0
    recall = true_positive / len(gold) if gold else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def percentile(values: list[float], percent: float) -> float | None:
    """Linear percentile. percent is in [0, 100]."""
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * (percent / 100.0)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return float(ordered[low])
    weight = rank - low
    return float(ordered[low] * (1.0 - weight) + ordered[high] * weight)


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def forces_definite_rsvp(output: dict[str, Any]) -> bool:
    """Gold ambiguous replies still carry attending. Forcing a definite answer means clearing that flag."""
    return output.get("ambiguous") is False


def rsvp_fields_match(gold: dict[str, Any], output: dict[str, Any]) -> bool:
    return (
        output.get("attending") == gold.get("attending")
        and output.get("party_size") == gold.get("party_size")
        and meal_set(output.get("meal_restrictions")) == meal_set(gold.get("meal_restrictions"))
        and output.get("kids_count") == gold.get("kids_count")
        and output.get("needs_ride") == gold.get("needs_ride")
        and output.get("ambiguous") == gold.get("ambiguous")
    )


def song_fields_match(gold: dict[str, Any], output: dict[str, Any]) -> bool:
    return (
        fuzzy_equal(output.get("title"), gold.get("title"))
        and fuzzy_equal(output.get("artist"), gold.get("artist"))
        and canonical_energy(output.get("energy")) == canonical_energy(gold.get("energy"))
        and output.get("ambiguous") == gold.get("ambiguous")
    )


def item_correct(gold: dict[str, Any], output: dict[str, Any] | None) -> bool:
    """All tracked fields match. Invalid output is incorrect."""
    if output is None:
        return False
    if gold["task"] == "rsvp":
        return rsvp_fields_match(gold, output)
    if gold["task"] == "song":
        return song_fields_match(gold, output)
    return False


def macro_f1(pairs: list[tuple[str, str | None]], labels: tuple[str, ...] = ATTENDING_LABELS) -> float | None:
    """Macro-F1 over labels that appear in the gold side of pairs."""
    present = [label for label in labels if any(gold == label for gold, _pred in pairs)]
    if not present:
        return None
    scores: list[float] = []
    for label in present:
        true_positive = false_positive = false_negative = 0
        for gold, predicted in pairs:
            if gold == label and predicted == label:
                true_positive += 1
            elif predicted == label and gold != label:
                false_positive += 1
            elif gold == label and predicted != label:
                false_negative += 1
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        scores.append(0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall))
    return sum(scores) / len(scores)


def _empty_task(task: str) -> dict[str, Any]:
    base: dict[str, Any] = {"n": 0, "invalid_json_rate": None, "all_fields_correct": None}
    if task == "rsvp":
        base.update(
            {
                "attending_accuracy": None,
                "attending_macro_f1": None,
                "party_size_exact": None,
                "meal_restrictions_exact": None,
                "meal_restrictions_set_f1": None,
                "kids_count_exact": None,
                "needs_ride_exact": None,
                "ambiguous_exact": None,
                "ambiguous_force_rate": None,
            }
        )
    else:
        base.update(
            {
                "title_artist_accuracy": None,
                "title_artist_n": 0,
                "energy_accuracy": None,
                "ambiguous_recall": None,
                "guess_rate": None,
            }
        )
    return base


def _rsvp_metrics(items: list[dict[str, Any]]) -> dict[str, Any]:
    if not items:
        return _empty_task("rsvp")
    n = len(items)
    usable = [item for item in items if item["output"] is not None]
    attending_pairs = [
        (item["gold"]["attending"], None if item["output"] is None else item["output"].get("attending"))
        for item in items
        if item["gold"].get("attending") in ATTENDING_LABELS
    ]
    attending_hits = sum(1 for gold, pred in attending_pairs if gold == pred)
    meal_exact = 0
    meal_f1_sum = 0.0
    party_hits = kids_hits = ride_hits = ambiguous_hits = all_hits = 0
    for item in items:
        output = item["output"]
        gold = item["gold"]
        if output is None:
            continue
        if output.get("party_size") == gold.get("party_size"):
            party_hits += 1
        gold_meals = meal_set(gold.get("meal_restrictions"))
        pred_meals = meal_set(output.get("meal_restrictions"))
        if gold_meals == pred_meals:
            meal_exact += 1
        meal_f1_sum += set_f1(gold_meals, pred_meals)
        if output.get("kids_count") == gold.get("kids_count"):
            kids_hits += 1
        if output.get("needs_ride") == gold.get("needs_ride"):
            ride_hits += 1
        if output.get("ambiguous") == gold.get("ambiguous"):
            ambiguous_hits += 1
        if item_correct(gold, output):
            all_hits += 1
    ambiguous_gold = [item for item in items if item["gold"].get("ambiguous") is True]
    forced = sum(
        1
        for item in ambiguous_gold
        if item["output"] is not None and forces_definite_rsvp(item["output"])
    )
    return {
        "n": n,
        "invalid_json_rate": _rate(n - len(usable), n),
        "attending_accuracy": _rate(attending_hits, len(attending_pairs)),
        "attending_macro_f1": macro_f1(attending_pairs),
        "party_size_exact": _rate(party_hits, n),
        "meal_restrictions_exact": _rate(meal_exact, n),
        "meal_restrictions_set_f1": meal_f1_sum / n,
        "kids_count_exact": _rate(kids_hits, n),
        "needs_ride_exact": _rate(ride_hits, n),
        "ambiguous_exact": _rate(ambiguous_hits, n),
        "ambiguous_force_rate": _rate(forced, len(ambiguous_gold)),
        "all_fields_correct": _rate(all_hits, n),
    }


def _song_metrics(items: list[dict[str, Any]]) -> dict[str, Any]:
    if not items:
        return _empty_task("song")
    n = len(items)
    usable = [item for item in items if item["output"] is not None]
    identified = [item for item in items if item["gold"].get("ambiguous") is False]
    ambiguous_gold = [item for item in items if item["gold"].get("ambiguous") is True]
    title_hits = energy_hits = all_hits = 0
    for item in identified:
        output = item["output"]
        if output is None:
            continue
        if fuzzy_equal(output.get("title"), item["gold"].get("title")) and fuzzy_equal(
            output.get("artist"), item["gold"].get("artist")
        ):
            title_hits += 1
    for item in items:
        output = item["output"]
        if output is None:
            continue
        if canonical_energy(output.get("energy")) == canonical_energy(item["gold"].get("energy")):
            energy_hits += 1
        if item_correct(item["gold"], output):
            all_hits += 1
    recalled = sum(1 for item in ambiguous_gold if item["output"] is not None and item["output"].get("ambiguous") is True)
    guesses = sum(
        1
        for item in ambiguous_gold
        if item["output"] is not None and item["output"].get("title")
    )
    return {
        "n": n,
        "invalid_json_rate": _rate(n - len(usable), n),
        "title_artist_accuracy": _rate(title_hits, len(identified)),
        "title_artist_n": len(identified),
        "energy_accuracy": _rate(energy_hits, n),
        "ambiguous_recall": _rate(recalled, len(ambiguous_gold)),
        "guess_rate": _rate(guesses, len(ambiguous_gold)),
        "all_fields_correct": _rate(all_hits, n),
        "fuzzy_threshold": FUZZY_THRESHOLD,
    }


def _block(items: list[dict[str, Any]], *, with_lang: bool = False) -> dict[str, Any]:
    latencies = [item["latency_ms"] for item in items if isinstance(item["latency_ms"], (int, float))]
    invalid = sum(1 for item in items if item["error"] in {"invalid_json", "missing_prediction"})
    block: dict[str, Any] = {
        "n": len(items),
        "invalid_json_rate": _rate(invalid, len(items)),
        "latency_ms": {
            "p50": percentile(latencies, 50),
            "p95": percentile(latencies, 95),
            "n": len(latencies),
        },
        TASK_TO_FEATURE["rsvp"]: _rsvp_metrics(
            [item for item in items if item["gold"]["task"] == "rsvp"]
        ),
        TASK_TO_FEATURE["song"]: _song_metrics(
            [item for item in items if item["gold"]["task"] == "song"]
        ),
    }
    if with_lang:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            grouped[item["gold"].get("lang") or "unk"].append(item)
        block["by_lang"] = {lang: _block(rows) for lang, rows in sorted(grouped.items())}
    return block


def align(golds: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Pair gold rows with predictions. Guest questions are counted and dropped."""
    by_id = {row["id"]: row for row in predictions}
    aligned: list[dict[str, Any]] = []
    skipped = 0
    for gold in golds:
        if gold.get("task") == "guest_question":
            skipped += 1
            continue
        if gold.get("task") == "wedding_info":
            skipped += 1
            continue
        if gold.get("task") not in {"rsvp", "song"}:
            skipped += 1
            continue
        output, error, latency, confidence = resolve_prediction(gold["task"], by_id.get(gold["id"]))
        aligned.append(
            {
                "gold": gold,
                "output": output,
                "error": error,
                "latency_ms": latency,
                "confidence": confidence,
            }
        )
    return aligned, skipped


def score_predictions(
    golds: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    *,
    backend: str,
    smoke: bool = False,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    aligned, skipped_questions = align(golds, predictions)
    overall = _block(aligned, with_lang=True)
    grouped_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in aligned:
        grouped_split[item["gold"].get("split") or "unk"].append(item)
    by_split = {split: _block(rows, with_lang=True) for split, rows in sorted(grouped_split.items())}
    summary: dict[str, Any] = {
        "backend": backend,
        "smoke": smoke,
        "n": overall["n"],
        "invalid_json_rate": overall["invalid_json_rate"],
        "latency_ms": overall["latency_ms"],
        "cost_usd_per_1000": cost_per_thousand(backend, overall["n"], meta),
        "fuzzy_threshold": FUZZY_THRESHOLD,
        TASK_TO_FEATURE["rsvp"]: overall[TASK_TO_FEATURE["rsvp"]],
        TASK_TO_FEATURE["song"]: overall[TASK_TO_FEATURE["song"]],
        "by_lang": overall.get("by_lang", {}),
        "by_split": by_split,
    }
    if backend == "gemma":
        summary["cost_basis"] = "Modal GPU-only list price from modal.com/pricing; CPU and memory excluded"
    elif backend in {"rules", "nano"}:
        summary["cost_basis"] = "no model fee"
    else:
        summary["cost_basis"] = "unknown without token counts"
    if skipped_questions:
        summary["guest_questions"] = {
            "status": "out_of_scope",
            "n_skipped": skipped_questions,
            "todo": (
                "Exact-match hook only. Unknown gold is "
                f"{UNKNOWN_ANSWER!r}. See evals/guest_questions.py."
            ),
        }
    return summary


def load_predictions(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        rows.append(json.loads(stripped))
    return rows


def index_predictions(predictions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in predictions}


def main() -> None:
    parser = argparse.ArgumentParser(description="Score a predictions JSONL against gold JSONL.")
    parser.add_argument("--gold", nargs="+", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--backend", default=None)
    parser.add_argument("--schema", type=Path, default=None)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--meta", type=Path, default=None, help="run_meta.json from the runner")
    args = parser.parse_args()
    meta = None
    if args.meta and args.meta.exists():
        meta = json.loads(args.meta.read_text(encoding="utf-8"))
    elif args.predictions.parent.joinpath("run_meta.json").exists() and args.meta is None:
        meta = json.loads(args.predictions.parent.joinpath("run_meta.json").read_text(encoding="utf-8"))
    backend = args.backend or (meta or {}).get("backend") or "unknown"
    smoke = args.smoke or bool((meta or {}).get("smoke")) or any("smoke" in path.name for path in args.gold)
    golds = load_paths(args.gold, schema_path=args.schema)
    predictions = load_predictions(args.predictions)
    summary = score_predictions(golds, predictions, backend=backend, smoke=smoke, meta=meta)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args.out} backend={backend} n={summary['n']} smoke={summary['smoke']}")


if __name__ == "__main__":
    main()
