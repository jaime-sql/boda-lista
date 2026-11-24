"""Pick an on-device confidence threshold from the DEV split only.

Selection refuses test and stress labels. The chosen threshold is applied
once to the test split by a separate function. Songs are not tuned on the
test file: with no song dev split the result is exactly
'no song threshold: no dev split'.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evals.guest_questions import answer_confidence, answer_text, format_guest_metric_line, is_fact_hallucination
from evals.parsing import resolve_prediction
from evals.score import index_predictions, item_correct, load_predictions, score_predictions

SONG_NO_DEV = "no song threshold: no dev split"
RSVP_NO_DEV = "no rsvp threshold: no dev split"
ACCURACY_SLACK = 0.01


class TestLabelLeakError(RuntimeError):
    """Threshold selection was asked to read a non-dev label."""

    __test__ = False


class NoDevRowsError(RuntimeError):
    """The threshold script was started with no dev rows to select on."""


NO_DEV_ROWS = (
    "refusing to run: no dev rows. Threshold selection does not read the test split."
)


def assert_dev_only(items: list[dict[str, Any]]) -> None:
    """Look at split and nothing else. Call this before any gold field is used."""
    for item in items:
        split = item.get("split")
        if split != "dev":
            raise TestLabelLeakError(
                "refusing to read "
                f"split={split!r} labels during threshold selection (id={item.get('id')!r})"
            )


def load_dev_for_selection(paths: list[Path | str], schema_path: Path | None = None) -> list[dict[str, Any]]:
    """Load dev rows. Known test and stress filenames are refused before open."""
    from evals.loader import load_paths

    return load_paths(list(paths), schema_path=schema_path, dev_only=True)


def _basis(confidence: float) -> int:
    return int(round(float(confidence) * 100))


def _device_keep(gold: dict[str, Any], prediction: dict[str, Any] | None, basis: int) -> tuple[bool, bool]:
    """Return (keep_on_device, correct). Invalid device JSON is never kept."""
    output, error, _latency, confidence = resolve_prediction(gold["task"], prediction)
    if error is not None or output is None or confidence is None:
        return False, False
    if _basis(confidence) < basis:
        return False, item_correct(gold, output)
    return True, item_correct(gold, output)


def select_threshold(
    items: list[dict[str, Any]],
    device_by_id: dict[str, dict[str, Any]],
    cloud_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Sweep thresholds on dev items already proven to be split=dev.

    The kept threshold is the lowest cutoff that maximizes on-device share
    while hybrid accuracy stays within 1 percentage point of cloud-only.
    Hybrid accuracy uses the on-device answer when its confidence is at or
    above the threshold and the cloud answer otherwise.
    """
    assert_dev_only(items)
    if not items:
        raise ValueError("no dev items for threshold selection")
    missing = [
        item["id"]
        for item in items
        if item["id"] not in device_by_id or item["id"] not in cloud_by_id
    ]
    if missing:
        raise ValueError(f"dev predictions missing for ids {missing[:5]}")

    cloud_correct = []
    for item in items:
        cloud_output, _error, _latency, _conf = resolve_prediction(item["task"], cloud_by_id[item["id"]])
        cloud_correct.append(item_correct(item, cloud_output))
    cloud_accuracy = sum(cloud_correct) / len(items)

    best_key: tuple[float, float, int] | None = None
    best_row: dict[str, Any] | None = None
    sweep: list[dict[str, Any]] = []
    for basis in range(0, 101):
        kept_correct: list[bool] = []
        hybrid_correct: list[bool] = []
        for item, cloud_ok in zip(items, cloud_correct):
            keep, device_ok = _device_keep(item, device_by_id[item["id"]], basis)
            if keep:
                kept_correct.append(device_ok)
                hybrid_correct.append(device_ok)
            else:
                hybrid_correct.append(cloud_ok)
        share = len(kept_correct) / len(items)
        hybrid_accuracy = sum(hybrid_correct) / len(items)
        kept_accuracy = (sum(kept_correct) / len(kept_correct)) if kept_correct else None
        row = {
            "threshold": basis / 100,
            "on_device_share": share,
            "kept_accuracy": kept_accuracy,
            "hybrid_accuracy": hybrid_accuracy,
        }
        sweep.append(row)
        if hybrid_accuracy + 1e-12 < cloud_accuracy - ACCURACY_SLACK:
            continue
        key = (share, hybrid_accuracy, -basis)
        if best_key is None or key > best_key:
            best_key = key
            best_row = row

    if best_row is None:
        chosen = {
            "threshold": 1.01,
            "on_device_share": 0.0,
            "kept_accuracy": None,
            "hybrid_accuracy": cloud_accuracy,
            "fallback": (
                "no threshold kept hybrid accuracy within 1 point of cloud-only; "
                "send all to cloud"
            ),
        }
    else:
        chosen = dict(best_row)
    chosen["cloud_accuracy"] = cloud_accuracy
    chosen["n"] = len(items)
    chosen["slack"] = ACCURACY_SLACK
    chosen["sweep"] = sweep
    # cloud_cutoff is the routing threshold above. high is the same rule with
    # zero slack, so the high band is never looser than the cloud cutoff.
    chosen["cloud_cutoff"] = chosen["threshold"]
    chosen["high"] = _high_cutoff(sweep, cloud_accuracy, chosen["cloud_cutoff"])
    return chosen


