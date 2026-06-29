# AEOS Memory Layer

**Date:** 2026-06-29
**Status:** Feature — Sprint 3G (Read CLI available)
**Sprints:** 3F (MVP write), 3G (Read CLI)
**Module:** `src/aeos/memory/`

---

## Summary

The AEOS Memory Layer is a local-first diagnostic memory system.
It stores structured snapshots of AEOS audit results as JSON files on disk,
project by project, without network access, without AI inference, and without
storing secret values.

The layer implements the third pillar of the AEOS architecture:

> AEOS Core guarantees. AEOS Agents reason. **AEOS Memory learns.** Humans validate.

In this MVP, "learning" means _persisting_: every audit run can optionally write
a structured record so that history is local, readable, and human-controllable.

---

## End-to-End Usage Guide

The Memory Layer chain has three steps, each triggered by a separate command:

```
aeos reclaim harden --memory-dir <dir>   →   creates a MemoryRecord JSON file
aeos memory list   --memory-dir <dir>    →   lists all records in that directory
aeos memory show   --memory-dir <dir> --record <id>   →   shows one record in detail
```

### Step 1 — Create a MemoryRecord

Run `aeos reclaim harden` with `--memory-dir` pointing to a directory **outside**
the audited project. AEOS writes a structured JSON snapshot of the audit result.

```bash
aeos reclaim harden \
  --path ~/aeos-client-audits/ma-mairie-digitale \
  --output /tmp/ma-mairie-report.md \
  --memory-dir /tmp/aeos-memory
```

Output includes:

```
Status:           ERROR ✗
Exported:         /tmp/ma-mairie-report.md
Critical risks:   3
Manual actions:   15
Generatable SQL:  25 block(s)
Memory:           /tmp/aeos-memory/ma-mairie-digitale/ma-mairie-digitale-20260629T115627-e94541fc.json
Read-only — no files modified, no migration applied.
  read_only: true  ·  applied: false
```

The `Memory:` line shows the exact path of the JSON file that was written.

**Why the memory directory must be outside the client project:**
The `--memory-dir` path must not be inside the audited project directory.
If it were, AEOS would be writing files into a project it is supposed to audit
read-only — violating the `OUTPUT BEFORE WRITE` and `GATE BEFORE APPLY` doctrines.
A separate directory (e.g. `/tmp/aeos-memory` or `~/.aeos/memory`) keeps the
memory store decoupled from the project being analysed.

---

### Step 2 — List records

```bash
aeos memory list --memory-dir /tmp/aeos-memory
```

Output:

```
Memory Records — /tmp/aeos-memory
Records found: 1

  record_id:      ma-mairie-digitale-20260629T115627-e94541fc
  project_name:   ma-mairie-digitale
  created_at:     2026-06-29T11:56:27.260150+00:00
  source_command: reclaim harden
  status:         ERROR
  generator:      lovable
  providers:      1

Read-only — no files modified.
```

JSON variant:

```bash
aeos memory list --memory-dir /tmp/aeos-memory --json
```

```json
{
  "memory_dir": "/tmp/aeos-memory",
  "total": 1,
  "records": [
    {
      "record_id": "ma-mairie-digitale-20260629T115627-e94541fc",
      "project_name": "ma-mairie-digitale",
      "created_at": "2026-06-29T11:56:27.260150+00:00",
      "source_command": "reclaim harden",
      "status": "ERROR",
      "generator_detected": "lovable",
      "provider_count": 1
    }
  ],
  "skipped_files": []
}
```

---

### Step 3 — Show a record in detail

Copy the `record_id` from the list output and pass it to `memory show`:

```bash
aeos memory show \
  --memory-dir /tmp/aeos-memory \
  --record ma-mairie-digitale-20260629T115627-e94541fc
```

Output:

```
Memory Record — ma-mairie-digitale-20260629T115627-e94541fc

  project_name:   ma-mairie-digitale
  project_path:   /Users/user/aeos-client-audits/ma-mairie-digitale
  created_at:     2026-06-29T11:56:27.260150+00:00
  source_command: reclaim harden
  status:         ERROR
  read_only:      True
  applied:        False
  human_validated:False
  generator:      lovable
  providers:      supabase
  control_level:  weak

── Findings Summary ─────────────────────────────────────
  critical     3
  important    72
  manual       15
  generated    25

── Remediation Summary ──────────────────────────────────
  phases_count         5
  immediate            3
  manual               8
  generatable          25
  strategic            5

── Strategic Options ────────────────────────────────────
  1. [low/partial] Stay on current provider but secure
  2. [medium/medium] Migrate to own Supabase Cloud project
  3. [high/high] Migrate to self-hosted Supabase
  4. [very_high/very_high] Migrate to PostgreSQL + open backend
  5. [extreme/maximum] Full sovereign rebuild

Read-only — no files modified.
```

