"""Single-pass Vertex AI Gemini evaluator for Boda Lista dev guest_question rows.

Hard guardrails:
- Model: gemini-3.5-flash-lite only
- Location: global only
- thinking_budget=0, max_output_tokens=256, temperature=0
- Dev split guest_question rows only (never test or stress rows)
- One pass, no retry loops (attempts=1)
- Pre-run cost estimate and hard USD spend cap
- Prompts generated directly via Node from src/features/qa/qaRequest.js
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evals.loader import REPO_ROOT, load_paths
from evals.parsing import parse_json_object

ALLOWED_MODEL = "gemini-3.5-flash-lite"
ALLOWED_LOCATION = "global"
INPUT_USD_PER_M = 0.30
OUTPUT_USD_PER_M = 2.50


def generate_prompts_via_node(
    rows: list[dict[str, Any]],
    sheet_path: Path,
    qa_request_js: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Invoke node to run src/features/qa/qaRequest.js for 100% prompt parity."""
    if not qa_request_js.exists():
        raise SystemExit(f"Missing {qa_request_js}; merge PR #9 first.")
    if not sheet_path.exists():
        raise SystemExit(f"Missing wedding info sheet: {sheet_path}")

    script = """
import fs from 'fs';
import { pathToFileURL } from 'url';

const [qaPath, sheetPath] = process.argv.slice(1);
const mod = await import(pathToFileURL(qaPath).href);
const sheet = JSON.parse(fs.readFileSync(sheetPath, 'utf8'));
const rows = JSON.parse(fs.readFileSync(0, 'utf8'));

const out = rows.map((row) => {
  const question = String(row.text ?? '');
  const detectedLang = mod.detectQuestionLanguage(question, 'es');
  const lang = row.lang === 'en' || row.lang === 'es' ? row.lang : detectedLang;
  const system = mod.buildQaSystemPrompt(sheet);
  const user = mod.buildQaUserTurn({ question, lang, sheet });
  return {
    id: row.id,
    lang,
    detected_lang: detectedLang,
    system,
    user,
    combined: `${system}\\n\\n${user}`,
  };
});

process.stdout.write(JSON.stringify({
  schema: mod.GUEST_QUESTION_RESPONSE_SCHEMA,
  prompts: out,
}));
"""
    payload = json.dumps([{"id": r["id"], "text": r.get("text", ""), "lang": r.get("lang")} for r in rows])
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script, str(qa_request_js.resolve()), str(sheet_path.resolve())],
        input=payload,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f"Node prompt parity script failed (exit {proc.returncode}):\n{proc.stderr}")
    parsed = json.loads(proc.stdout)
    return parsed["prompts"], parsed["schema"]


def verify_parity_sample(
    prompts: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    sheet_path: Path,
    qa_request_js: Path,
    n_check: int = 3,
) -> None:
    """Independently re-evaluate first n_check rows in Node and assert exact equality."""
    script = """
import fs from 'fs';
import { pathToFileURL } from 'url';

const [qaPath, sheetPath] = process.argv.slice(1);
const mod = await import(pathToFileURL(qaPath).href);
const sheet = JSON.parse(fs.readFileSync(sheetPath, 'utf8'));
const rows = JSON.parse(fs.readFileSync(0, 'utf8'));
const checks = rows.map((row) => {
  const lang = row.lang === 'en' || row.lang === 'es' ? row.lang : mod.detectQuestionLanguage(row.text || '', 'es');
  const sys = mod.buildQaSystemPrompt(sheet);
  const usr = mod.buildQaUserTurn({ question: row.text || '', lang, sheet });
  return { id: row.id, combined: `${sys}\\n\\n${usr}` };
});
process.stdout.write(JSON.stringify(checks));
"""
    sample = rows[:n_check]
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script, str(qa_request_js.resolve()), str(sheet_path.resolve())],
        input=json.dumps([{"id": r["id"], "text": r.get("text", ""), "lang": r.get("lang")} for r in sample]),
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        check=True,
    )
    checks = json.loads(proc.stdout)
    for idx, check in enumerate(checks):
        assert prompts[idx]["id"] == check["id"]
        assert prompts[idx]["combined"] == check["combined"], f"Prompt mismatch on {check['id']}"
    print(f"Verified exact JS prompt parity on {len(checks)} rows: {[c['id'] for c in checks]}")


