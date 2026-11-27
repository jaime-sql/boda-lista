# AGENTS.md — Boda Lista (`#BuildHybridAI 2026`)

Instructions for AI coding agents working in `jaime-sql/boda-lista`.

## 1. Project Summary

- **App:** Boda Lista — a Spanish-first wedding helper web app (with English support) built for Google's `#BuildHybridAI 2026` hackathon on Devpost.
- **License:** Apache-2.0 (`LICENSE`). Credit-only design inspirations are documented in `README.md` and `design/sources.md` — never copy third-party code, photos, or unlicensed illustrations.
- **Live URL:** `https://boda-lista.web.app` (deployed from `main` via GitHub Actions).
- **Schedule (America/El_Salvador, UTC-6):** Code freeze Sun Nov 29, 2026 noon SV; target submission Mon Nov 30 noon SV; hard Devpost deadline Mon Nov 30, 4:00 PM SV.
- **External state & task handoff:** Live progress, open blockers, Analytics panel spec (v1.2), and UX notes live in Notion (`Boda Lista — START HERE (handoff)` and `Boda Lista — #BuildHybridAI 2026`). Update the START HERE handoff after making meaningful progress.

## 2. Git, PR & Cost Guardrails

- **Never commit or push directly to `main`.** Always create a dedicated feature/fix branch off `origin/main` and open a pull request.
- **Commit authorship:** `jaime-sql` is the **only** commit, PR, and PR-comment author. Never add `Co-authored-by` trailers or agent attribution.
- **Approval required:** Do not merge PRs, spend Vertex AI money, trigger paid jobs, or register/send keys/tokens without Jaime's explicit OK.
- **No secrets anywhere:** Never commit `.env`, Firebase credentials, service-account JSONs, or App Check debug tokens to git, Notion, or chat.

## 3. Architecture & Locked Contracts

- **Stack:** Vite + React + TypeScript, Firebase AI Logic (`PREFER_ON_DEVICE` / hybrid fallback), App Check (`ReCaptchaEnterpriseProvider`), Cloud Firestore (`northamerica-south1`), Firebase Auth (Google), and Firebase Hosting.
- **Model routing (`src/ai/hybrid.ts`, `src/ai/fallback.ts`):**
  - Every AI call in the app goes through Firebase AI Logic (`ask()`), never bypassing it or calling third-party hosted LLM APIs directly.
  - On-device model: Gemini Nano via Chrome Prompt API (`window.LanguageModel`). Never add a force-on-device override.
  - Cloud fallback model: `gemini-3.5-flash-lite` (or `VITE_GEMINI_CLOUD_MODEL`).
  - Always show the truthful route badge (`RouteBadge`: **En tu teléfono** / **En la nube**, or **De la ficha de la boda** / **From the wedding info** for `route: "sheet"`).
- **Canonical feature keys (no alias maps anywhere):**
  - Always use the exact `data/schema.json` task keys: `guest_question`, `rsvp`, `song` (`src/ai/types.ts`, `src/config/config.json`, `firestore.rules`).
  - Do not add `qa`, `songs`, `budget`, or `seating` keys until a feature is built with its schema and rules.
- **Null-threshold rule (`src/config/config.json`, `src/config/confidence.ts`):**
  - `high` and `cloud_cutoff` stay `null` until calibrated against real on-device Gemini Nano dev runs. Never invent or hard-code cut-offs.
  - Online with `null` cut-offs -> cloud route with `fallback_reason: "no_threshold"`.
  - Offline with `null` cut-offs -> device route with `fallback_reason: "offline_no_threshold"` and UI label `"Respuesta poco segura"` (`UNSURE_LABEL`).
  - In analytics metrics/rollups, exclude `offline_no_threshold` rows from both numerator and denominator of device share and cloud calls saved, and report them as their own count/segment (`"Sin conexión, sin umbral"`).
- **Guest Q&A (`src/features/qa/`):**
  - Quick chips (`Horario`, `Lugar`, `Vestimenta`, `Parqueo`, `Regalos`, `Contactos`) answer deterministically from the wedding info sheet (`route: "sheet"`, `model: null`, `confidence: null`, `input_chars: 0`) without calling a model.
  - Typed questions detect language via `detectQuestionLanguage()` and build prompts with `buildQaUserTurn()` / `qaRequest.js`.
  - Exact out-of-scope refusal phrases (no trailing period):
    - Spanish (`UNKNOWN_ANSWER`): `No tengo esa información, pregúntale a los novios`
    - English (`UNKNOWN_ANSWER_EN`): `I don't have that information, ask the couple`
