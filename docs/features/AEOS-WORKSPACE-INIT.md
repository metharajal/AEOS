# AEOS Workspace Init

**Sprint:** MVP-UX-3
**Status:** SHIPPED

---

## Summary

`aeos workspace init` creates the AEOS home directory and default registry
file if they do not already exist. It is the recommended first command for any
new machine or clean setup.

Idempotent — running it multiple times is always safe.

---

## Usage

```sh
aeos workspace init
```

No flags required. AEOS always uses `~/.aeos/` and `~/.aeos/projects.json`.

---

## Example output — first run (fresh machine)

```
AEOS Workspace Init

Workspace home:    /Users/you/.aeos
Registry:          /Users/you/.aeos/projects.json
Initialized:       yes
Projects:          0 projects

Suggested next:    aeos project register --name <project> --memory-dir <path>/memory

  read_only: true  ·  applied: false
```

## Example output — already initialized

```
AEOS Workspace Init

Workspace home:    /Users/you/.aeos
Registry:          /Users/you/.aeos/projects.json
Initialized:       no (already existed)
Projects:          1 project

Suggested next:    aeos workspace status

  read_only: true  ·  applied: false
```

---

## What it does

1. Creates `~/.aeos/` if the directory does not exist.
2. If `~/.aeos/projects.json` does not exist, writes an empty registry:
   ```json
   {
     "updated_at": "...",
     "local_only": true,
     "read_only": true,
     "projects": []
   }
   ```
3. If the registry already exists, reads it to report the project count. Does
   not overwrite or modify it.
4. Returns a suggested next command based on state.

---

## Idempotency

| State | What happens |
|-------|-------------|
| `~/.aeos/` absent | Created |
| `~/.aeos/` present | Left untouched (`mkdir -p` semantics) |
| Registry absent | Written with empty project list |
| Registry present | Read only — never overwritten |

Running `aeos workspace init` twice on a machine that already has a registry
with projects will always report `Initialized: no (already existed)` and leave
the registry unchanged.

---

## Suggested next command logic

| State | Suggested command |
|-------|-----------------|
| 0 projects registered | `aeos project register --name <project> --memory-dir <path>/memory` |
| 1+ projects registered | `aeos workspace status` |

---

## Implementation

| File | Role |
|------|------|
| `src/aeos/workspace/init.py` | Library: `WorkspaceInitResult`, `workspace_init()` |
| `src/aeos/workspace/__init__.py` | Re-exports |
| `src/aeos/cli.py` | CLI command `workspace init` |
| `tests/unit/test_workspace_init.py` | Unit tests (library + CLI) |

---

## Safety guarantees

| Guarantee | Detail |
|-----------|--------|
| No `.env` read | Not referenced anywhere in the init path |
| No secrets exposed | Only filesystem paths and project counts |
| No client project mutation | Only touches `~/.aeos/` (AEOS own state) |
| No migration applied | `applied: false` in all output |
| No network call | Pure local filesystem I/O |
| No AI call | Deterministic Python logic |
| Idempotent | Safe to run on every session start |

---

## Full first-run workflow

```sh
# Step 0 — initialize (one time per machine)
aeos workspace init

# Step 1 — register a project
aeos project register \
  --name ma-mairie-digitale \
  --memory-dir /path/to/memory

# Step 2 — check state
aeos workspace status

# Step 3 — generate workspace
aeos workspace demo --output-dir ~/aeos-workspace

# Step 4 — open in browser
aeos workspace open --path ~/aeos-workspace/index.html
```
