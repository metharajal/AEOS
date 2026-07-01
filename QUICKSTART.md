# AEOS Quickstart

Get from zero to a complete local audit workspace in under 5 minutes.

---

## What AEOS Does

AEOS is a local-first software audit platform. It reads your project's audit
records (MemoryRecords), generates static HTML dashboards and evidence packs,
and organises everything into a navigable workspace — with no cloud, no
database, and no external services required.

Typical use case: you have run `aeos reclaim harden` on a client project and
want to see a complete portfolio, dashboard, and evidence pack without sending
anything outside your machine.

---

## Prerequisites

| Tool | Minimum version | Check |
|------|----------------|-------|
| Python | 3.11 | `python --version` |
| uv | 0.4+ | `uv --version` |
| Git | any | `git --version` |

Install `uv` if needed:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Install / Run Locally

Clone the repo and run AEOS directly with `uv run`:

```sh
git clone https://github.com/metharajal/AEOS.git
cd AEOS
uv run aeos --version
```

No `pip install`, no virtualenv setup — `uv` handles it automatically.

---

## Initialize the Workspace

On a fresh machine, run this once to create the AEOS home directory and an
empty registry:

```sh
aeos workspace init
```

Expected output:

```
AEOS Workspace Init

Workspace home:    /Users/you/.aeos
Registry:          /Users/you/.aeos/projects.json
Initialized:       yes
Projects:          0 projects

Suggested next:    aeos project register --name <project> --memory-dir <path>/memory

  read_only: true  ·  applied: false
```

This is idempotent — running it again on a machine that already has a registry
will report `Initialized: no (already existed)` and leave everything untouched.

---

## Register a Project

Tell AEOS where your project's audit records live:

```sh
aeos project register \
  --name ma-mairie-digitale \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --evidence-dir /tmp/aeos-ui-demo/ma-mairie-digitale \
  --type recovered-project
```

Expected output:

```
Registered:   ma-mairie-digitale
Type:         recovered-project
Memory:       /tmp/aeos-recovery-ma-mairie-digitale/memory
Evidence:     /tmp/aeos-ui-demo/ma-mairie-digitale
Last seen:    2026-07-01T21:07:39Z
Registry:     /Users/you/.aeos/projects.json
Total:        1 project(s) in registry
  read_only: true · applied: false
```

The project is saved to `~/.aeos/projects.json`. No `--registry` flag is
needed — AEOS uses this path automatically from now on.

Re-running the same command updates the entry without error (upsert).

### Options

| Flag | Required | Description |
|------|----------|-------------|
| `--name` | Yes | Short identifier for the project |
| `--memory-dir` | Yes | Directory containing local `*.json` MemoryRecord files |
| `--evidence-dir` | No | Optional directory with evidence output |
| `--type` | No | Project type label (default: `recovered-project`) |

---

## List Registered Projects

```sh
aeos project list
```

Expected output:

```
Registry: /Users/you/.aeos/projects.json  ·  1 project(s)  ·  local-only  ·  read-only

  NAME                            TYPE                    LAST SEEN
  ──────────────────────────────────────────────────────────────────────
  ma-mairie-digitale              recovered-project       2026-07-01

  read_only: true · applied: false
```

---

## Show One Project

```sh
aeos project show --name ma-mairie-digitale
```

Expected output:

```
Project:      ma-mairie-digitale
Type:         recovered-project
Memory:       /tmp/aeos-recovery-ma-mairie-digitale/memory
Evidence:     /tmp/aeos-ui-demo/ma-mairie-digitale
Registered:   2026-07-01T21:07:39Z
Last seen:    2026-07-01T21:37:39Z
Local only:   true
Read only:    true
Registry:     /Users/you/.aeos/projects.json
  read_only: true · applied: false
```

---

## Generate the Workspace

```sh
aeos workspace demo --output-dir /tmp/aeos-workspace-demo
```

Expected output:

```
Workspace:  /tmp/aeos-workspace-demo
Registry:   /Users/you/.aeos/projects.json
Portfolio:  /tmp/aeos-workspace-demo/index.html
Projects:   1 generated  ·  0 skipped
  [OK]   ma-mairie-digitale  →  /tmp/aeos-workspace-demo/ma-mairie-digitale
Read-only — no files modified, no migration applied.
  read_only: true  ·  applied: false
```