JSON variant:

```bash
aeos memory show \
  --memory-dir /tmp/aeos-memory \
  --record ma-mairie-digitale-20260629T115627-e94541fc \
  --json
```

---

### What AEOS does in this chain

| Action | Done by AEOS |
|---|---|
| Audit the project | Yes — `reclaim harden` |
| Build a safe JSON snapshot | Yes — secret guard enforced |
| Write the record to disk | Yes — to `<memory_dir>/<project_name>/` |
| List records | Yes — `aeos memory list` |
| Show a record in detail | Yes — `aeos memory show` |

### What AEOS does NOT do (yet)

| Action | Status |
|---|---|
| Compare two records (diff) | Not yet — planned Sprint 3H |
| Search across records | Not yet — planned |
| Modify a record | Never — all read operations are read-only |
| Apply any fix from a record | Never without explicit human gate |
| Read `.env` | Never |
| Display secret values | Never |
| Contact any database or API | Never |
| Write inside the audited project | Never |

---

### Memory guarantees

| Invariant | Enforced by |
|---|---|
| `read_only: true` in every record | `build_memory_record_from_reclaim_harden` hardcodes it |
| `applied: false` in every record | Same |
| No secret values stored | `save_record` scans all strings before writing |
| No `.env` read | Memory module never opens secrets files |
| No network access | Pure local filesystem writes |
| Memory dir outside audited project | Required by `save_record` convention |
| No database connection | No SQL, no Supabase, no migrations |
| `human_validated: false` by default | Humans set it to `true` after review |

---

## 1. Design Principles

| Principle | How it is enforced |
|---|---|
| Local-first | JSON files on disk only. No remote write, no cloud sync. |
| No secrets | `save_record` checks all string values for credential patterns and refuses the write if any match. |
| No `.env` read | The memory module never opens `.env` or any secrets file. |
| No network | No HTTP call, no Supabase connection, no external API. |
| No AI | Records are built deterministically from audit result fields. |
| No client modification | The memory directory is always outside the audited project. |
| Human validation | `human_validated` defaults to `false`. Humans change it when they review. |

---

## 2. Architecture

```
src/aeos/memory/
├── __init__.py        public API — see Section 8
├── models.py          MemoryRecord, MemoryRecordSummary, MemoryListResult
└── store.py           write: build_memory_record_from_reclaim_harden(), save_record()
                       read:  list_records(), load_record(), find_record_path()
                       guard: _looks_like_secret_value(), _iter_string_leaves()
```

---

## 3. MemoryRecord Schema

A `MemoryRecord` is a safe, serializable snapshot of one AEOS audit run.
It contains only counts, status labels, metadata, and human-readable option text.
It never contains secret values, raw credentials, or `.env` content.

```json
{
  "record_id": "ma-mairie-digitale-20260629T115627-e94541fc",
  "created_at": "2026-06-29T11:56:27.260150+00:00",
  "project_path": "/Users/.../ma-mairie-digitale",
  "project_name": "ma-mairie-digitale",
  "rail": "reclaim",
  "command": "reclaim harden",
  "status": "ERROR",
  "generator": "lovable",
  "providers": ["supabase"],
  "control_level": "weak",
  "read_only": true,
  "applied": false,
  "findings_summary": {
    "critical": 3,
    "important": 72,
    "manual": 15,
    "generated": 25
  },
  "remediation_summary": {
    "phases_count": 5,
    "immediate": 3,
    "manual": 8,
    "generatable": 25,
    "strategic": 5
  },
  "strategic_options": [
    "1. [low/partial] Stay on current provider but secure",
    "2. [medium/medium] Migrate to own Supabase Cloud project",
    "3. [high/high] Migrate to self-hosted Supabase",
    "4. [very_high/very_high] Migrate to PostgreSQL + open backend",
    "5. [extreme/maximum] Full sovereign rebuild"
  ],
  "human_validated": false,
  "notes": null
}
```

### Field reference

| Field | Type | Description |
|---|---|---|
| `record_id` | string | `<project_name>-<timestamp>-<8-char uuid>` |
| `created_at` | string | ISO 8601 timestamp with timezone |
| `project_path` | string | Absolute path to the audited project |
| `project_name` | string | Basename of `project_path` |
| `rail` | string | `"reclaim"` (extensible to other rails) |
| `command` | string | `"reclaim harden"` |
| `status` | string | `"OK"` · `"WARNING"` · `"ERROR"` |
| `generator` | string \| null | Generator detected — `"lovable"`, `"bolt"`, or null |
| `providers` | list[string] | Detected providers — e.g. `["supabase"]` |
| `control_level` | string | `"controlled"` · `"partial"` · `"weak"` · `"unknown"` |
| `read_only` | bool | Always `true` — enforced |
| `applied` | bool | Always `false` — enforced |
| `findings_summary` | dict | Count of critical / important / manual / generated findings |
| `remediation_summary` | dict \| null | Phase and action counts from the remediation plan |
| `strategic_options` | list[string] | Exit option labels, truncated to 80 chars |
| `human_validated` | bool | `false` by default — human sets to `true` after review |
| `notes` | string \| null | Free-form human notes, null by default |

