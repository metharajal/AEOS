# AEOS Agent Workflow Evidence

**Sprint:** MVP-AGENTS-4A
**Date:** 2026-07-02
**Branch at validation:** main @ `b8d396a`
**Project tested:** ma-mairie-digitale
**Status:** PASSED

---

## Executive Summary

AEOS now operates a complete deterministic agent workflow: it analyses project risk,
surfaces recommendations in every workspace surface, and generates a structured PR
proposal — all locally, without any LLM, without any network call, without modifying
any file in the client project or the local registry.

Four agent sprints were delivered and merged between MVP-AGENTS-1 and MVP-AGENTS-4.
This document records the validated state of the full chain as of `main @ b8d396a`.

---

## Agent Workflow Delivered

| Sprint | Command / Feature | Status |
|--------|-------------------|--------|
| MVP-AGENTS-1 | Local AI Assistant Policy (`docs/AI-DEVELOPMENT-POLICY.md`) | ✅ SHIPPED |
| MVP-AGENTS-2 | `aeos agent plan` — deterministic risk planner | ✅ SHIPPED — PR #72 |
| MVP-AGENTS-3 | Agent Recommendations in Workspace + Evidence Pack | ✅ SHIPPED — PR #73 |
| MVP-AGENTS-4 | `aeos agent pr-proposal` — PR proposal generator | ✅ SHIPPED — PR #74 |

---

## Commands Validated

```bash
# Agent risk plan — terminal summary
aeos agent plan --project ma-mairie-digitale

# Agent risk plan — JSON output
aeos agent plan --project ma-mairie-digitale --json

# Agent risk plan — Markdown file
aeos agent plan --project ma-mairie-digitale --output /tmp/aeos-agent-plan.md

# PR proposal — terminal summary
aeos agent pr-proposal --project ma-mairie-digitale

# PR proposal — full Markdown file
aeos agent pr-proposal --project ma-mairie-digitale --output /tmp/aeos-pr-proposal.md

# PR proposal — JSON
aeos agent pr-proposal --project ma-mairie-digitale --json

# Workspace with Agent Recommendations section
aeos ui project-workspace --project ma-mairie-digitale --memory-dir <path> --output /tmp/ws.html

# Evidence pack with agent-plan.md
aeos ui evidence-pack --memory-dir <path> --project ma-mairie-digitale --output-dir /tmp/ep

# Full demo — generates agent-plan.md per project automatically
aeos workspace demo --output-dir /tmp/aeos-workspace-demo --overwrite
```

---

## Real Validation — ma-mairie-digitale

Smoke tests executed on `2026-07-02` against the registered project `ma-mairie-digitale`.

### aeos agent plan

```
AEOS Agent Plan

Mode:    deterministic read-only planner
Project: ma-mairie-digitale
Status:  WARNING
Records: 6  (MemoryRecords read from ~/.aeos memory dir)

  critical    3
  important  59
  manual     15
  sql_blocks 15

  read_only: true  ·  applied: false
  No changes were applied. This is a proposal only.
```

### aeos agent pr-proposal

```
AEOS PR Proposal

Mode:     deterministic read-only planner
Project:  ma-mairie-digitale
Generated: 2026-07-02T09:03:10Z
Records:  6
Findings: critical=3  important=59  sql_blocks=15

  Title:  security: validate RLS hardening and resolve 3 critical finding(s)
          for ma-mairie-digitale

  Why now:
    ! 3 critical finding(s) are blocking production deployment
    ! 15 SQL hardening block(s) are pending staging review and apply
    ! 59 important security/sovereignty finding(s) remain unaddressed
    ! 15 manual action(s) require explicit human decision and execution
    ! Project is NOT READY FOR PRODUCTION

  Recommended scope:
    1. Review and document each of the 3 critical finding(s)
    2. Review and apply 15 SQL hardening block(s) to staging — NOT production
    3. Validate RLS policies on staging
    4. Complete 15 manual action(s) as listed in the AEOS hardening report
    ... and 3 more — see --output for full proposal

  Validation commands:
    → git status
    → aeos agent plan --project ma-mairie-digitale
    → aeos reclaim harden --path <project-path> --json

  read_only: true  ·  applied: false  ·  human validation required
  No changes were applied. This is a proposal only.
```

### Invariants verified

| Invariant | Result |
|-----------|--------|
| `read_only: true` in all output modes | ✅ |
| `applied: false` in all output modes | ✅ |
| Final statement present | ✅ "No changes were applied. This is a proposal only." |
| Registry `~/.aeos/projects.json` mtime | ✅ Unchanged (Jul 1 — not touched by Jul 2 smoke tests) |
| Client project files | ✅ Unchanged — `git status` clean |
| No LLM call | ✅ Pure Python rules engine |
| No network call | ✅ Local file I/O only |
| No .env read | ✅ |

---

## What the Planner Does

`aeos agent plan` is a deterministic risk analyser. It reads `~/.aeos/projects.json`
and the associated `MemoryRecord` JSON files. From those, it computes:

- **Status** — `OK`, `WARNING`, or `CRITICAL` based on finding counts
- **Blockers** — reasons why a project cannot go to production
- **Recommended actions** — prioritised list derived from findings (critical → generated SQL → important → manual → docs)
- **ProjectPlanEntry** — a typed dataclass consumed by the workspace and evidence pack

