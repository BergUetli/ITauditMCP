---
paths:
  - "knowledge/**/*.py"
---

# Knowledge Engine Rules

- models.py defines the Pydantic models that match Supabase tables EXACTLY
- If you change a model, you MUST create a matching Supabase migration
- store.py handles raw CRUD — no business logic here
- retriever.py assembles context — this is the "smart RAG" layer
- Confidence scores: start at 0.5, range 0.0-1.0, boost +0.02 on confirm, reduce -0.05 on correction
- Framework slugs are the canonical identifiers: cobit_2019, iso_27001_2022, nist_csf_2, ffiec_it, soc2_tsc
- Control ID patterns (regex) are defined in both models.py (per control) and quality/input_gate.py (global)
- ALWAYS search the full depth of knowledge (phases, risks, controls) when matching — process names alone miss most real audit vocabulary (e.g. "employee leavers" only matches via phase names and risk descriptions, not the process name "Logical Access Management")
