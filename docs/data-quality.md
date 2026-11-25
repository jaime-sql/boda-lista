# Data quality notes

## Known label quirks

- Test set `data/guest_questions.jsonl` (42 rows) has 4 English out-of-scope rows (`qa-0039`, `qa-0040`, `qa-0041`, `qa-0042`) whose gold `answer` is the Spanish refusal "No tengo esa información, pregúntale a los novios". The team decided (Nov 24, 2026) not to relabel them: the test set stays frozen. The fact-based scorer accepts either `UNKNOWN_ANSWER` or `UNKNOWN_ANSWER_EN` as a refusal, and it checks the answer's language against the question's language, not against the gold row.
- Dev generated rows (`guest_question_dev_generated.jsonl`) use the refusal that matches the row's `lang`. The English one is `I don't have that information, ask the couple` (no trailing period), matching `UNKNOWN_ANSWER_EN` in `src/features/qa/qaRequest.js` from PR #9 (`48e64ef`, line 2).

## Bilingual info-sheet gap

Nov 24, 2026 (SV). Two lines on `data/info_sheet.md` were monolingual. The venue note (a 25-minute drive from central Santa Tecla; a covered backup hall if it rains) existed only in English (`venue.notes`). The parking details (valet from 15:00; free shuttle from the north lot of Centro Comercial El Encuentro, estacionamiento norte, every 20 minutes from 15:00 to 19:00, return between 22:00 and 01:15; no parking on the highway shoulder) existed only in Spanish (`parking.details`). Guests asking in the other language were refused or answered in the wrong language.

Dev rows affected: `dev-qa-0056` and `dev-qa-0069` (language mismatch); `dev-qa-0070` and `dev-qa-0071` (false refusals). Gold for `dev-qa-0053` through `dev-qa-0056` and `dev-qa-0069` was verified correct against the sheet. Their `wrong_fact` labels come from the strict scorer counting true extra sheet times, handled separately by ML.

Fix: `venue.notes` stays the English pair and `venue.notes_es` adds the Spanish pair. `parking.details` stays the Spanish text and `parking.details_en` adds the English details. Times stay `HH:MM`. Place names stay Hacienda El Sauce, Santa Tecla, Centro Comercial El Encuentro, and estacionamiento norte. `data/info_sheet.md` shows both languages for those two items. The test split stayed frozen, including `data/guest_questions.jsonl`. Dev and stress JSONL files were not regenerated.
