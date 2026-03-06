---
paths:
  - "quality/**/*.py"
---

# Quality Layer Rules

- The quality gates (input_gate.py, output_gate.py) are DETERMINISTIC
- NEVER add LLM calls, network calls, or async operations to the quality layer
- Same input MUST produce same output every time — no randomness
- input_gate.py runs BEFORE knowledge retrieval and LLM calls
- output_gate.py runs AFTER LLM response, BEFORE returning to client
- Regex patterns for control IDs must match the framework's actual ID format:
  - COBIT: (EDM|APO|BAI|DSS|MEA)\d{2}\.\d{2}
  - ISO 27001: A\.\d{1,2}(\.\d{1,2}){0,2}
  - NIST CSF: (GV|ID|PR|DE|RS|RC)\.[A-Z]{2}-\d{1,2}
  - SOC 2: (CC|A|PI|P|C)\d\.\d
- When adding new frameworks, update BOTH input_gate.py AND output_gate.py patterns
