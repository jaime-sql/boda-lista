# Boda Lista synthetic data pack

Fake wedding data for the Boda Lista app and evals. **Nothing in this pack describes a real wedding or real people.** All names, venues, contacts, quotes and messages are invented. Phone numbers use a 555-style prefix and emails use `example.com`.

`data/` is committed at the repo root of [jaime-sql/boda-lista](https://github.com/jaime-sql/boda-lista). `tools/data/generate.py`, `tools/data/generate_dev.py`, `tools/data/rsvp_bank.py` and `tools/data/validate.py` generate and check it. This document lives at `docs/data.md`.

## Rebuild

Python >= 3.10 (`requirements-data.txt`). The hand-checked pack uses fixed seed `20261122` and the standard library:

```bash
python tools/data/generate.py
```

Dev and stress rows are a separate command, seed `20261124`. Install the leak-check pin first so validation uses rapidfuzz:

```bash
python -m pip install -r tools/data/requirements.txt
python tools/data/generate_dev.py
python tools/data/validate.py
```

Do not call Modal. The Modal token is expired; `generate.py --generate-modal` is a placeholder and exits without writing files. Dev and stress rows come from templates instead. See below.

## Files in `data/`

| File | Role |
|---|---|
| `schema.json` | JSON Schema draft 2020-12. Definitions: `rsvp`, `song`, `guest_question`, `wedding_info`. ML should build its loader from this file. |
| `rsvp_replies.jsonl` | **300 hand-checked RSVP replies, all `split=test`.** Stratified by language and ambiguity. Never use this file as dev. |
| `song_requests.jsonl` | 60 hand-checked song requests, all `split=test`. 15 are vague (`ambiguous=true`, `title=null`; `artist` may be filled if named). |
| `guest_questions.jsonl` | Hand-checked guest Q&A against the info sheet, all `split=test`. Out-of-scope gold answer is exactly `No tengo esa información, pregúntale a los novios`. |
| `wedding_info.json` | Fake info sheet for guest Q&A (`synthetic: true`): schedule, venue, dress code, parking, gifts, contacts. |
| `info_sheet.md` | Readable twin of `wedding_info.json`. |
| `guests.jsonl` | 150 synthetic guests, with `household_id` used by RSVPs and songs. |
| `households.jsonl` | Household rollup for those guests. |
| `vendor_quotes.jsonl` | Fake vendor quotes in USD. |
| `rsvp_dev_generated.jsonl` | 1,500 template RSVP replies, all `split=dev`. |
| `rsvp_stress.jsonl` | 500 template stress RSVPs, all `split=stress`. |
| `song_dev_generated.jsonl` | 60 template song requests, all `split=dev`. |
| `guest_question_dev_generated.jsonl` | 120 template guest questions, all `split=dev`. |
| `leak_report.json` | rapidfuzz leak check written by `tools/data/validate.py`. |

Generated files never use `split=test`. Ids start with `dev-` or `stress-` (`dev-rsvp-`, `stress-rsvp-`, `dev-song-`, `dev-qa-`) so they cannot match `rsvp-`, `song-`, or `qa-` test ids.

## Row contract

Every eval row has `id`, `split` (`dev` \| `test` \| `stress`), `task`, `text`, `lang` (`es` \| `en`).

**RSVP** (`task=rsvp`): `attending` (`yes` \| `no` \| `maybe`), `party_size` (positive int, or `null` if not stated), `meal_restrictions` (list of `vegetarian`, `vegan`, `gluten_free`, `kids_menu`, or `allergy:<tag>`). Extra fields: `kids_count`, `needs_ride`, `ambiguous`, `household_id`.

**Song** (`task=song`): `title` (string, or `null` when vague), `artist`, `energy` (`slow` \| `medium` \| `dance`, or `null`), `ambiguous`. Extra: `household_id`.

**Guest question** (`task=guest_question`): `answer`, `out_of_scope`. If `out_of_scope` is true, `answer` must be exactly `No tengo esa información, pregúntale a los novios`.

## Split policy (locked)

- The 300 hand-checked RSVP replies are the **test set only**. Do not tune on them.
- The template batch feeds **dev** and a separate **stress** set, never test. Modal was not used, because its token had expired.
- Hand-checked songs and guest questions are also `split=test`.

## Gold notes

- RSVP labels describe **that message**, not the household's final state.
- `party_size` is null when the text does not state a headcount (`sí vamos` with no number).
- `meal_restrictions` is empty when none are mentioned. An explicit "we eat everything" is also an empty list.
- Vague song requests are flagged `ambiguous=true` with `title=null`. If the guest named an artist ("la de Marc Anthony que siempre ponen"), `artist` is filled and `title` stays null.
- Clear song requests use real, well-known titles and artists.

## Dev and stress batch

No model was used, so there is no model license. Modal was not used because its token had expired. `tools/data/generate_dev.py` fills every row from deterministic templates. Seed `20261124` shuffles household ids and rotates the neutral filler sentences. Gold labels are the template slots (attending, headcount, meal tags, song title, or the info-sheet answer), not a model's reading of the text.

```bash
python tools/data/generate_dev.py
```

In-scope guest answers are interpolated from `data/wedding_info.json`, and the same strings are present in `data/info_sheet.md`. Gold answers are minimal, question-scoped, in the question's language. `gold_facts` stores times as zero-padded `HH:MM`, place names copied from the info sheet, and yes/no as `yes` or `no`. Spanish out-of-scope answers are exactly `No tengo esa información, pregúntale a los novios`. English out-of-scope answers are exactly `I don't have that information, ask the couple`. In-scope answers never use either phrase.

| File | Rows | Split | es | en | Other |
|---|---:|---|---:|---:|---|
| `rsvp_dev_generated.jsonl` | 1500 | dev | 1200 (80%) | 300 (20%) | yes / no / maybe, plus-ones, meal tags and allergies, typos, mixed language, ambiguous replies |
| `rsvp_stress.jsonl` | 500 | stress | 400 (80%) | 100 (20%) | very long, emoji-only, contradictory, prompt-injection, empty-ish, code-switching |
| `song_dev_generated.jsonl` | 60 | dev | 48 | 12 | 15 vague (`ambiguous=true`, `title=null`), including `algo para bailar` |
| `guest_question_dev_generated.jsonl` | 120 | dev | 90 | 30 | 80 in scope, 40 out of scope |

`tools/data/validate.py` checks each generated file against its schema definition and its split. A row is a leak if its id equals any hand-checked test id, or if its text, lowercased and whitespace-normalised, scores rapidfuzz `fuzz.ratio` >= 90 against any test text of the same task. The pin is `rapidfuzz==3.10.1` in `tools/data/requirements.txt`. If rapidfuzz is missing, the script prints a warning and uses `difflib.SequenceMatcher` instead. Leaks are errors. The generator does not keep a row that would score >= 90 on either engine.

`data/leak_report.json` from the rapidfuzz run:

| File | Rows | Text leaks | Id leaks | Max similarity |
|---|---:|---:|---:|---:|
| `rsvp_dev_generated.jsonl` | 1500 | 0 | 0 | 55.03 |
| `rsvp_stress.jsonl` | 500 | 0 | 0 | 46.53 |
| `song_dev_generated.jsonl` | 60 | 0 | 0 | 84.21 |
| `guest_question_dev_generated.jsonl` | 120 | 0 | 0 | 43.33 |

Threshold 90. Engine `rapidfuzz`. Every leak count is 0.
