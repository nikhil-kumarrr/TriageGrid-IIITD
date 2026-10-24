# How the supplied CAI dataset is used

| Supplied file | Application use |
| --- | --- |
| triage_dataset_flat.csv | TF-IDF / Logistic Regression training, grouped baseline evaluation and source example selection. 340 rows represent 65 unique input texts. |
| triage_dataset.jsonl | Canonical nested request/response reference and CSV parity checks. Same examples; never counted as additional data. |
| caregivers.csv | Actual roster names, qualifications, roles, languages, skills, service radius, ratings, active status and availability windows. Used in matching, detail cards and slot validation. |
| multi_turn_examples.jsonl | Regression tests for clarification-to-resolution and emergency bypass. |
| SOURCE_README.md | Dataset provenance, release enums, baseline weights and permitted event use. |

The source files are unchanged and checksummed in manifest.json. No external symptom dataset is used. The illustration is decorative and does not represent a real caregiver. The custom vector brand mark is decorative and shared by the app header and favicon.

## Scheduling assumptions

The roster gives times but no calendar dates, appointment duration or reservation state. For this synthetic prototype, windows repeat over the next seven calendar days and appointments take 30 minutes. These are software planning conventions, not claims about real provider availability. The UI labels them explicitly. Slots in the past are excluded. SQLite transactions prevent overlapping reservations across sessions. Teleconsultation does not require or score distance.

## Known source limitations

The release README describes machine-generated labels, not clinical ground truth. Emergency flags are sometimes unsupported by the request text; the safety engine does not reproduce invented symptoms. Data from the same input is grouped when validating. Dataset agreement after fitting is in-sample and must never be presented as generalization accuracy.

Service labels follow the actual release. Final organizer scoring columns and any newer schema still need confirmation. Arbitrary clinical generalization is not established by this small dataset.

Same-day care is restricted to today (IST); it cannot be postponed through the slot picker or API. The seven-day planning horizon applies to scheduled care only.
