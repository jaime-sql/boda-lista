import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_rules_smoke_pipeline(tmp_path: Path):
    out = tmp_path / "smoke-rules"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "evals.run",
            "--backend",
            "rules",
            "--data",
            "evals/data/smoke.jsonl",
            "--out",
            str(out),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "evals.score",
            "--gold",
            "evals/data/smoke.jsonl",
            "--predictions",
            str(out / "predictions.jsonl"),
            "--meta",
            str(out / "run_meta.json"),
            "--out",
            str(out / "summary.json"),
        ],
        cwd=ROOT,
        check=True,
    )
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["smoke"] is True
    assert summary["backend"] == "rules"
    assert summary["n"] == 15
    assert summary["invalid_json_rate"] == 0
    assert summary["rsvp"]["all_fields_correct"] == 1
    assert summary["songs"]["all_fields_correct"] == 1
    assert summary["by_split"]["stress"]["n"] == 4
    assert summary["by_lang"]["es"]["n"] > 0
    assert summary["by_lang"]["en"]["n"] > 0
