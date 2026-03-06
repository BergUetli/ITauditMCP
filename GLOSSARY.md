# Glossary

Plain English explanations for anyone reading this codebase — technical or not.

## Architecture Terms

**MCP (Model Context Protocol)** — A standard way for AI agents to talk to external tools. Think of it like a USB port — any AI can plug in and use our audit capabilities.

**MCP Server** — Our product. It sits there waiting for AI agents to ask it audit questions.

**MCP Tool** — A specific action an AI agent can ask our server to do. Like "identify risks" or "generate a finding."

**Pipeline** — The steps data goes through from input to output. Ours is: validate input → look up knowledge → AI thinks → validate output → return answer.

**Knowledge Base** — Our library of audit frameworks, controls, and expert interpretations. Stored in a database (Supabase).

**Knowledge Engine** — The code that searches and assembles knowledge from the database. It doesn't just find one thing — it pulls together controls, mappings, evidence requirements, and expert insights into a complete picture.

**Quality Layer** — The bouncers. Two checkpoints (input gate and output gate) that catch bad data going in and hallucinations coming out. Uses pattern matching, not AI — so it's reliable.

**Input Gate** — Checks input before the AI sees it. "Is this a real control ID? Which framework? Which industry?"

**Output Gate** — Checks AI output before the user sees it. "Did the AI make up a control that doesn't exist? Is the finding missing required parts?"

**Learning Loop** — How the system gets smarter over time. Users correct outputs → RP reviews corrections → knowledge base updates → better answers next time.

**Deterministic** — Same input always gives same output. No randomness. The quality layer is deterministic. The AI is not (which is why the quality layer exists).

## AI Terms

**LLM (Large Language Model)** — The AI brain. Claude and GPT are LLMs. They're good at reasoning but sometimes make things up.

**Analyst** — Our first AI call. It does the heavy thinking: identifies risks, maps controls, drafts findings.

**Reviewer** — Our second AI call. It challenges the analyst's work, like a senior manager reviewing a junior auditor's workpapers.

**RAG (Retrieval Augmented Generation)** — Giving the AI reference material before asking it to think. Instead of "what are the risks?" we say "here are the relevant controls and framework requirements — now what are the risks?"

**Hallucination** — When the AI makes something up that sounds right but isn't. Like citing "COBIT EDM07.03" which doesn't exist. Our output gate catches these.

**Confidence Score** — A number from 0 to 1 showing how sure the system is about a piece of data. 0.95 = very sure. 0.3 = probably wrong. Rises when users confirm, drops when users correct.

**Fine-tuning** — Training an AI model on your own data so it gets better at your specific task. We'll do this later once we have enough correction data from real auditors.

## Audit Terms

**Framework** — An audit standard published by a standards body. COBIT, ISO 27001, NIST CSF are all frameworks.

**Domain** — A category within a framework. COBIT has 5 domains (EDM, APO, BAI, DSS, MEA). ISO has 4 themes.

**Control** — A specific safeguard or procedure that reduces risk. "All changes require CAB approval" is a control.

**Control Mapping** — Showing how a control in one framework relates to controls in other frameworks. "COBIT BAI06.01 maps to ISO A.8.32" — both are about change management.

**Mapping Strength** — How closely two controls match: exact (same thing), strong (very similar), partial (some overlap), related (same topic, different requirements).

**Industry Overlay** — How a generic framework requirement gets interpreted in a specific industry. "Access reviews" means annual in most industries but quarterly in banking per OCC expectations.

**Interpretation** — Expert judgment about what a framework control really means in practice. This is RP's 8 years of banking audit experience, encoded as data.

**Finding** — A documented problem discovered during an audit. Must have 5 parts: Condition (what IS), Criteria (what SHOULD be), Cause (WHY), Effect (impact), Recommendation (what to DO).

**Design Effectiveness** — Is a control properly designed to work? Having a change approval process is good design. Having only one person approve everything is bad design (no segregation of duties).

**Operating Effectiveness** — Is a well-designed control actually working in practice? The process says changes need approval, but did the last 50 changes actually get approved? That's what evidence tells you.

**Evidence** — Proof that a control is working. Documents, logs, screenshots, interview notes, reports.

## Code Terms

**Pydantic Model** — A template that defines what data should look like. If data doesn't match the template, it gets rejected. Our models (Framework, Control, etc.) are all Pydantic models.

**Async / Await** — Python's way of saying "this might take a while, don't freeze everything else while waiting." Used for database calls and AI calls.

**Regex** — Pattern matching for text. How the input gate recognizes "BAI06.01" as a COBIT control ID. Fast and reliable.

**Supabase** — Our database host. It's PostgreSQL (a standard database) hosted in the cloud with a nice dashboard.

**FastMCP** — The Python library that handles the MCP protocol for us. We define tools, it handles the communication.

**Seed Data** — The initial data we load into the database. COBIT's 40 control objectives, ISO's 93 controls, etc. Without seed data, the knowledge base is empty and the system can't answer questions.
