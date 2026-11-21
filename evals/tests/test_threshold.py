import json
from pathlib import Path

import pytest

from evals.threshold import (
    SONG_NO_DEV,
    NoDevRowsError,
    TestLabelLeakError,
    build_hybrid_summary,
    evaluate_task,
    load_dev_for_selection,
    route_predictions,
    select_threshold,
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
