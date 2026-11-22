import json

import pytest

from evals.guest_questions import UNKNOWN_ANSWER, exact_match, is_unknown_answer
from evals.parsing import parse_json_object
from evals.score import (
    FUZZY_THRESHOLD,
    canonical_energy,
    fuzzy_equal,
    macro_f1,
    percentile,
    score_predictions,
    set_f1,
)


def _rsvp(attending="yes", party=2, meals=None, kids=None, ride=False, ambiguous=False, lang="es", split="test"):
    return {
        "id": "r",
        "split": split,
        "task": "rsvp",
        "text": "hola",
        "lang": lang,
        "attending": attending,
        "party_size": party,
        "meal_restrictions": meals or [],
        "kids_count": kids,
        "needs_ride": ride,
        "ambiguous": ambiguous,
    }


def _pred(output, raw=None, latency=10):
    body = output if raw is None else raw
    return {
        "id": output.get("id", "r") if isinstance(output, dict) else "r",
        "raw": raw if raw is not None else json.dumps(output),
        "latency_ms": latency,
    }


def test_macro_f1_hand_example():
    pairs = [("yes", "yes"), ("yes", "no"), ("no", "no"), ("maybe", "maybe")]
    assert macro_f1(pairs) == pytest.approx(7 / 9)


def test_set_f1_and_empty_sets():
    assert set_f1({"a", "b"}, {"b", "c"}) == pytest.approx(0.5)
    assert set_f1(set(), set()) == 1.0


def test_percentile_interpolates():
    assert percentile([1, 2, 3, 4], 50) == pytest.approx(2.5)
    assert percentile([1, 2, 3, 4], 95) == pytest.approx(3.85)


def test_rsvp_field_metrics_and_invalid_json():
    golds = [
        {**_rsvp("yes", 2, ["vegetarian"], 1, False), "id": "a", "lang": "es"},
        {**_rsvp("yes", 2, [], None, False), "id": "b", "lang": "es"},
        {**_rsvp("no", None, [], None, False), "id": "c", "lang": "en"},
        {**_rsvp("maybe", None, [], None, False), "id": "d", "lang": "en"},
        {**_rsvp(None, None, [], None, False, ambiguous=True), "id": "e", "lang": "es"},
    ]
    predictions = [
        {"id": "a", "raw": json.dumps({**_rsvp("yes", 2, ["vegetariano"], 1, False), "confidence": 0.9}), "latency_ms": 5},
        {"id": "b", "raw": json.dumps({**_rsvp("no", 2, [], None, False), "confidence": 0.4}), "latency_ms": 15},
        {"id": "c", "raw": json.dumps({**_rsvp("no", None, [], None, False), "confidence": 0.8}), "latency_ms": 25},
        {"id": "d", "raw": "this is not json", "latency_ms": 35},
        {
            "id": "e",
            "raw": json.dumps({**_rsvp("yes", 4, [], 0, True, ambiguous=False), "confidence": 0.99}),
            "latency_ms": 45,
        },
    ]
    # Drop gold-only keys from the raw objects by rebuilding clean outputs.
    predictions[0]["raw"] = json.dumps(
        {
            "attending": "yes",
            "party_size": 2,
            "meal_restrictions": ["vegetariano"],
            "kids_count": 1,
            "needs_ride": False,
            "ambiguous": False,
            "confidence": 0.9,
        }
    )
    predictions[1]["raw"] = json.dumps(
        {
            "attending": "no",
            "party_size": 2,
            "meal_restrictions": [],
            "kids_count": None,
            "needs_ride": False,
            "ambiguous": False,
            "confidence": 0.4,
        }
    )
    predictions[2]["raw"] = json.dumps(
        {
            "attending": "no",
            "party_size": None,
            "meal_restrictions": [],
            "kids_count": None,
            "needs_ride": False,
            "ambiguous": False,
            "confidence": 0.8,
        }
    )
    predictions[4]["raw"] = json.dumps(
        {
            "attending": "yes",
            "party_size": 4,
            "meal_restrictions": [],
            "kids_count": 0,
            "needs_ride": True,
            "ambiguous": False,
            "confidence": 0.99,
        }
    )
    summary = score_predictions(golds, predictions, backend="rules", smoke=False)
    rsvp = summary["rsvp"]
    assert rsvp["n"] == 5
    assert rsvp["invalid_json_rate"] == pytest.approx(0.2)
    # attending gold yes/yes/no/maybe; preds yes/no/no/invalid. "e" is null gold and excluded.
    assert rsvp["attending_accuracy"] == pytest.approx(0.5)
    assert rsvp["party_size_exact"] == pytest.approx(0.6)
    assert rsvp["meal_restrictions_exact"] == pytest.approx(0.8)
    assert rsvp["kids_count_exact"] == pytest.approx(0.6)
    assert rsvp["needs_ride_exact"] == pytest.approx(0.6)
    assert rsvp["ambiguous_force_rate"] == pytest.approx(1.0)
    assert rsvp["all_fields_correct"] == pytest.approx(0.4)
    assert summary["by_lang"]["es"]["rsvp"]["n"] == 3
    assert summary["by_lang"]["en"]["rsvp"]["n"] == 2
    assert summary["cost_usd_per_1000"] == 0.0
    assert summary["latency_ms"]["p50"] is not None


