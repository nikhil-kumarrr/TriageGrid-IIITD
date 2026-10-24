# Source-grounded clinical guidance update

25 October 2026

## Implemented
- Added a bounded curated reference service for animal bites/scratches, minor wounds and antibiotic requests for a suspected infection, with English/Hindi/Hinglish copies.
- Dog-bite guidance gives immediate first-aid information and prompt in-person assessment; it does not select a self-injection, a drug dose, or issue a prescription. A doctor request immediately after the bite note retains the urgent-assessment route instead of routine teleconsultation.
- Existing critical red-flag detection remains ahead of these notes. Severe bleeding triggers the emergency route.
- Guidance source URLs and reference-review date are persisted with the assistant message. Source links render in the chat and survive history reload.
- Subsequent wound/infection discussion can continue with the configured LLM rather than replaying the initial note on every turn. Provider prompt requires prioritising the current question, uncertainty and appropriate assessment.
- General arithmetic and general question support remain.

## Sources
- WHO rabies: https://www.who.int/news-room/fact-sheets/detail/rabies
- NHS animal and human bites: https://www.nhs.uk/conditions/animal-and-human-bites/
- NHS cuts and grazes: https://www.nhs.uk/conditions/cuts-and-grazes/
- CDC antibiotic use: https://www.cdc.gov/antibiotic-use/about/

## Verification and boundaries
95 backend tests passed with isolated local test memory. Frontend production build passed. Actual localhost synthetic dog-bite, antibiotic-request and arithmetic cases returned the intended guidance/source/action fields; synthetic sessions were deleted. See clinical_guidance_live_check.json.

No public dataset was downloaded, no new prescription labels were fabricated, and no LLM weights were trained. These are curated reference pathways and prompt/context changes. The service is not a medical device, prescribing clinician, validated diagnostic system or general live internet search. Lexical detection and LLM conversation remain limited; wider paraphrase and clinical review are needed. Real hospital/doctor fulfilment remains a separate integration. No Git push performed.
