# Boda Lista evaluation harness

Offline comparison of four RSVP and song-request readers on the same labeled rows. The wedding app calls Firebase AI Logic only. Gemma is used here for offline evaluation under the [Gemma Terms of Use](https://ai.google.dev/gemma/terms). It is not shipped in the app.

Python 3.11. From the repo root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r evals/requirements.txt
python -m pytest evals/tests
```

## Where each step runs

| Step | Where |
| --- | --- |
| `rules`, `score`, `threshold`, `report` | This machine, CPU. No GPU and no network. |
| `gemma` | Modal GPU (default L4). Scales to zero. One remote call batches the file. |
| `nano` and `cloud` | Desktop Chrome on the owner's laptop, `evals/nano_runner/index.html`. |

`data/schema.json` on main is the row contract (`$defs` for `rsvp`, `song`, `guest_question`, `wedding_info`). The loader validates with that file when it is present and falls back to `evals/schema_builtin.json` when it is missing. `evals/field_map.json` maps old names such as `meal_needs` onto `meal_restrictions`. The row's `split` field wins; a file name that disagrees only warns.

The hand-checked test pack is `data/rsvp_replies.jsonl` (300), `data/song_requests.jsonl` (60), and `data/guest_questions.jsonl` (42). Template dev and stress files are described in `docs/data.md`. The threshold command exits with an error when no dev rows exist, and it will not open `rsvp_replies.jsonl` or `song_requests.jsonl` while choosing a threshold.

Guest questions are out of scope. The unknown gold string is exactly `No tengo esa información, pregúntale a los novios` (`evals/guest_questions.py`).

## Tasks and fields

RSVP output: `attending` (`yes` \| `no` \| `maybe`), `party_size` (int ≥ 1 or null), `meal_restrictions` (tag list), `kids_count` (int or null), `needs_ride` (true, false, or null when unstated), `ambiguous`, `confidence` in [0, 1].

Song output: `title` (null when vague), `artist`, `energy` (`slow` \| `medium` \| `dance` or null), `ambiguous`, `confidence`. Vague requests stay ambiguous. The rules baseline does not guess a title. `Y - X` is artist then title. `X de Y` and `X by Y` are title then artist.

The prompt and output schema shared by Gemma, cloud, and Nano live in `evals/prompts/extract.json`.

## Commands

Smoke fixture only (`evals/data/smoke.jsonl`, labeled FAKE SMOKE DATA, not for the report):

```bash
python -m evals.run --backend rules --data evals/data/smoke.jsonl --out evals/results/smoke-rules
python -m evals.score --gold evals/data/smoke.jsonl --predictions evals/results/smoke-rules/predictions.jsonl --out evals/results/smoke-rules/summary.json
```

Test pack (after a real backend run). Do not pass these files to threshold selection.

```bash
python -m evals.run --backend rules --data data/rsvp_replies.jsonl data/song_requests.jsonl --out evals/results/rules-test
python -m evals.score --gold data/rsvp_replies.jsonl data/song_requests.jsonl --predictions evals/results/rules-test/predictions.jsonl --out evals/results/rules-test/summary.json
```

Gemma on Modal. Create the secret when the model is gated:

```bash
pip install -r evals/requirements-modal.txt
modal secret create huggingface HF_TOKEN=hf_...
modal run evals/modal_gemma.py --data data/rsvp_replies.jsonl,data/song_requests.jsonl --out evals/results/gemma-test
```

The entrypoint prints `estimated_gpu_seconds` (wall clock of the remote call, including model load). The container uses `min_containers=0` and `scaledown_window=5`. Default model id is `google/gemma-3-4b-it`; override with `--model-id`. If you are licensed to use an ungated mirror, start the process with `MODAL_SKIP_HF_SECRET=1` and pass that repo as `--model-id` (for example a mirror under an org you control). `GEMMA_GPU=A10G` selects another GPU. GPU-only list prices used for the optional cost figure are the Modal rates for L4 ($0.000222/s) and A10 ($0.000306/s) from [modal.com/pricing](https://modal.com/pricing). CPU and memory are not included.

Nano and cloud, on the owner's laptop. Copy `evals/nano_runner/firebase-config.example.json` to `evals/nano_runner/firebase-config.json` (gitignored) and fill the Firebase web config locally. Do not commit it.

```bash
python -m http.server 8765
```

Open `http://localhost:8765/evals/nano_runner/index.html` in desktop Chrome 139 or newer. Enable `chrome://flags/#prompt-api-for-gemini-nano-multimodal-input` for on-device mode. Pick the JSONL, the prompt file if fetch fails, and the Firebase config. Leave **On-device only** selected for Nano (`InferenceMode.ONLY_ON_DEVICE`). Switch to **Cloud only** for cloud Gemini (`ONLY_IN_CLOUD`). The Run button calls `initializeDeviceModel` on a click, then writes a predictions JSONL. If on-device mode reports an in-cloud source, the row is stored as `unexpected_cloud_fallback` and is not counted as Nano. `guest_question` rows use the app guest prompt (`src/features/qa/prompt.ts`) plus the wedding sheet and return `{"answer": string, "confidence": number 0..1}`.

Threshold selection uses dev rows only. If the dev files are missing, this command refuses to run:

```bash
python -m evals.threshold \
  --rsvp-dev data/rsvp_dev_generated.jsonl \
  --rsvp-test data/rsvp_replies.jsonl \
  --song-dev data/song_dev_generated.jsonl \
  --song-test data/song_requests.jsonl \
  --device-dev evals/results/nano-dev/predictions.jsonl \
  --cloud-dev evals/results/cloud-dev/predictions.jsonl \
  --device-test evals/results/nano-test/predictions.jsonl \
  --cloud-test evals/results/cloud-test/predictions.jsonl \
  --out evals/results/hybrid/summary.json
```

Omit `--song-dev` when that file does not exist. The summary then says `no song threshold: no dev split` and the song test file is not used for tuning. The chosen RSVP threshold is the lowest cutoff that maximizes the on-device share while hybrid accuracy stays within 1 percentage point of cloud-only. It is applied once to the test split.

The same command writes `evals/results/<run_id>/config.json` next to the summary, keyed `guest_question`, `rsvp`, and `song` (the schema task values). `cloud_cutoff` is the dev routing threshold: anything below it goes to the cloud. `high` is the stricter zero-slack cutoff from the same dev sweep. `min_n` is 20, the minimum number of dev items required before a cutoff is written. `guest_question` cutoffs are chosen on its dev split when that file exists: the smallest confidence whose kept answers have a hallucination rate of at most 2% and at least `min_n` rows. Until then it stays null with `"note": "no dev split"`. Any other feature without dev rows is null the same way. This file is not `tokens/config.json`. Copy the numbers across after review.

Report (skips any summary marked smoke; missing backends show `not run`):

```bash
python -m evals.report --results evals/results --out docs/evaluation.md
```

## Metrics

RSVP: attending accuracy and macro-F1 over `yes` / `no` / `maybe` labels present in gold, `party_size` exact, `meal_restrictions` set-F1 and exact match, `kids_count` exact, `needs_ride` exact, `ambiguous` exact, and the share of gold-ambiguous replies where the model set `ambiguous` to false. All-fields-correct requires every field.

Songs: title and artist accuracy on non-ambiguous rows uses rapidfuzz `token_sort_ratio` after lowercasing and stripping accents, threshold 90. Energy accuracy is exact after mapping aliases onto `slow` / `medium` / `dance`. Guess rate is the share of gold-ambiguous rows that returned a title. Ambiguous recall is the share flagged `ambiguous`. Invalid JSON is an error and counts as incorrect. Latency is the linear p50 and p95. Language breakdowns are `es` and `en`. Stress rows are reported under `by_split.stress`, separate from test.
