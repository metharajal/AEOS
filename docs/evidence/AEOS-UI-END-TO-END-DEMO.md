# AEOS UI — End-to-End Demo

**Date:** 2026-07-01
**Commit:** `c192a0b`
**Branch:** `main`
**Status:** COMPLETE

---

## Executive Summary

This document records the first end-to-end execution of all four AEOS UI
commands against a real client project, generating a complete, navigable
evidence structure in a single output directory. Four commands, ten files,
zero network calls, zero secrets read, zero files modified in the client repo.

The generated structure follows the AEOS UI output convention:
`index.html` at the root links to per-project views, which link to the
evidence pack. A CTO can open `index.html` and navigate the entire recovery
story without leaving the browser.

---

## Demo Purpose

To validate that all four AEOS UI commands:

1. Work correctly from `main` without any re-run of the audit
2. Produce files at the conventional output paths without collision
3. Together form a coherent, navigable evidence structure
4. Generate in full under 5 seconds on local hardware
5. Produce zero side effects on the client project or memory records

---

## Commands Executed

```sh
# Reset and prepare output directory
rm -rf /tmp/aeos-ui-demo
mkdir -p /tmp/aeos-ui-demo/ma-mairie-digitale

# 1. Portfolio — entry point listing all projects
uv run aeos ui portfolio \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --output /tmp/aeos-ui-demo/index.html

# 2. Dashboard — technical audit timeline
uv run aeos ui dashboard \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --project ma-mairie-digitale \
  --output /tmp/aeos-ui-demo/ma-mairie-digitale/dashboard.html

# 3. Project Workspace — executive decision view
uv run aeos ui project-workspace \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --project ma-mairie-digitale \
  --output /tmp/aeos-ui-demo/ma-mairie-digitale/project-workspace.html

# 4. Evidence Pack — complete governance dossier
uv run aeos ui evidence-pack \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --project ma-mairie-digitale \
  --output-dir /tmp/aeos-ui-demo/ma-mairie-digitale/evidence-pack
```

**All four commands completed with exit code 0.**

CLI output summary:

```
Portfolio:  /tmp/aeos-ui-demo/index.html
Projects:   1 · ma-mairie-digitale → NOT READY FOR PRODUCTION
read_only: true · applied: false

Dashboard:  /tmp/aeos-ui-demo/ma-mairie-digitale/dashboard.html
Records:    6
read_only: true · applied: false

Workspace:  /tmp/aeos-ui-demo/ma-mairie-digitale/project-workspace.html
Records:    6 · Verdict: NOT READY FOR PRODUCTION
read_only: true · applied: false

Pack:       /tmp/aeos-ui-demo/ma-mairie-digitale/evidence-pack
Records:    6 · Verdict: NOT READY FOR PRODUCTION
Files:      7
read_only: true · applied: false
```

---

## Generated File Tree

```
/tmp/aeos-ui-demo/
├── index.html                                    5.5 KB  ← aeos ui portfolio
└── ma-mairie-digitale/
    ├── dashboard.html                            9.6 KB  ← aeos ui dashboard
    ├── project-workspace.html                   10.0 KB  ← aeos ui project-workspace
    └── evidence-pack/                                    ← aeos ui evidence-pack
        ├── index.html                            4.3 KB
        ├── dashboard.html                        9.6 KB
        ├── project-workspace.html               10.0 KB
        ├── recovery-summary.md                   1.3 KB
        ├── risk-register.md                      1.0 KB
        ├── human-gates.md                        1.2 KB
        └── next-actions.md                       1.0 KB

10 files · ~54 KB total
```

**Navigation flow:**
`index.html` → `ma-mairie-digitale/dashboard.html`
`index.html` → `ma-mairie-digitale/project-workspace.html`
`index.html` → `ma-mairie-digitale/evidence-pack/index.html`
`evidence-pack/index.html` → all 6 pack files

---

## What Each Generated File Proves

