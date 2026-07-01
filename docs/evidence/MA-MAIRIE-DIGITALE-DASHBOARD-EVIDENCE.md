# Sprint MVP-UI-1 — Evidence: ma-mairie-digitale Dashboard

**Date:** 2026-07-01
**Sprint:** MVP-UI-1
**AEOS commit:** `7777c98`
**Branch merged:** `ui/mvp-client-dashboard` → `main` (PR #53)
**Status:** COMPLETE

---

## Executive Summary

Sprint MVP-UI-1 delivered the first AEOS UI capability: a local-first static
HTML dashboard generated from audit MemoryRecords. The dashboard was run
against a real client project (`ma-mairie-digitale`) and produced a 9.6 KB
self-contained HTML file — no backend, no cloud, no secrets — showing the
full recovery timeline, risk deltas, synthesis trends, and recommended next
actions derived from 6 audit runs spanning 2 days.

This sprint proves that AEOS can present its own audit data as a readable
cockpit for a CTO or lead engineer without introducing any new dependencies,
network calls, or data exposure vectors.

---

## Real Project Context

| Field | Value |
|---|---|
| Client project | `ma-mairie-digitale` |
| Project path | `~/aeos-client-audits/ma-mairie-digitale` |
| Generator detected | `lovable` |
| Providers detected | `supabase` |
| Recovery status | `in_recovery` |
| Control level | `weak` (plateau) |
| Audit runs | 6 MemoryRecords |
| Memory directory | `/tmp/aeos-recovery-ma-mairie-digitale/memory` |

---

## Commands Used

**Generate MemoryRecords (run before this sprint):**

```sh
cd ~/Development/AEOS

uv run aeos reclaim harden \
  --path ~/aeos-client-audits/ma-mairie-digitale \
  --output /tmp/aeos-recovery-ma-mairie-digitale/harden-run.md \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory
```

**Generate the dashboard (Sprint MVP-UI-1):**

```sh
uv run aeos ui dashboard \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --project ma-mairie-digitale \
  --output /tmp/aeos-ui/ma-mairie-digitale.html
```

**CLI output:**

```
Dashboard:  /tmp/aeos-ui/ma-mairie-digitale.html
Project:    ma-mairie-digitale
Records:    6
Read-only — no files modified, no migration applied.
  read_only: true  ·  applied: false
```

---

## Evidence Produced

| Artifact | Location | Size |
|---|---|---|
| HTML dashboard | `/tmp/aeos-ui/ma-mairie-digitale.html` | 9.6 KB |
| Feature documentation | `docs/features/AEOS-UI-DASHBOARD.md` | in repo |
| Unit tests | `tests/unit/test_ui_dashboard.py` | 25 tests, all pass |
| CLI module | `src/aeos/ui/dashboard.py` | in repo |

The HTML file is local-only and not committed to the repository — it contains
no secrets, only counts and record IDs, but its path is `/tmp` by design.

---

## Memory Timeline Summary

Six audit runs were recorded across the recovery sprints. All show
`read_only: true · applied: false`.

| # | Date | Status | Control | Critical | Important | Manual | Gen SQL | Event |
|---|---|---|---|---|---|---|---|---|
| 1 | 2026-06-30 11:00 | ERROR | weak | 3 | 72 | 15 | 25 | Baseline |
| 2 | 2026-07-01 08:02 | ERROR | weak | 3 | 71 | 15 | 25 | PR #2 — governance baseline |
| 3 | 2026-07-01 11:58 | ERROR | weak | 3 | **59** | 15 | **15** | PR #4 — RLS hardening review |
| 4 | 2026-07-01 13:02 | ERROR | weak | 3 | 59 | 15 | 15 | PR #5 — quality gate baseline |
| 5 | 2026-07-01 13:19 | ERROR | weak | 3 | 59 | 15 | 15 | Measurement run |
| 6 | 2026-07-01 13:19 | ERROR | weak | 3 | 59 | 15 | 15 | Measurement run |

**Progression from baseline:**

| Metric | Baseline | Plateau | Delta |
|---|---|---|---|
| Important findings | 72 | 59 | −13 |
| Generatable SQL | 25 | 15 | −10 |
| Critical findings | 3 | 3 | 0 (intentional — SELECT policies deferred) |
| Manual actions | 15 | 15 | 0 (FOR ALL policy splits deferred) |

The 3 remaining critical findings correspond to intentional decisions:
- `§Decision-C1` — `budget_entries` SELECT left public (participatory portal)
- `§Decision-C2` — `budget_projets` SELECT left public (participatory portal)
- `§Note-archives-select` — `archives` SELECT scoping deferred

All documented in `docs/governance/RLS-HARDENING-REVIEW.md` in the client repo.

---

## What the Dashboard Shows

The generated HTML dashboard (`ma-mairie-digitale.html`) contains:

**Current Status section** — KV metrics from the latest record:
- Status: ERROR
- Control level: weak
- Critical: 3 | Important: 59 | Manual: 15 | Gen SQL: 15
- Generator: lovable | Providers: supabase
- 5 strategic exit options (text labels, no secret values)

**Memory Timeline table** — all 6 records with:
- Absolute counts per column
- Delta indicators vs previous record (green = improvement, red = regression)
- Latest row highlighted

**Synthesis section** — cross-record trend analysis:
- Overall: unchanged (status stayed ERROR across all runs — expected at this stage)
- Important: ↑ improved (72 → 59)
- Critical: → unchanged
- Manual: → unchanged
- Generated: ↑ improved (25 → 15)

**Recommended Next Actions** — derived from last record findings:
1. `[CRITICAL]` Review and address 3 critical risk(s) — priority before deployment
2. `[GENERATED]` Apply 15 auto-generated SQL blocks to staging (human approval required)
3. `[MANUAL]` Complete 15 manual review actions
4. `[PLAN]` Follow the 5-phase remediation plan

**Footer** — `read_only: true · applied: false · human validation required`

---

## What This Proves for AEOS

1. **AEOS can render its own audit data as a readable cockpit.** A CTO or lead
   engineer can open a single HTML file and immediately see where a project
   stands — no dashboard service, no login, no cloud dependency.

2. **MemoryRecords are a sufficient data source.** The 6 JSON files in
   `/tmp/memory/` contain enough structured signal (counts, status, trends,
   options) to drive a useful view without re-running the audit.

3. **Delta tracking over time is visible without a database.** The timeline
   table makes recovery progress (or absence of it) immediately legible —
   `−13 important` and `−10 gen SQL` from PR #4 are visible at a glance.

4. **The local-first principle holds at the UI layer.** The command runs
   offline, writes one file, reads no `.env`, touches no network.

5. **The recovery story is explainable to a non-technical stakeholder.** The
   dashboard is readable as a status report, not just a developer tool.

---

## Current Limitations

| Limitation | Impact | Tracked in |
|---|---|---|
| No browser open shortcut (`--open`) | Minor friction | MVP-UI-2 backlog |
| Synthesis requires ≥ 2 records | Records 5 and 6 are redundant noise | Measurement hygiene |
| No per-record drill-down | Can't see finding details from the dashboard | MVP-UI-2 |
| No progress bar (baseline → target) | Recovery trajectory not visible | MVP-UI-2 |
| HTML only, no print/PDF | Sharing to non-technical stakeholders requires a browser | MVP-UI-2 backlog |
| Records 5 and 6 are duplicates | Output file conflict during a session caused a spurious run | Operational note |

---

## Decision for MVP-UI-2

**MVP-UI-2: Project Workspace**

The next sprint will move from a flat timeline view to a structured **project
workspace** — a richer single-page document centered on one project's full
recovery picture.

**Scope for MVP-UI-2:**

| Section | Content |
|---|---|
| Project Overview | name, generator, providers, path, recovery status, AEOS version |
| Recovery Status | control level, status badge, phase position on the recovery stage model |
| Risk Breakdown | critical / important / manual / generatable — with category labels |
| Timeline | same as MVP-UI-1 + expandable row detail |
| Evidence Links | links to governance docs present in the client repo |
| Recommended Actions | prioritized, tagged, with concrete commands |
| Human Gates | explicit list of what requires human approval before proceeding |

**Driving principle:** the workspace is a handoff document — something a CTO
can read before a decision, not just a developer debugging view.

**Input source:** same MemoryRecords + optional `--project-path` to read
governance doc presence directly from the client repo (read-only).

**Command target:**

```sh
aeos ui workspace \
  --memory-dir <dir> \
  --project <name> \
  --project-path <path/to/client/repo> \
  --output <path/to/workspace.html>
```
