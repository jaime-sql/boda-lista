"""Write docs/evaluation.md from computed summaries.

Smoke runs are skipped. A backend with no non-smoke summary is "not run".
Numbers in the table are formatted from summary.json only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

BACKENDS = ("rules", "gemma", "nano", "cloud", "hybrid")
REPO_ROOT = Path(__file__).resolve().parents[1]

# Older summaries used app feature names. Read them when the task key is absent.
LEGACY_FEATURE_KEYS = {"song": "songs", "guest_question": "qa"}

# (label, feature or None for a run-level metric, key, kind)
METRIC_ROWS = (
    ("RSVP all-fields correct", "rsvp", "all_fields_correct", "rate"),
    ("RSVP attending accuracy", "rsvp", "attending_accuracy", "rate"),
    ("RSVP attending macro-F1", "rsvp", "attending_macro_f1", "rate"),
    ("RSVP party_size exact", "rsvp", "party_size_exact", "rate"),
    ("RSVP meal_restrictions exact", "rsvp", "meal_restrictions_exact", "rate"),
    ("RSVP meal_restrictions set-F1", "rsvp", "meal_restrictions_set_f1", "rate"),
    ("RSVP kids_count exact", "rsvp", "kids_count_exact", "rate"),
    ("RSVP needs_ride exact", "rsvp", "needs_ride_exact", "rate"),
    ("RSVP ambiguous exact", "rsvp", "ambiguous_exact", "rate"),
    ("RSVP force-definite on ambiguous", "rsvp", "ambiguous_force_rate", "rate"),
    ("Song title+artist accuracy", "song", "title_artist_accuracy", "rate"),
    ("Song energy accuracy", "song", "energy_accuracy", "rate"),
    ("Song ambiguous recall", "song", "ambiguous_recall", "rate"),
    ("Song guess rate on ambiguous", "song", "guess_rate", "rate"),
    ("Song all-fields correct", "song", "all_fields_correct", "rate"),
    ("Invalid JSON", None, "invalid_json_rate", "rate"),
    ("Latency p50 (ms)", None, "latency_p50", "ms"),
    ("Latency p95 (ms)", None, "latency_p95", "ms"),
    ("Estimated USD per 1,000", None, "cost_usd_per_1000", "usd"),
    ("On-device share", "rsvp", "on_device_share", "rate"),
    ("RSVP threshold", "rsvp", "threshold", "threshold"),
    ("Guest fact correct", "guest_question", "fact_correct_rate", "rate"),
    ("Guest hallucination", "guest_question", "hallucination_rate", "rate"),
    ("Guest incomplete", "guest_question", "incomplete_rate", "rate"),
    ("Guest abstain", "guest_question", "abstain_rate", "rate"),
    ("Guest refusal F1", "guest_question", "refusal_f1", "rate"),
    ("Guest lang mismatch", "guest_question", "lang_mismatch_rate", "rate"),
    ("Guest legacy token-F1", "guest_question", "legacy_token_f1", "rate"),
)

GUEST_QUESTION_SCORING_V2 = """## Guest-question scoring v2 (fact-based), locked 2026-11-24

Token-F1 penalised short correct answers against verbose bilingual gold. On cloud dev with gemini-3.5-flash-lite and the old prompt, the legacy token-F1 scorer gave 27/120 hallucinations (22.5%) and 53/80 in-scope correct. A manual review found 0 wrong facts. The rule was fixed on dev before any re-scoring. The test split stays untouched until the final pass, and test rows are not relabeled.

`evals/guest_questions.py` applies the rule below. Token-F1 helpers and metrics remain as `legacy_*` and are reported with the fact label.

Normalization lowercases, strips accents, collapses whitespace, and strips leading and trailing punctuation.

A refusal is a normalized answer equal to `No tengo esa información, pregúntale a los novios` or to `I don't have that information, ask the couple`. The English phrase is `UNKNOWN_ANSWER_EN` in `src/features/qa/qaRequest.js` and has no trailing period. Python keeps both strings itself. Either phrase counts, including when an English out-of-scope gold row carries the English phrase and a Spanish row carries the Spanish phrase. A refusal in the other language for the row's `lang` is still a refusal, and it is also a language mismatch. The language check compares the answer with the row's question `lang`, not with the gold text.

Time and number canonicalisation maps `1:15 a.m.`, `01:15`, and `1:15` to `01:15`. A p.m. time adds 12 hours. Plain integers are kept.