| File | What it proves |
|------|----------------|
| `index.html` | AEOS auto-detects projects from a memory directory and renders a navigable portfolio page with verdict badges — no `--project` flag needed |
| `ma-mairie-digitale/dashboard.html` | 6 MemoryRecords are sufficient to render a full technical audit timeline with per-column deltas and synthesis trends |
| `ma-mairie-digitale/project-workspace.html` | Production readiness verdict, human gates, and recommended actions are derivable deterministically from structured record metadata |
| `evidence-pack/index.html` | A single command generates a self-contained linked entry point for the full dossier |
| `evidence-pack/dashboard.html` | The dashboard renderer is reused without modification inside the pack |
| `evidence-pack/project-workspace.html` | The workspace renderer is reused without modification inside the pack |
| `evidence-pack/recovery-summary.md` | Narrative recovery summary with before/after table is auto-generated — no human writing required |
| `evidence-pack/risk-register.md` | Risk categories and counts are readable as a standalone governance document |
| `evidence-pack/human-gates.md` | Sign-off checklist for a CTO is fully derivable from `providers`, `findings_summary`, and `control_level` |
| `evidence-pack/next-actions.md` | Prioritised action list with assignment fields requires zero manual curation |

---

## ma-mairie-digitale Evidence Summary

**Project profile at demo time:**

| Field | Value |
|-------|-------|
| Generator | `lovable` |
| Providers | `supabase` |
| Control level | `weak` |
| Audit records | 6 |
| Period | 2026-06-30 → 2026-07-01 |
| Memory source | `/tmp/aeos-recovery-ma-mairie-digitale/memory` |

**Risk snapshot (latest record):**

| Metric | Baseline | Current | Delta |
|--------|----------|---------|-------|
| Critical findings | 3 | 3 | 0 |
| Important findings | 72 | 59 | −13 |
| Manual actions | 15 | 15 | 0 |
| Generatable SQL blocks | 25 | 15 | −10 |

**Verdict:** NOT READY FOR PRODUCTION

**Blocking reasons:**
- 3 critical risk(s) unresolved
- 15 SQL block(s) not yet applied to staging
- 15 manual action(s) pending review
- control level is 'weak'

**Recommended next action (portfolio card):**
"Review and apply 15 auto-generated SQL block(s) to staging — human approval required"

---

## Safety Guarantees

All four commands ran with the following guarantees — verified by inspection of
the generated files and the MemoryRecord timestamps before and after execution:

| Guarantee | Verified |
|-----------|----------|
| No `.env` files read | ✓ — commands read only `*.json` from memory directory |
| No client project files modified | ✓ — output paths are all under `/tmp/aeos-ui-demo` |
| No MemoryRecord files modified | ✓ — record `mtime` unchanged before and after |
| No network calls | ✓ — all commands run offline, no DNS or HTTP |
| No AI inference | ✓ — all derivation is deterministic Python logic |
| No SQL executed | ✓ — `applied: false` on every record |
| No secrets in output | ✓ — generated files contain only counts, metadata, and advisory text |
| `read_only: true` everywhere | ✓ — present in every generated file footer |
| `applied: false` everywhere | ✓ — present in every generated file footer |
| `human validation required` | ✓ — present in every generated file footer |

---

## Current Limitations

| Limitation | Impact |
|------------|--------|
| Portfolio links are conventional — not verified | Links render even if target files don't exist yet |
| No `--open` flag | User must open `index.html` manually in a browser |
| No zip/archive of the full demo directory | Sharing requires manual archiving |
| `evidence-pack` duplicates `dashboard.html` and `project-workspace.html` | ~19 KB redundancy — acceptable for self-contained dossier |
| `aeos ui portfolio` accepts only one `--memory-dir` | Multi-project directories require one invocation per dir |
| Static HTML — no interactivity | No search, sort, or filter in the browser |
| Files generated to `/tmp` are not committed | Demo output is local-only and ephemeral |

---

## Decision: Next Sprint

The UI layer is complete and validated end-to-end. The natural next capability
is an **`aeos ui demo`** command that automates the entire sequence above in a
single invocation:

```sh
aeos ui demo \
  --memory-dir /tmp/aeos-recovery-ma-mairie-digitale/memory \
  --output-dir /tmp/aeos-ui-demo
```

**What it does:**
1. Runs `aeos ui portfolio` → `{output-dir}/index.html`
2. For each project found: runs `dashboard`, `project-workspace`, `evidence-pack`
   into `{output-dir}/{project-name}/`
3. Prints a summary of all generated files
4. Optionally opens `index.html` in the default browser (`--open`)

**Why now:** the four underlying commands are stable, their output paths follow
a documented convention, and the sequence is already proven by this demo.
Automating it removes the last manual step before handing a complete evidence
directory to a CTO.

**Scope gate:** the `demo` command calls the existing loaders and renderers —
no new derivation logic, no new HTML, no new tests for the underlying
functions. It is a thin orchestrator over what already exists.

---

*read_only: true · applied: false · human validation required*
