# AEOS UI Dashboard

**Sprint:** MVP-UI-1
**Status:** implemented
**Module:** `src/aeos/ui/dashboard.py`
**Command:** `aeos ui dashboard`

---

## What it does

Generates a static HTML dashboard from a local memory directory. The dashboard
shows the full recovery timeline of a reclaimed project — statuses, finding
counts, deltas, synthesis trends, and recommended next actions — in a
cockpit-style read-only view.

**No network. No AI. No database. No secrets. No .env.**

---

## Command

```sh
aeos ui dashboard \
  --memory-dir <path/to/memory> \
  --project <project-name> \
  --output <path/to/dashboard.html>
```

### Options

| Flag | Required | Description |
|---|---|---|
| `--memory-dir` | yes | Directory containing local `.json` MemoryRecord files |
| `--project` | yes | Project name (must match the subdirectory in `--memory-dir`) |
| `--output` | yes | Path to write the HTML file |
| `--overwrite` | no | Replace output file if it already exists |

### Example

```sh
aeos ui dashboard \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --project ma-mairie-digitale \
  --output /tmp/aeos-ui/ma-mairie-digitale.html
```

Then open `/tmp/aeos-ui/ma-mairie-digitale.html` in any browser.

---

## Dashboard sections

| Section | Content |
|---|---|
| **Current Status** | Key metrics from latest record: status, control level, critical / important / manual / gen SQL counts, generator, providers, strategic exit options |
| **Memory Timeline** | All records in chronological order with delta indicators (↑ green / ↓ red vs previous row) |
| **Synthesis** | Overall trend across all records: overall, critical, important, manual, gen SQL — requires ≥ 2 records |
| **Recommended Next Actions** | Derived from latest record findings: CRITICAL, GENERATED, MANUAL, PLAN tags |
| **Footer** | Generation metadata, read_only / applied=false / human validation required |

---

## Design constraints

- **HTML only** — no JavaScript, no external CSS, no CDN
- **CSS inline** — single self-contained file, works offline
- **No framework** — monospace cockpit-style, not a marketing dashboard
- **No secrets** — only counts, labels, and record IDs are emitted
- **Idempotent** — running the same command twice produces the same output
- **Overwrite-safe** — refuses to replace existing file without `--overwrite`

---

## Data source

The dashboard reads from `MemoryRecord` JSON files produced by:

```sh
aeos reclaim harden --path <project> --memory-dir <dir>
```

Each record contains:
- `findings_summary`: `{critical, important, manual, generated}`
- `status`, `control_level`, `generator`, `providers`
- `strategic_options`: exit path labels
- `remediation_summary`: phases / counts

No external data. No database connection. No Supabase. No network.

---

## Read-only guarantee

The dashboard command:
- Only reads from `--memory-dir`
- Only writes to `--output`
- Never modifies MemoryRecord files
- Never reads `.env`
- Never connects to any network or database

`read_only: true · applied: false · human validation required`

---

## Planned additions (future sprints)

- Progress bar showing baseline → target recovery
- Per-record detail expansion (click to expand)
- Multiple project comparison view
- `--open` flag to launch browser automatically
- Export to PDF via `wkhtmltopdf` (optional, local only)
