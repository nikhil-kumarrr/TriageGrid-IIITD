# Current implementation

Implemented: provided-data training, strict API, text/voice intake, request review, basic multi-turn clarification, negation-aware lexical safety, model prediction, roster matching, caregiver detail, slot selection, transactional local reservations and cancellation, Golden Bay consent/receiver, TinyFish asynchronous lookup/cache/failures, main-control translations, accessibility preferences, Help, mentor metrics, CSV predictions, notebook and local deployment configuration.

Verified: source checksums, CSV/JSONL parity, supplied multi-turn cases, API and booking tests, concurrent slot conflicts, frontend production build and browser booking journey. Live TinyFish returned public AIIMS information. Individual browser microphone consent/recognition availability depends on user platform and is not a clinical feature.

Not claimed: production security, clinical validity, real appointments/dispatch, live beds, full natural-language coverage or public hosting. Docker is configured but not run because unavailable. Final scorer shape and source annotation inconsistencies still need organizer confirmation. The admin portal remains a separate phase.

## Source preservation

All original exports and the old notebook/package remain intact. New runtime excludes Streamlit. Source datasets are unchanged and checksummed. Decorative illustrations/avatars do not claim actual caregiver identities.
