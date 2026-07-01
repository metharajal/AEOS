# AEOS UI: Evidence Pack

**Command:** `aeos ui evidence-pack`
**Sprint:** MVP-UI-3
**Status:** SHIPPED

---

## Overview

`aeos ui evidence-pack` generates a complete multi-file evidence bundle from
local MemoryRecords. Where `aeos ui dashboard` shows a technical audit timeline
and `aeos ui project-workspace` provides an executive decision view, the evidence
pack combines both into a structured folder that can be shared, archived, or used
as a handoff dossier before a production decision.

All 7 files are generated from the same MemoryRecords — no network, no AI, no
secrets, no backend.

---

## Usage

```sh
aeos ui evidence-pack \
  --memory-dir /tmp/aeos-recovery-<project>/memory \
  --project <project-name> \
  --output-dir /tmp/aeos-ui/<project>-pack
```

### Options

| Flag | Required | Description |
|------|----------|-------------|
| `--memory-dir` | Yes | Path to directory containing local `*.json` MemoryRecord files |
| `--project` | Yes | Project name — used to filter records from the memory directory |
| `--output-dir` | Yes | Output directory — created with parent directories if needed |
| `--overwrite` | No | Overwrite an existing non-empty output directory (default: error if non-empty) |

### Example output

```
Pack:       /tmp/aeos-ui/ma-mairie-digitale-pack
Project:    ma-mairie-digitale
Records:    6
Verdict:    NOT READY FOR PRODUCTION
Files:      7
  index.html
  dashboard.html
  project-workspace.html
  recovery-summary.md
  risk-register.md
  human-gates.md
  next-actions.md
Read-only — no files modified, no migration applied.
  read_only: true  ·  applied: false
```

---

## Pack Contents

| File | Format | Content |
|------|--------|---------|
| `index.html` | HTML | Entry point — global verdict, metrics, links to all files |
| `dashboard.html` | HTML | Technical audit timeline — all records, deltas, synthesis trends |
| `project-workspace.html` | HTML | Executive workspace — verdict, gates, risk register, next actions |
| `recovery-summary.md` | Markdown | Narrative recovery summary — baseline vs current, production verdict |
| `risk-register.md` | Markdown | Risk register — categorised findings with severity and action notes |
| `human-gates.md` | Markdown | Human validation gates — sign-off checklist before production |
| `next-actions.md` | Markdown | Next recommended actions — ordered with assignment fields |

---

## File Details

### `index.html`

Entry point for the pack. Shows:
- Global production verdict (READY / NOT READY) — large badge
- Key metrics (records, period, critical count, important count)
- Linked table of all pack files with descriptions

### `dashboard.html`

Reuses `aeos ui dashboard` output verbatim — technical cockpit for lead engineers.
Includes full memory timeline, delta indicators, and synthesis trends.

### `project-workspace.html`

Reuses `aeos ui project-workspace` output verbatim — decision-ready document for
CTOs, DSIs, and founders. Includes all 9 sections: overview, summary, production
readiness, recovery progress, completed work, human gates, risk register, evidence,
next actions.

### `recovery-summary.md`

Narrative markdown with:
- Executive summary (plain language)
- Baseline vs current state (comparison table)
- Production verdict + blocking reasons

### `risk-register.md`

Markdown table with all four risk categories:
- Critical findings (HIGH severity — blocks production)
- Important findings (MEDIUM — staged remediation)
- Manual actions (MEDIUM — require human decision)
- Generatable SQL blocks (LOW — require review before applying)

### `human-gates.md`

One section per human gate, each with empty sign-off fields:
```
## Gate 1
○ Rotate Supabase service_role and anon keys — verify no credential exposure in git history

- [ ] Validated by:
- [ ] Date:
- [ ] Notes:
```

### `next-actions.md`

One section per recommended action, each with assignment fields:
```
### Action 1
Review and apply N auto-generated SQL remediation block(s) to staging ...

- [ ] Assigned to:
- [ ] Target date:
- [ ] Done:
```

---

## Code Architecture

The pack reuses existing UI modules without modification:

| Module | Role |
|--------|------|
| `aeos.ui.dashboard` | Provides `load_dashboard_data` + `render_dashboard` for `dashboard.html` |
| `aeos.ui.workspace` | Provides `load_workspace_data` + `render_workspace` for `project-workspace.html` and all markdown derivation |
| `aeos.ui.evidence_pack` | New — markdown renderers, `render_index`, `generate_evidence_pack` |

`WorkspaceData` is loaded once and reused for the workspace HTML, all 4 markdown
files, and the index page. `DashboardData` is loaded separately for `dashboard.html`.

---

## Design Constraints

| Constraint | Implementation |
|------------|---------------|
| Read-only | Never writes to project directory or MemoryRecord files |
| No network | Zero HTTP calls — pure local file I/O |
| No AI | All derivation is deterministic Python logic |
| No secrets | MemoryRecords contain only counts and metadata — no `.env` values |
| No backend | Self-contained static files — no server required |
| Non-destructive | Errors if output directory is non-empty without `--overwrite` |

---

## Relationship to Other UI Commands

| Command | Output | Files | Audience |
|---------|--------|-------|----------|
| `aeos ui dashboard` | Single HTML | 1 | Lead engineer / audit view |
| `aeos ui project-workspace` | Single HTML | 1 | CTO / DSI / founder decision |
| `aeos ui evidence-pack` | Directory | 7 | Handoff dossier / archive |

All three commands read the same MemoryRecords and can be run together.

---

## Read-Only Guarantee

Every generated file carries the footer:
```
read_only: true  ·  applied: false  ·  human validation required
```

The command:
- Does not read any `.env` files
- Does not modify any MemoryRecord files
- Does not contact any database or external service
- Does not apply any SQL migration
- Does not call any external AI model
