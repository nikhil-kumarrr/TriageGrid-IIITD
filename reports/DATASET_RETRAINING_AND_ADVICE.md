# Supplied dataset retraining and basic advice update

Updated 25 October 2026 (India).

## Data and training
- User supplied triage CSV: 340 rows, 65 unique normalised symptom texts.
- Caregiver CSV: 60 profiles, used for rule-based matching, not prescription training.
- Supplied records equal the previously integrated organiser records. No new medical supervision was introduced.
- Retrained word/character TF-IDF + Logistic Regression pipelines, saved to models/baseline/care_type_pipeline.pkl and urgency_pipeline.pkl.
- Reproducible command: .venv/bin/python scripts/train_models.py
- Grouped five-fold CV keeps exact normalised duplicate texts together. It does not eliminate every semantic near-duplicate or constitute independent clinical validation.
- Care-type CV accuracy: 0.7147; macro F1: 0.6466.
- Urgency CV accuracy: 0.7471; macro F1: 0.6116.
- Standalone classifier emergency recall: care type 0.6964; urgency 0.5357. These figures do NOT evaluate the final safety-rule-plus-classifier system; they are insufficient for autonomous medical decisions.

## Assistant update
Added source-grounded prompt guidance for brief self-care and educational paracetamol information. It checks relevant missing safety context, avoids universal medicine recommendations and personalised dosing, and distinguishes paediatric and liver-risk cases. Existing diagnosis/prescription boundaries remain. No LLM fine-tuning or chat-based weight updates were performed. Prompt instructions do not guarantee safe outputs.

Sources: NHS adults https://www.nhs.uk/medicines/paracetamol-for-adults/ ; NHS children https://www.nhs.uk/medicines/paracetamol-for-children/ ; FDA https://www.fda.gov/drugs/safe-use-over-counter-pain-relievers-and-fever-reducers/acetaminophen .

## Memory
The app retains its configured AWS DynamoDB session memory; no patient history was used as training data. Model artifacts and prompt changes persist across restart. AWS memory itself was not revalidated in this turn.

## Verification
- 58 backend tests passed with isolated SQLite test memory and provider mocks. Initial run against configured AWS failed due to restricted network, so it is not reported as AWS verification.
- Three actual Gemini calls used synthetic adult medicine-information, child adult-tablet, and liver-risk cases. All responded in Hinglish; no personalised dose was given in these samples. See basic_advice_live_check.json.
- One liver-risk sample combined two follow-up topics despite the one-topic prompt; conversation quality remains a limitation requiring further evaluation.
- No Git commit or push performed. Restart a non-reloading backend to load the updated prompt and model artifacts.
