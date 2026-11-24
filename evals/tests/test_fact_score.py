"""Fact-based guest-question labels. Dev examples only; the test split is not read."""

import re

from evals.guest_questions import (
    UNKNOWN_ANSWER,
    UNKNOWN_ANSWER_EN,
    canonical_quantities,
    detect_answer_language,
    fact_label,
    is_refusal,
    language_mismatch,
    legacy_is_hallucination,
    score_guest_questions,
    wedding_info_path,
)
from evals.loader import REPO_ROOT

_CLOSURE = (
    "Cierre / End of celebration es a las 01:00 en Salón El Encanto. "
    "El servicio de shuttle cierra a las 01:15."
)
_DANCE = "First dance is at 20:00 in Salón El Encanto."
_PARKING = "No estacionar en el hombro de la carretera"


def _js_export(source: str, name: str) -> str:
    match = re.search(rf"^export const {name} = (['\"])(.*)\1;$", source, re.MULTILINE)
    assert match is not None, name
    return match.group(2)


def test_refusal_constants_match_qa_request_js():
    source = (REPO_ROOT / "src/features/qa/qaRequest.js").read_text(encoding="utf-8")
    spanish = _js_export(source, "UNKNOWN_ANSWER")
    english = _js_export(source, "UNKNOWN_ANSWER_EN")
    assert spanish == UNKNOWN_ANSWER
    assert english == UNKNOWN_ANSWER_EN
    assert not english.endswith(".")
    assert is_refusal(UNKNOWN_ANSWER)
    assert is_refusal(UNKNOWN_ANSWER_EN)
    assert is_refusal(UNKNOWN_ANSWER_EN + ".")
    assert language_mismatch(UNKNOWN_ANSWER, "en")
    assert language_mismatch(UNKNOWN_ANSWER_EN, "es")
    assert not language_mismatch(UNKNOWN_ANSWER, "es")
    assert not language_mismatch(UNKNOWN_ANSWER_EN, "en")
    # A wrong-language refusal is still a refusal.
    row = {
        "id": "refuse-en",
        "split": "dev",
        "out_of_scope": False,
        "lang": "en",
        "answer": "20:00",
    }
    assert fact_label(row, UNKNOWN_ANSWER) == "abstain"
    assert is_refusal(UNKNOWN_ANSWER)
    scored = score_guest_questions([row], [{"id": "refuse-en", "output": {"answer": UNKNOWN_ANSWER}}])
    assert scored["n_refusal"] == 1
    assert scored["abstain_rate"] == 1.0
    # The published mismatch rate covers in-scope answers that are not refusals.
    assert scored["lang_mismatch_count"] == 0


def test_clock_canonical_form():
    assert canonical_quantities("1:15 a.m.")[0] == ["01:15"]
    assert canonical_quantities("01:15")[0] == ["01:15"]
    assert canonical_quantities("1:15")[0] == ["01:15"]
    assert canonical_quantities("1:15 p.m.")[0] == ["13:15"]
    assert canonical_quantities("8:00 pm")[0] == ["20:00"]
    assert canonical_quantities("cada 20 minutos")[1] == ["20"]


def test_short_time_with_gold_facts_is_correct_and_legacy_flags_it():
    gold = {
        "id": "close",
        "split": "dev",
        "task": "guest_question",
        "text": "¿a qué hora cierra la fiesta?",
        "lang": "es",
        "answer": _CLOSURE,
        "out_of_scope": False,
        "gold_facts": ["01:00"],
    }
    prediction = "01:00"
    assert fact_label(gold, prediction) == "correct"
    assert legacy_is_hallucination(gold, prediction)
    scored = score_guest_questions([gold], [{"id": "close", "output": {"answer": prediction}}])
    assert scored["fact_correct_rate"] == 1.0
    assert scored["hallucination_rate"] == 0.0
    assert scored["legacy_hallucination_rate"] == 1.0
    assert scored["legacy_token_f1"] is not None

    without = dict(gold)
    without.pop("gold_facts")
    assert fact_label(without, prediction) == "incomplete"
    incomplete = score_guest_questions([without], [{"id": "close", "output": {"answer": prediction}}])
    assert incomplete["incomplete_rate"] == 1.0
    assert incomplete["hallucination_rate"] == 0.0
    assert incomplete["legacy_hallucination_rate"] == 1.0


def test_place_and_time_facts_with_english_row_mismatch():
    gold = {
        "id": "dance",
        "split": "dev",
        "lang": "en",
        "answer": _DANCE,
        "out_of_scope": False,
        "gold_facts": ["20:00", "Salón El Encanto"],
    }
    prediction = "A las 20:00 en Salón El Encanto"
    assert fact_label(gold, prediction) == "correct"
    assert detect_answer_language(prediction) == "es"
    assert language_mismatch(prediction, gold["lang"])


def test_wrong_clock_is_wrong_fact():
    gold = {
        "id": "dance-wrong",
        "split": "dev",
        "lang": "es",
        "answer": _DANCE,
        "out_of_scope": False,
        "gold_facts": ["20:00"],
    }
    assert fact_label(gold, "A las 21:00") == "wrong_fact"


def test_out_of_scope_refusal_and_non_refusal():
    gold = {
        "id": "oos",
        "split": "dev",
        "lang": "es",
        "answer": UNKNOWN_ANSWER,
        "out_of_scope": True,
    }
    assert fact_label(gold, "Son las 16:00.") == "hallucination"
    assert fact_label(gold, UNKNOWN_ANSWER) == "correct"
    assert fact_label(gold, UNKNOWN_ANSWER_EN) == "correct"
    assert language_mismatch(UNKNOWN_ANSWER_EN, "es")
    english_row = dict(gold, lang="en", answer=UNKNOWN_ANSWER)
    assert fact_label(english_row, UNKNOWN_ANSWER_EN) == "correct"
    assert not language_mismatch(UNKNOWN_ANSWER_EN, "en")


def test_polarity_yes_no_is_not_a_substring():
    gold = {
        "id": "park",
        "split": "dev",
        "lang": "es",
        "answer": _PARKING,
        "out_of_scope": False,
        "gold_facts": ["no"],
    }
    assert fact_label(gold, _PARKING) == "correct"
    assert fact_label(gold, "No se puede estacionar en el hombro.") == "correct"
    assert fact_label(gold, "do not park on the shoulder") == "correct"
    assert fact_label(gold, "Sí") == "wrong_fact"
    assert fact_label(gold, "Si") == "wrong_fact"
    assert fact_label(gold, "Yes") == "wrong_fact"
    assert fact_label(gold, "Conocemos el horario.") == "incomplete"
    yes_gold = dict(gold, gold_facts=["yes"])
    assert fact_label(yes_gold, "Sí, se puede.") == "correct"
    assert fact_label(yes_gold, "No") == "wrong_fact"


def test_english_answer_at_a_place_name_matches_question_lang():
    prediction = "It's at 17:30 at Terraza de los Izotes"
    assert detect_answer_language(prediction) == "en"
    assert detect_answer_language("It's at Terraza de los Izotes") == "en"
    # Gold text is Spanish. The check uses the row lang, not the gold text.
    assert not language_mismatch(prediction, "en")
    assert language_mismatch(prediction, "es")
    assert wedding_info_path() == REPO_ROOT / "data" / "wedding_info.json"
    assert wedding_info_path().is_file()
