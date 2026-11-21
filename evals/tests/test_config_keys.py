import json
from pathlib import Path

from evals.threshold import FEATURES, app_config

SCHEMA = Path(__file__).resolve().parents[1] / "schema_builtin.json"


def _task_consts(node) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        task = node.get("task")
        if isinstance(task, dict) and isinstance(task.get("const"), str):
            found.append(task["const"])
        for value in node.values():
            found.extend(_task_consts(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_task_consts(item))
    return found


def test_config_keys_equal_schema_task_consts():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    tasks = set(_task_consts(schema))
    config = app_config({"rsvp": {}, "song": {}})
    assert set(config) == tasks
    assert set(config) == set(FEATURES)
    assert FEATURES == ("guest_question", "rsvp", "song")
    assert "budget" not in config
    assert "seating" not in config
    assert "qa" not in config
    assert "songs" not in config
