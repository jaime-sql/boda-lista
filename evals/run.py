"""Run the rules baseline and write predictions JSONL.

Gemma runs on Modal (`evals/modal_gemma.py`). Nano and cloud Gemini run
in desktop Chrome (`evals/nano_runner/index.html`). This command is the
local CPU step.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from evals.guest_questions import UNKNOWN_ANSWER
from evals.loader import load_paths
from evals.rules import predict_all


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one evaluation backend.")
    parser.add_argument("--backend", required=True, choices=["rules", "gemma", "nano", "cloud"])
    parser.add_argument("--data", required=True, nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path, help="Directory for predictions.jsonl")
    parser.add_argument("--schema", type=Path, default=None)
    args = parser.parse_args()
    if args.backend == "gemma":
        raise SystemExit(
            "Gemma runs on Modal, not in this process.\n"
            "  modal run evals/modal_gemma.py --data <jsonl> --out evals/results/<run_id>"
        )
    if args.backend in {"nano", "cloud"}:
        raise SystemExit(
            "Nano and cloud Gemini run in desktop Chrome on Jaime's laptop.\n"
            "  python -m http.server 8765\n"
            "  open http://localhost:8765/evals/nano_runner/index.html\n"
            "Use the on-device toggle for nano and the cloud-only toggle for cloud."
        )

    rows = load_paths(args.data, schema_path=args.schema)
    skipped = [row for row in rows if row.get("task") not in {"rsvp", "song"}]
    scoped = [row for row in rows if row.get("task") in {"rsvp", "song"}]
    if skipped:
        print(
            f"skipped {len(skipped)} out-of-scope rows "
            f"(guest_questions TODO, unknown gold {UNKNOWN_ANSWER!r})"
        )
    predictions = predict_all(scoped)
    args.out.mkdir(parents=True, exist_ok=True)
    pred_path = args.out / "predictions.jsonl"
    with pred_path.open("w", encoding="utf-8") as handle:
        for row in predictions:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    smoke = any("smoke" in path.name for path in args.data)
    meta = {
        "backend": "rules",
        "smoke": smoke,
        "n": len(predictions),
        "data": [str(path) for path in args.data],
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "estimated_gpu_seconds": 0,
        "gpu": None,
    }
    (args.out / "run_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {pred_path} n={len(predictions)} smoke={smoke}")


if __name__ == "__main__":
    main()
