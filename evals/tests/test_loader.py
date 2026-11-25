import json
import warnings
from pathlib import Path

import pytest

from evals.loader import RowValidationError, load_jsonl, schema_bundle, schema_root
from evals.prompting import build_prompt, load_prompt_spec

BUILTIN = Path("evals/schema_builtin.json")
ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, row: dict) -> None:
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")


def _rsvp(**overrides):
    row = {
        "id": "a",
        "split": "dev",
        "task": "rsvp",
        "text": "vamos",
        "lang": "es",
        "attending": "yes",
        "party_size": 1,
        "meal_restrictions": [],
        "kids_count": None,
        "needs_ride": False,
        "ambiguous": False,
    }
    row.update(overrides)
    return row


def test_split_field_wins_when_the_file_name_disagrees(tmp_path):
    path = tmp_path / "rsvp_dev_generated.jsonl"
    _write(path, _rsvp(split="test", id="row-1"))
    with pytest.warns(UserWarning, match="disagrees"):
        rows = load_jsonl(path, schema_path=BUILTIN)
    assert rows[0]["split"] == "test"


def test_meal_needs_alias_maps_before_validation(tmp_path):
    path = tmp_path / "custom.jsonl"
    row = _rsvp()
    row.pop("meal_restrictions")
    row["meal_needs"] = ["vegetarian"]
    _write(path, row)
    loaded = load_jsonl(path, schema_path=BUILTIN)
    assert loaded[0]["meal_restrictions"] == ["vegetarian"]
    assert "meal_needs" not in loaded[0]


def test_missing_schema_file_falls_back_to_builtin(tmp_path):
    path = tmp_path / "smoke.jsonl"
    _write(path, _rsvp())
    missing = tmp_path / "absent-schema.json"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rows = load_jsonl(path, schema_path=missing)
        bundle = schema_bundle(missing)
    assert rows[0]["id"] == "a"
    assert bundle["rsvp"][1] == "builtin"
    assert any("built-in" in str(item.message) for item in caught)


def test_present_schema_file_is_the_one_that_validates(tmp_path):
    schema = tmp_path / "schema.json"
    schema.write_text(
        json.dumps(
            {
                "rsvp": {
                    "type": "object",
                    "required": ["magic_marker"],
                    "properties": {"magic_marker": {"const": "yes"}},
                }
            }
        ),
        encoding="utf-8",
    )
    path = tmp_path / "rows.jsonl"
    _write(path, _rsvp())
    with pytest.raises(Exception, match="magic_marker"):
        load_jsonl(path, schema_path=schema)
    marked = _rsvp(magic_marker="yes")
    _write(path, marked)
    loaded = load_jsonl(path, schema_path=schema)
    assert loaded[0]["magic_marker"] == "yes"


def _fake_rsvp(**overrides):
    row = {
        "id": "fake-rsvp",
        "split": "test",
        "task": "rsvp",
        "text": "FAKE SCHEMA FIXTURE vamos 2",
        "lang": "es",
        "attending": "yes",
        "party_size": 2,
        "meal_restrictions": ["vegetarian"],
        "kids_count": None,
        "needs_ride": None,
        "ambiguous": False,
    }
    row.update(overrides)
    return row


def test_fake_fixture_matches_repo_schema_shape(tmp_path):
    """Validate a tiny fake row against data/schema.json from main, not a copied pack."""
    schema = ROOT / "data" / "schema.json"
    root, sources = schema_root(None)
    assert sources["rsvp"] == "file"
    assert sources["song"] == "file"
    assert set(root["$defs"]) >= {"rsvp", "song", "guest_question", "wedding_info"}
    path = tmp_path / "fake.jsonl"
    path.write_text("# FAKE SCHEMA FIXTURE\n" + json.dumps(_fake_rsvp()) + "\n", encoding="utf-8")
    loaded = load_jsonl(path, schema_path=schema)
    assert loaded[0]["needs_ride"] is None
    assert loaded[0]["meal_restrictions"] == ["vegetarian"]

    path.write_text(json.dumps(_fake_rsvp(attending=None)) + "\n", encoding="utf-8")
    with pytest.raises(RowValidationError):
        load_jsonl(path, schema_path=schema)

    vague = {
        "id": "fake-song",
        "split": "test",
        "task": "song",
        "text": "FAKE SCHEMA FIXTURE la de alguien",
        "lang": "es",
        "title": "Guessed Title",
        "artist": "Someone",
        "energy": "high",
        "ambiguous": True,
    }
    path.write_text(json.dumps(vague) + "\n", encoding="utf-8")
    with pytest.raises(RowValidationError):
        load_jsonl(path, schema_path=schema)

    vague["title"] = None
    vague["energy"] = "dance"
    path.write_text(json.dumps(vague) + "\n", encoding="utf-8")
    song = load_jsonl(path, schema_path=schema)
    assert song[0]["title"] is None
    assert song[0]["energy"] == "dance"


