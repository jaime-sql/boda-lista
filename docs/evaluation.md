# Evaluation

## Guest-question scoring v2 (fact-based), locked 2026-11-24

Token-F1 penalised short correct answers against verbose bilingual gold. On cloud dev with gemini-3.5-flash-lite and the old prompt, the legacy token-F1 scorer gave 27/120 hallucinations (22.5%) and 53/80 in-scope correct. A manual review found 0 wrong facts. The rule was fixed on dev before any re-scoring. The test split stays untouched until the final pass, and test rows are not relabeled.

`evals/guest_questions.py` applies the rule below. Token-F1 helpers and metrics remain as `legacy_*` and are reported with the fact label.

Normalization lowercases, strips accents, collapses whitespace, and strips leading and trailing punctuation.

A refusal is a normalized answer equal to `No tengo esa información, pregúntale a los novios` or to `I don't have that information, ask the couple`. The English phrase is `UNKNOWN_ANSWER_EN` in `src/features/qa/qaRequest.js` and has no trailing period. Python keeps both strings itself. Either phrase counts, including when an English out-of-scope gold row carries the English phrase and a Spanish row carries the Spanish phrase. A refusal in the other language for the row's `lang` is still a refusal, and it is also a language mismatch. The language check compares the answer with the row's question `lang`, not with the gold text.

Time and number canonicalisation maps `1:15 a.m.`, `01:15`, and `1:15` to `01:15`. A p.m. time adds 12 hours. Plain integers are kept.

Gold facts come from the optional `gold_facts` list when the row has one. Times in that list are `HH:MM`, place names are copied from the info sheet, and polarity is the literal item `yes` or `no`. A `yes` or `no` item is polarity, not a substring. It matches when the answer's leading polarity agrees: Sí, Si, or Yes for `yes`; No, or a clear negation such as "no se puede", "no estacionar", or "do not", for `no`. A contradiction is `wrong_fact`. When `gold_facts` is absent, the facts are the canonical time and number tokens in `answer`, plus a leading Sí / Yes / No polarity recorded as `yes` or `no`.

Out-of-scope rows are correct only when the answer is a refusal. Any other answer is a hallucination.

In-scope rows:

- A refusal is `abstain`, and it is not a hallucination.
- Otherwise the label is `wrong_fact` (a hallucination) when the answer contains a canonical time or number that is not in the gold facts or the gold answer, or when the polarity contradicts the gold polarity.
- Otherwise the label is `correct` when every gold fact is present: a normalized substring for a text fact, a canonical match for a time or a number, and polarity agreement when the gold fact is `yes` or `no`.
- Otherwise the label is `incomplete`, which is not a hallucination.

Language mismatch is reported separately and does not change the fact label. The row `lang` is `en` or `es`. Detection is a stopword ratio after removing tokens that appear in proper nouns from `data/wedding_info.json` (venue and place names such as Salón El Encanto, Terraza de los Izotes, Patio de ceibas, and Jardín Principal).

Metrics: `n`, `fact_correct_rate` on in-scope rows, `wrong_fact_rate` / `hallucination_rate` on all rows, `incomplete_rate`, `abstain_rate`, refusal precision / recall / F1 on out-of-scope rows, `lang_mismatch_count` and `lang_mismatch_rate` on in-scope non-refusals, and the legacy token-F1 metrics.

## Sheet-grounded scoring and cloud dev runs (2026-11-24)

The strict fact scorer remains the default in `evals/guest_questions.py`. It flags `wrong_fact` whenever an in-scope answer includes a canonical time or number absent from `gold_facts` and the gold answer. On the pre-PR #12 cloud dev run (`gemini-3.5-flash-lite`, `thinking_budget=0`, `max_output_tokens=256`, `n=120`), strict scoring gave 59/80 = 73.75% fact correct and 5/120 = 4.17% hallucination (`dev-qa-0053`–`0056` and `0069`). Review against `data/info_sheet.md` and `data/wedding_info.json` showed those five predictions only added true sheet details omitted from `gold_facts` (shuttle times `19:00`, `22:00`, `01:15`, and the `25`-minute drive).

To separate true ungrounded hallucinations from extra sheet facts, `evals/guest_questions.py` adds a `sheet_grounded` mode (`mode="sheet_grounded"` / `fact_label_sheet`) derived directly from the info sheet across both languages using the same time/number canonicalization. Extra values present on the sheet are not treated as hallucinations (`correct` if all `gold_facts` are present, else `incomplete`); values absent from the sheet remain `wrong_fact`.

After PR #12 made the venue rain/drive note (`notes_es`) and parking details (`details_en`) bilingual, a single post-PR #12 cloud dev pass was executed on the same 120 dev rows (`data/guest_question_dev_generated.jsonl` unchanged, test split untouched):

| Run | Scorer | Fact correct (n=80) | Hallucination (n=120) | Incomplete | Abstain | OOS refused (n=40) | Refusal P / R / F1 | Lang mismatch | p50 / p95 ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pre-PR #12 (`4f8ea86`) | strict | 59/80 (73.75%) | 5/120 (4.17%) | 14 | 2 | 40/40 (0 hall.) | 95.24% / 100% / 97.56% | 4 (5.13%) | 773.5 / 963.4 |
| Pre-PR #12 (`4f8ea86`) | sheet_grounded | 59/80 (73.75%) | 0/120 (0.00%, <=2.5% UB) | 19 | 2 | 40/40 (0 hall.) | 95.24% / 100% / 97.56% | 4 (5.13%) | 773.5 / 963.4 |
| Post-PR #12 (`8357d00`) | strict | 66/80 (82.50%) | 4/120 (3.33%) | 10 | 0 | 40/40 (0 hall.) | 100% / 100% / 100% | 0 (0.00%) | 800.8 / 1102.8 |
| Post-PR #12 (`8357d00`) | sheet_grounded | 66/80 (82.50%) | 1/120 (0.83%) | 13 | 0 | 40/40 (0 hall.) | 100% / 100% / 100% | 0 (0.00%) | 800.8 / 1102.8 |

By language on post-PR #12 (`sheet_grounded`): `es` (`n=90`, 60 in-scope) scored 51/60 = 85.00% fact correct with 0/90 hallucinations (95% rule-of-three upper bound 3.33%), 9 incomplete, 0 abstain, 0 lang mismatch; `en` (`n=30`, 20 in-scope) scored 15/20 = 75.00% fact correct with 1/30 = 3.33% `wrong_fact`, 4 incomplete, 0 abstain, 0 lang mismatch. The single post-PR #12 `sheet_grounded` `wrong_fact` (`dev-qa-0020`) is a polarity heuristic collision where the appended dress-code sentence `"Please do not wear white, ivory or cream."` triggered `"no"` against `gold_facts=["yes", "guayabera"]`, even though `"Guayaberas are welcome"` appeared in the answer.

Spend (`gemini-3.5-flash-lite` at $0.30/1M input, $2.50/1M output):
- Pre-PR #12 dev pass: 247,609 input + 4,953 output tokens = $0.086665 ($0.762665 cumulative of $5.00 cap).
- Post-PR #12 dev pass: 274,969 input + 4,844 output tokens = $0.094601 ($0.857266 cumulative of $5.00 cap).

Caveat: cloud dev results and threshold checks (`evals/results/final-dev/cloud/summary.json`, `evals/results/final-dev-pre12/cloud/summary.json`) do not set on-device Nano routing cut-offs; app config cut-offs stay `null` until the on-device Nano dev run completes.
