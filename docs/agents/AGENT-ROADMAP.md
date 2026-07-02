# AEOS Agent Roadmap

**Version:** 1.2
**Updated:** CAP-1 (2026-07-02)
**Status:** UPDATED — reflects sprints as delivered through CAP-1

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

**Status:** COMPLETE
**Branch:** `agents/local-planner`
**PR:** #72 · `96ac91d`

**What was built:**
- Command `aeos agent plan [--project] [--output] [--json] [--registry]`
- `AgentPlan` dataclass, `ProjectPlanEntry` dataclass
- `generate_plan()` — deterministic rules engine, no model
- `generate_project_entry()` — per-project recommendation builder
- Plan output carries `read_only: true · applied: false`
- Full test coverage

**What was NOT built:**
- No model integration — pure deterministic logic as planned

**Constraints met:**
- Read-only, no model calls, no network
- Gates 1–4 from `AGENT-SAFETY-GATES.md` pass

---

## MVP-AGENTS-3 — Agent Recommendations in Workspace

**Status:** COMPLETE
**Branch:** `agents/workspace-recommendations`
**PR:** #73 · `fd16037`

**What was built:**
- "Recommendations" section embedded in `aeos ui project-workspace` HTML (11-section workspace)
- Agent plan output consumed in `aeos workspace demo` orchestration
- Evidence pack includes plan output when present
- Workspace renders cleanly when plan is absent (graceful skip)

**Constraints met:**
- Read-only HTML generation
- No inline model calls in HTML
- Plan must be present; section skipped if absent

---

## MVP-AGENTS-4 — PR Proposal Generator

**Status:** COMPLETE
**Branch:** `agents/pr-proposal`
**PR:** #74 · `2d8bb7c`

**What was built:**
- Command `aeos agent pr-proposal [--project] [--output] [--json] [--registry]`
- `PRProposal` dataclass (14-section structured proposal)
- `generate_pr_proposal()` — deterministic, no LLM, no network
- `generate_pr_proposal_from_memory()` — reads MemoryRecords directly
- PR proposal carries `read_only: true · applied: false`
- Human copies proposal text, then runs `gh pr create` themselves

**What was NOT built:**
- Agent does not call `gh pr create` — human action required
- No model calls

**Constraints met:**
- Agent never opens the PR autonomously
- Gates 1–5 from `AGENT-SAFETY-GATES.md` pass (Gate 5 = human review)

---

## MVP-AGENTS-4A — Agent Workflow Evidence

**Status:** COMPLETE
**PR:** #75 · `167f0f3`

**What was built:**
- `docs/evidence/AEOS-AGENT-WORKFLOW-EVIDENCE.md`
- Complete evidence document covering MVP-AGENTS-2, 3, and 4
- Smoke test output, quality gate results, safety invariants verified

---

## MVP-AGENTS-5 — PR Proposal in Workspace

**Status:** COMPLETE
**Branch:** `agents/agentic-workspace`
**PR:** #76 · `dec1ac0`

> **Scope note:** The original MVP-AGENTS-5 planned Controlled Local Model
> Integration (Ollama). That work was deferred and is now tracked as
> MVP-AGENTS-7. This sprint delivered PR Proposal integration into the
> static workspace and evidence pack.

**What was built:**
- PR Proposal section embedded in `aeos ui project-workspace` HTML
- `aeos workspace demo` now produces PR proposal file as part of the evidence pack
- Workspace HTML shows a "Suggested PR" block drawn from the generated proposal
- Evidence pack (9 files per project) includes `pr-proposal.md`

**Constraints met:**
- Read-only HTML generation only
- No model calls — proposal sourced from `generate_pr_proposal_from_memory()`

---

## MVP-AGENTS-5A — Agentic Workspace Evidence

**Status:** COMPLETE
**PR:** #77 · `e912cc7`

**What was built:**
- `docs/evidence/AEOS-AGENTIC-WORKSPACE-EVIDENCE.md`
- Evidence document covering the agentic workspace integration
- Smoke test output, quality gate results, invariants verified

---

## MVP-AGENTS-6 — Controlled PR Management

**Status:** COMPLETE
**Branch:** `agents/controlled-pr-management`
**PR:** #78 · `0047bec`

> **Scope note:** The original MVP-AGENTS-6 planned a Frontier Escalation
> Workflow. That work was deferred and is now tracked as MVP-AGENTS-8.
> This sprint delivered a read-only local PR proposal management layer.

