# Architecture & Design Decisions

This document records WHY things are built the way they are.
Read this before making changes — every decision has a reason.

---

## Core Architecture: The Learning Knowledge System

This is NOT a simple RAG app. It's a learning knowledge system with four parts:

```
KNOWLEDGE BASE  →  QUALITY LAYER  →  MCP SERVER  →  LEARNING QUEUE
     ↑                                                      │
     └──────────────────────────────────────────────────────┘
                    (loop closes — system improves)
```

### Why a loop, not just RAG?

Static RAG retrieves documents and passes them to an LLM. Our system does that
AND learns from every interaction. After 1,000 corrections from real auditors,
a competitor starting from scratch is 1,000 corrections behind us.

---

## Decision: Three-Layer Pipeline (Input Gate → LLM → Output Gate)

```
User Input → INPUT GATE → Knowledge Retrieval → LLM (Analyst) → LLM (Reviewer) → OUTPUT GATE → Response
```

### Why deterministic gates around the LLM?

The LLM is creative and unreliable. It might say "COBIT EDM07.03" — which
doesn't exist. Or generate a finding missing the Cause component. The gates
are deterministic (same input = same output) and catch what the LLM misses.

- **Input Gate**: Regex-based. Normalizes framework references, detects control IDs,
  classifies input type, catches garbage. Fast, no network calls.
- **Output Gate**: Validates control IDs against the database, checks finding structure,
  verifies cross-framework mappings. Catches hallucinations.

### Why not just better prompts?

Prompts help. But prompts don't guarantee. A prompted LLM will get control IDs
right 95% of the time. The output gate catches the remaining 5%. For an audit
product where credibility is everything, 95% isn't good enough.

---

## Decision: Analyst + Reviewer (Two-LLM Pattern)

### Why two LLMs instead of one?

Same reason audit firms have review partners. The analyst does creative reasoning
(identifies risks, spots patterns). The reviewer is skeptical (challenges
assumptions, catches errors, adds missing items).

### Current setup:
- **Analyst**: Claude (Anthropic) — best at structured reasoning
- **Reviewer**: GPT-4o (OpenAI) — different perspective catches blind spots

### Future setup (post fine-tuning):
- **Analyst**: Fine-tuned specialist model — trained on our correction data
- **Reviewer**: General-purpose model — stays broad to catch blind spots
- **Important**: The architecture supports swapping models without changing other code

### When to skip the reviewer:
- Simple lookups (control details, framework queries)
- Process parsing (no judgment needed)
- Use `engine.analyze_single()` instead of `engine.analyze()`

---

## Decision: Supabase (PostgreSQL)

### Why Supabase?

- It's hosted PostgreSQL — nothing proprietary, migratable anytime
- Free tier is enough for development and early customers
- Built-in auth (for future web dashboard)
- Built-in REST API (could expose knowledge base directly if needed)
- Supports pgvector (for semantic search when voice SaaS needs it)

### Why not a graph database?

The data is cross-referenced (controls map to controls across frameworks).
That sounds like a graph problem. But:

- The query patterns are predictable (lookup by ID, lookup by framework+industry,
  traverse mappings from a source control)
- PostgreSQL with proper indexes handles these queries efficiently
- A mapping table with bidirectional lookups is simpler than a graph schema
- The team (RP) knows SQL, not Cypher

### Migration path:
- Supabase for development and early customers
- Azure Database for PostgreSQL when banking clients require it
  (same queries, same schema, different host)

### Supabase Project Details:
- **Project name**: AuditMCP
- **Project ID**: `inhioznyfkjcvjjepdxq`
- **Region**: eu-central-1
- **Tables**: 9 (frameworks, domains, controls, control_mappings,
  industry_overlays, evidence_requirements, interpretations, feedback, usage_log)

---

## Decision: Frameworks in Scope (and NOT in scope)

### In scope for MVP:
| Framework | Why |
|-----------|-----|
| COBIT 2019 | THE IT governance framework. No COBIT MCP server exists. Our front door. |
| ISO 27001:2022 | Information security. Every IT audit touches this. |
| NIST CSF 2.0 | Cybersecurity framework. Widely adopted. |
| FFIEC IT Handbooks | Banking-specific. Our wedge market. |
| SOC 2 TSC | IT auditors directly support SOC 2. |

### Dropped from MVP:
| Framework | Why dropped |
|-----------|-------------|
| COSO | Financial reporting framework, not IT-specific |
| PCI DSS | Only relevant for payment processing — too niche for launch |
| ITIL | Service management best practices, not an audit framework |

