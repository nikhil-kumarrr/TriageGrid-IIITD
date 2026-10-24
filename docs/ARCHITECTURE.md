# Architecture

React UI -> FastAPI contract -> conversation state -> negation-aware safety rules -> classifier/clarification -> eligible caregiver ranking. A shared prediction service must serve both API and CSV outputs.

Use official release enums: paramedic_home_visit, home_nursing, lab_test_home, teleconsultation, emergency_112. Urgency: same_day, scheduled, emergency. Clarification returns null care_type/urgency. Emergency returns no matches.

SQLite booking writes must be transactional and reject overlaps; reservations need server validation and request ownership before use beyond a local prototype. No invented prices or ETAs. Golden Bay uses explicit consent and a simulated receiver. TinyFish accepts only approved hospital URLs and no patient payload. Production operations and admin portal are out of scope for this first phase.

The exact conversation_history adapter and scorer columns require organizer confirmation. Preserve source requests and support explicit answers; do not concatenate history blindly.
