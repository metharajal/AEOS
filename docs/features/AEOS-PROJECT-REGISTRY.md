# AEOS Project Registry

**Commands:** `aeos project register` · `aeos project list` · `aeos project show`
**Sprint:** MVP-CORE-1
**Status:** SHIPPED

---

## Overview

The Project Registry gives AEOS a persistent, local-first index of watched
projects. Before this feature, every UI and analysis command required the
full `--memory-dir` path on each invocation. The registry lets AEOS remember
a project's metadata — its memory directory, evidence directory, type, and
timestamps — in a single JSON file on the operator's machine.

The registry never stores MemoryRecord content, secrets, or credentials.
It stores only paths and metadata. It never contacts a network, database,
or AI provider.

---

## Commands

### `aeos project register`

Upsert a project into the local registry.

```sh
aeos project register \
  --name ma-mairie-digitale \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --evidence-dir /tmp/aeos-ui-demo/ma-mairie-digitale \
  --type recovered-project \
  --registry /tmp/aeos-projects.json
```

**Options:**

| Flag | Required | Description |
|------|----------|-------------|
| `--name` | Yes | Project name (unique key in the registry) |
| `--memory-dir` | Yes | Path to the local memory directory — must exist |
| `--evidence-dir` | No | Path to the evidence output directory — must exist if given |
| `--type` / `-t` | No | Project type (default: `recovered-project`) |
| `--registry` | No | Registry file path (default: `~/.aeos/registry.json`) |
| `--json` | No | JSON output |

**Upsert behaviour:**
- If the project does not exist → create new entry, `registered_at` = now
- If the project already exists → update all fields, preserve `registered_at`, refresh `last_seen_at`

**Example output:**
```
Registered:     ma-mairie-digitale
Type:         recovered-project
Memory:       /tmp/aeos-recovery-ma-mairie-digitale/memory
Evidence:     /tmp/aeos-ui-demo/ma-mairie-digitale
Last seen:    2026-07-01T19:36:25Z
Registry:     /tmp/aeos-projects.json
Total:        1 project(s) in registry
  read_only: true · applied: false
```

---

### `aeos project list`

List all projects in the registry.

```sh
aeos project list \
  --registry /tmp/aeos-projects.json
```

**Options:**

| Flag | Required | Description |
|------|----------|-------------|
| `--registry` | No | Registry file path (default: `~/.aeos/registry.json`) |
| `--json` | No | JSON output |

**Example output:**
```
Registry: /tmp/aeos-projects.json  ·  1 project(s)  ·  local-only  ·  read-only

  NAME                            TYPE                    LAST SEEN
  ──────────────────────────────────────────────────────────────────────
  ma-mairie-digitale              recovered-project       2026-07-01

  read_only: true · applied: false
```

If the registry file does not yet exist, the command reports this without
error and suggests running `aeos project register`.

---

### `aeos project show`

Show full details for one registered project.

```sh
aeos project show \
  --name ma-mairie-digitale \
  --registry /tmp/aeos-projects.json
```

**Options:**

| Flag | Required | Description |
|------|----------|-------------|
| `--name` | Yes | Project name to look up |
| `--registry` | No | Registry file path (default: `~/.aeos/registry.json`) |
| `--json` | No | JSON output |

**Example output:**
```
Project:      ma-mairie-digitale
Type:         recovered-project
Memory:       /tmp/aeos-recovery-ma-mairie-digitale/memory
Evidence:     /tmp/aeos-ui-demo/ma-mairie-digitale
Registered:   2026-07-01T19:36:25Z
Last seen:    2026-07-01T19:36:25Z
Local only:   true
Read only:    true
Registry:     /tmp/aeos-projects.json
  read_only: true · applied: false
```

Exit code 1 if the project name is not found.

---

## Registry JSON Schema

```json
{
  "updated_at": "2026-07-01T19:36:25Z",
  "local_only": true,
  "read_only": true,
  "projects": [
    {
      "name": "ma-mairie-digitale",
      "type": "recovered-project",
      "memory_dir": "/tmp/aeos-recovery-ma-mairie-digitale/memory",
      "evidence_dir": "/tmp/aeos-ui-demo/ma-mairie-digitale",
      "registered_at": "2026-07-01T19:36:25Z",
      "last_seen_at": "2026-07-01T19:36:25Z",
      "local_only": true,
      "read_only": true
    }
  ]
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique project identifier |
| `type` | string | Project type label |
| `memory_dir` | string | Absolute path to the memory records directory |
| `evidence_dir` | string \| null | Absolute path to the evidence output directory |
| `registered_at` | ISO 8601 | First registration timestamp — never overwritten |
| `last_seen_at` | ISO 8601 | Most recent registration call timestamp |
| `local_only` | bool | Always `true` — AEOS never syncs to cloud |
| `read_only` | bool | Always `true` — AEOS never modifies project source files |

Projects are sorted alphabetically by name in the file.

---

## Default Registry Path

`~/.aeos/registry.json`

Parent directories are created automatically on first write. Pass `--registry`
to override, e.g. for per-workspace or per-client registries.

---

## Project Types

Any string is accepted. Recommended values:

| Type | Meaning |
|------|---------|
| `recovered-project` | Project rescued from an AI generator (main AEOS use-case) |
| `audited-project` | Project audited but not yet in recovery |
| `monitored-project` | Healthy project under periodic AEOS monitoring |
| `native-project` | Project built from scratch with AEOS |

---

## Design Constraints

| Constraint | Implementation |
|------------|---------------|
| Local-first | Registry file is a plain JSON file on the operator's machine |
| No network | Zero HTTP calls — pure file I/O |
| No secrets | Only paths and metadata — no MemoryRecord content |
| No `.env` read | Command never opens `.env` files |
| No client modification | Registry is written to `~/.aeos/` — never to the project dir |
| No SQL | Not applicable |
| Tolerant load | Corrupt or missing registry file → empty registry, no crash |

---

## Relationship to Other Commands

The registry stores the `memory_dir` that UI commands need. A future sprint
will allow UI commands to resolve `--memory-dir` from a registered project
name, eliminating the need to pass full paths:

```sh
# Future (not yet implemented):
aeos ui dashboard --project ma-mairie-digitale

# Current (requires explicit path):
aeos ui dashboard \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --project ma-mairie-digitale \
  --output /tmp/aeos-ui-demo/ma-mairie-digitale/dashboard.html
```

---

*read_only: true · applied: false · human validation required*
