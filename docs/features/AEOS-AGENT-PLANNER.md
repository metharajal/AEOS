# AEOS Agent Planner

**Sprint:** MVP-AGENTS-2
**Status:** SHIPPED

---

## Summary

`aeos agent plan` is AEOS's first agent command. It is a **deterministic
read-only planner** — no LLM, no network, no secrets. It reads the project
registry and MemoryRecords, applies fixed rules, and produces a prioritised
action plan with per-project risk analysis.

---

## Usage

```sh
# Plan for all registered projects
aeos agent plan

# Plan for a specific project
aeos agent plan --project ma-mairie-digitale

# Write plan to Markdown file
aeos agent plan --project ma-mairie-digitale --output /tmp/aeos-agent-plan.md

# Machine-readable JSON output
aeos agent plan --json

# Custom registry path
aeos agent plan --registry /path/to/projects.json
```

---

## Example output

```
AEOS Agent Plan

Mode:              deterministic read-only planner
Registry:          /Users/you/.aeos/projects.json
Projects:          1
Global status:     WARNING

  [WARNING]  ma-mairie-digitale  —  3 record(s)  critical=0  important=2
             ! 2 important finding(s) pending review
             → Review evidence pack: aeos ui evidence-pack ...

Suggested next:
  1. Generate workspace: aeos workspace demo --output-dir ...

  read_only: true  ·  applied: false  ·  human validation required
```

---

## Decision rules

| Condition | Status | Risk | Action |
|-----------|--------|------|--------|
| Registry absent | ERROR | Registry not found | `aeos workspace init` |
| Project not registered | ERROR | Project not in registry | `aeos project register` |
| No projects in registry | WARNING | No projects | `aeos project register` |
| `memory_dir` missing | ERROR | memory_dir not found | Re-run `aeos reclaim harden` |
| No MemoryRecords in memory_dir | WARNING | No audit records | Run `aeos reclaim harden` |
| `critical > 0` in latest record | WARNING | Critical findings | Human review before production |
| `important > 0` in latest record | WARNING | Important findings | Review evidence pack |
| `evidence_dir` configured but absent | WARNING | Evidence missing | Re-run `aeos workspace demo` |
| Workspace index.html absent | WARNING | Workspace not generated | `aeos workspace demo` |
| All OK + index exists | OK | — | `aeos workspace open` |

---

## Output formats

### Terminal (default)

Compact per-project summary with status tag, record count, findings counts,
risks, and suggested actions. Ends with global suggested next commands.

### Markdown (`--output <file>`)

Full structured report with:
- Agent mode statement
- Registry path and generation timestamp
- Global risks and suggested actions
- Per-project table with all fields
- Evidence references if evidence_dir exists
- Explicit statement: no changes applied

### JSON (`--json`)

Machine-readable payload suitable for piping or scripting:

```json
{
  "agent_mode": "deterministic read-only planner",
  "registry_path": "...",
  "generated_at": "2026-07-02T...",
  "global_status": "WARNING",
  "projects_inspected": 1,
  "projects": [...],
  "risks": [...],
  "suggested_actions": [...],
  "read_only": true,
  "applied": false,
  "human_validation_required": true
}
```

---

## Exit codes

| Exit code | Meaning |
|-----------|---------|
| `0` | OK or WARNING — plan generated successfully |
| `1` | ERROR — registry missing, project not found, or memory_dir missing |

---

## Implementation

| File | Role |
|------|------|
| `src/aeos/agent/planner.py` | `ProjectPlanEntry`, `AgentPlan`, `generate_plan()`, renderers |
| `src/aeos/agent/__init__.py` | Public exports |
| `src/aeos/cli.py` | `agent plan` CLI command |
| `tests/unit/test_agent_planner.py` | Unit tests (library + CLI) |

---

## Safety guarantees

| Guarantee | Detail |
|-----------|--------|
| No LLM | Deterministic rules only |
| No `.env` read | Not referenced anywhere |
| No secrets | Only MemoryRecord metadata (counts, status) |
| No network | Pure local filesystem I/O |
| No client project mutation | Zero write operations to project files |
| `--output` only | Writes only to the path explicitly specified |
| `read_only: true · applied: false` | Present in every output |
| Human validation required | Stated in every output format |

---

## Policy compliance

This command complies with:
- `docs/agents/LOCAL-AI-ASSISTANT-POLICY.md` — read-only, no secrets, no
  autonomous apply, human validation required
- `docs/agents/AGENT-SAFETY-GATES.md` — Gates 1–4 pass before output;
  Gate 5 (human validation) required before any action
- `docs/agents/AGENT-ROADMAP.md` — MVP-AGENTS-2 specification