Gold facts come from the optional `gold_facts` list when the row has one. Times in that list are `HH:MM`, place names are copied from the info sheet, and polarity is the literal item `yes` or `no`. A `yes` or `no` item is polarity, not a substring. It matches when the answer's leading polarity agrees: Sí, Si, or Yes for `yes`; No, or a clear negation such as "no se puede", "no estacionar", or "do not", for `no`. A contradiction is `wrong_fact`. When `gold_facts` is absent, the facts are the canonical time and number tokens in `answer`, plus a leading Sí / Yes / No polarity recorded as `yes` or `no`.

Out-of-scope rows are correct only when the answer is a refusal. Any other answer is a hallucination.

In-scope rows:

- A refusal is `abstain`, and it is not a hallucination.
- Otherwise the label is `wrong_fact` (a hallucination) when the answer contains a canonical time or number that is not in the gold facts or the gold answer, or when the polarity contradicts the gold polarity.
- Otherwise the label is `correct` when every gold fact is present: a normalized substring for a text fact, a canonical match for a time or a number, and polarity agreement when the gold fact is `yes` or `no`.
- Otherwise the label is `incomplete`, which is not a hallucination.

Language mismatch is reported separately and does not change the fact label. The row `lang` is `en` or `es`. Detection is a stopword ratio after removing tokens that appear in proper nouns from `data/wedding_info.json` (venue and place names such as Salón El Encanto, Terraza de los Izotes, Patio de ceibas, and Jardín Principal).