---

## 4. Secret Guard

`save_record` scans every string value in the payload before writing.
If any string matches a credential pattern, the write is refused and a
`ValueError` is raised. No partial file is written.

Patterns checked:

| Pattern | Example |
|---|---|
| JWT (`eyJ…`) | Supabase anon key, service role key |
| Long base64 (60+ chars) | Raw API secrets, encoded tokens |
| Stripe-style live key (`sk_live_…`, `pk_live_…`) | Payment provider keys |

`findings_summary` and `remediation_summary` store only integers.
`strategic_options` stores short label strings (≤ 80 chars) that are
always safe (e.g. `"1. [low/partial] Stay on current provider but secure"`).

---

## 5. File Layout

Memory records are written to:

```
<memory_dir>/<project_name>/<record_id>.json
```

Example:

```
/tmp/aeos-memory-test/
└── ma-mairie-digitale/
    └── ma-mairie-digitale-20260629T115627-e94541fc.json
```

The memory directory is **always outside the audited project directory**.
`save_record` creates `<memory_dir>/<project_name>/` if it does not exist.

---

## 6. CLI Integration

The `--memory-dir` option is available on `aeos reclaim harden`.

```
aeos reclaim harden --path <project> --memory-dir <dir>
aeos reclaim harden --path <project> --output <file> --memory-dir <dir>
aeos reclaim harden --path <project> --json --memory-dir <dir>
```

When `--memory-dir` is provided:
- A `MemoryRecord` is built from the audit result.
- The record is saved to `<memory_dir>/<project_name>/<record_id>.json`.
- Text output includes a `Memory: <path>` line.
- JSON output includes a `memory_record_path` field.

### Text output

```
Status:           ERROR ✗
Exported:         /tmp/ma-mairie-digitale-reclaim-report.md
Critical risks:   3
Manual actions:   15
Generatable SQL:  25 block(s)
Memory:           /tmp/aeos-memory-test/ma-mairie-digitale/ma-mairie-digitale-20260629T115627-e94541fc.json
Read-only — no files modified, no migration applied.
  read_only: true  ·  applied: false
```

### JSON output

```json
{
  "status": "ERROR",
  "read_only": true,
  "applied": false,
  "memory_record_path": "/tmp/aeos-memory-test/ma-mairie-digitale/ma-mairie-digitale-20260629T115627-e94541fc.json",
  ...
}
```

---

## 7. Security Guarantees

These invariants are enforced in code and verified by tests.

| Invariant | Value |
|---|---|
| `read_only` | `true` in every record |
| `applied` | `false` in every record |
| No secret values | Secret guard rejects write if credential pattern detected |
| No `.env` read | Memory module never opens any secrets file |
| No network access | All writes are local filesystem only |
| No client project write | Memory dir must be outside the audited project |
| `human_validated` | `false` by default — humans validate manually |

---

## 8. Public API

### Write (Sprint 3F)

```python
from aeos.memory import build_memory_record_from_reclaim_harden, save_record

record = build_memory_record_from_reclaim_harden(result, Path("/path/to/project"))
record_path = save_record(record, Path("/tmp/aeos-memory"))
# → /tmp/aeos-memory/<project_name>/<record_id>.json
```

### Read (Sprint 3G)

```python
from aeos.memory import list_records, load_record, find_record_path

# List all records in a directory (returns MemoryListResult)
result = list_records(Path("/tmp/aeos-memory"))
for summary in result.records:
    print(summary.record_id, summary.status)
for bad_file in result.skipped_files:
    print("Skipped:", bad_file)

# Load a full record by ID (returns MemoryRecord)
record = load_record(Path("/tmp/aeos-memory"), "ma-mairie-digitale-20260629T115627-e94541fc")

# Find the file path for a given record_id
path = find_record_path(Path("/tmp/aeos-memory"), "ma-mairie-digitale-20260629T115627-e94541fc")
```

### Models

```python
from aeos.memory import MemoryRecord, MemoryRecordSummary, MemoryListResult
```

