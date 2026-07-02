# AEOS Agentic Workspace Evidence

**Sprint:** MVP-AGENTS-5A
**Date:** 2026-07-02
**Branch at validation:** main @ `9418b13`
**Project tested:** ma-mairie-digitale
**Status:** PASSED

---

## Executive Summary

The AEOS Project Workspace is now an agentic workspace. It combines project state,
risk analysis, deterministic recommendations, and a structured PR proposal — all
generated locally, without any LLM, network call, or file mutation.

Every workspace surface (HTML, evidence pack, demo) now contains five categories
of structured intelligence derived from local MemoryRecords:

1. **Project state** — production readiness, risk register, recovery progress
2. **Agent recommendations** — deterministic planner, risks, blockers, actions
3. **PR proposal** — structured 14-section proposal with title, scope, checklist
4. **Evidence** — audit trail, record count, finding aggregates, human gates
5. **Human gates** — explicit sign-off requirements before any production action

The doctrine is fully implemented and verified: **Agent proposes. AEOS verifies.
Human validates.**

---

## Agentic Workspace Contents

Every project workspace now contains the following sections and files.

### Project Workspace HTML (`aeos ui project-workspace`)

| Section | Content |
|---------|---------|
| Project Overview | Status, control level, generator, providers, last audit |
| Executive Summary | Narrative derived from finding counts and recovery progress |
| **Agent Recommendations** | Planner status (OK/WARNING/CRITICAL), blockers, recommended actions |
| **Suggested PR** | PR title, objective, why now, recommended scope, validation commands |
| Production Readiness | Verdict (READY / NOT READY), blocking reasons |
| Recovery Progress | Baseline → current delta table across all finding categories |
| Completed Recovery Work | What has been addressed vs baseline |
| Human Gates | Sign-off checklist before production |
| Risk Register | Critical / important / manual / sql_blocks with counts and notes |
| Evidence | Record count, first/last record ID, read_only / applied / human_validated |
| Next Recommended Actions | Ordered list from planner |

### Evidence Pack (`aeos ui evidence-pack`)

9 files generated per project:

| # | File | Description |
|---|------|-------------|
| 1 | `index.html` | Pack index with all file links and production verdict |
| 2 | `dashboard.html` | Audit timeline — all records, deltas, synthesis trends |
| 3 | `project-workspace.html` | Executive workspace — all 11 sections above |
| 4 | `recovery-summary.md` | Narrative recovery — baseline vs current, verdict |
| 5 | `risk-register.md` | Categorised findings with severity and action notes |
| 6 | `human-gates.md` | Sign-off checklist with date and notes fields |
| 7 | `next-actions.md` | Ordered actions with assignment and target date fields |
| 8 | `agent-plan.md` | Deterministic agent plan — risks, blockers, actions (no LLM) |
| 9 | `pr-proposal.md` | 14-section PR proposal — no LLM, no network |

### Workspace Demo (`aeos workspace demo`)

Per-project directory structure:

```
/tmp/aeos-workspace-demo/
└── ma-mairie-digitale/
    ├── workspace.html
    ├── dashboard.html
    └── evidence-pack/
        ├── index.html
        ├── dashboard.html
        ├── project-workspace.html
        ├── recovery-summary.md
        ├── risk-register.md
        ├── human-gates.md
        ├── next-actions.md
        ├── agent-plan.md
        └── pr-proposal.md       ← added in MVP-AGENTS-5
```

---

## Commands Validated

```bash
# Project workspace — all 11 sections including Suggested PR
aeos ui project-workspace \
  --project ma-mairie-digitale \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --output /tmp/aeos-ui/ma-mairie-digitale-workspace.html

# Evidence pack — 9 files including pr-proposal.md
aeos ui evidence-pack \
  --project ma-mairie-digitale \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --output-dir /tmp/aeos-ui/ma-mairie-digitale-pack

# Full workspace demo — pr-proposal.md per project
aeos workspace demo \
  --output-dir /tmp/aeos-workspace-demo \
  --overwrite

# Standalone agent plan
aeos agent plan --project ma-mairie-digitale

# Standalone PR proposal
aeos agent pr-proposal --project ma-mairie-digitale
aeos agent pr-proposal --project ma-mairie-digitale --output /tmp/aeos-pr-proposal.md
aeos agent pr-proposal --project ma-mairie-digitale --json
```

---

## Real Validation — ma-mairie-digitale (2026-07-02)

### Workspace HTML — Suggested PR section

```
<h2>Suggested PR</h2>
Proposed title:
  security: validate RLS hardening and resolve 3 critical finding(s)
  for ma-mairie-digitale

Why this PR now:
  ! 3 critical finding(s) are blocking production deployment
  ! 15 SQL hardening block(s) are pending staging review and apply
  ! 59 important security/sovereignty finding(s) remain unaddressed
  ! 15 manual action(s) require explicit human decision and execution
  ! Project is NOT READY FOR PRODUCTION

read_only: true · applied: false · human validation required
No changes were applied. This is a proposal only.
```

