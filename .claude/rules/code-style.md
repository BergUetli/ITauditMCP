---
paths:
  - "**/*.py"
---

# Python Code Style Rules

## Commenting Rules (IMPORTANT)
- Every file starts with a short header comment: what this file does and where it fits in the system (2-4 lines max)
- Do NOT comment every line — only add comments above large blocks of logic explaining what that block achieves
- Comments should be plain English, one short sentence. If a 10-year-old can't understand it, simplify it.
- No jargon in comments. Say "look up the control in the database" not "execute a parameterized query against the ORM layer"
- Function docstrings: one line saying what it does. Add Args/Returns only if the function has 3+ parameters.
- Class docstrings: one line saying what this class represents and when you'd use it.
- Bad: `# Iterate over the list and apply a filter predicate to each element`
- Good: `# Keep only the controls that match this framework`

## Code Rules
- Use type hints on all function parameters and return types
- Async functions use `async def` and `await` — all LLM and DB calls are async
- Enum values must be converted to `.value` strings before sending to Supabase
- Import order: stdlib → third-party → local modules (separated by blank lines)
- Use f-strings for string formatting
- Handle errors with try/except, never silently swallow exceptions (except telemetry)
- Keep functions under 50 lines — split if longer