- **Privacy & Firestore (`firestore.rules`, `src/firebase/logs.ts`):**
  - `prompt_logs` stores only telemetry (`ts`, `feature`, `route`, `fallback_reason`, `latency_ms`, `input_chars`, `output_chars`, `model`, `confidence`, `session_id`, optional `lang`, optional `edited_by_guest`) — never question text, model answers, raw RSVP messages, or guest names.
  - `rsvps` stores extracted fields (`household_id`, `attending`, `party_size`, `meal_restrictions`, `kids_count`, `needs_ride`, `ambiguous`, `edited`, `ts`) — never the raw message or guest names.
  - `songs` stores song requests (`household_id`, `slot` 1–3, `title`, `artist`, `energy`, `ambiguous`, `raw_text`, `ts`) — append-only `create` and authenticated organizer `read`.
  - All committed data in `data/` is synthetic (`data/wedding_info.json`: Lucía Mendoza & Andrés Solís, Hacienda El Sauce, Santa Tecla, `2026-12-12`). Never put real guest PII in the repo or public demo unless consented.
- **Debug gate (`?debug=1`):**
  - Preview Hosting builds set `VITE_ENABLE_DEBUG=true`; production Hosting builds omit it. Keep `?debug=1` hidden in production builds.

## 4. UI & Design Tokens ("Izote y Barro")

- **Tokens only:** Style components exclusively with CSS custom properties from `src/styles/tokens.css` (`--color-*`, `--font-*`, `--text-*`, `--space-*`, `--radius-*`, `--shadow-*`, `--tap-*`). Never hard-code raw hex colors in component CSS (`src/styles/tokens.test.ts` enforces this).
- **Accessibility & layout:**
  - Spanish first (`lang="es"`) with a visible ES/EN toggle.
  - Minimum `18px` body text (`--text-base: 1.125rem`), minimum `48px` tap targets (`--tap-min: 48px`), WCAG AA contrast, visible `:focus-visible` ring, icons/text alongside color state, and zero horizontal overflow at `390px`.
  - Respect `prefers-reduced-motion` and the in-app reduced-motion switch (`[data-motion="reduced"]`).

## 5. Data & Evaluation Rules

- **Schema & test/dev split (`data/schema.json`, `docs/data.md`, `evals/README.md`):**
  - `data/rsvp_replies.jsonl` (300), `data/song_requests.jsonl` (60), and `data/guest_questions.jsonl` (42) are **`split=test` only**. Never tune prompts or thresholds on test data.
  - Generated dev/stress files (`guest_question_dev_generated.jsonl` 120, `rsvp_dev_generated.jsonl` 1,500, `rsvp_stress.jsonl` 500, `song_dev_generated.jsonl` 60) must pass `python tools/data/validate.py` (`rapidfuzz` ratio >= 90 leak check = 0 leaks).
- **Prompts:** Shared extraction instructions and JSON schemas live in `evals/prompts/extract.json`.
- **Vertex & metrics discipline:**
  - Always estimate Vertex AI cost before running cloud evals; keep to one run per dev split and stay well under the `$5.00` cap (`docs/evaluation.md` tracks exact runs and spend).
  - Never invent, extrapolate, or hard-code metrics in the app, Notion, charts, or Devpost copy.

## 6. Repository Map & Commands

| Path | Purpose |
| --- | --- |
| `src/ai/` | Hybrid `ask()`, route/fallback logic, sheet logging, device probe |
| `src/config/` | Confidence threshold loader & `config.json` |
| `src/data/` | `wedding_info` loader, `localStorage` offline cache, sample sheet |
| `src/features/` | `qa/`, `rsvp/`, `song/` (feature-specific prompts, parsers, extraction, persistence), `analytics/` (rollup math + `/admin` panel `Cómo responde la IA`) |
| `src/pages/` | Guest Q&A (`/`), RSVP (`/rsvp`), Organizer diagnostics (`/admin`) |
| `src/styles/` | Design tokens (`tokens.css` / `tokens.json`) and stylesheets |
| `firestore.rules` | Strict field-allowlisted Firestore rules + CI deploy workflow |
| `data/` & `tools/data/` | Synthetic JSONL datasets, `schema.json`, generators & leak validator |
| `evals/` | Python eval harness, `prompts/extract.json`, `nano_runner/`, results |
| `e2e/` | Playwright tests (writing mobile/desktop screenshots to `docs/screenshots/`) |
| `.github/workflows/` | Live Hosting (`main`), PR Preview, Firestore rules, data validation |

