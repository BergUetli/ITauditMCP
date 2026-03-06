---
name: Reflect on Session
description: Review this session for mistakes and learnings, suggest rules to save
---

Review the conversation in this session. For each mistake, correction, or discovery:

1. **What happened?** (one sentence)
2. **What's the general rule?** (ALWAYS/NEVER format, one line)
3. **Where should it go?**
   - CLAUDE.md "Learned Rules" section (project-wide)
   - A specific `.claude/rules/*.md` file (module-specific)
   - `ARCHITECTURE.md` (design decision)

Present your suggestions to RP as a numbered list. Wait for approval before writing anything.

Example output:
```
Session learnings:

1. Supabase rejects arrays — must convert Python lists to JSON before insert.
   Rule: ALWAYS json.dumps() list fields before Supabase insert
   Save to: .claude/rules/knowledge-engine.md

2. FastMCP tool docstrings become the tool description AI agents see.
   Rule: ALWAYS write tool docstrings as if explaining to an AI agent, not a developer
   Save to: .claude/rules/mcp-tools.md

Which of these should I save? (all / numbers / none)
```
