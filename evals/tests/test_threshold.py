import json
import subprocess
import sys
from pathlib import Path

import pytest

from evals.threshold import (
    MIN_N,
    SONG_NO_DEV,
    NoDevRowsError,
    TestLabelLeakError,
    app_config,
    build_hybrid_summary,
    evaluate_task,
    load_dev_for_selection,
    route_predictions,
    select_threshold,
    write_app_config,
)


def _gold(index, attending="yes"):
    return {
        "id": f"d{index}",
        "split": "dev",
        "task": "rsvp",
        "text": "x",
        "lang": "es",
        "attending": attending,
        "party_size": 2,
        "meal_restrictions": [],
        "kids_count": None,
        "needs_ride": False,
        "ambiguous": False,
    }


def _output(attending):
    return {
        "attending": attending,
        "party_size": 2,
        "meal_restrictions": [],
        "kids_count": None,
        "needs_ride": False,
        "ambiguous": False,
        "confidence": 0.9,
    }


def _pred(index, attending, confidence):
    output = _output(attending)
    output["confidence"] = confidence
    return {"id": f"d{index}", "confidence": confidence, "latency_ms": 3, "raw": json.dumps(output)}


def test_guard_raises_before_scoring_test_labels(monkeypatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("test labels were scored")

    monkeypatch.setattr("evals.threshold.item_correct", boom)
    with pytest.raises(TestLabelLeakError):
        select_threshold(
            [{"id": "t", "split": "test", "task": "rsvp", "attending": "yes"}],
            {},
            {},
        )


def test_guard_rejects_stress_split():
    with pytest.raises(TestLabelLeakError):
        select_threshold([{"id": "s", "split": "stress", "task": "song"}], {}, {})


def test_known_test_filenames_are_refused_before_open(tmp_path):
    for name in ("rsvp_replies.jsonl", "song_requests.jsonl", "rsvp_stress.jsonl"):
        missing = tmp_path / name
        with pytest.raises(TestLabelLeakError):
            load_dev_for_selection([missing])


def test_selects_lowest_threshold_that_maximizes_on_device_share():
    items = [_gold(index) for index in range(10)]
    device = {}
    cloud = {}
    for index in range(10):
        if index < 6:
            device[f"d{index}"] = _pred(index, "yes", 0.9)
        else:
            device[f"d{index}"] = _pred(index, "no", 0.2)
        cloud[f"d{index}"] = _pred(index, "yes", 0.99)
    chosen = select_threshold(items, device, cloud)
    assert chosen["threshold"] == pytest.approx(0.21)
    assert chosen["on_device_share"] == pytest.approx(0.6)
    assert chosen["hybrid_accuracy"] == pytest.approx(1.0)
    assert chosen["cloud_accuracy"] == pytest.approx(1.0)
    assert chosen["kept_accuracy"] == pytest.approx(1.0)


def test_apply_does_not_reselect(monkeypatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("selection ran during apply")

    monkeypatch.setattr("evals.threshold.select_threshold", boom)
    items = [_gold(0)]
    items[0]["split"] = "test"
    device = {"d0": _pred(0, "yes", 0.95)}
    cloud = {"d0": _pred(0, "no", 0.99)}
    routed, share = route_predictions(items, device, cloud, 0.9)
    assert share == pytest.approx(1.0)
    assert json.loads(routed[0]["raw"])["attending"] == "yes"


def test_refuses_to_run_when_no_dev_rows_exist(tmp_path):
    test_file = tmp_path / "rsvp_replies.jsonl"
    with pytest.raises(NoDevRowsError, match="no dev rows"):
        build_hybrid_summary(
            rsvp_dev=None,
            song_dev=None,
            rsvp_test=[test_file],
            song_test=[tmp_path / "song_requests.jsonl"],
            device_dev_path=None,
            cloud_dev_path=None,
            device_test_path=None,
            cloud_test_path=None,
        )
    assert not test_file.exists()


def test_song_without_dev_does_not_read_test_labels(tmp_path):
    def load_test():
        raise AssertionError("song test labels were read")

    missing_test = tmp_path / "song_requests.jsonl"
    result = evaluate_task(
        task="song",
        dev_paths=None,
        test_paths=[missing_test],
        device_dev=None,
        cloud_dev=None,
        device_test=None,
        cloud_test=None,
        no_dev_message=SONG_NO_DEV,
    )
    assert result == {"status": SONG_NO_DEV}
    assert load_test  # the helper exists so a future edit that calls it will fail the raise above
    assert not missing_test.exists()


def test_dev_file_with_only_rsvp_rows_does_not_open_song_test(tmp_path):
    dev = tmp_path / "song_dev_generated.jsonl"
    dev.write_text(
        json.dumps(
            {
                "id": "only-rsvp",
                "split": "dev",
                "task": "rsvp",
                "text": "vamos 1",
                "lang": "es",
                "attending": "yes",
                "party_size": 1,
                "meal_restrictions": [],
                "kids_count": None,
                "needs_ride": False,
                "ambiguous": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    test = tmp_path / "do-not-open.jsonl"
    result = evaluate_task(
        task="song",
        dev_paths=[dev],
        test_paths=[test],
        device_dev={},
        cloud_dev={},
        device_test=None,
        cloud_test=None,
        no_dev_message=SONG_NO_DEV,
        schema_path=Path("evals/schema_builtin.json"),
    )
    assert result["status"] == SONG_NO_DEV
    assert not test.exists()


def _selection(high, cloud_cutoff, n):
    return {"threshold": cloud_cutoff, "high": high, "cloud_cutoff": cloud_cutoff, "n": n}


def test_config_file_shape(tmp_path):
    routing = {
        "rsvp": _selection(0.8, 0.55, MIN_N),
        "songs": {"status": SONG_NO_DEV},
    }
    run_dir = tmp_path / "results" / "dev-run"
    path = write_app_config(routing, run_dir)
    assert path == run_dir / "config.json"
    assert path.name == "config.json"
    assert "tokens" not in path.parts

    config = json.loads(path.read_text(encoding="utf-8"))
    assert list(config) == ["qa", "rsvp", "songs"]
    assert "analytics" not in json.dumps(config)

    published = config["rsvp"]
    assert set(published) == {"high", "cloud_cutoff", "min_n"}
    assert published["high"] == 0.8
    assert published["cloud_cutoff"] == 0.55
    assert published["high"] >= published["cloud_cutoff"]
    assert published["min_n"] == 20

    for feature in ("qa", "songs"):
        block = config[feature]
        assert block["high"] is None
        assert block["cloud_cutoff"] is None
        assert block["min_n"] is None
        assert block["note"] == "no dev split"

    short = app_config({"rsvp": _selection(0.9, 0.4, MIN_N - 1), "songs": {}})
    assert short["rsvp"] == {"high": None, "cloud_cutoff": None, "min_n": 20}
    assert "note" not in short["rsvp"]

    items = [_gold(0)]
    items[0]["split"] = "test"
    device = {"d0": _pred(0, "yes", 0.54)}
    cloud = {"d0": _pred(0, "no", 0.99)}
    routed, share = route_predictions(items, device, cloud, published["cloud_cutoff"])
    assert share == 0.0
    assert json.loads(routed[0]["raw"])["attending"] == "no"


ROOT = Path(__file__).resolve().parents[2]
README_THRESHOLD_ARGS = [
    "--rsvp-dev",
    "data/rsvp_dev_generated.jsonl",
    "--rsvp-test",
    "data/rsvp_replies.jsonl",
    "--song-dev",
    "data/song_dev_generated.jsonl",
    "--song-test",
    "data/song_requests.jsonl",
    "--device-dev",
    "evals/results/nano-dev/predictions.jsonl",
    "--cloud-dev",
    "evals/results/cloud-dev/predictions.jsonl",
    "--device-test",
    "evals/results/nano-test/predictions.jsonl",
    "--cloud-test",
    "evals/results/cloud-test/predictions.jsonl",
    "--out",
    "evals/results/hybrid/summary.json",
]


def _run_threshold(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "evals.threshold", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_threshold_refuses_without_dev_rows():
    cases = [
        [],
        README_THRESHOLD_ARGS,
        ["--out", "evals/results/hybrid/summary.json"],
    ]
    assert not (ROOT / "data" / "rsvp_dev_generated.jsonl").exists()
    assert not (ROOT / "data" / "song_dev_generated.jsonl").exists()
    assert not (ROOT / "evals" / "results" / "nano-dev" / "predictions.jsonl").exists()
    for args in cases:
        result = _run_threshold(args)
        combined = result.stdout + result.stderr
        assert result.returncode != 0
        assert combined.startswith("refusing to run: no dev rows") or "refusing to run: no dev rows" in combined.splitlines()
        assert "refusing to run: no dev rows" in combined
        assert "FileNotFoundError" not in combined
        assert "Traceback" not in combined
        assert "--out required" not in combined
        assert "arguments are required: --out" not in combined
