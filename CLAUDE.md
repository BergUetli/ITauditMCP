# Claude Code Instructions for IT Audit MCP Server

## About This Project

An MCP server that gives AI agents IT audit capabilities (risk identification,
control assessment, framework mapping) grounded in real audit standards.

**Owner**: RP — ex-bank IT auditor, 8 years experience. Not a Python expert.
Comment all code thoroughly. Explain what functions do, not just how.

## Tech Stack

- Python 3.11+
- FastMCP 3.0+ (MCP server framework)
- Supabase (PostgreSQL) — Project ID: `inhioznyfkjcvjjepdxq` (eu-central-1)
- Anthropic SDK (Claude) — analyst LLM
- OpenAI SDK (OpenAI + Azure OpenAI) — reviewer LLM
- Pydantic 2.0+ — data models and validation

## File Index

### Root
- `ARCHITECTURE.md` — All design decisions, pipeline architecture, moat assessment, two entry points, three control layers, scoping engine, 30 audit processes, schema design, build order, OPEN items (COBIT licensing risk). READ THIS FIRST.
- `GLOSSARY.md` — Terminology definitions
- `server.py` — MCP server entry point (stdio or HTTP)
- `requirements.txt` — Python dependencies

### `knowledge/` — Database models and access
- `models.py` — Pydantic models for ALL tables: Framework, Domain, Control, ControlMapping, IndustryOverlay, EvidenceRequirement, Interpretation, Feedback, UsageLog, **AuditProcess, ProcessPhase, Risk, RiskControlMapping, TestingProcedure**
- `store.py` — Supabase CRUD layer. Framework-centric methods (get_control_by_code, get_mappings_for_control, etc.) AND process-centric methods (get_audit_process_by_code, get_risks_for_process, get_testing_procedures, etc.)
- `retriever.py` — Assembles full context for LLM injection. Has `ControlContext` (framework-centric) and `ProcessContext` (process-centric) with `to_llm_context()` formatters. `find_process_candidates()` does deep keyword matching against process names, phase names, risk descriptions, and control descriptions.

### `tools/` — MCP tool definitions
- `audit_tools.py` — All MCP tools AI agents call. Pipeline tools (parse_process, identify_risks, etc.), knowledge base tools (list_audit_processes, get_process_detail, etc.), and Entry Point B tools (`scope_audit`, `get_audit_content`).

### `audit/` — Pipeline orchestration
- `pipeline.py` — Main audit pipeline: Input Gate → Knowledge Retrieval → LLM Analyst → LLM Reviewer → Output Gate. Also has `resolve_process()` (hybrid keyword+LLM process matching) and `scope_audit()` (Entry Point B orchestration).
- `prompts.py` — System prompts for each pipeline function. Includes `PROCESS_RESOLVER_PROMPT` for matching descriptions to audit programmes.

### `quality/` — Deterministic validation gates
- `input_gate.py` — Regex-based input normalization and validation
- `output_gate.py` — Output validation (control ID verification, finding structure checks)

### `llm/` — LLM provider abstraction
- `engine.py` — Analyst + Reviewer dual-LLM engine. All LLM calls go through here.

### `learning/` — Feedback and confidence
- `feedback_handler.py` — Processes user corrections, adjusts confidence scores

### `config/`
- `settings.py` — Environment config (Supabase keys, LLM keys, transport mode)

### `seeds/` — Seed data scripts (in session working dir, not committed)
- seed_change_mgmt.py (P04), seed_access_mgmt.py (P07), seed_pam.py (P08), seed_incident_mgmt.py (P16), seed_disaster_recovery.py (P20), seed_data_protection.py (P12)

## Architecture (Read ARCHITECTURE.md for full details)

Pipeline: Input Gate → Knowledge Retrieval → LLM Analyst → LLM Reviewer → Output Gate

Six modules: knowledge/, quality/, llm/, audit/, tools/, learning/

## Database — Current State

Supabase project: `inhioznyfkjcvjfepdxq` (AuditMCP, eu-central-1)

### Framework-centric tables (original schema):
- frameworks, domains, controls, control_mappings
- industry_overlays, evidence_requirements, interpretations
- feedback, usage_log

### Process-centric tables (added via migrations):
- audit_processes (30 processes P01-P30)
- process_phases (lifecycle phases per process)
- risks (parent risks level 1, sub-risks level 2)
- risk_control_mappings (expected control per sub-risk + framework refs)
- testing_procedures (step-by-step audit test steps)
- evidence_requirements (also linked via risk_control_mapping_id)

### Seeded data (as of 2026-03-07):

All 30 processes (P01-P30) are now populated. The 6 original processes were seeded organically with full depth. The remaining 23 were initially templated (3 sub-risks per phase), then augmented via framework gap analysis against COBIT 2019, ISO 27001:2022, NIST CSF 2.0, FFIEC, and SOC 2.

**Knowledge base totals (all 30 processes combined):**
| Metric | Count |
|--------|-------|
| Parent risks | 255 |
| Sub-risks | 832 |
| Risk-control mappings | 832 |
| Testing procedures | 3,329 |
| Evidence requirements | 2,408 |

