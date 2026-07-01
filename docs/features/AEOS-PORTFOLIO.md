# AEOS UI: Portfolio

**Command:** `aeos ui portfolio`
**Sprint:** MVP-UI-4
**Status:** SHIPPED

---

## Overview

`aeos ui portfolio` generates a single static HTML page that lists all projects
found in a memory directory. It is designed as the entry point for a CTO or
technical director managing multiple recovered or monitored software projects —
a cockpit that surfaces the production readiness verdict, key risk metrics, and
recommended next action for each project at a glance.

---

## Usage

```sh
aeos ui portfolio \
  --memory-dir /tmp/aeos-recovery-<project>/memory \
  --output /tmp/aeos-ui/index.html
```

### Options

| Flag | Required | Description |
|------|----------|-------------|
| `--memory-dir` | Yes | Directory containing local `*.json` MemoryRecord files |
| `--output` / `-o` | Yes | Output HTML file path — parent directories created if needed |
| `--overwrite` | No | Overwrite an existing output file (default: error if exists) |

### Example output

```
Portfolio:  /tmp/aeos-ui/index.html
Projects:   1
  ma-mairie-digitale  →  NOT READY FOR PRODUCTION
Read-only — no files modified, no migration applied.
  read_only: true  ·  applied: false
```

---

## What the Portfolio Page Shows

The generated page shows one card per project found in the memory directory.

Each project card displays:

| Field | Source |
|-------|--------|
| Project name | `MemoryRecord.project_name` |
| Status | `last_record.status` |
| Control level | `last_record.control_level` |
| Generator | `last_record.generator` |
| Providers | `last_record.providers` |
| Last record date | `last_record.created_at[:10]` |
| Critical findings | `findings_summary["critical"]` |
| Important findings | `findings_summary["important"]` |
| Manual actions | `findings_summary["manual"]` |
| Generatable SQL blocks | `findings_summary["generated"]` |
| Production verdict | Derived: READY / NOT READY + reasons |
| Recommended next action | Derived from findings + providers |
| Audit record count | Count of records for this project |

Each card also includes three conventional relative links:

| Link label | Relative path |
|------------|--------------|
| Dashboard | `{project-name}/dashboard.html` |
| Workspace | `{project-name}/project-workspace.html` |
| Evidence Pack | `{project-name}/evidence-pack/index.html` |

These links assume the AEOS output convention described below.

---

## Output Convention for Links

The portfolio page is designed to sit at the root of an AEOS UI output
directory. The conventional layout is:

```
/tmp/aeos-ui/
  index.html                          ← portfolio (this file)
  {project-name}/
    dashboard.html                    ← aeos ui dashboard output
    project-workspace.html            ← aeos ui project-workspace output
    evidence-pack/
      index.html                      ← aeos ui evidence-pack output
      dashboard.html
      project-workspace.html
      recovery-summary.md
      risk-register.md
      human-gates.md
      next-actions.md
```

If the linked files have not been generated yet, the links are still rendered
but will return a 404 in the browser. They are intentional forward references.

---

## Project Auto-Detection

The portfolio command scans the `--memory-dir` for all `*.json` files and
automatically discovers the unique project names present. No `--project` flag
is required.

This makes it easy to generate a portfolio from a shared memory directory that
receives records from multiple projects:

```sh
# After running harden for proj-a and proj-b into the same memory dir:
aeos ui portfolio \
  --memory-dir /tmp/aeos-recovery/memory \
  --output /tmp/aeos-ui/index.html
```

The resulting page will show one card for `proj-a` and one for `proj-b`,
sorted alphabetically.

---

## Production Readiness Derivation

The verdict for each project is derived from the **latest** MemoryRecord:

```
NOT READY FOR PRODUCTION if any of:
  - critical > 0
  - generated > 0   (SQL blocks not yet applied to staging)
  - manual > 0      (actions pending human review)
  - control_level == "weak"
```

Blocking reasons are listed per project card.

---

## Design

| Property | Value |
|----------|-------|
| Format | Self-contained HTML, embedded CSS |
| Layout | Card grid — one card per project, responsive columns |
| Theme | Dark cockpit (`#0d1117` background, monospace font) |
| Max width | Fluid grid (min 420px per column) |
| JavaScript | None |
| Framework | None |

---

## Future: Multiple Memory Directories

The underlying `load_portfolio_data(memory_dirs: list[Path])` function already
accepts multiple directories. A future CLI extension will expose this:

```sh
# MVP-UI-5 target (not yet implemented):
aeos ui portfolio \
  --memory-dir /tmp/proj-a/memory \
  --memory-dir /tmp/proj-b/memory \
  --output /tmp/aeos-ui/index.html
```

Project names are deduplicated across directories — the first directory
encountered wins for any given project name.

---

## Design Constraints

| Constraint | Implementation |
|------------|---------------|
| Read-only | Never writes to project directory or MemoryRecord files |
| No network | Zero HTTP calls — pure local file I/O |
| No AI | All derivation is deterministic Python logic |
| No secrets | MemoryRecords contain only counts and metadata |
| No backend | One self-contained HTML file |
| Static | No JavaScript required |

---

## Read-Only Guarantee

The command:
- Does not read any `.env` files
- Does not modify any MemoryRecord files
- Does not contact any database or external service
- Does not apply any SQL migration
- Does not call any external AI model

Every generated page carries the footer:
```
read_only: true  ·  applied: false  ·  human validation required
```

---

## Relationship to Other UI Commands

| Command | Output | Audience |
|---------|--------|----------|
| `aeos ui portfolio` | Single HTML — all projects | CTO portfolio overview |
| `aeos ui dashboard` | Single HTML — one project | Lead engineer audit view |
| `aeos ui project-workspace` | Single HTML — one project | Decision briefing |
| `aeos ui evidence-pack` | Directory — one project | Handoff dossier / archive |
