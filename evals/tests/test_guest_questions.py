import json
from pathlib import Path

import pytest

from evals.score import score_predictions

from evals.guest_questions import (
    UNKNOWN_ANSWER,
    facts_match,
    is_hallucination,
    is_in_scope_correct,
    is_refusal,
    score_guest_questions,
)
from evals.threshold import (
    MIN_N,
    TestLabelLeakError,
    app_config,
    evaluate_guest_question,
    select_guest_question_cutoff,
)


def test_refusal_normalization_ignores_case_accents_and_trailing_punctuation():
    assert is_refusal("NO TENGO ESA INFORMACION, PREGUNTALE A LOS NOVIOS.")
    assert is_refusal("  ¿" + UNKNOWN_ANSWER + "!  ")
    assert not is_refusal("No sé, pregúntale a los novios.")
    assert not is_refusal("")


def test_in_scope_correctness_requires_overlap_and_numbers():
    gold = "La ceremonia es a las 16:00 en el jardin principal."
    full = "La ceremonia es a las 16:00 en el jardin principal de la hacienda."
    missing_time = "La ceremonia es en el jardin principal de la hacienda esta tarde."
    assert facts_match(full, gold)
    assert not facts_match(missing_time, gold)
    row = {"out_of_scope": False, "answer": gold}
    assert is_in_scope_correct(row, full)
    assert not is_in_scope_correct(row, missing_time)
    assert not is_in_scope_correct(row, UNKNOWN_ANSWER)
    assert not is_hallucination(row, UNKNOWN_ANSWER)
    assert is_hallucination(row, missing_time)
    assert is_hallucination({"out_of_scope": True, "answer": UNKNOWN_ANSWER}, "Son las 16:00.")
    assert not is_hallucination({"out_of_scope": True, "answer": UNKNOWN_ANSWER}, UNKNOWN_ANSWER + ".")


def _guest(index: int, split: str, answer: str, out_of_scope: bool = False) -> dict:
    return {
        "id": f"q{index}",
        "split": split,
        "task": "guest_question",
        "text": "pregunta",
        "lang": "es",
        "answer": answer,
        "out_of_scope": out_of_scope,
    }


def _pred(index: int, answer: str, confidence: float) -> dict:
    return {"id": f"q{index}", "confidence": confidence, "output": {"answer": answer, "confidence": confidence}}


def test_guest_cutoff_is_the_smallest_t_under_two_percent():
    items = []
    preds = {}
    for index in range(50):
        items.append(_guest(index, "dev", "La ceremonia es a las 16:00."))
        preds[f"q{index}"] = _pred(index, "La ceremonia es a las 16:00 en el jardin.", 0.9)
    items.append(_guest(50, "dev", "La ceremonia es a las 16:00."))
    preds["q50"] = _pred(50, "No hay horario.", 0.6)
    for index in range(51, 61):
        items.append(_guest(index, "dev", "La ceremonia es a las 16:00."))
        preds[f"q{index}"] = _pred(index, "Inventado.", 0.1)
    chosen = select_guest_question_cutoff(items, preds)
    assert chosen["cloud_cutoff"] == pytest.approx(0.11)
    assert chosen["high"] == pytest.approx(0.61)
    assert chosen["high"] >= chosen["cloud_cutoff"]
    assert chosen["n"] >= MIN_N
    config = app_config({"guest_question": chosen, "rsvp": {}, "song": {}})
    assert config["guest_question"]["cloud_cutoff"] == pytest.approx(0.11)
    assert config["guest_question"]["min_n"] == 20


def test_guest_question_without_dev_stays_null():
    config = app_config({"rsvp": {}, "song": {}})
    assert config["guest_question"]["high"] is None
    assert config["guest_question"]["cloud_cutoff"] is None
    assert config["guest_question"]["min_n"] is None
    assert config["guest_question"]["note"] == "no dev split"