Common verification commands:

```bash
npm test                     # Vitest unit tests (mocked Firebase / AI SDKs)
npm run build                # tsc --noEmit && vite build
npm run test:e2e             # Playwright tests against VITE_E2E preview build
npm run lhci                 # Lighthouse CI accessibility >= 0.95
python tools/data/validate.py
python -m pytest evals/tests
```

## 7. Last Worked State & Open Blockers (Updated 2026-11-26 SV)

> Check git log and Notion `Boda Lista — START HERE (handoff)` for updates newer than `b2e93e2`.

- **Latest shipped `main` (`b2e93e2`):**
  - **PR #16 (`a7180a4`):** Added `AGENTS.md` repository guide.
  - **PR #14 (`132a111`):** Fixed Google Calendar event time window (`start`/`end` range + `ctz` timezone) in `src/features/qa/sheetView.ts`.
  - **PR #15 (`b2e93e2`):** Shipped **Feature 2b (Songs & DJ Playlist)** — up to 3 song inputs on `/rsvp` (for `yes`/`maybe` guests), `feature: "song"` hybrid inference with cloud retry, `RouteBadge` song summary on confirmation, `songs` rules in `firestore.rules`, and `Lista para el DJ` on `/admin` (deduplication, `slow` -> `medium` -> `dance` ordering, `Revisar` section for ambiguous songs, CSV export, and print CSS).
- **Deploy & test status at `b2e93e2`:**
  - `npm test` passed (`23` files, `90` tests) and `npm run build` passed on `main`. (`npm run test:e2e` passed `12` Playwright tests on PR #15 prior to merge.)
  - **Live Firebase Hosting (`https://boda-lista.web.app`):** `Deploy to Firebase Hosting` run `45771011758` succeeded and includes `VITE_APPCHECK_SITE_KEY`, PR #14, PR #15, and PR #16.
- **Firestore rules CI (`Deploy Firestore rules` run `45771011677` failed with `HTTP Error: 403, Permission denied to get service [firestore.googleapis.com]`):**
  - Cause: `firebase-tools deploy` checks Service Usage first and needs `serviceusage.services.get`, which the deploy service account (`roles/firebase.rulesAdmin` only) lacks.
  - Fix: `.github/workflows/firestore-rules.yml` now runs `tools/ci/deploy-firestore-rules.sh`, which publishes `firestore.rules` through the Firebase Rules REST API (create ruleset, then update the `cloud.firestore` release). That needs only `roles/firebase.rulesAdmin`; no new IAM role is required.
  - The first run with the new script reached the Rules API and failed with `The Ruleset provided does not compile` (`Recursive call is not allowed` in `mealsOk`). Firestore rules cannot recurse, so `mealsOk` now checks the 8 allowed list slots with `mealTagOk`. Validate rule changes with the emulator before merging: `npx firebase-tools emulators:exec --only firestore --project demo-boda-lista <script>`.
  - After the compile fix merges to `main`, the workflow runs on its own. Confirm it is green and that `/songs` reads/writes work live.
- **Next open priorities:**
  1. Confirm `Deploy Firestore rules` is green after the REST-based deploy lands, for live `songs` reads/writes.
  2. Analytics panel (`src/features/analytics/`) is built per Notion spec v1.2, with one deviation: there is no Modal job. `buildRollup()` computes the spec's rollup JSON in the browser from `prompt_logs` for the signed-in organizer, and the panel falls back to a static `/analytics/rollup.json`. **At code freeze (Sun Nov 29 noon SV):** open `/admin` signed in, click `Descargar rollup.json`, commit it as `public/analytics/rollup.json`, and cite its `generated_at` in the video and Devpost. Do not commit a placeholder file. Rows with `source` other than `live` are dropped; rows with no `source` count as live because the log does not write `source` yet (adding it needs a `firestore.rules` change).
  3. Complete Gemini Nano on-device dev eval (`evals/nano_runner/index.html`) if Chrome Prompt API + Optimization Guide flags work on Jaime's desktop Chrome; otherwise keep `src/config/config.json` cut-offs at `null` per Jaime's decision.
  4. Fill remaining Devpost text and 3-minute video script placeholders from verified metrics before the Sun Nov 29 noon SV code freeze.
