# Gemini 108-case dataset integration review

25 October 2026

## Decision
Use patient-only inputs for offline exploratory evaluation. Do not train the clinical classifier or Gemini on the unreviewed medicine answers. Do not add the supplied few-shot retriever to the live app. This does not establish a competition-rules exception: organiser training and scoring remain separate.

## Audit
- CSV: 108 unique first-turn scenarios in 12 categories.
- JSONL: 108 well-formed records, matching the CSV patient turns exactly. These are alternate formats of the same examples, not independent data.
- No organiser care-type/urgency labels or clinician-reviewed prescription gold standard.
- Bot file has a SyntaxError at line 8. It was parsed only, never executed. Its retrieval code would return top-five records even with zero matching score; including complete teacher answers/system instructions would risk irrelevant or unreviewed medical guidance.
- Teacher answers include child fever sponging and fresh-burn cream recommendations that conflict with the cited NHS first-aid guidance. Other dose/remedy and fixed fluid recommendations require individual clinical review.

## Implemented
- Patient-only JSONL and source/checksum manifest in data/evaluation/synthetic108.
- Reproducible importer with CSV/JSONL matching assertions.
- Local schema/routing evaluator; no external patient uploads, LLM calls or AWS memory changes required.
- Provider prompt gained independently sourced corrections on fresh thermal burns and child fever. Raw teacher answers never become runtime context.

## Results and limits
216 local turn checks returned valid triage output schema. This is schema coverage, not 100% accuracy. There are no gold labels, so no clinical accuracy, F1 or improvement can be computed. The evaluator invokes the local triage engine, not the full conversational LLM; it uses patient turns and does not invent an intervening doctor's answer. Existing backend regression suite: 100 tests passed.

No model-weight retraining or Gemini fine-tuning performed. Existing trained organiser models unchanged. For training approval, obtain clinical review, provenance/license confirmation, care taxonomy labels, and independently held-out cases; keep generated duplicates and scenarios grouped across splits.

## Sources
https://www.nhs.uk/conditions/burns-and-scalds/
https://www.nhs.uk/symptoms/fever-in-children/