def test_guest_selection_does_not_open_test_rows(tmp_path, monkeypatch):
    dev = tmp_path / "guest_dev.jsonl"
    test = tmp_path / "guest_test.jsonl"
    rows = []
    preds = {}
    for index in range(25):
        row = _guest(index, "dev", "La ceremonia es a las 16:00.")
        rows.append(row)
        preds[row["id"]] = _pred(index, "La ceremonia es a las 16:00.", 0.95)
    dev.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    test.write_text(
        json.dumps(_guest(99, "test", "La ceremonia es a las 16:00.")) + "\n",
        encoding="utf-8",
    )
    opened: list[str] = []
    from evals import loader

    real_load = loader.load_paths

    def spy(paths, **kwargs):
        opened.extend(Path(path).name for path in paths)
        return real_load(paths, **kwargs)

    monkeypatch.setattr(loader, "load_paths", spy)
    with pytest.raises(TestLabelLeakError):
        select_guest_question_cutoff([_guest(1, "test", "x", True)], {})
    assert opened == []
    result = evaluate_guest_question(
        dev_paths=[dev],
        test_paths=[test],
        device_by_id=preds,
        test_by_id={},
        schema_path=Path("evals/schema_builtin.json"),
    )
    assert result["cloud_cutoff"] == pytest.approx(0.0)
    assert opened[0] == "guest_dev.jsonl"
    assert opened[-1] == "guest_test.jsonl"
    assert opened.index("guest_test.jsonl") > opened.index("guest_dev.jsonl")
    scored = score_guest_questions(rows, preds)
    assert scored["by_split"]["dev"]["n"] == 25
    assert scored["hallucination_rate"] == 0.0


def test_nano_guest_prediction_jsonl_scores_without_test_split():
    phrase = "No tengo esa información, pregúntale a los novios"
    golds = [
        {
            "id": "fake-dev-time",
            "split": "dev",
            "task": "guest_question",
            "text": "A que hora es la ceremonia?",
            "lang": "es",
            "answer": "La ceremonia es a las 16:00.",
            "out_of_scope": False,
        },
        {
            "id": "fake-dev-unknown",
            "split": "dev",
            "task": "guest_question",
            "text": "Cual es el menu secreto?",
            "lang": "es",
            "answer": phrase,
            "out_of_scope": True,
        },
    ]
    predictions = [
        {
            "id": "fake-dev-time",
            "task": "guest_question",
            "split": "dev",
            "lang": "es",
            "ok": True,
            "error": None,
            "confidence": 0.91,
            "latency_ms": 12,
            "inference_source": "ON_DEVICE",
            "output": {"answer": "La ceremonia es a las 16:00.", "confidence": 0.91},
            "raw": json.dumps({"answer": "La ceremonia es a las 16:00.", "confidence": 0.91}),
        },
        {
            "id": "fake-dev-unknown",
            "task": "guest_question",
            "split": "dev",
            "lang": "es",
            "ok": True,
            "error": None,
            "confidence": None,
            "latency_ms": 8,
            "inference_source": "ON_DEVICE",
            "output": None,
            "raw": json.dumps({"answer": phrase + ".", "confidence": 0.4}),
        },
    ]
    summary = score_predictions(golds, predictions, backend="nano", smoke=True)
    guest = summary["guest_question"]
    assert set(guest["by_split"]) == {"dev"}
    assert guest["n"] == 2
    assert guest["in_scope_correctness"] == 1.0
    assert guest["refusal_recall"] == 1.0
    assert guest["hallucination_rate"] == 0.0
    assert guest["by_split"]["dev"]["n_refusal"] == 1
    page = Path("evals/nano_runner/index.html").read_text(encoding="utf-8")
    prompt = Path("src/features/qa/qaRequest.js").read_text(encoding="utf-8")
    assert "src/features/qa/qaRequest.js" in page
    assert "buildQaSystemPrompt" in page
    assert "buildQaUserTurn" in page
    assert "lang:" in prompt
    assert phrase in prompt
    assert "I don't have that information, ask the couple" in prompt
    assert 'row.task === "guest_question"' in page
    assert "unexpected_cloud_fallback" in page
    assert "ONLY_ON_DEVICE" in page
    assert "ONLY_IN_CLOUD" in page
    assert "appCheckDebugToken || true" not in page
    assert '{"answer": string, "confidence": number 0..1}' in page