### Adding frameworks later:
Add them as industry overlays. The architecture supports this because
industry-specific knowledge is isolated in the `industry_overlays` and
`interpretations` tables — the rest of the stack is shared.

---

## Decision: Self-Improvement with Human Review

### Three levels of learning:

1. **Memory** — Store corrections. Next time, return the corrected answer.
2. **Patterns** — After enough corrections, detect categories of mistakes.
3. **Confidence** — Every piece of knowledge has a score that rises/falls with usage.

### Why human review is mandatory:

This is an audit product. If a bad correction slips through and an auditor
relies on it, that's a professional liability issue. The system surfaces
what SHOULD change. RP says yes or no.

- Corrections → go to review queue → RP approves/rejects → knowledge base updates
- Confirmations → auto-applied (boosting confidence is safe)

### How confidence scores work:
- Start at 0.5 (neutral)
- Each user confirmation: +0.02
- Each applied correction: -0.05 on the corrected item
- After 500 confirmations with no corrections: score approaches 1.0
- Score is surfaced to AI agents so they know how much to trust each piece of data

---

## Decision: MCP Server vs Agent (Where to Draw the Line)

### The MCP server is stateless and reusable.
Each tool call is independent. `identify_risks` doesn't need to know
you already called `parse_process`. Any agent, any platform, any workflow.

### The agent (future voice SaaS) is stateful.
It tracks: which audit, which client, which process, which step we're on.
It manages conversations. It assembles workpapers.

### Split:
| Step | Who does it | Why |
|------|-------------|-----|
| 1. Understand process | Agent calls `parse_process` | Interactive, needs conversation |
| 2. Identify controls | MCP `identify_expected_controls` | Pure knowledge lookup |
| 3. Identify risks | MCP `identify_risks` | LLM + knowledge, core value |
| 4. Expected controls | MCP `identify_expected_controls` | Knowledge + reasoning |
| 5. Actual controls | Agent gathers, MCP gap analysis | Needs auditor input |
| 6. Design effectiveness | MCP `assess_design_effectiveness` | Framework criteria |
| 7. Operating effectiveness | Agent gathers evidence, MCP `assess_evidence` | Evidence evaluation |

---

## Decision: Python over TypeScript

### Why Python:
- Faster to prototype
- Better LLM ecosystem (Anthropic SDK, OpenAI SDK, LangChain if needed)
- FastMCP (Python MCP SDK) auto-generates schemas from type hints
- RP is learning Python — better to learn one language for the whole stack

### Why not TypeScript:
- Would have been fine technically
- TypeScript MCP SDK exists and is well-maintained
- But splitting the codebase across languages adds complexity for a solo founder

---

## Decision: Azure OpenAI Support from Day 1

Banking clients almost always require Azure OpenAI because:
- Data stays in their Azure tenant (data residency compliance)
- Their security team has already approved Azure
- Regulatory requirements around data handling

The `openai_provider.py` supports both standard OpenAI and Azure OpenAI
via a config toggle (`OPENAI_API_TYPE=azure`). No code changes needed.

---

## Decision: Two Products, One Engine

```
Product 1: MCP Server (usage-based API) ─┐
                                          ├──→ Shared Knowledge Engine
Product 2: Voice SaaS (subscription)   ──┘
```

### Why this architecture:
- MCP server validates the engine with real customers
- Voice SaaS gets a proven engine for free
- Every correction from either product improves both
- MCP server funds development of the voice SaaS

### Revenue sequencing:
1. MCP Server + demo wrapper (now) → revenue + validation
2. Voice SaaS (6-12 months) → subscription revenue + retention

---

## Decision: "The Moat" — Honest Assessment

### What's NOT a moat (copyable in days-weeks):
| Layer | Why it's not a moat |
|-------|---------------------|
| Framework data | COBIT, ISO, NIST are public |
| MCP server code | Protocol is open, SDKs are free |
| LLM access | Everyone has Claude/GPT |
| Expert interpretations | Any audit firm with access to audit reports can build comparable knowledge in days. An experienced auditor or AI reading enough reports gets here fast. |
| Cross-framework mappings | Expert judgment needed but reproducible by any firm with audit experience |
| Industry overlays | Same — any banking auditor can produce these |

### What IS a moat (requires real users over time):
| Layer | Why it compounds |
|-------|-----------------|
| Learned corrections from real usage | Zero on day one. After 1,000 real interactions, a competitor starting fresh is 1,000 corrections behind. Can't be shortcut. |
| Confidence scores validated over time | Requires months of real volume to become meaningful. |
| Distribution / ecosystem lock-in | If we're the MCP server AI agents already integrate with, switching costs matter. First-mover in the tool ecosystem. |
| Speed of iteration | One person shipping in hours vs. a Big 4 committee taking 18 months. |

