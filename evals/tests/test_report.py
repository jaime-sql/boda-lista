import json
from pathlib import Path

from evals.report import write_report


def _summary(backend, all_fields, smoke=False):
    block = {
        "n": 4,
        "invalid_json_rate": 0.0,
        "latency_ms": {"p50": 12.0, "p95": 40.0, "n": 4},
        "by_lang": {
            "es": {
                "rsvp": {"all_fields_correct": all_fields, "n": 2},
                "song": {"all_fields_correct": all_fields, "n": 2},
            }
        },
        "rsvp": {"all_fields_correct": all_fields, "n": 2, "attending_accuracy": all_fields},
        "song": {"all_fields_correct": all_fields, "n": 2, "title_artist_accuracy": all_fields},
    }
    return {
        "backend": backend,
        "smoke": smoke,
        "n": 4,
        "invalid_json_rate": 0.0,
        "latency_ms": block["latency_ms"],
        "cost_usd_per_1000": 0.0 if not smoke else 0.123,
        "by_lang": block["by_lang"],
        "by_split": {"test": block},
        "rsvp": block["rsvp"],
        "song": block["song"],
    }


def test_report_skips_smoke_and_marks_missing_backends(tmp_path: Path):
    smoke_dir = tmp_path / "results" / "smoke-rules"
    real_dir = tmp_path / "results" / "rules-test"
    smoke_dir.mkdir(parents=True)
    real_dir.mkdir()
    (smoke_dir / "summary.json").write_text(
        json.dumps(_summary("rules", 0.123, smoke=True)),
        encoding="utf-8",
    )
    (real_dir / "summary.json").write_text(
        json.dumps(_summary("rules", 0.5, smoke=False)),
        encoding="utf-8",
    )
    out = tmp_path / "evaluation.md"
    text = write_report(tmp_path / "results", out)
    assert "12.3%" not in text
    assert "50.0%" in text
    assert "not run" in text
    assert "gemma" in text


def test_legacy_songs_and_qa_keys_still_score(tmp_path: Path):
    legacy_dir = tmp_path / "results" / "rules-old"
    legacy_dir.mkdir(parents=True)
    block = {
        "n": 2,
        "invalid_json_rate": 0.0,
        "latency_ms": {"p50": 1.0, "p95": 2.0, "n": 2},
        "by_lang": {"es": {"songs": {"all_fields_correct": 0.25, "n": 2}, "qa": {"all_fields_correct": 0.5, "n": 1}}},
        "songs": {"all_fields_correct": 0.25, "n": 2, "title_artist_accuracy": 0.25},
        "qa": {"all_fields_correct": 0.5, "n": 1},
    }
    (legacy_dir / "summary.json").write_text(
        json.dumps(
            {
                "backend": "rules",
                "smoke": False,
                "n": 2,
                "invalid_json_rate": 0.0,
                "latency_ms": block["latency_ms"],
                "by_split": {"test": block},
                "songs": block["songs"],
                "qa": block["qa"],
            }
        ),
        encoding="utf-8",
    )
    text = write_report(tmp_path / "results", tmp_path / "evaluation.md")
    assert "25.0%" in text


def test_empty_results_are_not_run(tmp_path: Path):
    out = tmp_path / "evaluation.md"
    text = write_report(tmp_path / "missing", out)
    assert "not run" in text
    assert "0.0%" not in text
