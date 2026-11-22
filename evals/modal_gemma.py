"""Gemma 3 4B instruct baseline on Modal.

Gemma is used only for offline evaluation under the Gemma Terms of Use.
It is not part of the Boda Lista app. App inference goes through Firebase
AI Logic only.

The GPU container scales to zero (min_containers=0). One remote call batches
the whole file. Per-item latency is recorded inside that call. The local
entrypoint prints estimated GPU seconds as the wall clock of the remote
call, which covers model load and generation. Modal also bills idle time up
to scaledown_window (5 seconds) after the call returns.

Hugging Face token: Modal secret named `huggingface` (key HF_TOKEN), when
present. `google/gemma-3-4b-it` is gated. For an ungated mirror you are
licensed to use, start the process with MODAL_SKIP_HF_SECRET=1 and pass
--model-id your-org/gemma-3-4b-it (or set GEMMA_MODEL_ID).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GPU = os.environ.get("GEMMA_GPU", "L4")
SKIP_HF_SECRET = os.environ.get("MODAL_SKIP_HF_SECRET", "").lower() in {"1", "true", "yes"}
DEFAULT_MODEL_ID = os.environ.get("GEMMA_MODEL_ID", "google/gemma-3-4b-it")

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "torch",
    "transformers>=4.51",
    "accelerate",
    "huggingface_hub",
    "safetensors",
)
secrets = [] if SKIP_HF_SECRET else [modal.Secret.from_name("huggingface")]
hf_cache = modal.Volume.from_name("boda-lista-evals-hf-cache", create_if_missing=True)

app = modal.App("boda-lista-evals-gemma")


@app.cls(
    image=image,
    gpu=GPU,
    secrets=secrets,
    volumes={"/cache/huggingface": hf_cache},
    timeout=60 * 60 * 2,
    startup_timeout=60 * 20,
    scaledown_window=5,
    min_containers=0,
    max_containers=1,
)
class GemmaExtractor:
    model_id: str = modal.parameter(default=DEFAULT_MODEL_ID)

    @modal.enter()
    def load(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        os.environ.setdefault("HF_HOME", "/cache/huggingface")
        token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, token=token)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            token=token,
        )
        self.model.eval()
        hf_cache.commit()

    @modal.method()
    def predict_batch(self, prompts: list[dict]) -> dict:
        import time

        import torch

        started = time.perf_counter()
        rows = []
        for item in prompts:
            item_started = time.perf_counter()
            rows.append(
                {
                    "id": item["id"],
                    "raw": self._generate(item["prompt"]),
                    "latency_ms": (time.perf_counter() - item_started) * 1000.0,
                }
            )
        return {"rows": rows, "infer_seconds": time.perf_counter() - started}

    def _generate(self, prompt: str) -> str:
        import torch

        messages = [{"role": "user", "content": prompt}]
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(self.model.device)
        with torch.inference_mode():
            output = self.model.generate(inputs, max_new_tokens=512, do_sample=False)
        generated = output[0, inputs.shape[-1] :]
        return self.tokenizer.decode(generated, skip_special_tokens=True)


@app.local_entrypoint()
def main(data: str, out: str = "evals/results/gemma", model_id: str = DEFAULT_MODEL_ID) -> None:
    import json
    import time
    from datetime import datetime, timezone

    from evals.loader import load_paths
    from evals.parsing import resolve_prediction
    from evals.prompting import build_prompt, load_prompt_spec

    paths = [Path(part) for part in data.split(",") if part.strip()]
    rows = [row for row in load_paths(paths) if row.get("task") in {"rsvp", "song"}]
    spec = load_prompt_spec()
    payloads = [
        {
            "id": row["id"],
            "prompt": build_prompt(row["task"], row["text"], row.get("lang") or "", spec),
        }
        for row in rows
    ]
    started = time.perf_counter()
    result = GemmaExtractor(model_id=model_id).predict_batch.remote(payloads)
    estimated_gpu_seconds = time.perf_counter() - started
    by_id = {row["id"]: row for row in result["rows"]}
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    pred_path = out_dir / "predictions.jsonl"
    with pred_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            remote = by_id.get(row["id"], {})
            raw = remote.get("raw") or ""
            output, error, _latency, confidence = resolve_prediction(row["task"], {"raw": raw})
            prediction = {
                "id": row["id"],
                "task": row["task"],
                "split": row.get("split"),
                "lang": row.get("lang"),
                "ok": error is None,
                "error": error,
                "confidence": confidence,
                "latency_ms": remote.get("latency_ms"),
                "output": output,
                "raw": raw,
            }
            handle.write(json.dumps(prediction, ensure_ascii=False) + "\n")
    meta = {
        "backend": "gemma",
        "smoke": any("smoke" in path.name for path in paths),
        "n": len(rows),
        "model_id": model_id,
        "gpu": GPU,
        "estimated_gpu_seconds": estimated_gpu_seconds,
        "infer_seconds": result.get("infer_seconds"),
        "scaledown_window_s": 5,
        "data": [str(path) for path in paths],
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (out_dir / "run_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"estimated_gpu_seconds={estimated_gpu_seconds:.3f}")
    print(f"inference_seconds={result.get('infer_seconds')}")
    print(f"model_id={model_id} gpu={GPU} n={len(rows)}")
    print(f"wrote {pred_path}")
