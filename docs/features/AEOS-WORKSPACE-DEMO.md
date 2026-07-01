# AEOS Workspace Demo

**Command:** `aeos workspace demo`
**Sprint:** MVP-DEMO-1
**Status:** SHIPPED

---

## Overview

`aeos workspace demo` generates a complete static workspace from a Project
Registry in a single command. It is the primary entry point for producing
a full CTO-ready handoff dossier from any registered project collection.

It orchestrates all existing AEOS UI generators:

| Generator | Output per project |
|-----------|-------------------|
| `aeos ui portfolio` | `index.html` — multi-project overview |
| `aeos ui dashboard` | `{project}/dashboard.html` |
| `aeos ui project-workspace` | `{project}/project-workspace.html` |
| `aeos ui evidence-pack` | `{project}/evidence-pack/` (7 files) |

---

## Usage

```sh
aeos workspace demo \
  --registry ~/.aeos/registry.json \
  --output-dir /tmp/aeos-workspace-demo
```

### Options

| Flag | Required | Description |
|------|----------|-------------|
| `--registry` | Yes | Path to AEOS project registry JSON (from `aeos project register`) |
| `--output-dir` | Yes | Directory to write the workspace into |
| `--overwrite` | No | Overwrite existing output files (default: error if non-empty evidence-pack exists) |

---

## Output Structure

```
{output-dir}/
  index.html                          ← portfolio across all projects
  {project-name}/
    dashboard.html                    ← audit cockpit view
    project-workspace.html            ← decision-ready briefing
    evidence-pack/
      index.html                      ← evidence pack landing page
      dashboard.html
      project-workspace.html
      recovery-summary.md
      risk-register.md
      human-gates.md
      next-actions.md
```

---

## Example Output

```
Workspace:  /tmp/aeos-workspace-demo
Registry:   /tmp/aeos-projects.json
Portfolio:  /tmp/aeos-workspace-demo/index.html
Projects:   1 generated  ·  0 skipped
  [OK]   ma-mairie-digitale  →  /tmp/aeos-workspace-demo/ma-mairie-digitale
Read-only — no files modified, no migration applied.
  read_only: true  ·  applied: false
```

---

## Graceful Degradation

If a registered project's `memory_dir` no longer exists, the project is
**skipped** with a warning — it does not cause the entire command to fail.

```
Projects:   1 generated  ·  1 skipped
  [OK]   active-project  →  /tmp/ws/active-project
  [SKIP] ghost-project   (memory_dir missing: /tmp/old-memory)

Warnings:
  ! Skipping 'ghost-project': memory_dir '/tmp/old-memory' does not exist.
```

The portfolio (`index.html`) is still generated for all valid projects.

---

## Error Cases

| Condition | Behaviour |
|-----------|-----------|
| `--registry` file does not exist | Exit 1 with clear error |
| Registry is empty (0 projects) | Exit 1 with clear error |
| `memory_dir` missing for a project | Warn + skip that project |
| Output dir exists and non-empty without `--overwrite` | Exit 1 (evidence-pack raises) |

---

## Workflow

```sh
# Step 1 — register projects
aeos project register \
  --name ma-mairie-digitale \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --type recovered-project

# Step 2 — generate full workspace
aeos workspace demo \
  --registry ~/.aeos/registry.json \
  --output-dir /tmp/aeos-workspace-demo \
  --overwrite
```

---

## Design Constraints

| Constraint | Implementation |
|------------|---------------|
| Read-only | Never writes to project source or MemoryRecord files |
| No network | Zero HTTP calls — pure local file I/O |
| No AI | All derivation is deterministic Python logic |
| No secrets | MemoryRecords contain only counts and metadata |
| No backend | Self-contained static HTML files |
| No `.env` read | Not referenced anywhere in the pipeline |
| Registry not modified | `load_registry` only — never `save_registry` |

Every generated page carries:
```
read_only: true  ·  applied: false  ·  human validation required
```

---

## Relationship to Other Commands

| Command | Scope | Audience |
|---------|-------|----------|
| `aeos workspace demo` | Full workspace, all projects | CTO handoff |
| `aeos ui portfolio` | Portfolio page only | Quick overview |
| `aeos ui dashboard` | One project | Lead engineer |
| `aeos ui project-workspace` | One project | Decision briefing |
| `aeos ui evidence-pack` | One project | Handoff dossier |
| `aeos project register` | Registry write | Setup |
| `aeos project list` | Registry read | Inventory |
