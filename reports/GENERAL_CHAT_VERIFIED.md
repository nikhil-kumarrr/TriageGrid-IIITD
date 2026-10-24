# General chat and topic-switch fix

25 October 2026

The assistant no longer intentionally redirects all non-medical questions into symptom intake. Provider responses carry a general/health intent; general turns cannot overwrite medical facts or generate caregiver recommendations. Gemini and Grok adapters parse this field. The current question takes priority over an earlier intake question.

Standalone bounded arithmetic uses a Decimal/AST calculator without eval, executable code, unbounded exponentiation or external calls. It supports arithmetic operators, parentheses and English/Devanagari digits; precision is 28 significant digits, not arbitrary symbolic mathematics. Unsupported mixed prose goes to the language model.

Validation: 85 backend tests passed. A live synthetic localhost conversation with the configured Gemini and AWS memory produced:
- Fever: relevant follow-up.
- 2+2 ?: 2+2 = 4, no fever question or care routing.
- 2+2=4 HOTA H YAAD RAKHNA: acknowledged, no fever question or care routing.
- France ki capital kya hai?: Paris, no fever question or care routing.
Synthetic session deleted afterwards. Live response samples: general_chat_live_check.json.

This is a routing and calculation improvement, not an accuracy guarantee or LLM fine-tuning. General knowledge still depends on the configured model, and no live web retrieval was added. No automatic Git push performed.
