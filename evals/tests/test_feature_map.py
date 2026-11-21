import json
from pathlib import Path

from evals.feature_map import TASK_TO_FEATURE
from evals.threshold import FEATURES

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


def test_schema_task_consts_map_to_features():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    tasks = _task_consts(schema)
    assert tasks == ["rsvp", "song", "guest_question"]
    for task in tasks:
        assert TASK_TO_FEATURE[task] in FEATURES
    assert FEATURES == ("qa", "rsvp", "songs")