No model. No prompt. No API key. No inference. Every output is a pure function of
the local record state.

---

## What the PR Proposal Generator Does

`aeos agent pr-proposal` converts the planner's analysis into a structured 14-section
PR proposal. Decision rules (priority cascade):

| Priority | Condition | Title prefix |
|----------|-----------|--------------|
| 1 | `critical > 0` | `security: validate RLS hardening and resolve N critical finding(s)` |
| 2 | `generated > 0` | `security: stage N SQL hardening block(s) and validate on staging` |
| 3 | `important > 0` | `security: address N important finding(s) and staging validation` |
| 4 | `control_level == "weak"` | `governance: strengthen project control and document sovereignty policy` |
| 5 | not production-ready | `security: resolve remaining production blockers` |
| 6 | all OK | `docs: release readiness review` |

Each section is filled by a dedicated `_build_*` function. No shared mutable state.
Every output is a typed `PRProposal` dataclass. Three renderers: terminal summary,
Markdown (14 sections), JSON.

---

## How Recommendations Appear in the Workspace

`aeos ui project-workspace` now renders an **Agent Recommendations** section between
Executive Summary and Production Readiness:

- **Plan status** — OK / WARNING / CRITICAL badge
- **Blockers** — bulleted list from the planner
- **Recommended actions** — numbered, priority-ordered
- **Finding counts** — critical / important / manual / sql_blocks

`aeos ui evidence-pack` now includes `agent-plan.md` as the 8th file in every pack.
`aeos workspace demo` generates `agent-plan.md` for each registered project automatically
(no code change needed — it calls `generate_evidence_pack()` which picks up the new file).

---

## Safety Guarantees

These are enforced in code and verified by the test suite (1863 tests as of `b8d396a`):

| Guarantee | Enforcement |
|-----------|-------------|
| `read_only: true` always | Hardcoded field default in `PRProposal` dataclass |
| `applied: false` always | Hardcoded field default in `PRProposal` dataclass |
| `human_validation_required: true` always | Hardcoded field default |
| Final statement always present | `field(default="No changes were applied. This is a proposal only.")` |
| Registry never written | `generate_pr_proposal()` opens registry read-only; `test_does_not_modify_registry` verifies mtime |
| Memory dir never written | `load_project_records()` is read-only; `test_does_not_modify_memory_dir` verifies file set |
| No LLM in any field | `test_no_llm_in_title` checks for "claude", "openai", "gpt" |
| Production always in `out_of_scope` | `_OUT_OF_SCOPE_ALWAYS` constant, verified by test |
| No .env read | No `os.environ` access in agent module |
| No network call | No `requests`, `httpx`, `urllib` import in agent module |

---

## What Agents Still Cannot Do

By design. These constraints are permanent.

- Apply any change autonomously — every action requires explicit human sign-off
- Read or write `.env` files
- Contact any database (Supabase or otherwise)
- Apply any SQL migration
- Push to any remote repository
- Modify existing MemoryRecords
- Create or overwrite client project files
- Rotate credentials
- Deploy to production
- Call any external AI API

---

## Product Value Proven

Before this sprint series, AEOS could diagnose and report. After:

| Capability | Before | After |
|-----------|--------|-------|
| Risk analysis from local records | ✗ | ✅ `aeos agent plan` |
| Recommendations in workspace HTML | ✗ | ✅ Agent Recommendations section |
| `agent-plan.md` in evidence packs | ✗ | ✅ 8th file in every pack |
| Structured PR proposal (14 sections) | ✗ | ✅ `aeos agent pr-proposal` |
| Title matched to actual risk level | ✗ | ✅ Decision cascade |
| Machine-readable JSON output | ✗ | ✅ `--json` flag on both commands |
| Full Markdown proposal file | ✗ | ✅ `--output` flag |

AEOS now closes the loop from diagnosis to action proposal. The agent proposes.
The human decides. Nothing is applied without explicit sign-off.

---

## Current Limitations

| Limitation | Notes |
|-----------|-------|
| PR proposal not yet in Workspace HTML | Planned: MVP-AGENTS-5 |
| `pr-proposal.md` not yet in evidence packs | Planned: MVP-AGENTS-5 |
| No multi-project plan aggregation | Single project per command |
| No historical trend comparison across records | Records read as flat list, not time-series |
| No automatic PR creation | By design — human creates the PR from the proposal |

---

## Decision: Next Phase

**MVP-AGENTS-5 — PR Proposal in Workspace**

Integrate the PR proposal into every workspace surface, mirroring how MVP-AGENTS-3
integrated the agent plan:

| Surface | Change |
|---------|--------|
| `aeos ui project-workspace` | Add "Suggested PR" section after Agent Recommendations |
| `aeos ui evidence-pack` | Add `pr-proposal.md` as 9th file in every pack |
| `aeos workspace demo` | Auto-generates `pr-proposal.md` per project (no extra code if evidence-pack is updated) |

Constraints unchanged: deterministic, read-only, no LLM, no network, no mutation.

The pattern is now established and proven across two sprints (MVP-AGENTS-2→3,
MVP-AGENTS-3→4). MVP-AGENTS-5 follows the same path.
