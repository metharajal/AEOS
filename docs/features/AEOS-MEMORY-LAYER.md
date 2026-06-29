# AEOS Memory Layer

**Date:** 2026-06-29
**Status:** Feature — MVP
**Sprint:** 3F
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
├── __init__.py        public API: MemoryRecord, build_memory_record_from_reclaim_harden, save_record
├── models.py          MemoryRecord dataclass
└── store.py           build_memory_record_from_reclaim_harden(), save_record(), secret guard
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

```python
from aeos.memory import MemoryRecord, build_memory_record_from_reclaim_harden, save_record

record = build_memory_record_from_reclaim_harden(result, Path("/path/to/project"))
record_path = save_record(record, Path("/tmp/aeos-memory"))
```

---

## 9. Current Limits

| Limit | Detail |
|---|---|
| Single-command coverage | Only `reclaim harden` builds memory records in this MVP. Other rails (security, supabase) are not yet wired. |
| No memory read command | There is no `aeos memory list` or `aeos memory show` yet. Records are plain JSON — read them with any JSON viewer. |
| No memory search | Records must be browsed manually. Full-text or field-based search is planned. |
| No deduplication | Each run creates a new file. Old records are not pruned automatically. |
| No diff | No comparison between successive records for the same project. |

---

## 10. Next Steps

| Item | Status |
|---|---|
| Memory MVP — `reclaim harden` | **Done — Sprint 3F** |
| Memory read CLI (`aeos memory list`, `aeos memory show`) | Planned |
| Memory for other rails (security, supabase) | Planned |
| Record diff — compare successive audits | Planned |
| Human validation workflow (`human_validated: true`, `notes`) | Planned |

---

## See Also

- [`docs/features/AEOS-RECLAIM-HARDEN.md`](AEOS-RECLAIM-HARDEN.md) — reclaim harden command documentation
- [`docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md`](../strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md) — Memory Rail context
