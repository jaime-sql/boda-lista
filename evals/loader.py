"""Load JSONL rows, map field aliases, and validate them.

The row's `split` field is the source of truth. A file name such as
`rsvp_replies.jsonl` only produces a warning when a row disagrees with it.
When `data/schema.json` exists it supplies one JSON Schema per row type.
Otherwise the built-in schema in this package is used.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import jsonschema

BUILTIN_SCHEMA_PATH = Path(__file__).resolve().parent / "schema_builtin.json"
FIELD_MAP_PATH = Path(__file__).resolve().parent / "field_map.json"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = REPO_ROOT / "data" / "schema.json"

TASK_KEYS = ("rsvp", "song", "guest_question", "wedding_info")


class RowValidationError(ValueError):
    """A row does not match the active schema."""


def repo_root() -> Path:
    return REPO_ROOT


def load_field_map(path: Path | None = None) -> dict[str, Any]:
    source = path or FIELD_MAP_PATH
    return json.loads(source.read_text(encoding="utf-8"))


def _defs_from(document: dict[str, Any]) -> dict[str, Any]:
    """Collect $defs plus a top-level schema keyed by row type."""
    found: dict[str, Any] = {}
    for pocket in ("$defs", "definitions"):
        nested = document.get(pocket)
        if isinstance(nested, dict):
            found.update(nested)
    for key in TASK_KEYS:
        if isinstance(document.get(key), dict):
            found[key] = document[key]
    return found


def schema_root(schema_path: Path | None = None) -> tuple[dict[str, Any], dict[str, str]]:
    """Return a draft-2020 document and the source ('file' or 'builtin') of each task.

    `data/schema.json` uses `$defs` (rsvp, song, guest_question, wedding_info)
    plus helper defs referenced with `$ref`. A missing file falls back to the
    built-in copy of that shape. A present file that omits a task keeps the
    built-in def for that task only.
    """
    builtin_doc = json.loads(BUILTIN_SCHEMA_PATH.read_text(encoding="utf-8"))
    builtin_defs = _defs_from(builtin_doc)
    path = DEFAULT_SCHEMA_PATH if schema_path is None else schema_path
    if not path.exists():
        if schema_path is not None:
            warnings.warn(
                f"schema file {path} is missing; using the built-in schema",
                UserWarning,
                stacklevel=2,
            )
        root = {"$schema": builtin_doc.get("$schema"), "$defs": builtin_defs}
        return root, {task: "builtin" for task in TASK_KEYS}
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise RowValidationError(f"{path} must be a JSON object of schemas")
    file_defs = _defs_from(document)
    merged = dict(builtin_defs)
    pocket = document.get("$defs") if isinstance(document.get("$defs"), dict) else {}
    merged.update(pocket)
    sources: dict[str, str] = {}
    for task in TASK_KEYS:
        if task in file_defs:
            merged[task] = file_defs[task]
            sources[task] = "file"
        else:
            warnings.warn(
                f"{path} has no {task} schema; using the built-in schema for {task}",
                UserWarning,
                stacklevel=2,
            )
            sources[task] = "builtin"
    root = {
        "$schema": document.get("$schema", builtin_doc.get("$schema")),
        "$defs": merged,
    }
    return root, sources


def schema_bundle(schema_path: Path | None = None) -> dict[str, tuple[dict[str, Any], str]]:
    """Return task -> (schema, source) where source is 'file' or 'builtin'."""
    root, sources = schema_root(schema_path)
    return {task: (root["$defs"][task], sources[task]) for task in TASK_KEYS}


def apply_aliases(row: dict[str, Any], aliases: dict[str, str]) -> dict[str, Any]:
    mapped = dict(row)
    for source, target in aliases.items():
        if source not in mapped:
            continue
        if target not in mapped:
            mapped[target] = mapped.pop(source)
        else:
            mapped.pop(source)
    return mapped


def _coerce_int(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return value


def _coerce_bool(value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes"}:
            return True
        if lowered in {"false", "no"}:
            return False
    return value


def coerce_row(row: dict[str, Any]) -> dict[str, Any]:
    coerced = dict(row)
    for key in ("party_size", "kids_count"):
        if key in coerced:
            coerced[key] = _coerce_int(coerced[key])
    for key in ("needs_ride", "ambiguous"):
        if key in coerced:
            coerced[key] = _coerce_bool(coerced[key])
    attending = coerced.get("attending")
    if isinstance(attending, str):
        coerced["attending"] = attending.strip().lower()
    return coerced


def _validate(row: dict[str, Any], root: dict[str, Any], task: str, origin: str) -> None:
    """Validate against `#/$defs/<task>` so `$ref` and `if`/`then` resolve."""
    if task not in root.get("$defs", {}):
        raise RowValidationError(f"{origin} id={row.get('id')!r} has unknown task {task!r}")
    schema = {
        "$schema": root.get("$schema", "https://json-schema.org/draft/2020-12/schema"),
        "$defs": root["$defs"],
        "$ref": f"#/$defs/{task}",
    }
    validator_cls = jsonschema.validators.validator_for(schema)
    errors = sorted(validator_cls(schema).iter_errors(row), key=lambda err: list(err.absolute_path))
    if not errors:
        return
    detail = "; ".join(error.message for error in errors[:3])
    raise RowValidationError(f"{origin} id={row.get('id')!r} failed schema validation: {detail}")


def iter_raw_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix == ".json":
        payload = json.loads(text)
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict):
            records = [payload]
        else:
            raise RowValidationError(f"{path} JSON must be an object or a list")
        if not all(isinstance(record, dict) for record in records):
            raise RowValidationError(f"{path} JSON records must be objects")
        return records

    records = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            record = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise RowValidationError(f"{path}:{line_no} is not JSON: {exc}") from exc
        if not isinstance(record, dict):
            raise RowValidationError(f"{path}:{line_no} must be a JSON object")
        records.append(record)
    return records


def load_jsonl(
    path: Path | str,
    *,
    schema_path: Path | None = None,
    field_map: dict[str, Any] | None = None,
    dev_only: bool = False,
) -> list[dict[str, Any]]:
    """Load one labeled file.

    dev_only is for threshold selection. A known test or stress filename
    raises TestLabelLeakError before the file is opened.
    """
    # Imported here so the loader can be used without the threshold module,
    # while selection still shares one exception type.
    from evals.threshold import TestLabelLeakError

    path = Path(path)
    mapping = field_map if field_map is not None else load_field_map()
    blocked = set(mapping.get("test_label_filenames", []))
    if dev_only and path.name in blocked:
        raise TestLabelLeakError(f"refusing to read {path.name} during threshold selection")

    file_meta = mapping.get("files", {}).get(path.name, {})
    aliases = mapping.get("aliases", {})
    root, _sources = schema_root(schema_path)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in iter_raw_records(path):
        row = coerce_row(apply_aliases(record, aliases))
        # wedding_info.json is one document, not an RSVP/song row. Validate it
        # before adding task or id so additionalProperties: false still passes.
        if file_meta.get("expected_task") == "wedding_info" and "task" not in row:
            _validate(row, root, "wedding_info", str(path))
            row["id"] = path.stem
            row["task"] = "wedding_info"
            row["_source_file"] = path.name
            return [row]
        if dev_only and row.get("split") != "dev":
            raise TestLabelLeakError(
                "refusing to read "
                f"split={row.get('split')!r} labels during threshold selection "
                f"(id={row.get('id')!r})"
            )
        expected_split = file_meta.get("expected_split")
        if expected_split and row.get("split") and row.get("split") != expected_split:
            warnings.warn(
                f"{path.name} row {row.get('id')!r}: split {row.get('split')!r} "
                f"disagrees with the file name (expected {expected_split}). "
                "Using the row split.",
                UserWarning,
                stacklevel=2,
            )
        expected_task = file_meta.get("expected_task")
        if expected_task and row.get("task") and row.get("task") != expected_task:
            warnings.warn(
                f"{path.name} row {row.get('id')!r}: task {row.get('task')!r} "
                f"disagrees with the file name (expected {expected_task}). "
                "Using the row task.",
                UserWarning,
                stacklevel=2,
            )
        task = row.get("task")
        if task not in root.get("$defs", {}):
            raise RowValidationError(f"{path} id={row.get('id')!r} has unknown task {task!r}")
        _validate(row, root, str(task), str(path))
        row_id = row.get("id")
        if not isinstance(row_id, str):
            raise RowValidationError(f"{path} row is missing string id")
        if row_id in seen:
            raise RowValidationError(f"{path} duplicate id {row_id!r}")
        seen.add(row_id)
        row["_source_file"] = path.name
        rows.append(row)
    return rows


def load_paths(
    paths: list[Path | str],
    *,
    schema_path: Path | None = None,
    dev_only: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        for row in load_jsonl(path, schema_path=schema_path, dev_only=dev_only):
            if row["id"] in seen:
                raise RowValidationError(f"duplicate id {row['id']!r} across input files")
            seen.add(row["id"])
            rows.append(row)
    return rows