def estimate_cost_usd(prompts: list[dict[str, Any]], max_output_tokens: int) -> dict[str, Any]:
    total_chars = sum(len(p["combined"]) for p in prompts)
    # Conservative 3.5 chars/token estimate for bilingual text + JSON
    est_input_tokens = int(total_chars / 3.5) + len(prompts) * 16
    worst_output_tokens = len(prompts) * max_output_tokens
    est_input_usd = (est_input_tokens / 1_000_000) * INPUT_USD_PER_M
    worst_output_usd = (worst_output_tokens / 1_000_000) * OUTPUT_USD_PER_M
    worst_total_usd = est_input_usd + worst_output_usd
    return {
        "total_chars": total_chars,
        "est_input_tokens": est_input_tokens,
        "worst_output_tokens": worst_output_tokens,
        "est_input_usd": est_input_usd,
        "worst_output_usd": worst_output_usd,
        "worst_total_usd": worst_total_usd,
    }


def compute_usd(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000) * INPUT_USD_PER_M + (output_tokens / 1_000_000) * OUTPUT_USD_PER_M


def _git_sha() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Vertex Gemini 3.5 Flash Lite dev guest_question pass.")
    parser.add_argument("--data", required=True, nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--model", default=ALLOWED_MODEL)
    parser.add_argument("--location", default=ALLOWED_LOCATION)
    parser.add_argument("--max-output-tokens", type=int, default=256)
    parser.add_argument("--thinking-budget", type=int, default=0)
    parser.add_argument("--spent-so-far-usd", type=float, default=0.0)
    parser.add_argument("--spend-cap-usd", type=float, default=5.0)
    parser.add_argument("--sheet", type=Path, default=REPO_ROOT / "data" / "wedding_info.json")
    parser.add_argument("--qa-js", type=Path, default=REPO_ROOT / "src" / "features" / "qa" / "qaRequest.js")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Guardrails
    if args.model != ALLOWED_MODEL:
        raise SystemExit(f"Forbidden model {args.model!r}; only {ALLOWED_MODEL!r} is allowed.")
    if args.location != ALLOWED_LOCATION:
        raise SystemExit(f"Forbidden location {args.location!r}; only {ALLOWED_LOCATION!r} is allowed.")
    if args.thinking_budget != 0:
        raise SystemExit(f"Forbidden thinking_budget={args.thinking_budget}; must be 0.")
    if args.max_output_tokens != 256:
        raise SystemExit(f"Forbidden max_output_tokens={args.max_output_tokens}; must be 256.")

    for p in args.data:
        name = p.name.lower()
        if "test" in name or "stress" in name or "rsvp_replies" in name or "song_requests" in name or name == "guest_questions.jsonl":
            raise SystemExit(f"Refusing non-dev dataset path: {p}")

    rows = load_paths(args.data, dev_only=True)
    if not rows:
        raise SystemExit("No rows loaded.")
    non_dev = [r["id"] for r in rows if r.get("split") != "dev"]
    if non_dev:
        raise SystemExit(f"Refusing non-dev rows: {non_dev[:5]}")
    non_gq = [r["id"] for r in rows if r.get("task") != "guest_question"]
    if non_gq:
        raise SystemExit(f"Refusing non-guest_question rows: {non_gq[:5]}")

    prompts, response_schema = generate_prompts_via_node(rows, args.sheet, args.qa_js)
    verify_parity_sample(prompts, rows, args.sheet, args.qa_js, n_check=3)

    lang_diffs = sum(1 for p in prompts if p["lang"] != p["detected_lang"])
    print(f"Loaded {len(rows)} dev guest_question rows (detectQuestionLanguage diffs vs row.lang: {lang_diffs})")

    est = estimate_cost_usd(prompts, args.max_output_tokens)
    projected_cumulative = args.spent_so_far_usd + est["worst_total_usd"]
    print(
        f"Cost estimate: chars={est['total_chars']} est_in_tok={est['est_input_tokens']} "
        f"worst_out_tok={est['worst_output_tokens']} worst_run_usd=${est['worst_total_usd']:.4f} "
        f"projected_cumulative_usd=${projected_cumulative:.4f} (cap=${args.spend_cap_usd:.2f})"
    )
    if est["worst_total_usd"] > 5.0 or projected_cumulative > args.spend_cap_usd:
        raise SystemExit("Estimated cost exceeds $5 / spend cap. Aborting without API calls.")

    if args.dry_run:
        print("Dry run complete. No API calls made.")
        return

    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        raise SystemExit("GOOGLE_APPLICATION_CREDENTIALS must be set.")

    import google.auth
    from google import genai
    from google.genai import types

    _creds, project_id = google.auth.default()
    if not project_id:
        raise SystemExit("Could not determine GCP project from GOOGLE_APPLICATION_CREDENTIALS.")

    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=args.location,
        http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=1)),
    )
    config = types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=args.max_output_tokens,
        response_mime_type="application/json",
        response_schema=response_schema,
        thinking_config=types.ThinkingConfig(thinking_budget=args.thinking_budget),
    )

    args.out.mkdir(parents=True, exist_ok=True)
    pred_path = args.out / "predictions.jsonl"
    meta_path = args.out / "run_meta.json"

    total_in_tokens = 0
    total_out_tokens = 0
    predictions: list[dict[str, Any]] = []

    for idx, (row, prompt_obj) in enumerate(zip(rows, prompts), start=1):
        actual_run_usd = compute_usd(total_in_tokens, total_out_tokens)
        if args.spent_so_far_usd + actual_run_usd >= args.spend_cap_usd:
            print(f"Spend cap reached at row {idx - 1}/{len(rows)}; stopping.", file=sys.stderr)
            break

        started = time.perf_counter()
        raw = ""
        error: str | None = None
        output: dict[str, Any] | None = None
        confidence: float | None = None
        in_tok = 0
        out_tok = 0
        try:
            resp = client.models.generate_content(
                model=args.model,
                contents=prompt_obj["combined"],
                config=config,
            )
            latency_ms = (time.perf_counter() - started) * 1000.0
            raw = resp.text or ""
            usage = getattr(resp, "usage_metadata", None)
            if usage is not None:
                in_tok = int(getattr(usage, "prompt_token_count", 0) or 0)
                out_tok = int(getattr(usage, "candidates_token_count", 0) or 0)
            total_in_tokens += in_tok
            total_out_tokens += out_tok
            try:
                parsed = parse_json_object(raw)
                if isinstance(parsed.get("answer"), str):
                    ans = parsed["answer"].strip()
                    conf_val = parsed.get("confidence")
                    if isinstance(conf_val, (int, float)) and not isinstance(conf_val, bool) and 0.0 <= float(conf_val) <= 1.0:
                        confidence = float(conf_val)
                    output = {"answer": ans, "confidence": confidence}
                else:
                    error = "missing_answer"
            except Exception as exc:
                error = f"invalid_json: {exc}"
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000.0
            error = f"api_error: {type(exc).__name__}: {exc}"

        pred_row = {
            "id": row["id"],
            "task": "guest_question",
            "split": row.get("split"),
            "lang": prompt_obj["lang"],
            "ok": error is None,
            "error": error,
            "confidence": confidence,
            "latency_ms": round(latency_ms, 2),
            "output": output,
            "raw": raw,
            "usage": {"input_tokens": in_tok, "output_tokens": out_tok},
        }
        predictions.append(pred_row)
        if idx % 20 == 0 or idx == len(rows):
            run_usd = compute_usd(total_in_tokens, total_out_tokens)
            print(f"[{idx}/{len(rows)}] in_tok={total_in_tokens} out_tok={total_out_tokens} run_usd=${run_usd:.4f}")

    with pred_path.open("w", encoding="utf-8") as handle:
        for pred in predictions:
            handle.write(json.dumps(pred, ensure_ascii=False) + "\n")

    actual_run_usd = compute_usd(total_in_tokens, total_out_tokens)
    new_cumulative_usd = args.spent_so_far_usd + actual_run_usd
    meta = {
        "backend": "cloud",
        "runner": "vertex_gemini",
        "model": args.model,
        "location": args.location,
        "thinking_budget": args.thinking_budget,
        "max_output_tokens": args.max_output_tokens,
        "temperature": 0.0,
        "smoke": False,
        "n": len(predictions),
        "input_tokens": total_in_tokens,
        "output_tokens": total_out_tokens,
        "pricing_usd_per_m": {"input": INPUT_USD_PER_M, "output": OUTPUT_USD_PER_M},
        "run_usd": round(actual_run_usd, 6),
        "spent_so_far_usd": args.spent_so_far_usd,
        "new_cumulative_usd": round(new_cumulative_usd, 6),
        "spend_cap_usd": args.spend_cap_usd,
        "data": [str(p) for p in args.data],
        "git_sha": _git_sha(),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {pred_path} (n={len(predictions)}) and {meta_path}")
    print(
        f"Actual tokens: input={total_in_tokens}, output={total_out_tokens}, "
        f"run_usd=${actual_run_usd:.6f}, new_cumulative_usd=${new_cumulative_usd:.6f}"
    )


if __name__ == "__main__":
    main()
