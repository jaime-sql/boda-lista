# Boda Lista synthetic data pack

Fake wedding data for the Boda Lista app and evals. **Nothing in this pack describes a real wedding or real people.** All names, venues, contacts, quotes and messages are invented. Phone numbers use a 555-style prefix and emails use `example.com`.

`data/` is committed at the repo root of [jaime-sql/boda-lista](https://github.com/jaime-sql/boda-lista). `tools/data/generate.py`, `tools/data/rsvp_bank.py` and `tools/data/validate.py` generate and check it. This document lives at `docs/data.md`.

## Rebuild

Stdlib only. Fixed seed `20261122`. Python >= 3.10 (`requirements-data.txt`).

```bash
python tools/data/generate.py
python tools/data/validate.py
```

Do not call Modal from this script. The Modal token is expired; `--generate-modal` is a placeholder and exits without writing files.

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

Placeholder files, **not written until Modal generation is wired**:

| File | Role |
|---|---|
| `rsvp_dev_generated.jsonl` | Future ~2,000-row minus stress slice, `split=dev` only. |
| `rsvp_stress.jsonl` | Future stress slice, `split=stress` only. |

Those generated files must never use `split=test` and must not reuse test ids or texts. `tools/data/validate.py` will enforce that if the files appear.

## Row contract

Every eval row has `id`, `split` (`dev` \| `test` \| `stress`), `task`, `text`, `lang` (`es` \| `en`).

**RSVP** (`task=rsvp`): `attending` (`yes` \| `no` \| `maybe`), `party_size` (positive int, or `null` if not stated), `meal_restrictions` (list of `vegetarian`, `vegan`, `gluten_free`, `kids_menu`, or `allergy:<tag>`). Extra fields: `kids_count`, `needs_ride`, `ambiguous`, `household_id`.

**Song** (`task=song`): `title` (string, or `null` when vague), `artist`, `energy` (`slow` \| `medium` \| `dance`, or `null`), `ambiguous`. Extra: `household_id`.

**Guest question** (`task=guest_question`): `answer`, `out_of_scope`. If `out_of_scope` is true, `answer` must be exactly `No tengo esa información, pregúntale a los novios`.

## Split policy (locked)

- The 300 hand-checked RSVP replies are the **test set only**. Do not tune on them.
- A later Modal-generated set (~2,000) feeds **dev** and a separate **stress** set, never test.
- Hand-checked songs and guest questions are also `split=test`.

## Gold notes

- RSVP labels describe **that message**, not the household's final state.
- `party_size` is null when the text does not state a headcount (`sí vamos` with no number).
- `meal_restrictions` is empty when none are mentioned. An explicit "we eat everything" is also an empty list.
- Vague song requests are flagged `ambiguous=true` with `title=null`. If the guest named an artist ("la de Marc Anthony que siempre ponen"), `artist` is filled and `title` stays null.
- Clear song requests use real, well-known titles and artists.
