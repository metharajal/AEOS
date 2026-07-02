# AEOS Agent Roadmap

**Version:** 1.0
**Sprint:** MVP-AGENTS-1
**Status:** RATIFIED

---

## Vision

AEOS agents are not autonomous operators. They are **controlled intelligence
layers** that make human engineering decisions faster, more evidence-backed,
and more consistent — without removing the human from the loop.

Every sprint in this roadmap adds one well-bounded agent capability. No sprint
ships an agent that can act without human confirmation. No sprint removes a
safety gate added by a previous sprint.

---

## MVP-AGENTS-1 — Local AI Assistant Policy

**Status:** COMPLETE
**Branch:** `agents/local-ai-policy`

**What was built:**
- Policy document: what agents can and cannot do
- Safety gates: mandatory checks before any agent action
- Frontier escalation policy: when and how to involve remote models
- This roadmap

**What was NOT built:**
- No agent code
- No model integration
- No inference pipeline

**Why this sprint first:**
Shipping policy before code is the only way to ensure the code is written
within a known boundary. Policy written after the fact rationalises code that
may already have violated it.

---

## MVP-AGENTS-2 — Local Assistant Planner (Read-Only)

**Status:** PLANNED
**Target branch:** `agents/local-planner`

**Objective:**
A command `aeos agent plan --project <name>` that reads a project's
MemoryRecords and produces a prioritised action plan as a Markdown file.

**Scope:**
- Read MemoryRecords from registered project
- Apply deterministic rules to identify top 5 recommended actions
- Produce `agent-plan.md` in the project's evidence directory
- Display plan in terminal
- No model required for this sprint — pure deterministic logic

**Constraints:**
- Read-only. No model calls. No network.
- Output must carry `read_only: true · applied: false`
- Gates 1–4 from `AGENT-SAFETY-GATES.md` must pass

**Success criteria:**
- `uv run aeos agent plan --project ma-mairie-digitale` produces a valid plan
- Plan references specific MemoryRecord findings
- Plan does not contain any secret or file content

---

## MVP-AGENTS-3 — Agent Recommendations in Workspace

**Status:** PLANNED
**Target branch:** `agents/workspace-recommendations`

**Objective:**
Embed the agent plan output into the generated workspace HTML, so a CTO
browsing the workspace sees AI-assisted recommendations alongside audit
findings.

**Scope:**
- Extend `workspace demo` to include `agent-plan.md` in the evidence pack
- Add a "Recommendations" section to `project-workspace.html`
- Source content from plan file if present, skip gracefully if absent
- No new model calls — consumes the plan produced by MVP-AGENTS-2

**Constraints:**
- Read-only HTML generation only
- Plan must be present and human-reviewed before inclusion
- No inline JavaScript model calls in the HTML

**Success criteria:**
- Workspace HTML shows recommendations when plan file exists
- Workspace HTML renders cleanly when plan file is absent
- Evidence pack includes the plan file

---

## MVP-AGENTS-4 — PR Proposal Generator

**Status:** PLANNED
**Target branch:** `agents/pr-proposal`

**Objective:**
A command `aeos agent propose-pr --project <name>` that generates a
structured PR description based on the agent plan, ready for human review
before the human runs `gh pr create` manually.

**Scope:**
- Read agent plan from evidence directory
- Generate PR title, body, and checklist as a Markdown file
- Display in terminal
- Human copies or approves, then runs `gh pr create` themselves

**Constraints:**
- Agent never calls `gh pr create`
- PR proposal must reference evidence files for every claim
- Must carry `read_only: true · applied: false`
- Gates 1–5 from `AGENT-SAFETY-GATES.md` must pass (Gate 5 = human review)

**Success criteria:**
- Proposal is coherent and references specific findings
- Human can create the PR in one copy-paste step
- Agent never opens the PR autonomously

---

## MVP-AGENTS-5 — Controlled Local Model Integration