### Evidence Pack — pr-proposal.md confirmed

```
/tmp/aeos-ui/ma-mairie-digitale-pack/pr-proposal.md
  → # AEOS PR Proposal
  → 14 sections including final statement
  → read_only: true · applied: false

Evidence pack file count: 9
  dashboard.html
  project-workspace.html
  recovery-summary.md
  risk-register.md
  human-gates.md
  next-actions.md
  agent-plan.md
  pr-proposal.md        ← new
  index.html
```

### Workspace Demo — pr-proposal.md confirmed

```
/tmp/aeos-workspace-demo/ma-mairie-digitale/evidence-pack/pr-proposal.md
```

### Invariants verified

| Invariant | Result |
|-----------|--------|
| `read_only: true` in all workspace surfaces | ✅ |
| `applied: false` in all workspace surfaces | ✅ |
| "No changes were applied" in HTML and Markdown | ✅ |
| Registry `~/.aeos/projects.json` mtime | ✅ Unchanged (Jul 1 23:37) |
| Client project files | ✅ Unchanged |
| No LLM reference in any generated output | ✅ |
| No network call | ✅ |
| No .env access | ✅ |

---

## How the Agentic Workspace Is Generated

All intelligence is computed locally by pure Python functions from `MemoryRecord`
JSON files. No external call is made at any stage.

```
MemoryRecord JSON files
       ↓
load_project_records(memory_dir, project_name)
       ↓
load_workspace_data(memory_dir, project_name)
  ├── _derive_production_readiness(last_record)
  ├── _derive_executive_summary(last_record, progress)
  ├── _derive_human_gates(last_record)
  ├── _derive_next_actions(last_record, readiness)
  ├── generate_project_entry(name, memory_dir)       ← agent planner
  └── generate_pr_proposal_from_memory(name, dir)   ← PR proposal
       ↓
render_workspace(ws_data)                 → HTML (11 sections)
generate_evidence_pack(memory_dir, ...)   → 9 files
```

---

## Safety Architecture

These guarantees are enforced in code, not by convention.

| Layer | Guarantee | How enforced |
|-------|-----------|--------------|
| `PRProposal` dataclass | `read_only=True` always | Python field default |
| `PRProposal` dataclass | `applied=False` always | Python field default |
| `PRProposal` dataclass | `human_validation_required=True` always | Python field default |
| `PRProposal` dataclass | Final statement always present | `field(default=...)` |
| `generate_pr_proposal_from_memory()` | No writes | Reads `MemoryRecord` JSON only |
| `render_workspace()` | No writes | Pure string builder |
| `generate_evidence_pack()` | Writes only to `output_dir` | All writes scoped to arg |
| Test suite | Safety verified on every commit | 1892 tests as of `9418b13` |

---

## Sprint History

| Sprint | Deliverable | PR | Commit |
|--------|-------------|-----|--------|
| MVP-AGENTS-1 | Local AI Assistant Policy | — | — |
| MVP-AGENTS-2 | `aeos agent plan` | #72 | `96ac91d` |
| MVP-AGENTS-3 | Agent Recommendations in Workspace | #73 | `fd16037` |
| MVP-AGENTS-4 | `aeos agent pr-proposal` | #74 | `2d8bb7c` |
| MVP-AGENTS-4A | Agent Workflow Evidence | #75 | `167f0f3` |
| MVP-AGENTS-5 | PR Proposal in Workspace | #76 | `dec1ac0` |
| MVP-AGENTS-5A | Agentic Workspace Evidence (this doc) | — | — |

---

## What the Workspace Does NOT Do

By design. These constraints are permanent and enforced in code.

- Apply any change autonomously
- Open a GitHub PR
- Call any LLM or AI API
- Make any network request
- Read `.env` files or environment secrets
- Write to the project source directory
- Write to `~/.aeos/projects.json`
- Modify existing `MemoryRecord` files
- Execute SQL against any database
- Deploy to staging or production

---

## Decision: Next Phase

**MVP-AGENTS-6 — Controlled PR Draft**

Before opening any PR automatically, AEOS will generate a local PR draft folder:

```
/tmp/aeos-pr-draft/<project>/
  ├── TITLE.txt           — proposed PR title (one line)
  ├── BODY.md             — full PR body with scope, checklist, safety
  ├── FILES-CANDIDATE.md  — files the PR would likely touch
  ├── CHECKLIST.md        — human approval checklist
  └── EVIDENCE-REFS.md    — evidence pack references
```

Generated by: `aeos agent pr-draft --project <name> --output-dir <path>`

Constraints unchanged: deterministic, local-only, read-only, no LLM, no GitHub API,
no autonomous apply. The human reviews the draft folder and creates the PR manually.
