---
paths:
  - "tools/**/*.py"
  - "server.py"
---

# MCP Server & Tools Rules

- Tools are THIN WRAPPERS — they call audit/pipeline.py, nothing else
- Every tool must have a clear docstring — FastMCP uses it to describe the tool to AI agents
- Tool parameters use simple types (str, Optional[str]) — no complex objects
- Tool return type is always str (formatted by _format_result)
- The pipeline is created once at startup (register_tools) — not per-call
- server.py handles transport selection (stdio vs streamable-http) via config
- When adding a new tool: add to tools/audit_tools.py, add pipeline method in audit/pipeline.py