Metrics: `n`, `fact_correct_rate` on in-scope rows, `wrong_fact_rate` / `hallucination_rate` on all rows, `incomplete_rate`, `abstain_rate`, refusal precision / recall / F1 on out-of-scope rows, `lang_mismatch_count` and `lang_mismatch_rate` on in-scope non-refusals, and the legacy token-F1 metrics.
"""


def _lookup(container: dict[str, Any] | None, feature: str) -> Any:
    """Read a task key, falling back to an older songs/qa summary key."""
    if not isinstance(container, dict):
        return None
    primary = container.get(feature)
    legacy_name = LEGACY_FEATURE_KEYS.get(feature)
    legacy = container.get(legacy_name) if legacy_name else None
    if isinstance(primary, dict) and primary:
        return primary
    if isinstance(legacy, dict) and legacy:
        return legacy
    if isinstance(primary, dict):
        return primary
    return legacy if isinstance(legacy, dict) else None


def load_summaries(results_dir: Path) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    if not results_dir.exists():
        return found
    for path in sorted(results_dir.glob("*/summary.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("smoke"):
            continue
        backend = data.get("backend")
        if backend not in BACKENDS:
            continue
        data["_path"] = str(path)
        previous = found.get(backend)
        if previous is None or path.stat().st_mtime >= Path(previous["_path"]).stat().st_mtime:
            found[backend] = data
    return found


def _test_section(summary: dict[str, Any] | None) -> dict[str, Any] | None:
    if summary is None:
        return None
    by_split = summary.get("by_split") or {}
    if "test" in by_split:
        return by_split["test"]
    return summary


def _guest_question_block(summary: dict[str, Any] | None) -> dict[str, Any] | None:
    """Fact metrics live on summary['guest_question'], with a per-split copy."""
    if summary is None:
        return None
    block = summary.get("guest_question")
    if not isinstance(block, dict) or not block:
        block = _lookup(summary, "guest_question")
    if not isinstance(block, dict) or not block:
        return None
    by_split = block.get("by_split")
    if isinstance(by_split, dict) and isinstance(by_split.get("test"), dict):
        return by_split["test"]
    if block.get("n") is None and "fact_correct_rate" not in block and "hallucination_rate" not in block:
        return None
    return block


def _task_block(summary: dict[str, Any] | None, task: str) -> dict[str, Any] | None:
    if summary is None:
        return None
    if task == "guest_question":
        return _guest_question_block(summary)
    routing = _lookup(summary.get("routing") or {}, task) or {}
    if isinstance(routing, dict) and routing.get("status") and "threshold" not in routing:
        return None
    section = _test_section(summary)
    if not section:
        return None
    block = _lookup(section, task)
    return block if isinstance(block, dict) else None


def _raw_value(summary: dict[str, Any] | None, task: str | None, key: str) -> Any:
    if summary is None:
        return None
    section = _test_section(summary) or {}
    if task is None:
        if key == "latency_p50":
            return (section.get("latency_ms") or {}).get("p50")
        if key == "latency_p95":
            return (section.get("latency_ms") or {}).get("p95")
        if key == "cost_usd_per_1000":
            return summary.get("cost_usd_per_1000")
        return section.get(key)
    block = _task_block(summary, task)
    if block is None:
        return None
    return block.get(key)


def format_metric(value: Any, kind: str, *, ran: bool) -> str:
    if not ran:
        return "not run"
    if value is None:
        return "n/a"
    if kind == "rate":
        return f"{float(value) * 100:.1f}%"
    if kind == "ms":
        return f"{float(value):.1f}"
    if kind == "usd":
        return f"{float(value):.4f}"
    if kind == "threshold":
        return f"{float(value):.2f}"
    return str(value)


def _routing_note(summary: dict[str, Any] | None, task: str) -> str | None:
    if summary is None:
        return None
    routing = _lookup(summary.get("routing") or {}, task) or {}
    status = routing.get("status") if isinstance(routing, dict) else None
    if isinstance(status, str):
        return status
    return None


def render_markdown(summaries: dict[str, dict[str, Any]]) -> str:
    lines = [
        "# Evaluation",
        "",
        "Comparison on the test split. Each cell is computed from a run summary.",
        "Smoke fixtures are excluded. A backend that has no summary is `not run`.",
        "",
        "Song title and artist use rapidfuzz `token_sort_ratio` with threshold 90",
        "after lowercasing and stripping accents. Hybrid keeps an on-device answer",
        "when its confidence is at least the dev-selected threshold.",
        "",
        "| Metric | " + " | ".join(BACKENDS) + " |",
        "| --- | " + " | ".join("---" for _ in BACKENDS) + " |",
    ]
    for label, task, key, kind in METRIC_ROWS:
        cells = []
        for backend in BACKENDS:
            summary = summaries.get(backend)
            value = _raw_value(summary, task, key)
            cells.append(format_metric(value, kind, ran=summary is not None))
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines.append("")
    hybrid = summaries.get("hybrid")
    for feature, label in (("rsvp", "RSVP"), ("song", "Songs")):
        note = _routing_note(hybrid, feature)
        if note:
            lines.append(f"{label} routing: {note}")
            lines.append("")
    rsvp_routing = _lookup((hybrid or {}).get("routing") or {}, "rsvp") or {}
    if isinstance(rsvp_routing, dict) and rsvp_routing.get("threshold") is not None:
        threshold = rsvp_routing["threshold"]
        lines.append(
            f"RSVP threshold {float(threshold):.2f} was selected on the dev split "
            "and applied once to the test split."
        )
        lines.append("")
    lines.append("## Language breakdown (test)")
    lines.append("")
    lines.append("| Backend | Lang | RSVP all-fields | Song all-fields |")
    lines.append("| --- | --- | --- | --- |")
    wrote_lang = False
    for backend in BACKENDS:
        summary = summaries.get(backend)
        if summary is None:
            continue
        section = _test_section(summary) or {}
        by_lang = section.get("by_lang") or {}
        for lang, block in sorted(by_lang.items()):
            wrote_lang = True
            rsvp = format_metric((_lookup(block, "rsvp") or {}).get("all_fields_correct"), "rate", ran=True)
            song = format_metric((_lookup(block, "song") or {}).get("all_fields_correct"), "rate", ran=True)
            lines.append(f"| {backend} | {lang} | {rsvp} | {song} |")
    if not wrote_lang:
        lines.append("| not run | n/a | not run | not run |")
    lines.append("")
    lines.append("## Sources")
    lines.append("")
    if not summaries:
        lines.append("No non-smoke summaries found.")
    else:
        for backend in BACKENDS:
            summary = summaries.get(backend)
            if summary is None:
                lines.append(f"- {backend}: not run")
            else:
                lines.append(f"- {backend}: `{summary.get('_path')}`")
    lines.append("")
    lines.append(GUEST_QUESTION_SCORING_V2.rstrip())
    lines.append("")
    return "\n".join(lines)


def write_report(results_dir: Path, out_path: Path) -> str:
    markdown = render_markdown(load_summaries(results_dir))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    return markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the evaluation report from summaries.")
    parser.add_argument("--results", type=Path, default=REPO_ROOT / "evals" / "results")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "docs" / "evaluation.md")
    args = parser.parse_args()
    write_report(args.results, args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
