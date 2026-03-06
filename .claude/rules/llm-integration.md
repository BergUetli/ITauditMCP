---
paths:
  - "llm/**/*.py"
  - "audit/prompts.py"
---

# LLM Integration Rules

- ALL LLM calls go through llm/engine.py — never call providers directly from audit code
- The analyst+reviewer pattern: LLM #1 analyzes, LLM #2 challenges
- Default: Analyst = Claude (Anthropic), Reviewer = GPT-4o (OpenAI)
- Both Azure OpenAI and standard OpenAI are supported via config toggle
- Temperature default is 0.3 — audit needs consistency, not creativity
- System prompts live in audit/prompts.py — not hardcoded in engine.py
- Every prompt must define: role, task instructions, output format, quality requirements
- For simple lookups, use engine.analyze_single() — skip the reviewer
- For risk identification and findings, always use the full analyst+reviewer pipeline