| Model | Used for |
|---|---|
| `MemoryRecord` | Full record — all fields |
| `MemoryRecordSummary` | Lightweight view for `list` output |
| `MemoryListResult` | Wraps `list[MemoryRecordSummary]` + `skipped_files` |

---

## 9. Memory Read CLI

Introduced in **Sprint 3G**. Two read-only commands for browsing local memory records.

### `aeos memory list`

Lists all records in a local memory directory.

```bash
aeos memory list --memory-dir /tmp/aeos-memory
aeos memory list --memory-dir /tmp/aeos-memory --json
```

**Text output example:**

```
Memory Records — /tmp/aeos-memory
Records found: 1

  record_id:      ma-mairie-digitale-20260629T115627-e94541fc
  project_name:   ma-mairie-digitale
  created_at:     2026-06-29T11:56:27.260150+00:00
  source_command: reclaim harden
  status:         ERROR
  generator:      lovable
  providers:      1

Read-only — no files modified.
```

**JSON output example:**

```json
{
  "memory_dir": "/tmp/aeos-memory",
  "total": 1,
  "records": [
    {
      "record_id": "ma-mairie-digitale-20260629T115627-e94541fc",
      "project_name": "ma-mairie-digitale",
      "created_at": "2026-06-29T11:56:27.260150+00:00",
      "source_command": "reclaim harden",
      "status": "ERROR",
      "generator_detected": "lovable",
      "provider_count": 1
    }
  ],
  "skipped_files": []
}
```

**Behaviour:**
- If `--memory-dir` does not exist → clear error message + exit code 1.
- If directory is empty or has no records → `No records found.` + exit code 0.
- If a JSON file is invalid → warning displayed, file skipped, other records listed normally.
- Never reads `.env`. Never modifies any file.

---

### `aeos memory show`

Shows a single record in detail.

```bash
aeos memory show --memory-dir /tmp/aeos-memory --record ma-mairie-digitale-20260629T115627-e94541fc
aeos memory show --memory-dir /tmp/aeos-memory --record ma-mairie-digitale-20260629T115627-e94541fc --json
```

**Text output example:**

```
Memory Record — ma-mairie-digitale-20260629T115627-e94541fc

  project_name:   ma-mairie-digitale
  project_path:   /Users/.../ma-mairie-digitale
  created_at:     2026-06-29T11:56:27.260150+00:00
  source_command: reclaim harden
  status:         ERROR
  read_only:      True
  applied:        False
  human_validated:False
  generator:      lovable
  providers:      supabase
  control_level:  weak

── Findings Summary ─────────────────────────────────────
  critical     3
  important    72
  manual       15
  generated    25

── Remediation Summary ──────────────────────────────────
  phases_count         5
  immediate            3
  manual               8
  generatable          25
  strategic            5

── Strategic Options ────────────────────────────────────
  1. [low/partial] Stay on current provider but secure
  2. [medium/medium] Migrate to own Supabase Cloud project
  ...

Read-only — no files modified.
```

**JSON output** includes all fields: `record_id`, `project_name`, `project_path`,
`created_at`, `rail`, `source_command`, `status`, `generator_detected`, `providers`,
`control_level`, `read_only`, `applied`, `findings_summary`, `remediation_summary`,
`strategic_options`, `human_validated`, `notes`.

**Behaviour:**
- If `--memory-dir` does not exist → clear error + exit code 1.
- If `--record` not found → clear error + exit code 1.
- If JSON is invalid → clear error + exit code 1 (does not skip unlike `list`).
- Never reads `.env`. Never modifies any file.

---

## 10. Current Limits

| Limit | Detail |
|---|---|
| Single-command coverage | Only `reclaim harden` builds memory records. Other rails (security, supabase) are not yet wired. |
| No memory search | Records must be browsed by record_id. Full-text or field-based search is planned. |
| No deduplication | Each run creates a new file. Old records are not pruned automatically. |
| No diff | No comparison between successive records for the same project. |
| No compare/search/learn | Planned for a future sprint after foundational read CLI is stable. |

---

## 11. Next Steps

| Item | Status |
|---|---|
| Memory MVP — `reclaim harden` | **Done — Sprint 3F** |
| Memory read CLI (`aeos memory list`, `aeos memory show`) | **Done — Sprint 3G** |
| Memory for other rails (security, supabase) | Planned |
| Record diff — compare successive audits | Planned |
| Human validation workflow (`human_validated: true`, `notes`) | Planned |
| Memory search (`aeos memory search`) | Planned — after compare/diff |
| Memory learn — pattern extraction from history | Future |

---

## See Also

- [`docs/features/AEOS-RECLAIM-HARDEN.md`](AEOS-RECLAIM-HARDEN.md) — reclaim harden command documentation
- [`docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md`](../strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md) — Memory Rail context
