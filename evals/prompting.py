"""Build the prompt shared by Gemma, cloud Gemini, and Gemini Nano."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

PROMPTS_PATH = Path(__file__).resolve().parent / "prompts" / "extract.json"


@lru_cache(maxsize=1)
def load_prompt_spec(path: str | None = None) -> dict[str, Any]:
    source = Path(path) if path else PROMPTS_PATH
    return json.loads(source.read_text(encoding="utf-8"))


def build_prompt(task: str, text: str, lang: str, spec: dict[str, Any] | None = None) -> str:
    """Assemble system text, task instructions, JSON schema, and the message.

    The Nano runner fills the same user_template and joins the same four parts.
    """
    spec = spec or load_prompt_spec()
    task_spec = spec["tasks"][task]
    body = (
        spec["user_template"]
        .replace("{task}", task)
        .replace("{lang}", lang)
        .replace("{text}", text)
    )
    schema = json.dumps(task_spec["output_schema"], ensure_ascii=False, indent=2)
    return "\n\n".join(
        [
            spec["system"],
            task_spec["instruction"],
            "JSON schema:",
            schema,
            body,
        ]
    )
