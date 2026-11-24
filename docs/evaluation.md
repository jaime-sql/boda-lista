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
