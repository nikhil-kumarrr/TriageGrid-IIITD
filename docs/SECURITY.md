# Security and deployment boundaries

## Local prototype controls

- API keys remain server-side in ignored `.env`; no keys in UI builds or data exports.
- Session tokens are random, stored hashed by the backend and checked for request/booking/handover ownership.
- SQL uses parameterized values. Reservations use BEGIN IMMEDIATE, overlap checks and per-session idempotency keys.
- Strict bounded API inputs, allowlisted enum values and explicit nullable clarification contract.
- Basic process-local request limits, lookup concurrency checks and payload-size limits.
- React escapes displayed input and web-source text; no remote HTML execution.
- Hospital IDs map only to approved public URLs. No arbitrary URL or patient payload accepted.
- TinyFish calls have total/read timeouts and bounded returned content. Keys/provider errors are not echoed.
- Audio is not persisted; no live GPS or real medical records are requested.
- Static frontend fonts and icons are bundled locally. Nginx adds CSP, frame and permissions headers.
- Clear-session operation deletes only that session's synthetic records and releases reservations.

## Remaining production requirements

This is a local synthetic-data prototype, not a production healthcare deployment. Before exposure beyond the local environment: proper authenticated identities and hospital receiver roles, TLS, shared infrastructure rate limiting, queue-based durable jobs, retention/expiry, audit policy, endpoint monitoring and clinical validation. Browser localStorage session tokens are vulnerable to a compromised origin; they are not a production authentication strategy. Do not log request payloads or secrets. Pickle files must come only from trusted explicit training.

API docs remain enabled for hackathon integration. Admin portal is not implemented. The receiver is a simulation scoped to the local session, never real hospital access.