**Status:** PLANNED
**Target branch:** `agents/local-model`

**Objective:**
Connect AEOS to a locally-served open model (Ollama) to power plan generation
with natural language reasoning instead of deterministic rules.

**Scope:**
- Detect whether Ollama is running on `localhost:11434`
- If available: use model for plan generation (still read-only)
- If unavailable: fall back to deterministic rules (MVP-AGENTS-2 behaviour)
- User chooses model via `--model` flag (e.g. `--model llama3`)
- No model is bundled or downloaded by AEOS

**Constraints:**
- Model must run locally — no remote Ollama endpoints
- All safety gates from `AGENT-SAFETY-GATES.md` apply
- Context payload constructed according to `LOCAL-AI-ASSISTANT-POLICY.md`
- No secrets, no file contents, no connection strings in context

**Success criteria:**
- Plan quality improves with local model vs deterministic rules
- Fallback to deterministic rules is automatic and silent
- No data leaves the machine

---

## MVP-AGENTS-6 — Frontier Escalation Workflow

**Status:** PLANNED
**Target branch:** `agents/frontier-escalation`

**Objective:**
Implement the escalation protocol from `FRONTIER-AI-ESCALATION.md` as an
executable workflow — a controlled, consent-gated path to frontier models
when local analysis is insufficient.

**Scope:**
- `aeos agent plan --project <name> --escalate` triggers escalation workflow
- Displays sanitised payload for user review before any API call
- Requires explicit `yes` confirmation
- Writes escalation evidence record before API call
- Calls frontier model (Claude by default) with sanitised context
- Returns response marked `read_only: true · applied: false`

**Constraints:**
- No secrets in payload (abort if detected)
- User must confirm before every escalation
- Evidence record immutable after creation
- Frontier model cannot apply anything — output is text only
- Full compliance with `FRONTIER-AI-ESCALATION.md`

**Success criteria:**
- Escalation workflow requires two explicit user actions (flag + confirmation)
- Evidence record exists before API call is made
- Escalation aborts if secret pattern detected in context
- Output clearly distinguishes frontier-generated from local-generated content

---

## What Is Never on the Roadmap

The following will not be added to AEOS, regardless of frontier model
capability or user request:

| Feature | Why it will never ship |
|---------|----------------------|
| Autonomous commit bot | Removes human from the loop |
| Auto-apply mode | Violates core invariant |
| Background agent daemon | No human checkpoint |
| Model that reads `.env` | Secret policy |
| Agent that modifies MemoryRecords | Evidence integrity |
| "Trust me, apply it" flag | Human gate cannot be bypassed |
| Cloud sync of agent logs | Local-first doctrine |
| Agent that registers/removes projects | Registry integrity |

---

## Governance

Each agent sprint is gated by:

1. Policy review — does the new capability comply with `LOCAL-AI-ASSISTANT-POLICY.md`?
2. Gate verification — do all safety gates from `AGENT-SAFETY-GATES.md` pass?
3. Escalation check — if frontier AI is involved, does `FRONTIER-AI-ESCALATION.md` apply?
4. Evidence — does the sprint produce an evidence document?
5. Human test — has a real human reviewed a real output before the sprint closes?

No agent sprint closes without all five gates satisfied.

---

## Summary Timeline

| Sprint | Command | Capability | Model required |
|--------|---------|-----------|----------------|
| MVP-AGENTS-1 | — | Policy only | No |
| MVP-AGENTS-2 | `aeos agent plan` | Deterministic plan | No |
| MVP-AGENTS-3 | `aeos workspace demo` | Plan in workspace | No |
| MVP-AGENTS-4 | `aeos agent propose-pr` | PR proposal | No |
| MVP-AGENTS-5 | `aeos agent plan --model` | Local model plan | Ollama (local) |
| MVP-AGENTS-6 | `aeos agent plan --escalate` | Frontier escalation | Claude / GPT-4 |