def test_wedding_info_sheet_is_bilingual_for_venue_and_parking():
    schema = ROOT / "data" / "schema.json"
    path = ROOT / "data" / "wedding_info.json"
    info = load_jsonl(path, schema_path=schema)[0]
    builtin = load_jsonl(path, schema_path=BUILTIN)[0]
    for row in (info, builtin):
        notes = row["venue"]["notes"]
        notes_es = row["venue"]["notes_es"]
        details = row["parking"]["details"]
        details_en = row["parking"]["details_en"]
        assert "25-minute drive from central Santa Tecla" in notes
        assert "covered backup hall" in notes
        assert "25 minutos" in notes_es and "Santa Tecla" in notes_es
        assert "salón cubierto" in notes_es and "llueve" in notes_es
        assert "estacionamiento norte" in details and "15:00" in details and "01:15" in details
        assert "Centro Comercial El Encuentro" in details_en
        assert "estacionamiento norte" in details_en
        assert "15:00" in details_en and "19:00" in details_en
        assert "22:00" in details_en and "01:15" in details_en
        assert "20 minutes" in details_en and "highway shoulder" in details_en
    sheet = (ROOT / "data" / "info_sheet.md").read_text(encoding="utf-8")
    assert info["venue"]["notes"] in sheet
    assert info["venue"]["notes_es"] in sheet
    assert info["parking"]["details"] in sheet
    assert info["parking"]["details_en"] in sheet


def test_labeled_pack_on_main_loads_as_test_only():
    schema = ROOT / "data" / "schema.json"
    rsvp = load_jsonl(ROOT / "data" / "rsvp_replies.jsonl", schema_path=schema)
    songs = load_jsonl(ROOT / "data" / "song_requests.jsonl", schema_path=schema)
    questions = load_jsonl(ROOT / "data" / "guest_questions.jsonl", schema_path=schema)
    assert len(rsvp) == 300
    assert len(songs) == 60
    assert len(questions) == 42
    assert {row["split"] for row in rsvp + songs + questions} == {"test"}
    assert all(row["title"] is None for row in songs if row["ambiguous"])


def test_smoke_fixture_is_labeled_and_loads():
    text = (ROOT / "evals" / "data" / "smoke.jsonl").read_text(encoding="utf-8")
    assert "FAKE SMOKE DATA" in text
    rows = load_jsonl(ROOT / "evals" / "data" / "smoke.jsonl", schema_path=BUILTIN)
    assert len(rows) == 15
    assert {row["task"] for row in rows} == {"rsvp", "song"}
    assert {row["split"] for row in rows} == {"dev", "test", "stress"}


def test_prompt_file_is_shared_and_uses_meal_restrictions():
    spec = load_prompt_spec()
    text = json.dumps(spec)
    assert "meal_restrictions" in text
    assert "meal_needs" not in text
    assert "kids_count" in text
    assert "needs_ride" in text
    assert "energy" in text
    prompt = build_prompt("rsvp", "vamos 3", "es", spec)
    assert "vamos 3" in prompt
    assert "JSON schema:" in prompt
    html = (ROOT / "evals" / "nano_runner" / "index.html").read_text(encoding="utf-8")
    assert "prompts/extract.json" in html
    assert "ONLY_ON_DEVICE" in html
    assert "ONLY_IN_CLOUD" in html
    assert "user_template" in html
    assert spec["system"] not in html
