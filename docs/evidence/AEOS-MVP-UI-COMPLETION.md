# AEOS MVP UI — Completion Record

**Date:** 2026-07-01
**Commit:** `8804c1a`
**Branch:** `main`
**Status:** COMPLETE

---

## Executive Summary

The AEOS MVP UI cycle delivered three local-first static UI commands in three
consecutive sprints, all merged to `main` with full quality gates. Starting
from zero UI capability, AEOS can now produce — from a directory of JSON
MemoryRecords and a single command — a complete evidence dossier for a
recovered software project: a technical audit cockpit, an executive decision
workspace, and a seven-file evidence pack ready for CTO handoff or governance
archive.

All three commands run offline, produce no side effects, read no secrets, and
write exactly what they say they will write — nothing else.

This document closes the MVP UI cycle and records what was built, validated,
and decided.

---

## Commands Delivered

| Command | PR | Commit | Sprint |
|---------|----|--------|--------|
| `aeos ui dashboard` | #53 | `2e18d96` | MVP-UI-1 |
| `aeos ui project-workspace` | #55 | `fbc7f53` | MVP-UI-2 |
| `aeos ui evidence-pack` | #56 | `3f4626b` | MVP-UI-3 |

All three commands are sub-commands of `aeos ui`, registered under a single
`ui_app` Typer group in `src/aeos/cli.py`. Each follows the same invocation
pattern:

```sh
aeos ui <command> \
  --memory-dir <path/to/memory> \
  --project    <project-name> \
  --output     <path/to/output>   # or --output-dir for evidence-pack
```

---

## What Each Command Produces

### `aeos ui dashboard`

A single self-contained HTML file (≈ 10 KB). Audience: lead engineer or CTO
reviewing the raw audit timeline.

Sections:
- Current status (KV metrics from the latest MemoryRecord)
- Memory timeline table (all records with per-column delta indicators)
- Synthesis trends (improved / degraded / unchanged per metric)
- Recommended next actions (derived from last record findings)
- Footer: `read_only: true · applied: false · human validation required`

### `aeos ui project-workspace`

A single self-contained HTML file (≈ 10 KB). Audience: CTO, DSI, or founder
before a deployment or governance decision.

Sections (9):
1. Project Overview — status, control level, generator, providers, last audit
2. Executive Summary — plain-language narrative derived from findings
3. Production Readiness — binary READY / NOT READY verdict + blocking reasons
4. Recovery Progress — before/after comparison table with delta indicators
5. Completed Recovery Work — measurable improvements with date range
6. Human Gates — checklist of approvals required before proceeding
7. Risk Register — categorised risk counts with severity and notes
8. Evidence — MemoryRecord metadata (first/last record IDs, flags)
9. Next Recommended Actions — ordered list of concrete next steps

### `aeos ui evidence-pack`

A directory of 7 files (≈ 29 KB total). Audience: CTO handoff, governance
archive, or pre-production sign-off dossier.

| File | Format | Content |
|------|--------|---------|
| `index.html` | HTML | Entry point — verdict badge, metrics, links to all files |
| `dashboard.html` | HTML | Full technical audit timeline (reuses dashboard renderer) |
| `project-workspace.html` | HTML | Full executive workspace (reuses workspace renderer) |
| `recovery-summary.md` | Markdown | Narrative: baseline → current, production verdict |
| `risk-register.md` | Markdown | Risk table: categories, counts, severity, action notes |
| `human-gates.md` | Markdown | Sign-off checklist: one section per gate with date/name fields |
| `next-actions.md` | Markdown | Ordered actions with assignment and target date fields |

---

## Real Validation — ma-mairie-digitale

All three commands were run against a real client project using 6 MemoryRecords
generated during the active recovery sprint (`aeos reclaim harden`).

**Project profile:**

| Field | Value |
|-------|-------|
| Project | `ma-mairie-digitale` |
| Generator | `lovable` |
| Providers | `supabase` |
| Control level | `weak` |
| Audit records | 6 |
| Period | 2026-06-30 → 2026-07-01 |
| Memory directory | `/tmp/aeos-recovery-ma-mairie-digitale/memory` |

**Findings at closure:**

| Metric | Baseline | Current | Delta |
|--------|----------|---------|-------|
| Critical findings | 3 | 3 | 0 (intentional — public budget SELECT deferred) |
| Important findings | 72 | 59 | −13 |
| Manual actions | 15 | 15 | 0 (FOR ALL policy splits deferred) |
| Generatable SQL blocks | 25 | 15 | −10 |

**Verdict:** NOT READY FOR PRODUCTION

**Commands run:**

```sh
uv run aeos ui dashboard \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --project ma-mairie-digitale \
  --output /tmp/aeos-ui/ma-mairie-digitale.html

uv run aeos ui project-workspace \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --project ma-mairie-digitale \
  --output /tmp/aeos-ui/ma-mairie-digitale-workspace.html

uv run aeos ui evidence-pack \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --project ma-mairie-digitale \
  --output-dir /tmp/aeos-ui/ma-mairie-digitale-pack
```

All three commands completed with exit code 0. Output files were inspected
manually in a browser. No secrets present. No files modified in the client
repo or memory directory.

---

## Product Value Proven

