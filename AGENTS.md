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
| `src/features/` | `qa/`, `rsvp/` (and feature-specific modules/prompts/parsers) |
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