**What was built:**
- Commands `aeos agent pr list [--proposals-dir]` and `aeos agent pr show <id> [--proposals-dir]`
- `ProposalStatus(StrEnum)` — `pending`, `applied`, `dismissed`
- `Proposal` dataclass — local PR proposal from `workspace/proposals/<id>/proposal.json`
- `ProposalRepository` — read-only store: `list()` + `get(id)`
- `render_proposal_list()` / `render_proposal_detail()` — terminal renderers
- `DEFAULT_PROPOSALS_DIR` = `~/.aeos/workspace/proposals/`
- 58 new tests covering all behaviors, edge cases, and safety invariants
- Every output carries `read_only: true · applied: false · human validation required`

**Constraints met:**
- No GitHub API call. No git command. No network. No file mutation.
- Repository never writes — `list()` and `get()` are read-only

---

## MVP-AGENTS-6A — Controlled PR Management Evidence

**Status:** COMPLETE
**PR:** #79 · `e17e24f`

**What was built:**
- `docs/evidence/AEOS-CONTROLLED-PR-MANAGEMENT-EVIDENCE.md`
- Complete evidence document covering MVP-AGENTS-6
- Lifecycle diagram, safety architecture table, smoke test output, 1950-test quality gate

---

## CAP-1 — Human-Gated Apply Engine

**Status:** COMPLETE
**Branch:** `cap1/sprint-a`
**PR:** #84 · `0f5563fd`

**What was built:**
- `src/aeos/agent/apply_engine.py` — `ApplyContext`, `ApplyResult`, `run_apply()`
- `aeos agent pr apply <id>` CLI command — shows proposal, prompts for `APPLY <id>`, calls engine on correct confirmation, displays paths on success
- Evidence-first invariant: `apply-log.json` written before `status → applied`
- APPLY.PRE.05 guard: `FileExistsError` if apply-log already exists (prevents evidence destruction on retry)
- `build_memory_record_from_apply()` in `store.py` — `human_validated=True`, `applied=True`
- 44 unit tests (`test_apply_engine.py`) + 23 CLI tests (`test_cli_agent_pr_apply.py`)

**Constraints met:**
- `--yes` forever forbidden — only `APPLY <id>` typed exactly by human is accepted
- Wrong or partial confirmation: exit 0, zero files written
- Status transitions to `applied` only after `apply-log.json` exists on disk
- `ProposalRepository` remains read-only — `run_apply()` calls `update_proposal_status()` directly
- No network call, no secret access, no write outside `proposals_dir/<id>/` and `memory_dir/`

**Closes:** Core Loop (Flux A) — `Inspect → MemoryRecord → Proposal → Human Gate → Apply → Evidence → MemoryRecord`

---

## MVP-AGENTS-7 — Controlled Local Model Integration

**Status:** PLANNED
**Target branch:** `agents/local-model`

> This sprint was originally numbered MVP-AGENTS-5. Its scope is unchanged.
> It was deferred to allow PR proposal and workspace integration to ship first.

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

## MVP-AGENTS-8 — Frontier Escalation Workflow

**Status:** PLANNED
**Target branch:** `agents/frontier-escalation`

> This sprint was originally numbered MVP-AGENTS-6. Its scope is unchanged.
> It was deferred to allow PR proposal and PR management to ship first.

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

| Sprint | Command | Capability | Model required | Status |
|--------|---------|-----------|----------------|--------|
| MVP-AGENTS-1 | — | Policy only | No | COMPLETE |
| MVP-AGENTS-2 | `aeos agent plan` | Deterministic plan | No | COMPLETE |
| MVP-AGENTS-3 | `aeos workspace demo` | Plan in workspace | No | COMPLETE |
| MVP-AGENTS-4 | `aeos agent pr-proposal` | PR proposal (deterministic) | No | COMPLETE |
| MVP-AGENTS-4A | — | Evidence doc | No | COMPLETE |
| MVP-AGENTS-5 | `aeos workspace demo` | PR proposal in workspace | No | COMPLETE |
| MVP-AGENTS-5A | — | Evidence doc | No | COMPLETE |
| MVP-AGENTS-6 | `aeos agent pr list/show` | Controlled PR management | No | COMPLETE |
| MVP-AGENTS-6A | — | Evidence doc | No | COMPLETE |
| CAP-1 | `aeos agent pr apply` | Human-gated Apply Engine | No | COMPLETE |
| MVP-AGENTS-7 | `aeos agent plan --model` | Local model plan | Ollama (local) | PLANNED |
| MVP-AGENTS-8 | `aeos agent plan --escalate` | Frontier escalation | Claude / GPT-4 | PLANNED |