If you have run this before and the output directory already exists, add
`--overwrite`:

```sh
aeos workspace demo --output-dir /tmp/aeos-workspace-demo --overwrite
```

---

## Check Workspace Status

```sh
aeos workspace status
```

Shows what is registered, whether the workspace has been generated, and the
suggested next command. No files are written.

---

## Open the Workspace in a Browser

```sh
aeos workspace open --path /tmp/aeos-workspace-demo/index.html
```

Opens the portfolio in your default browser using Python's `webbrowser`
module — no `open` / `xdg-open` / subprocess needed.

If you omit `--path`, AEOS uses the default workspace location
(`$TMPDIR/aeos-workspace-demo/index.html`):

```sh
aeos workspace open
```

**Manual alternatives:**

| Platform | Command |
|----------|---------|
| macOS | `open /tmp/aeos-workspace-demo/index.html` |
| Linux | `xdg-open /tmp/aeos-workspace-demo/index.html` |
| Windows (WSL) | `explorer.exe "$(wslpath -w /tmp/aeos-workspace-demo/index.html)"` |

---

## Expected Result

Your browser opens a dark-theme portfolio page listing all registered
projects. Each project card shows:

- Production readiness verdict (`READY` / `NOT READY FOR PRODUCTION`)
- Critical, important, and manual findings counts
- Last audit record date
- Links to: dashboard → project workspace → evidence pack

The generated file tree looks like this:

```
/tmp/aeos-workspace-demo/
  index.html                          ← portfolio (all projects)
  ma-mairie-digitale/
    dashboard.html                    ← audit cockpit
    project-workspace.html            ← decision briefing
    evidence-pack/
      index.html                      ← evidence pack landing
      dashboard.html
      project-workspace.html
      recovery-summary.md
      risk-register.md
      human-gates.md
      next-actions.md
```

All files are self-contained static HTML or Markdown. No server needed.

---

## Safety Guarantees

| Guarantee | Detail |
|-----------|--------|
| **Local-first** | Everything stays on your machine. No data leaves. |
| **Read-only** | AEOS never modifies your project files or MemoryRecords. |
| **No cloud** | No API calls, no sync, no remote storage. |
| **No network required** | Workspace generation is pure local file I/O. |
| **No secrets** | MemoryRecords contain only counts and status strings — never credentials, keys, or `.env` values. |
| **No `.env` access** | AEOS never reads environment variable files. |
| **No migration applied** | Every output carries `applied: false`. No SQL is run. |

Every generated page includes the footer:

```
read_only: true  ·  applied: false  ·  human validation required
```

---

## Troubleshooting

### `Error: memory directory '...' does not exist`

The `--memory-dir` path must exist before registering. Run `aeos reclaim
harden` on your project first to populate it, or point to an existing
memory directory.

### `Error: registry file '...' does not exist`

No projects have been registered yet. Run `aeos project register` first.

### `Error: '...' already exists. Use --overwrite to replace it.`

The output directory or file already exists. Add `--overwrite` to the
command to replace it.

### `[SKIP] project-name  (memory_dir missing: /path/to/memory)`

A registered project's memory directory was not found at generation time
(e.g. it was in `/tmp` and was cleaned up). Re-run `aeos reclaim harden`
to repopulate the memory directory, or remove and re-register the project.

### Command not found: `aeos`

Make sure you are running from inside the AEOS repo with `uv run aeos ...`,
or that AEOS has been installed with `uv tool install .`.

---

## Next Steps

Once the workspace is generated, you can:

| Command | What it generates |
|---------|-----------------|
| `aeos ui portfolio --output <file>` | Portfolio page only (no per-project files) |
| `aeos ui dashboard --memory-dir <path> --project <name> --output <file>` | Single-project audit cockpit |
| `aeos ui project-workspace --memory-dir <path> --project <name> --output <file>` | Single-project decision briefing |
| `aeos ui evidence-pack --memory-dir <path> --project <name> --output-dir <dir>` | Full evidence pack for one project |

To add more projects to the workspace:

```sh
aeos project register --name <another-project> --memory-dir <path>/memory
aeos workspace demo --output-dir /tmp/aeos-workspace-demo --overwrite
```

To inspect the registry at any time:

```sh
aeos project list
aeos project show --name <project>
cat ~/.aeos/projects.json
```
