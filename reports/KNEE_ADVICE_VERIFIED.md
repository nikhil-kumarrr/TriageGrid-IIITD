# Knee pain response improvement

25 October 2026

Changed refusal-only medicine replies into source-grounded self-care and conditional OTC information for knee pain. The assistant explains reducing aggravating activity, wrapped cold packs, and paracetamol as an option for some adults subject to suitability/product label/pharmacist advice. It names relevant risks, duplicate products, paediatric differences and urgent warning signs, without issuing a prescription or an individual dose.

Short medicine follow-ups can resolve the immediately preceding patient-reported clinical topic. Known age/medicine context is reused rather than repeating duration questions. General chat and nonmedical calculations remain separate. Source links are persisted by the existing guidance mechanism.

100 backend tests passed. Actual localhost synthetic knee-pain/Tiger Balm followed by PRESCRIBE BHI KRDE BHAI returned the knee-pain information and NHS references, rather than refusal-only text or a repeated duration question. Test session deleted. See knee_advice_live_check.json.

This is a response/routing improvement, not evidence of improved diagnostic prediction accuracy or prescription competence. No LLM weight training or additional clinical dataset was used. No automated Git push performed.

Sources checked:
https://111.wales.nhs.uk/Kneepain/
https://www.nhs.uk/medicines/paracetamol-for-adults/