**1. AEOS can render its own audit data as readable artifacts.**

A CTO can receive a single HTML file or a seven-file folder and immediately
understand where a project stands — no dashboard service, no login, no cloud
dependency, no second system to maintain.

**2. MemoryRecords are a sufficient data source for multi-format output.**

Six JSON files on disk, each ≈ 1 KB, are enough to drive a technical cockpit,
an executive decision document, and a complete evidence pack. No database. No
rerun of the audit. No network.

**3. Recovery progress is legible without a database.**

The timeline table and before/after comparison table make progress (or the
absence of it) immediately visible. `−13 important` and `−10 gen SQL` over two
days of recovery work are visible at a glance without scrolling or querying.

**4. A binary production verdict is derivable from structured metadata.**

`critical > 0`, `generated > 0`, `manual > 0`, and `control_level == "weak"`
are sufficient signals to produce a READY / NOT READY verdict with concrete
blocking reasons — without human interpretation or AI inference.

**5. Human gates can be made explicit and signable from MemoryRecords.**

The `human-gates.md` output is a ready-to-fill sign-off checklist derived
entirely from `providers`, `findings_summary`, and `control_level`. A CTO can
print it, fill it, and archive it as governance evidence.

**6. The local-first principle holds at the UI layer.**

Three commands, zero network calls, zero AI inference, zero secrets read,
zero side effects. Each command is idempotent and reversible (output files can
be deleted without consequence).

**7. The recovery story is explainable to a non-technical stakeholder.**

The evidence pack is readable as a handoff dossier by a founder, a compliance
officer, or a DSI who has never seen the codebase — not just by the engineer
who ran the audit.

---

## Safety Guarantees

All three commands unconditionally guarantee:

| Guarantee | Mechanism |
|-----------|-----------|
| No secrets in output | MemoryRecords contain only counts and metadata — never `.env` values or credentials |
| No project mutation | Commands write only to `--output` / `--output-dir` paths, never to the project directory |
| No MemoryRecord mutation | Record files are opened read-only via `load_project_records` |
| No network calls | Zero HTTP, zero DNS, zero socket — pure local file I/O |
| No AI inference | All derivation is deterministic Python logic — no external model calls |
| No migration applied | `applied: false` on every record; no SQL is executed |
| Overwrite protection | `--overwrite` flag required to replace existing output; default is a clean error |
| Human validation required | Every generated page and file carries the `human validation required` footer |

These guarantees are enforced by the MemoryRecord data model (`read_only: true`,
`applied: false`) and verified by unit tests that assert no secret tokens appear
in rendered output.

---

## Current Limitations

| Limitation | Impact | Planned in |
|------------|--------|------------|
| No `--open` flag | Manual browser open required after generation | MVP-UI-4 backlog |
| HTML only — no PDF export | Sharing to non-browser contexts requires a browser | MVP-UI-4 backlog |
| No per-record drill-down in dashboard | Can't expand a row to see finding details | MVP-UI-4 backlog |
| Evidence pack is loose files, no zip | Sharing requires manual archiving | MVP-UI-4 backlog |
| No portfolio view (single project only) | Can't compare multiple recovered projects side by side | MVP-UI-4 |
| No timestamp in output filenames | Multiple runs overwrite unless `--overwrite` or different paths used | Operational |
| Synthesis requires ≥ 2 records | Single-record projects show `insufficient_data` trends | By design |
| Static HTML — no interactivity | No search, sort, or filter in the browser | By design |

---

## Decision: Next Sprint is MVP-UI-4 Portfolio

With three single-project UI commands stable on `main`, the natural next
capability is a **portfolio view** — a single page that shows multiple
recovered projects side by side.

**Command target:**

```sh
aeos ui portfolio \
  --memory-dirs /tmp/proj-a/memory,/tmp/proj-b/memory \
  --projects proj-a,proj-b \
  --output /tmp/aeos-ui/portfolio.html
```

**Sections:**

| Section | Content |
|---------|---------|
| Portfolio Summary | Total projects, projects ready, projects not ready |
| Project Cards | One card per project: verdict badge, key metrics, last audit date |
| Comparative Risk Table | All projects × risk categories — side by side |
| Aggregate Human Gates | Consolidated gate list across all projects |
| Per-project links | Links to individual evidence packs if generated |

**Why now:**

AEOS is designed to operate across a portfolio of client projects. The
MemoryRecord schema is already project-namespaced. A portfolio view requires
no new data model — only a new loader (`load_multiple_projects`) and a new
renderer. The three existing renderers and derivation logic are reused
unchanged.

**Driving constraint:** the portfolio view must remain local-first. It reads
N memory directories, produces one HTML file, makes zero network calls — same
guarantees as MVP-UI-1 through MVP-UI-3.

---

## Closing Statement

Three sprints. Three commands. Three PRs. 1644 tests passing. Zero regressions.
Zero secrets. Zero network.

AEOS now has a complete local-first UI layer: from raw audit timeline to
executive decision workspace to handoff evidence pack. Every artifact is derived
from the same structured MemoryRecords, produced in seconds, and readable
without any server, login, or cloud service.

The MVP UI cycle is closed.

---

*read_only: true · applied: false · human validation required*
