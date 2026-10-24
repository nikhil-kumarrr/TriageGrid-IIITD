# Conversational assistant changes

User wording now takes priority over UI language. Hindi script, Hinglish vocabulary and explicit language requests are detected; short ambiguous replies retain conversation language.

The assistant prompt requests concise acknowledgements, one relevant follow-up, matching-language answer chips, review of previous facts, and no invented diagnoses or document text. Questions are saved separately and included in subsequent model context. The UI now renders follow-up questions for live and restored messages, and labels the sender as You/Aap rather than assuming a family patient. Partial fact updates preserve known scalar facts and warning-sign denials while accepting explicit corrections.

## Verification
- 58 backend tests passed with SQLite isolated from live AWS memory.
- Frontend TypeScript/production build passed.
- Actual Gemini + AWS two-turn synthetic check passed: Hinglish response, relevant next question, retained four-day duration and cough/breathing-denial context; four messages persisted. Script verification memory was cleared afterward.
- Browser chat showed a Hinglish question and matching chips for Hinglish symptom input.

Memory provides conversational context. Model weights are not trained from live chats. Automated checks and these examples do not establish clinical accuracy or guarantee language/question quality for every case. Supported conversation languages remain English, Hindi and Hinglish.
