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

# (label, task or None for a run-level metric, key, kind)
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
)


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


def _task_block(summary: dict[str, Any] | None, task: str) -> dict[str, Any] | None:
    if summary is None:
        return None
    routing = (summary.get("routing") or {}).get(task) or {}
    if routing.get("status") and "threshold" not in routing:
        return None
    section = _test_section(summary)
    if not section:
        return None
    block = section.get(task)
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
    routing = (summary.get("routing") or {}).get(task) or {}
    status = routing.get("status")
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
    for task, label in (("rsvp", "RSVP"), ("song", "Song")):
        note = _routing_note(hybrid, task)
        if note:
            lines.append(f"{label} routing: {note}")
            lines.append("")
    if hybrid and hybrid.get("routing", {}).get("rsvp", {}).get("threshold") is not None:
        threshold = hybrid["routing"]["rsvp"]["threshold"]
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
            rsvp = format_metric((block.get("rsvp") or {}).get("all_fields_correct"), "rate", ran=True)
            song = format_metric((block.get("song") or {}).get("all_fields_correct"), "rate", ran=True)
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