def _high_cutoff(sweep: list[dict[str, Any]], cloud_accuracy: float, cloud_cutoff: float) -> float:
    """Lowest zero-slack threshold that maximizes on-device share."""
    best_key: tuple[float, float, int] | None = None
    best_threshold: float | None = None
    for row in sweep:
        if row["hybrid_accuracy"] + 1e-12 < cloud_accuracy:
            continue
        basis = int(round(float(row["threshold"]) * 100))
        key = (row["on_device_share"], row["hybrid_accuracy"], -basis)
        if best_key is None or key > best_key:
            best_key = key
            best_threshold = float(row["threshold"])
    if best_threshold is None or best_threshold < cloud_cutoff:
        return cloud_cutoff
    return best_threshold


def route_predictions(
    items: list[dict[str, Any]],
    device_by_id: dict[str, dict[str, Any]],
    cloud_by_id: dict[str, dict[str, Any]],
    threshold: float,
) -> tuple[list[dict[str, Any]], float]:
    """Apply a frozen threshold. This does not look for a new threshold."""
    basis = _basis(threshold) if threshold <= 1 else 101
    routed: list[dict[str, Any]] = []
    kept = 0
    for item in items:
        keep, _correct = _device_keep(item, device_by_id.get(item["id"]), basis)
        if keep:
            kept += 1
            chosen = device_by_id[item["id"]]
        else:
            chosen = cloud_by_id.get(item["id"]) or {"id": item["id"]}
        routed.append(chosen)
    share = kept / len(items) if items else 0.0
    return routed, share


def evaluate_task(
    *,
    task: str,
    dev_paths: list[Path] | None,
    test_paths: list[Path] | None,
    device_dev: dict[str, dict[str, Any]] | None,
    cloud_dev: dict[str, dict[str, Any]] | None,
    device_test: dict[str, dict[str, Any]] | None,
    cloud_test: dict[str, dict[str, Any]] | None,
    no_dev_message: str,
    schema_path: Path | None = None,
) -> dict[str, Any]:
    """Select on dev, then apply once to test.

    An empty dev path list returns no_dev_message and does not read test labels.
    """
    if not dev_paths:
        return {"status": no_dev_message}
    dev_items = [
        row
        for row in load_dev_for_selection(dev_paths, schema_path=schema_path)
        if row.get("task") == task
    ]
    if not dev_items:
        return {"status": no_dev_message}
    if device_dev is None or cloud_dev is None:
        raise ValueError(f"{task} dev predictions are required when a dev split is present")
    chosen = select_threshold(dev_items, device_dev, cloud_dev)
    result: dict[str, Any] = {
        "threshold": chosen["threshold"],
        "high": chosen["high"],
        "cloud_cutoff": chosen["cloud_cutoff"],
        "dev": {key: value for key, value in chosen.items() if key != "sweep"},
        "sweep": chosen["sweep"],
    }
    if not test_paths:
        return result
    from evals.loader import load_paths

    test_items = [
        row
        for row in load_paths(test_paths, schema_path=schema_path)
        if row.get("task") == task and row.get("split") == "test"
    ]
    if device_test is None or cloud_test is None:
        raise ValueError(f"{task} test predictions are required to apply the threshold")
    routed, share = route_predictions(test_items, device_test, cloud_test, chosen["threshold"])
    result["test_items"] = test_items
    result["test_predictions"] = routed
    result["on_device_share"] = share
    return result


