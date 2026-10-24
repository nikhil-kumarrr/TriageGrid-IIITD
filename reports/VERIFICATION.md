# Verification

- All five source files checksummed without modification.
- 44 backend tests passed: contracts, safety examples, CSV/JSONL parity, supplied multi-turn conversations, request ownership, booking and cancellation, concurrent slot conflict, same-day date enforcement, handover consent/ownership and mocked lookup outcomes.
- Frontend TypeScript and production build passed.
- API-service/CSV prediction parity passed for eight supplied cases.
- Browser verified: supplied consultation case -> trained prediction -> roster match -> valid slot -> persisted prototype booking.
- Real TinyFish extraction returned AIIMS public-site contact/address/service information; report saved without credentials. Later run timed out and correctly became unavailable. No current bed/dispatch claim.
- Browser microphone implementation uses real recognition with permission explanation and text fallback. Physical device recognition/permission was not exercised automatically.
- Docker is unavailable here, so Docker execution is unverified.
- Git repository initialized and successfully published to https://github.com/nikhil-kumarrr/TriageGrid (branch main). Root pytest.ini configured for direct pytest execution.

Classifier metrics are grouped model-selection results, not clinical validation. Known source flag errors are documented in DATA_USAGE.md.

Browser verification also completed consent-gated Golden Bay transfer, manual receiver acknowledgement and labelled cached TinyFish public information. Same-day scheduling enforcement and past-slot exclusion are included in tests.