### Strategic implication:
The moat at launch is thin. The static knowledge (frameworks, interpretations,
mappings) is reproducible by anyone with audit experience and a few days.
The moat only becomes meaningful after real users generate corrections and
the learning loop starts compounding. Strategy: get to paying users as fast
as possible so the compounding begins.

---

## Decision: Two Entry Points Into the Knowledge Base

The system serves two fundamentally different audit scenarios:

### Entry Point A — GITC Audit (top-down)
Auditor comes in with a specific IT topic scoped at the enterprise level.
Example: "We're auditing Global Change Management across the firm."

Flow: Auditor selects audit process → system provides risks, controls, testing
procedures, evidence requirements for that process. Deep and focused.

### Entry Point B — Business Process Audit (bottom-up)
Auditor comes in with a business context described in plain English.
Example: "We want to audit how the bank handles employee joiners and leavers
and their access to systems."

Flow (two-tool design):
1. Agent calls `scope_audit(process_description, scope_decisions)` →
   hybrid keyword+LLM matching resolves description to process codes →
   returns matched programmes with summaries and scope boundaries.
2. Agent calls `get_audit_content(process_code, risk_focus?)` for each
   matched code → returns full risks, controls, testing procedures, evidence.

### Why both matter:
Some audits are purely IT-driven (e.g., "Global Change Management review").
Some start from a business process where IT audit topics become relevant
(e.g., "trading desk audit"). We need both or we're only half useful.

---

## Decision: Three Layers of Controls

### Layer 1: General IT Controls (GITCs)
The 30 audit processes (P01-P30). Apply to ALL IT systems regardless of what
the application does. Examples: change management, access management, BCP,
incident management. Same structure for every engagement.

### Layer 2: Application Controls
Specific to what the application DOES. Vary by application type. Three sub-categories:
- **Input controls**: Is data entering the system valid, complete, authorized?
- **Processing controls**: Does the system process data correctly?
- **Output controls**: Is output complete, accurate, distributed correctly?

Organized by application TYPE (trading systems, core banking, payment processing,
loan origination, AML, regulatory reporting). Harder to systematize than GITCs
but common patterns exist within each type.

### Layer 3: Business Process Controls (IT-dependent)
Manual controls in the business process that rely on IT system output.
Example: manager reviews exception report generated by system.
Out of scope for v1 — architecture should not prevent adding later.

---

## Decision: Scoping Engine (Hybrid Keywords + LLM)

When a user describes a business process (Entry Point B), the system figures
out what's relevant using two layers:

### Keywords layer (deterministic, always runs first)
`retriever.find_process_candidates()` builds a rich text blob for each seeded
process from its name, description, category, phase names, risk descriptions,
and control descriptions. Scores by word overlap with the input. This catches
vocabulary matches that process names alone would miss — e.g. "employee leavers"
matches Logical Access Management via the "Deprovisioning" phase and risk
descriptions about "timely removal of access upon termination."

### LLM layer (reasoning, confirms/adjusts keyword results) — DONE
`pipeline.resolve_process()` sends keyword candidates + the full programme list
to the LLM via `PROCESS_RESOLVER_PROMPT`. The LLM picks which programmes are
genuinely relevant (high/medium/low) and can catch matches keywords missed —
e.g. recognising that "who can approve payments" implies Privileged Access
Management even if keyword overlap is low.

### Auditor feedback loop
The calling agent presents matched programmes with relevance and reasoning.
The auditor can accept, remove, add, or adjust priority. Feedback improves
rules over time.

---

## Knowledge Base: 30 Audit Processes (IT Audit Universe)

Organized into 7 categories. Full detail in Knowledge_Base_Architecture.xlsx.

| Category | Processes | Banking Priority |
|----------|-----------|-----------------|
| IT Governance & Strategy | P01 IT Governance, P02 IT Risk Mgmt, P03 IT Policy Mgmt | HIGH/HIGH/MED |
| Development & Change | P04 Change Mgmt/SDLC, P05 Patch Mgmt, P06 Release Mgmt | HIGH/HIGH/MED |
| Access & Security | P07 Logical Access, P08 Privileged Access, P09 InfoSec, P10 Cybersecurity, P11 Vuln Mgmt, P12 Data Protection, P13 Encryption, P14 Physical Access | HIGH across the board |
| Operations | P15 IT Ops, P16 Incident Mgmt, P17 Problem Mgmt, P18 Job Scheduling | HIGH for P16/P18 |
| Continuity & Recovery | P19 BCP, P20 DR, P21 Backup & Restore | ALL HIGH |
| Infrastructure & Assets | P22 Network Security, P23 Cloud, P24 Database, P25 IT Assets, P26 End User Computing | HIGH for P22/P23 |
| Third Party | P27 Vendor Risk, P28 Outsourcing Mgmt | ALL HIGH |
| Data & Reporting | P29 Data Mgmt, P30 Regulatory Reporting | HIGH for banking |

