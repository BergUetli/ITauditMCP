---
paths:
  - "learning/**/*.py"
---

# Learning Loop Rules

- CRITICAL: Nothing changes in the knowledge base without RP's approval
- Corrections go to review queue → RP approves/rejects → then knowledge base updates
- Confirmations are auto-applied (boosting confidence is safe)
- Confidence adjustments: +0.02 per confirmation, -0.05 per applied correction
- Confidence floor: 0.0, ceiling: 1.0
- Feedback records are never deleted — even rejected ones stay for pattern analysis
- The feedback table tracks source_product ('mcp_server' or 'voice_saas') for analytics