**Notable:** P09 Information Security was the largest augmentation — gained a new Phase 8 (Mobile, Remote & Endpoint Security) with parent risk IS8.P and 4 sub-risks (IS8.1-IS8.4), plus 8 additional sub-risks across existing phases.

Each sub-risk follows the standard pattern: 1 risk row + 1 risk_control_mapping + 4 testing_procedures + 3 evidence_requirements. Parent risks have NO control mappings — controls only attach to sub-risks (leaf nodes).

5 frameworks seeded: COBIT 2019, ISO 27001:2022, NIST CSF 2.0, FFIEC IT, SOC 2 TSC.

## Key Design Rules

1. **Every function must have a docstring** explaining what it does in plain English
2. **The quality gates are deterministic** — no LLM calls in input_gate.py or output_gate.py
3. **Nothing changes in the knowledge base without human approval** (learning/feedback_handler.py)
4. **The MCP tools are thin wrappers** — real logic lives in audit/pipeline.py or knowledge/retriever.py
5. **Enum values must be converted to strings** before sending to Supabase
6. **All LLM calls go through llm/engine.py** — never call providers directly from audit code
7. **Don't create version files** — keep one file, update in place. Check with RP before creating new files.

## OPEN Issues

- **COBIT Licensing**: ISACA requires commercial license for COBIT content in software products. Email sent 2026-03-06. Fallback: strip COBIT refs, lean on NIST/FFIEC (public domain). See ARCHITECTURE.md for details.

## Running the Server

```bash
# Local (stdio, for Claude Desktop)
python server.py

# Remote (HTTP)
MCP_TRANSPORT=streamable-http python server.py
```

## Testing

```bash
pytest tests/
```

## Self-Learning Rules

Claude should learn from mistakes across sessions. Follow this process:

**When you discover something important** (a bug pattern, a project quirk, a better approach):
1. Fix the immediate problem
2. Ask RP: "I learned that [X]. Should I save this as a permanent rule?"
3. If yes → add it to the right place:
   - Project-wide rule → add to this file under "Learned Rules" below
   - Module-specific rule → add to the matching file in `.claude/rules/`
   - Architecture decision → add to `ARCHITECTURE.md`

**When RP corrects you:**
1. Don't just fix it — understand WHY you were wrong
2. Ask: "Should I add a rule so I don't make this mistake again?"
3. Write the rule as: NEVER/ALWAYS + short reason + example

**Rule format:**
- ALWAYS: `ALWAYS convert enum values to .value before Supabase inserts`
- NEVER: `NEVER call LLM providers directly — go through llm/engine.py`
- Keep rules to one line. If it needs more, it belongs in `.claude/rules/`

## Learned Rules

- ALWAYS use `--break-system-packages` flag with pip install
- NEVER create version files (v1, v2) — update the single file in place
- ALWAYS check with RP before creating new files
- ALWAYS use plpgsql DO blocks for seeding hierarchical data (parent ID needed for children)
- NEVER assume process codes map to names — query the database (P01 is NOT Access Management)
- NEVER use 'system' or 'system_type' in tool parameters — this is a process audit tool, not a system audit tool
- NEVER hardcode confidence scores — always compute from actual data or LLM output
- ALWAYS use column name `code` (not `process_code`) when querying `audit_processes` table
- ALWAYS use valid `evidence_type` values: document, report, config, log, screenshot, observation, interview (NOT 'record')
- ALWAYS use `risk_level` 1 or 2 only — check constraint rejects level 3
- NEVER add control mappings to parent risks — controls only attach to sub-risks (leaf nodes)

## Open: Hardcoded Numbers to Fix

All confidence scores and thresholds must be computed or configurable — no made-up numbers.

### In new code (scope/resolve tools — this session)
- `audit/pipeline.py:139` — `keyword_fallback_threshold = 0.3` in `resolve_process()`. Remove the threshold entirely. If LLM fails, return ALL keyword candidates with score > 0, derive relevance from rank position not arbitrary bins.
- `audit/pipeline.py:143,145` — `0.6` and `0.4` bins for mapping keyword scores to relevance. Remove when fallback is reworked.
- `audit/pipeline.py:214` — `relevance_weights = {"high": 0.9, "medium": 0.7, "low": 0.5, "none": 0.2}` in `scope_audit()`. These map LLM categorical output to numeric confidence. Move to `config/settings.py` so they're visible and tunable.
- `audit/pipeline.py:219` — `0.3` fallback confidence when zero matches. Should be derived, not invented.

### In pre-existing code
- `audit/pipeline.py:252` — `confidence_score=0.8` in `parse_process()`. Same problem already fixed in `scope_audit()`. Needs same treatment.
- `quality/output_gate.py:66` — `confidence_score = 0.7` "Neutral default". Should be computed from validation results.
- `llm/engine.py:178` — `overlap > 0.7` similarity threshold for detecting reviewer changes. Magic number.
- `llm/anthropic_provider.py:25`, `llm/openai_provider.py:37` — `temperature = 0.3` should be in `config/settings.py`, not buried in provider code.

### Already fine (documented design decisions)
- `0.5` starting confidence, `0.02` boost, `0.05` reduction — documented in `.claude/rules/knowledge-engine.md`
- Model field defaults in `models.py` — starting values for new database records
- `config/settings.py` MIN_CONFIDENCE_THRESHOLD — already configurable via .env