def select_guest_question_cutoff(
    items: list[dict[str, Any]],
    predictions_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Smallest dev confidence t with fact-hallucination rate <= 2% and n >= min_n.

    A hallucination is an in-scope wrong_fact or an out-of-scope non-refusal.
    Incomplete and abstain answers are not hallucinations. Rows below t are the
    ones the app sends to the cloud. Test rows are refused before any gold
    answer is scored.
    """
    assert_dev_only(items)
    if not items:
        raise ValueError("no dev guest_question rows")
    scored: list[tuple[float | None, bool]] = []
    for item in items:
        prediction = predictions_by_id.get(item["id"])
        scored.append((answer_confidence(prediction), is_fact_hallucination(item, answer_text(prediction))))

    def kept_rate(basis: int) -> tuple[int, float]:
        kept = [hallucinated for confidence, hallucinated in scored if confidence is not None and _basis(confidence) >= basis]
        if not kept:
            return 0, 1.0
        return len(kept), sum(kept) / len(kept)

    cloud_basis: int | None = None
    for basis in range(0, 101):
        count, rate = kept_rate(basis)
        if count >= MIN_N and rate <= 0.02 + 1e-12:
            cloud_basis = basis
            break
    high_basis: int | None = None
    for basis in range(0, 101):
        count, rate = kept_rate(basis)
        if count >= MIN_N and rate <= 1e-12:
            high_basis = basis
            break
    if cloud_basis is None:
        cloud_cutoff = 1.01
        high = 1.01
    else:
        cloud_cutoff = cloud_basis / 100
        high = (high_basis / 100) if high_basis is not None else cloud_cutoff
        if high < cloud_cutoff:
            high = cloud_cutoff
    return {
        "threshold": cloud_cutoff,
        "cloud_cutoff": cloud_cutoff,
        "high": high,
        "n": len(items),
        "dev": {"n": len(items), "hallucination_rate_at_cutoff": None if cloud_basis is None else kept_rate(cloud_basis)[1]},
    }


def evaluate_guest_question(
    *,
    dev_paths: list[Path] | None,
    test_paths: list[Path] | None,
    device_by_id: dict[str, dict[str, Any]] | None,
    test_by_id: dict[str, dict[str, Any]] | None = None,
    schema_path: Path | None = None,
) -> dict[str, Any]:
    """Select on dev guest_question rows, then score the test split once."""
    if not dev_paths:
        return {"status": NO_DEV_NOTE}
    dev_items = [
        row
        for row in load_dev_for_selection(dev_paths, schema_path=schema_path)
        if row.get("task") == "guest_question"
    ]
    if not dev_items:
        return {"status": NO_DEV_NOTE}
    if device_by_id is None:
        raise ValueError("guest_question dev predictions are required when a dev split is present")
    chosen = select_guest_question_cutoff(dev_items, device_by_id)
    result = dict(chosen)
    if not test_paths:
        return result
    from evals.guest_questions import score_guest_questions
    from evals.loader import load_paths

    test_items = [
        row
        for row in load_paths(test_paths, schema_path=schema_path)
        if row.get("task") == "guest_question" and row.get("split") == "test"
    ]
    result["test"] = score_guest_questions(test_items, test_by_id or {})
    return result


def build_hybrid_summary(
    *,
    rsvp_dev: list[Path] | None,
    song_dev: list[Path] | None,
    rsvp_test: list[Path] | None,
    song_test: list[Path] | None,
    device_dev_path: Path | None,
    cloud_dev_path: Path | None,
    device_test_path: Path | None,
    cloud_test_path: Path | None,
    guest_dev: list[Path] | None = None,
    guest_test: list[Path] | None = None,
    schema_path: Path | None = None,
) -> dict[str, Any]:
    if not rsvp_dev and not song_dev and not guest_dev:
        raise NoDevRowsError(NO_DEV_ROWS)
    device_dev = index_predictions(load_predictions(device_dev_path)) if device_dev_path else None
    cloud_dev = index_predictions(load_predictions(cloud_dev_path)) if cloud_dev_path else None
    device_test = index_predictions(load_predictions(device_test_path)) if device_test_path else None
    cloud_test = index_predictions(load_predictions(cloud_test_path)) if cloud_test_path else None

    # Song dev is optional. Do not open the song test file when it is absent.
    # The current labeled pack is test-only; with no dev rows at all, refuse.
    song = evaluate_task(
        task="song",
        dev_paths=song_dev,
        test_paths=song_test,
        device_dev=device_dev,
        cloud_dev=cloud_dev,
        device_test=device_test,
        cloud_test=cloud_test,
        no_dev_message=SONG_NO_DEV,
        schema_path=schema_path,
    )
    rsvp = evaluate_task(
        task="rsvp",
        dev_paths=rsvp_dev,
        test_paths=rsvp_test,
        device_dev=device_dev,
        cloud_dev=cloud_dev,
        device_test=device_test,
        cloud_test=cloud_test,
        no_dev_message=RSVP_NO_DEV,
        schema_path=schema_path,
    )
    guest = evaluate_guest_question(
        dev_paths=guest_dev,
        test_paths=guest_test,
        device_by_id=device_dev,
        test_by_id=device_test,
        schema_path=schema_path,
    )
    if "threshold" not in rsvp and "threshold" not in song and "threshold" not in guest:
        raise NoDevRowsError(NO_DEV_ROWS)
    golds: list[dict[str, Any]] = []
    preds: list[dict[str, Any]] = []
    for task_result in (rsvp, song):
        golds.extend(task_result.get("test_items") or [])
        preds.extend(task_result.get("test_predictions") or [])
    if golds:
        summary = score_predictions(golds, preds, backend="hybrid", smoke=False)
    else:
        summary = {
            "backend": "hybrid",
            "smoke": False,
            "n": 0,
            "invalid_json_rate": None,
            "latency_ms": {"p50": None, "p95": None, "n": 0},
            "cost_usd_per_1000": None,
            "guest_question": {},
            "rsvp": {},
            "song": {},
            "by_lang": {},
            "by_split": {},
        }
    for task_name, task_result in (("rsvp", rsvp), ("song", song)):
        if "on_device_share" not in task_result:
            continue
        for block in (
            summary.get("by_split", {}).get("test", {}).get(task_name),
            summary.get(task_name),
        ):
            if isinstance(block, dict) and block.get("n"):
                block["on_device_share"] = task_result["on_device_share"]
                block["threshold"] = task_result["threshold"]
    summary["routing"] = {
        "guest_question": {key: value for key, value in guest.items() if key != "test"},
        "rsvp": {key: value for key, value in rsvp.items() if key not in {"test_items", "test_predictions"}},
        "song": {key: value for key, value in song.items() if key not in {"test_items", "test_predictions"}},
    }
    summary["cost_basis"] = "hybrid cost is not estimated; on-device calls are free and cloud tokens are uncounted"
    guest_test = guest.get("test")
    if isinstance(guest_test, dict) and "n" in guest_test:
        summary["guest_question"] = guest_test
    return summary


# App config shape. min_n is a fixed sample floor, not fit on labels.
# The harness never writes the app file at tokens/config.json.
FEATURES = ("guest_question", "rsvp", "song")
MIN_N = 20
NO_DEV_NOTE = "no dev split"


def empty_feature_config() -> dict[str, Any]:
    return {"high": None, "cloud_cutoff": None, "min_n": None, "note": NO_DEV_NOTE}


def _dev_count(selection: dict[str, Any]) -> int:
    if isinstance(selection.get("n"), int):
        return selection["n"]
    dev = selection.get("dev")
    if isinstance(dev, dict) and isinstance(dev.get("n"), int):
        return dev["n"]
    return 0


def feature_config_from_selection(selection: dict[str, Any]) -> dict[str, Any]:
    """Build one feature block from a dev-only selection.

    Cutoffs are published only when the dev split has at least min_n rows.
    Anything below cloud_cutoff is sent to the cloud. This function does not
    read gold labels.
    """
    if "threshold" not in selection or "high" not in selection or "cloud_cutoff" not in selection:
        return empty_feature_config()
    if _dev_count(selection) < MIN_N:
        return {"high": None, "cloud_cutoff": None, "min_n": MIN_N}
    return {
        "high": selection["high"],
        "cloud_cutoff": selection["cloud_cutoff"],
        "min_n": MIN_N,
    }


def app_config(routing: dict[str, Any]) -> dict[str, Any]:
    """Config keyed by the schema task values. guest_question has no dev split."""
    config = {feature: empty_feature_config() for feature in FEATURES}
    for feature in FEATURES:
        config[feature] = feature_config_from_selection(routing.get(feature) or {})
    return config


def write_app_config(routing: dict[str, Any], directory: Path) -> Path:
    """Write evals/results/<run_id>/config.json. Does not touch tokens/config.json."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "config.json"
    path.write_text(json.dumps(app_config(routing), indent=2) + "\n", encoding="utf-8")
    return path


def _existing(paths: list[Path] | None) -> list[Path] | None:
    """Keep paths that exist. Return None when nothing remains."""
    if not paths:
        return None
    kept = [path for path in paths if Path(path).exists()]
    return kept or None


def main() -> None:
    parser = argparse.ArgumentParser(description="Select a dev threshold and apply it once to test.")
    parser.add_argument("--device-dev", type=Path)
    parser.add_argument("--cloud-dev", type=Path)
    parser.add_argument("--device-test", type=Path)
    parser.add_argument("--cloud-test", type=Path)
    parser.add_argument("--rsvp-dev", type=Path, nargs="*", default=None)
    parser.add_argument("--rsvp-test", type=Path, nargs="*", default=None)
    parser.add_argument("--song-dev", type=Path, nargs="*", default=None)
    parser.add_argument("--song-test", type=Path, nargs="*", default=None)
    parser.add_argument("--guest-dev", type=Path, nargs="*", default=None)
    parser.add_argument("--guest-test", type=Path, nargs="*", default=None)
    parser.add_argument("--schema", type=Path, default=None)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    rsvp_dev = _existing(args.rsvp_dev)
    song_dev = _existing(args.song_dev)
    guest_dev = _existing(args.guest_dev)
    if not rsvp_dev and not song_dev and not guest_dev:
        raise SystemExit(NO_DEV_ROWS)
    if args.out is None:
        parser.error("the following arguments are required: --out")
    missing = [
        name
        for name, value in (
            ("--device-dev", args.device_dev),
            ("--cloud-dev", args.cloud_dev),
            ("--device-test", args.device_test),
            ("--cloud-test", args.cloud_test),
        )
        if value is None
    ]
    if missing:
        raise SystemExit("missing " + ", ".join(missing))
    try:
        summary = build_hybrid_summary(
            rsvp_dev=rsvp_dev,
            song_dev=song_dev,
            rsvp_test=_existing(args.rsvp_test),
            song_test=_existing(args.song_test),
            guest_dev=guest_dev,
            guest_test=_existing(args.guest_test),
            device_dev_path=args.device_dev,
            cloud_dev_path=args.cloud_dev,
            device_test_path=args.device_test,
            cloud_test_path=args.cloud_test,
            schema_path=args.schema,
        )
    except NoDevRowsError as exc:
        raise SystemExit(str(exc)) from exc
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    config_path = write_app_config(summary["routing"], args.out.parent)
    song_status = summary["routing"]["song"].get("status", "selected")
    rsvp_threshold = summary["routing"]["rsvp"].get("threshold")
    print(f"wrote {args.out} rsvp_threshold={rsvp_threshold} song={song_status}")
    print(f"wrote {config_path}")
    guest_line = format_guest_metric_line(summary.get("guest_question"))
    if guest_line:
        print(guest_line)


if __name__ == "__main__":
    main()
