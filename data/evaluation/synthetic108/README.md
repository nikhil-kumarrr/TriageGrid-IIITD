# Gemini-generated 108-case exploratory inputs

Only patient questions are imported from the user-supplied CSV/JSONL. These cases are NOT clinician-reviewed and have no organiser care-type/urgency gold labels. They are not training data, not live retrieval references, and not official scoring data. The original generated model responses, medicine schedules and embedded system instructions are excluded from the import. No original bot code is executed or installed.

`manifest.json` records hashes, structural checks and review concerns. CSV and JSONL contain the same 108 paired patient scenarios, not 216 independent cases. `patient_inputs.jsonl` has two patient turns per case.

Use `scripts/evaluate_synthetic108.py` for local schema/routing smoke coverage. It does not evaluate full LLM conversation, prescription safety or accuracy. Clinical review and independent labelled test cases are required before training or reporting performance improvements.