def test_song_fuzzy_match_guess_rate_and_energy():
    assert fuzzy_equal("Vivir mi vida", "vivir mi vida")
    assert not fuzzy_equal("Despacito", "Vivir mi vida")
    assert canonical_energy("romántica") == "slow"
    assert FUZZY_THRESHOLD == 90
    golds = [
        {
            "id": "s1",
            "split": "test",
            "task": "song",
            "text": "x",
            "lang": "es",
            "title": "Vivir mi vida",
            "artist": "Marc Anthony",
            "energy": None,
            "ambiguous": False,
        },
        {
            "id": "s2",
            "split": "test",
            "task": "song",
            "text": "y",
            "lang": "es",
            "title": None,
            "artist": "Marc Anthony",
            "energy": "dance",
            "ambiguous": True,
        },
    ]
    predictions = [
        {
            "id": "s1",
            "latency_ms": 4,
            "raw": json.dumps(
                {
                    "title": "Vivir Mi Vida",
                    "artist": "marc anthony",
                    "energy": None,
                    "ambiguous": False,
                    "confidence": 0.9,
                }
            ),
        },
        {
            "id": "s2",
            "latency_ms": 8,
            "raw": json.dumps(
                {
                    "title": "Valio la Pena",
                    "artist": "Marc Anthony",
                    "energy": "upbeat",
                    "ambiguous": False,
                    "confidence": 0.4,
                }
            ),
        },
    ]
    summary = score_predictions(golds, predictions, backend="nano", smoke=False)
    song = summary["song"]
    assert song["title_artist_accuracy"] == pytest.approx(1.0)
    assert song["title_artist_n"] == 1
    assert song["energy_accuracy"] == pytest.approx(1.0)
    assert song["guess_rate"] == pytest.approx(1.0)
    assert song["ambiguous_recall"] == pytest.approx(0.0)
    assert song["all_fields_correct"] == pytest.approx(0.5)
    assert summary["cost_usd_per_1000"] == 0.0


def test_parser_accepts_fenced_json_and_rejects_prose():
    parsed = parse_json_object('note\n```json\n{"attending": "yes"}\n```\nthanks')
    assert parsed["attending"] == "yes"
    with pytest.raises(Exception):
        parse_json_object("no braces here")
    with pytest.raises(Exception):
        parse_json_object("[1, 2, 3]")


def test_guest_question_hook_is_exact_and_out_of_scope():
    assert UNKNOWN_ANSWER == "No tengo esa información, pregúntale a los novios"
    assert is_unknown_answer("  " + UNKNOWN_ANSWER + " ")
    assert exact_match(UNKNOWN_ANSWER, UNKNOWN_ANSWER)
    assert not exact_match("No sé", UNKNOWN_ANSWER)
    golds = [
        {
            "id": "q",
            "split": "test",
            "task": "guest_question",
            "text": "¿A qué hora?",
            "lang": "es",
            "answer": UNKNOWN_ANSWER,
            "out_of_scope": True,
        }
    ]
    summary = score_predictions(golds, [], backend="rules")
    assert summary["n"] == 0
    assert summary["guest_question"]["n"] == 1
    assert summary["guest_question"]["by_split"]["test"]["n"] == 1
    assert summary["guest_question"]["refusal_recall"] == 0.0
