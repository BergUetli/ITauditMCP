# IT Audit MCP Server

An MCP (Model Context Protocol) server that gives AI agents deep IT audit capabilities — risk identification, control assessment, cross-framework mapping, and finding generation — grounded in real audit frameworks.

## What This Does

AI agents (Claude, GPT, custom agents) call this server to perform audit analysis. The server combines:

- **Knowledge Base** — COBIT 2019, ISO 27001:2022, NIST CSF 2.0, FFIEC IT Handbooks, SOC 2 TSC
- **Quality Layer** — Regex-based validation that catches hallucinated control IDs and enforces finding structure
- **LLM Pipeline** — Analyst + Reviewer pattern (two LLMs check each other's work)
- **Learning Loop** — User corrections improve the system over time (with human approval)

## MCP Tools Available

| Tool | What it does |
|------|-------------|
| `parse_process` | Break down a business process into structured steps, actors, systems |
| `identify_risks` | Identify risks in a process with framework references |
| `identify_expected_controls` | Given risks, determine what controls should exist |
| `assess_design_effectiveness` | Evaluate if a control is properly designed |
| `assess_evidence` | Assess operating effectiveness from evidence provided |
| `generate_finding` | Draft a complete finding (Condition, Criteria, Cause, Effect, Recommendation) |
| `map_frameworks` | Cross-walk a control across COBIT ↔ ISO ↔ NIST ↔ FFIEC ↔ SOC 2 |

## Quick Start

```bash
# 1. Clone and enter the project
cd it-audit-mcp

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.template .env
# Edit .env with your API keys (Supabase, Anthropic, OpenAI)

# 4. Seed the database (first time only)
python -m knowledge.seed  # TODO: build this

# 5. Run the server
python server.py                          # stdio mode (Claude Desktop)
MCP_TRANSPORT=streamable-http python server.py  # HTTP mode (remote)
```

## Project Structure

```
it-audit-mcp/
├── server.py              # Entry point — starts the MCP server
├── requirements.txt       # Python dependencies
├── .env.template          # Environment variable template
│
├── config/
│   └── settings.py        # Loads .env, validates all configuration
│
├── knowledge/             # THE MOAT — audit framework data
│   ├── models.py          # Pydantic models (Framework, Control, Mapping, etc.)
│   ├── store.py           # Database access (Supabase CRUD operations)
│   └── retriever.py       # Smart context assembly (enriched RAG)
│
├── quality/               # Deterministic validation layer
│   ├── input_gate.py      # Validates input BEFORE the LLM sees it
│   └── output_gate.py     # Validates output AFTER the LLM generates it
│
├── llm/                   # LLM integration (analyst + reviewer)
│   ├── base.py            # Abstract provider interface
│   ├── anthropic_provider.py  # Claude integration
│   ├── openai_provider.py     # OpenAI + Azure OpenAI integration
│   └── engine.py          # Orchestrates analyst → reviewer pipeline
│
├── audit/                 # Audit methodology
│   ├── prompts.py         # System prompts for each audit task
│   └── pipeline.py        # Full analysis pipeline (ties everything together)
│
├── tools/                 # MCP tool definitions
│   └── audit_tools.py     # Thin wrappers exposing pipeline as MCP tools
│
├── learning/              # Self-improvement loop
│   └── feedback_handler.py  # Corrections, approvals, confidence scoring
│
├── tests/                 # Test suite (TODO)
│
├── ARCHITECTURE.md        # Design decisions and system architecture
├── CLAUDE.md              # Instructions for Claude Code sessions
└── README.md              # This file
```

## Database

Uses Supabase (hosted PostgreSQL). The `AuditMCP` project contains:

| Table | Purpose |
|-------|---------|
| `frameworks` | Audit standards (COBIT, ISO, NIST, FFIEC, SOC 2) |
| `domains` | Framework groupings (COBIT domains, ISO clauses, NIST functions) |
| `controls` | Individual controls that auditors test |
| `control_mappings` | Cross-framework mappings (highest-value table) |
| `industry_overlays` | Industry-specific requirements (banking first) |
| `evidence_requirements` | What evidence proves a control works |
| `interpretations` | Expert audit judgment (the moat) |
| `feedback` | User corrections for the learning loop |
| `usage_log` | Telemetry for pattern detection |

Supabase Project ID: `inhioznyfkjcvjjepdxq`

## Technology Choices

- **Python** — Faster to prototype, better LLM ecosystem
- **FastMCP** — Python MCP SDK, auto-generates tool schemas from type hints
- **Supabase** — Hosted PostgreSQL, easy to start, migratable to Azure PostgreSQL later
- **Pydantic** — Data validation and type safety
- **Anthropic SDK** — Claude as primary analyst LLM
- **OpenAI SDK** — GPT as reviewer LLM (also supports Azure OpenAI for banking clients)

## Revenue Model

Two products, one engine:

1. **MCP Server** (usage-based) — Third-party AI agents and GRC platforms call the tools
2. **Voice SaaS** (subscription, future) — Voice-controlled audit assistant for fieldwork

Both consume the same Knowledge Engine. See ARCHITECTURE.md for details.
