# TriageGrid

## Approach

TriageGrid implements the CareCompass journey: multilingual intake, care routing with urgency, caregiver matching and prototype booking. Emergency decisions skip matching and present a clear call-for-help path. A separate Golden Bay screen previews a consented synthetic handover and an interactive simulated hospital receiver. It does not arrange real care.

## Data and models

The supplied Sanocare synthetic care-triage dataset v1 (2026), provided for the IIIT-Delhi hackathon, contains 340 rows with 65 distinct request texts. The CSV and JSONL are alternative representations of the same examples. TF-IDF word/character features feed two Logistic Regression pipelines for care type and urgency/clarification. Repeated inputs are grouped during validation. Source examples, not invented cases, are available in the UI. The supplied 60-caregiver roster drives eligibility, skills, language, radius, ratings and scheduling windows.

Recorded grouped model-selection macro-F1 is 0.6466 for care type and 0.6116 for urgency. These are baseline classifier results, not clinical validation or an untouched hidden-test score. API and CSV predictions share one inference function.

## Safety and matching

Lexical red-flag rules handle supported negated and uncertain phrases and preserve prior reported warning signs. Clarification leaves care type and urgency null. Reasons do not add diagnoses or unreported symptoms. Emergency responses contain no caregiver matches. Matching hard-filters role and required skills, then scores language, skill, distance and rating; virtual consultations ignore distance. Missing injection route is not assumed intramuscular.

SQLite transactions reject overlapping prototype reservations and duplicate submissions. The undated synthetic roster repeats over a seven-day planning horizon with configured 30-minute slots; the UI discloses this assumption. No real appointment is booked.

## TinyFish and interface

React uses the supplied blue-theme direction, a provided logo, locally bundled fonts, medical icons and decorative care graphics. Browser voice input has transcript review and text fallback. Main controls and question templates support English, Hindi and Hinglish. Some source descriptions remain English.

TinyFish reads allowlisted official hospital sites for published contact/address/service information. It never receives patient details. Source links, checked-at times, cached status and errors are visible. Lookup runs separately from emergency action. A live AIIMS lookup succeeded; extracted content does not verify current bed availability or dispatch.

## Limitations and handling

The release is machine-generated and contains inconsistent red-flag annotations; it is not clinical ground truth. Rules and language coverage remain limited. Only supplied synthetic data is used; real patient information must not be collected or uploaded. Local session ownership, server-only secrets and transactional storage support the demonstration but do not replace production authentication, clinical review or regulatory assessment. The receiver is explicitly simulated. Docker is configured but not executed on the development machine.

References: supplied Sanocare dataset v1 and README; CareCompass problem statement; scikit-learn sparse text-classification documentation; TinyFish official cookbook; MDN SpeechRecognition documentation. Lucide icons and Fontsource fonts are bundled under their package licences.

Same-day care is restricted to today (IST); it cannot be postponed through the slot picker or API. The seven-day planning horizon applies to scheduled care only.
