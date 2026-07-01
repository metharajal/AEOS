# AEOS Workspace UX — Status & Open

**Sprint:** MVP-UX-2
**Status:** SHIPPED

---

## Summary

Two new CLI commands that complete the local workspace loop without any
network, backend, or external service:

| Command | Purpose |
|---------|---------|
| `aeos workspace status` | Show the current state of the registry and generated workspace |
| `aeos workspace open` | Open the generated workspace in the default browser |

---

## `aeos workspace status`

Shows a snapshot of AEOS state at the current moment: what is registered,
where the workspace was last generated, and what the suggested next command is.

### Usage

```sh
aeos workspace status [--output-dir <dir>]
```

`--output-dir` defaults to `$TMPDIR/aeos-workspace-demo`.

### Example output — nothing registered yet

```
AEOS Workspace Status

Registry:          /Users/you/.aeos/projects.json
Registry exists:   no

Workspace dir:     /var/folders/.../aeos-workspace-demo
index.html exists: no

Suggested next:    aeos project register --name <project> --memory-dir <path>/memory

  read_only: true  ·  applied: false
```

### Example output — workspace ready

```
AEOS Workspace Status

Registry:          /Users/you/.aeos/projects.json
Registry exists:   yes
Registered:        1 project

Workspace dir:     /var/folders/.../aeos-workspace-demo
index.html exists: yes

Suggested next:    open /var/folders/.../aeos-workspace-demo/index.html

  read_only: true  ·  applied: false
```

### Suggested next command logic

| State | Suggested command |
|-------|-----------------|
| No registry file | `aeos project register ...` |
| Registry empty (0 projects) | `aeos project register ...` |
| Projects registered, no workspace | `aeos workspace demo --output-dir <dir>` |
| Workspace index.html exists | `open <path>/index.html` |

---

## `aeos workspace open`

Opens a generated workspace `index.html` in the default browser using
Python's `webbrowser.open()` — no subprocess, no shell, no network.

### Usage

```sh
aeos workspace open [--path <index.html>]
```

`--path` defaults to `$TMPDIR/aeos-workspace-demo/index.html`.

### Example output

```sh
aeos workspace open --path /tmp/aeos-workspace-demo/index.html
# Opening: /tmp/aeos-workspace-demo/index.html
#   read_only: true  ·  applied: false
```

### Error — workspace not generated yet

```sh
aeos workspace open
# Error: Workspace file '/var/folders/.../aeos-workspace-demo/index.html' does not exist.
#   Run: aeos workspace demo --output-dir /var/folders/.../aeos-workspace-demo
# exit code: 1
```

---

## Implementation

| File | Role |
|------|------|
| `src/aeos/workspace/ux.py` | Library: `workspace_status()`, `workspace_open()`, `WorkspaceStatusResult` |
| `src/aeos/workspace/__init__.py` | Re-exports all public symbols |
| `src/aeos/cli.py` | CLI commands `workspace status` and `workspace open` |
| `tests/unit/test_workspace_ux.py` | Unit tests for library + CLI |

### Key design decisions

- **`webbrowser.open()`** — Python stdlib, cross-platform, no subprocess. File
  URL is constructed via `path.resolve().as_uri()` so it works on macOS,
  Linux, and Windows without any platform detection.

- **`DEFAULT_WORKSPACE_DIR`** — uses `Path(tempfile.gettempdir())` instead of
  hardcoded `/tmp` to avoid ruff S108 and to work correctly on macOS (where
  `$TMPDIR` is under `/var/folders`).

- **Read-only** — neither command writes any file. `workspace_status()` calls
  `load_registry()` (read-only) and checks path existence only.
  `workspace_open()` calls `webbrowser.open()` only.

- **Lazy imports inside CLI function bodies** — consistent with the rest of
  `cli.py`. Avoids circular imports and keeps startup time fast.

---

## Safety Guarantees

| Guarantee | How it is enforced |
|-----------|--------------------|
| No `.env` read | Not imported or referenced |
| No secrets shown | Only metadata from `ProjectRegistration` |
| No client project mutation | No write operations anywhere |
| No network call | `webbrowser.open()` opens a local `file://` URL |
| No AI call | Pure deterministic Python |
| `read_only: true · applied: false` | Present in every terminal output |

---

## Full Workspace Loop

```sh
# 1. Register a project (once)
aeos project register --name my-project --memory-dir /path/to/memory

# 2. Check current state at any time
aeos workspace status

# 3. Generate the workspace
aeos workspace demo --output-dir ~/aeos-workspace

# 4. Open it in the browser
aeos workspace open --path ~/aeos-workspace/index.html
```