### Build order:
- ~~**Tier 1** (banking essentials): P04, P07, P08, P10, P16, P19, P20, P27~~ — DONE
- ~~**Tier 2** (complete banking): P01, P02, P05, P09, P11, P12, P18, P21, P22, P29, P30~~ — DONE
- ~~**Tier 3** (full coverage): Everything else~~ — DONE
- All 30 processes populated as of 2026-03-07 via framework gap analysis

---

## Schema: Process-Centric Layer (Needed)

The current schema is framework-centric (framework → domain → control).
Auditors work process-centric (process → risk → control). We need to add:

| New Table | Purpose |
|-----------|---------|
| `audit_processes` | The 30 IT audit topics (P01-P30). Framework-agnostic. |
| `process_phases` | Lifecycle stages within a process (e.g., 7 SDLC phases) |
| `risks` | What could go wrong. Self-referencing for sub-risks. Linked to processes and phases. |
| `risk_control_mappings` | Which control mitigates which risk. Join table. |
| `testing_procedures` | Structured step-by-step testing. Linked to risk-control pairs. |
| `audit_programs` | Template for auditing a process end-to-end. |
| `application_types` | Categories of applications (trading system, core banking, etc.) |

Existing tables stay. No breaking changes. Process layer sits on top.

### Data volume at full scale:
~450 GITC sub-risks + ~120 application controls + ~2000 testing procedures +
~1350 evidence requirements + ~500 expert interpretations + ~300 cross-framework
mappings = ~5000-7000 structured records. Quality dataset, not big data.

---

## OPEN: COBIT Licensing Risk

ISACA requires an annual commercial license for any product incorporating COBIT content
(process names, control descriptions, identifiers like "DSS02.01"). Email sent to
licensing@isaca.org on 2026-03-06 to clarify scope and cost.

**If too expensive, fallback plan:**
- Strip all COBIT references from framework_refs
- Lean on NIST CSF 2.0 + FFIEC (public domain, free to use)
- ISO 27001 control *numbers* (A.5.24) likely OK as identifiers; don't reproduce ISO text
- SOC 2 / AICPA Trust Services Criteria — monitor, similar IP considerations
- Our P01-P30 process codes are our own, not COBIT's

**Action needed:** Wait for ISACA response, then decide before launch.

---

## What's NOT Built Yet

| Item | Priority | Notes |
|------|----------|-------|
| ~~Schema migration (process-centric tables)~~ | ~~DONE~~ | 12 migrations applied |
| ~~Seed data (6 core processes)~~ | ~~DONE~~ | P04, P07, P08, P12, P16, P20 — organically seeded with full depth |
| ~~Knowledge base gap analysis (23 templated processes)~~ | ~~DONE~~ | P01-P03, P05-P06, P09-P11, P13-P15, P17-P19, P21-P30 augmented via framework gap analysis against COBIT 2019, ISO 27001, NIST CSF 2.0, FFIEC, SOC 2. All 30 processes now populated: 255 parent risks, 832 sub-risks, 3,329 test procedures, 2,408 evidence requirements |
| ~~Scoping engine (keywords layer)~~ | ~~DONE~~ | `retriever.find_process_candidates()` — deep keyword matching |
| ~~Scoping engine (LLM layer)~~ | ~~DONE~~ | `pipeline.resolve_process()` — hybrid keyword+LLM resolution |
| Cross-framework mapping seed data | HIGH | The highest-value feature |
| RP's banking interpretations | HIGH | The moat — encode your experience |
| First application control template | MEDIUM | Trading system or core banking |
| Hardcoded numbers cleanup | MEDIUM | See CLAUDE.md "Open: Hardcoded Numbers to Fix" |
| Test suite | MEDIUM | Unit tests for quality gates, integration tests for pipeline |
| OAuth 2.1 authentication | MEDIUM | Needed before going live |
| Stripe billing integration | MEDIUM | Needed for revenue |
| Web demo wrapper | MEDIUM | Sales tool, not the product |
| Usage pattern detection | LOW | Part of learning loop, needs usage data |
| Semantic search (pgvector) | LOW | Needed for voice SaaS, not MCP server |
