# Intent routing update

25 October 2026

- Explicit doctor requests in English, Hindi and Hinglish bypass symptom interrogation and the LLM. The user can view supplied mock doctor matches and consultation booking slots directly.
- Ambiguous human-help requests receive one support-category question with doctor, emotional support and app-help options. No live operator connection is claimed.
- Emotional distress opens a supportive conversation choice, without assigning diagnosis or routine symptom triage. Subsequent conversational reasoning uses the configured LLM. This is not a validated mental-health screening instrument.
- Explicit imminent self-harm phrases trigger an urgent-help action; existing medical red-flag checks take priority. Lexical rules are limited and do not guarantee comprehensive danger detection.
- Requested actions, intent and follow-up are saved in session message metadata; existing memory provider is retained.
- Doctor requests preserve explicit warning-sign denials without assuming unmentioned signs absent. Timing in the direct consultation result is a service-access category, not a clinical urgency assessment.
- UI action buttons recover their own request by ID, settings actions open settings, and fresh urgent actions clear stale care recommendations. Chat receives bottom spacing for navigation clearance.

## Validation

- 72 backend tests passed using isolated local test storage and mocked providers.
- Frontend TypeScript check and Vite production build passed.
- Live localhost API with configured AWS memory: human request produced one clarification; doctor chip produced no follow-up, a Recommendation action, and three supplied mock doctor matches. Synthetic test session deleted afterwards.
- Browser interaction/layout was not visually checked in this turn.
- Existing model/prompt training changes remain uncommitted; no automatic Git push performed.
