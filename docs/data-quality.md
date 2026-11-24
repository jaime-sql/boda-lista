# Data quality notes

## Known label quirks

- Test set `data/guest_questions.jsonl` (42 rows) has 4 English out-of-scope rows (`qa-0039`, `qa-0040`, `qa-0041`, `qa-0042`) whose gold `answer` is the Spanish refusal "No tengo esa información, pregúntale a los novios". The team decided (Nov 24, 2026) not to relabel them: the test set stays frozen. The fact-based scorer accepts either `UNKNOWN_ANSWER` or `UNKNOWN_ANSWER_EN` as a refusal, and it checks the answer's language against the question's language, not against the gold row.
- Dev generated rows (`guest_question_dev_generated.jsonl`) use the refusal that matches the row's `lang`. The English one is `I don't have that information, ask the couple` (no trailing period), matching `UNKNOWN_ANSWER_EN` in `src/features/qa/qaRequest.js` from PR #9 (`48e64ef`, line 2).
