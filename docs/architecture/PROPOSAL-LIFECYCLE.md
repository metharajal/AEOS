# AEOS Proposal Lifecycle Contract

**Version:** 1.0
**Status:** PROPOSED
**Date:** 2026-07-02
**Sprint:** MVP-AGENTS-6B
**Authority:** [CONSTITUTION.md](../../CONSTITUTION.md) §5.3 · [AI-RUNTIME-DOCTRINE.md](AI-RUNTIME-DOCTRINE.md)

---

## Purpose

This document defines the complete lifecycle contract for an AEOS Proposal.

It is the architecture reference for every past, present, and future component that
creates, reads, transforms, stores, applies, or archives a Proposal. Before any code
implementing `aeos agent pr apply` is written, every architecture decision must be
resolvable from this document alone.

This document does not implement anything. It freezes decisions.

---

## Clarification: Two Distinct Objects

The current codebase contains two objects whose names overlap but whose roles are
different. The lifecycle contract must be understood as operating on **both** objects.

### PRProposal — ephemeral, rich, generated in memory

Defined in `src/aeos/agent/pr_proposal.py`.

`PRProposal` is a 14-section rich dataclass generated deterministically from
MemoryRecords. It is **never persisted to disk by AEOS**. It lives in memory
for the duration of a CLI invocation, then disappears. It contains:

- Title, objective, why-now reasoning
- Recommended scope (4–8 items)
- Out-of-scope list (permanent, from `_OUT_OF_SCOPE_ALWAYS`)
- Likely files (candidate + confirmed)
- Safety constraints (permanent, from `_SAFETY_CONSTRAINTS`)
- Implementation steps (numbered, project-specific)
- Validation commands
- Human approval checklist (checkboxes)
- Risks
- Rollback notes
- Evidence references (counts, IDs, paths)
- Invariant flags: `read_only=True`, `applied=False`, `human_validation_required=True`

`PRProposal` is the **reasoning product**. It is what an agent produces.

### Proposal — persisted, minimal, stored in JSON

Defined in `src/aeos/agent/pr_management.py`.

`Proposal` is the lightweight dataclass that represents a persisted proposal on
disk at `~/.aeos/workspace/proposals/<id>/proposal.json`. It contains only:

```json
{
  "id":           "string",
  "title":        "string",
  "status":       "pending | applied | dismissed",
  "created_at":   "ISO 8601",
  "summary":      "string",
  "files":        ["list of strings"],
  "diff_preview": "string | null"
}
```

`Proposal` is the **governance record**. It is what is tracked, listed, shown,
and eventually acted upon.

### The intentional gap between them

AEOS currently has no `aeos agent pr save` command. The transition from
`PRProposal` (ephemeral) to `Proposal` (persisted) is a **human action**:

```
aeos agent pr-proposal --output proposal.md   # human reads
human decides: worth saving?
human creates: ~/.aeos/workspace/proposals/<id>/proposal.json
aeos agent pr list                            # now visible
```

**This gap is intentional**, not a missing feature. It is a human gate. An
operator must make an explicit decision to persist a proposal before it becomes
a governance record. This prevents automatic accumulation of un-reviewed proposals.

The contract for this transition is defined in §5 (Data Structure) and §6 (Ownership).

---

## 1. What Is a Proposal?

### 1.1 Role

A Proposal is the **contract between AEOS's analysis and a human's action**.

It is the artifact that translates a machine-readable audit result (MemoryRecord)
into a human-reviewable, human-executable plan. It is not a suggestion. It is not
a command. It is a structured, evidence-backed proposal that a human must validate
before anything is executed.

### 1.2 Responsibility

A Proposal is responsible for:
- Stating precisely what should be done (scope)
- Stating precisely what should NOT be done (out of scope)
- Citing the evidence that justifies the proposal (evidence references)
- Providing a validation checklist that must be cleared before merge
- Providing rollback notes in case of failure
- Carrying its governance flags at all times: `read_only: true · applied: false`

A Proposal is NOT responsible for:
- Executing any action
- Opening a GitHub PR
- Pushing code
- Running migrations
- Making any decision on behalf of the human

### 1.3 Scope

A single Proposal:
- Targets one project (one `project_name`)
- Addresses findings from the most recent MemoryRecord
- Has a single status at any point in time
- Is immutable after creation (fields are not edited in-place — see §4)
- Has a unique ID that never changes

### 1.4 Invariants (object-level)

```
PROP.01  A Proposal always has: id, title, status, created_at
PROP.02  A Proposal's id never changes after creation
PROP.03  A Proposal's created_at never changes after creation
PROP.04  A Proposal carries read_only: true from creation to archival
PROP.05  A Proposal carries applied: false until status = applied
PROP.06  A Proposal is immutable — fields are not edited; state transitions
         create a new version or write to a separate log (see §5.4)
PROP.07  A Proposal must cite evidence before status can leave pending
PROP.08  A Proposal without evidence_references is invalid
```

---

## 2. Lifecycle

### 2.1 Complete lifecycle diagram

```
MemoryRecord files
(~/<project>/memory/<id>.json)
         │
         │  aeos reclaim harden --path <project>
         │  creates one MemoryRecord per run
         ▼
MemoryRecord (latest)
findings_summary: {critical, important, manual, generated}
control_level, providers, production_ready
         │
         │  aeos agent plan --project <name>
         │  (deterministic, no LLM, read-only)
         ▼
AgentPlan [ephemeral in memory]
risks, actions, global_status per project
         │
         │  aeos agent pr-proposal --project <name> [--output file]
         │  (deterministic, no LLM, read-only, may write --output file)
         ▼
PRProposal [ephemeral in memory]                ←── 14-section rich object
title, objective, scope, steps, checklist,          disappears after CLI exits
rollback, evidence_references
         │
         │  HUMAN GATE 1 — review
         │  Human reads PRProposal (terminal or --output file)
         │  Human decides: is this worth persisting?
         ▼
 ┌─ NO: discard, do not save, run again later
 │
 └─ YES: human creates proposal.json manually
         OR (future) aeos agent pr save <id>
         │
         │  ~/.aeos/workspace/proposals/<id>/proposal.json
         ▼
Proposal [persisted]                            ←── minimal governance record
{id, title, status: pending,                        status starts at pending
 created_at, summary, files, diff_preview}
         │
         │  aeos agent pr list
         │  aeos agent pr show <id>
         ▼
Proposal visible in ProposalRepository          ←── read-only listing
status: pending
         │
         │  (optional) aeos ui project-workspace
         │  (optional) aeos workspace demo
         ▼
Proposal visible in Workspace HTML              ←── "Suggested PR" section
         │
         │  HUMAN GATE 2 — validation
         │  Human reviews show output + workspace
         │  Human validates: approval checklist, evidence, rollback
         ▼
 ┌─ DISMISSED: human sets status: dismissed
 │  aeos agent pr dismiss <id>  (future)
 │  status: dismissed → archived, never applied
 │
 └─ APPROVED: human creates PR manually (gh pr create)
         │
         │  HUMAN GATE 3 — apply
         │  Human runs: aeos workspace apply-pr <id>
         │  OR: aeos agent pr apply <id>  (future — see §10)
         ▼
Apply Engine [future]
preconditions verified (see §10)
backup created
dry-run executed
human confirms
changes applied
         │
         ▼
Proposal status → applied
apply_log created (~/.aeos/workspace/proposals/<id>/apply-log.json)
         │
         ▼
MemoryRecord regenerated                        ←── HUMAN GATE 4 — verify
aeos reclaim harden --path <project>
         │
         ▼
Evidence updated
aeos workspace demo --overwrite
         │
         ▼
History preserved
~/.aeos/workspace/proposals/<id>/
  proposal.json      (status: applied)
  apply-log.json     (immutable apply record)
  pre-apply-memory/  (snapshot of MemoryRecord before apply)
```

### 2.2 The four human gates

Every state transition requires a human action. There are no automatic progressions.

| Gate | What the human does | What AEOS does |
|---|---|---|
| Gate 1 — Review | Reads PRProposal, decides to persist | Nothing — waits |
| Gate 2 — Validate | Reviews show output, approval checklist | Nothing — waits |
| Gate 3 — Apply | Runs apply command explicitly | Verifies preconditions, then executes |
| Gate 4 — Verify | Runs harden + workspace demo | Creates new MemoryRecord evidence |

None of the four gates can be automated, skipped, or bypassed via flag.

---

## 3. States

### 3.1 Current states

```
ProposalStatus(StrEnum):
  pending    # created, awaiting human decision
  applied    # apply engine ran successfully, human confirmed
  dismissed  # human explicitly closed without applying
```

**State transition rules:**

```
pending → applied      requires: Apply Engine ran + human confirmed (Gate 3)
pending → dismissed    requires: explicit human action (future: aeos agent pr dismiss)
applied → (terminal)   no further transitions — immutable
dismissed → (terminal) no further transitions — immutable
```

**There is no `pending → pending` update.** A Proposal is never edited. If
findings change, a new Proposal is generated and a new lifecycle begins.

### 3.2 Are current states sufficient?

For V1 (the MVP), yes. Three states cover all lifecycle paths:
- Everything starts as `pending`
- It ends as either `applied` (done) or `dismissed` (closed)
- Nothing needs to be in-between for the first implementation of Apply

### 3.3 Future states (documented, not implemented)

These states are not part of the current codebase. They are documented here so
that future sprints can adopt them without breaking the existing status contract.

| Status | When | Notes |
|---|---|---|
| `in_review` | Proposal is on a PR that has been opened but not merged | Intermediate — avoids confusion when PR is open |
| `blocked` | Apply preconditions failed — human must resolve manually | Explicit "stopped" state distinct from dismissed |
| `partially_applied` | Apply ran but not all items were completed | Only relevant for multi-step apply |
| `expired` | Proposal not acted on within a defined TTL | Optional — AEOS may warn rather than auto-expire |

**Decision deferred to MVP-AGENTS-7:** whether to add `in_review` before `applied`.

---

## 4. Invariants

### 4.1 Lifecycle invariants

```
LC.01  A Proposal is never modified after creation.
       New findings → new Proposal. Never edit proposal.json in-place.

LC.02  Status transitions are one-way and terminal.
       pending → applied or pending → dismissed. Nothing reverts.

LC.03  No status transition happens without a human action.
       No background process, no agent, no timer changes status.

LC.04  An applied Proposal creates an apply-log.json before any change is applied.
       If apply-log.json cannot be written, the apply engine aborts.

LC.05  A dismissed Proposal is preserved, not deleted.
       Dismissal is governance evidence. The directory is kept.

LC.06  A Proposal's storage directory is named after its id.
       ~/.aeos/workspace/proposals/<id>/   — directory name = proposal id.
```

### 4.2 Read-only invariants

```
RO.01  ProposalRepository.list() never writes to the proposals directory.
RO.02  ProposalRepository.get() never writes to the proposals directory.
RO.03  render_proposal_list() and render_proposal_detail() are pure functions.
RO.04  aeos agent pr list and aeos agent pr show produce no side effects.
RO.05  aeos agent pr-proposal produces no side effects unless --output is used.
RO.06  The --output file is an operator-controlled write, not an internal side effect.
```

### 4.3 Security invariants

```
SEC.01  No Proposal contains secret values (API keys, tokens, passwords).
SEC.02  No Proposal contains file contents (source code, SQL, config files).
SEC.03  The diff_preview field is capped at 20 lines (enforced by render_proposal_detail).
SEC.04  No network call is made at any stage of the lifecycle.
SEC.05  No GitHub API is called at any stage.
SEC.06  No git command is run by AEOS at any stage.
SEC.07  The apply engine (future) must create a backup before any write.
        If backup fails, apply aborts. No exceptions.
```

### 4.4 Evidence invariants

```
EV.01  A Proposal must reference at least one MemoryRecord (latest_record_id).
EV.02  An applied Proposal produces an apply-log.json immutable after creation.
EV.03  A pre-apply snapshot of MemoryRecord data is preserved before any apply.
EV.04  Evidence is never regenerated retroactively.
        What was true at generation time is preserved as-is.
```

---

## 5. Data Structure

### 5.1 Storage layout

```
~/.aeos/workspace/proposals/
└── <proposal-id>/                        # directory name = id (UUID or slug)
    ├── proposal.json                     # required — persisted Proposal (§5.2)
    ├── summary.md                        # optional — human-readable full summary
    ├── diff.patch                        # optional — unified diff of proposed changes
    └── apply-log.json                    # written by Apply Engine only (§5.4)
        (not present until status = applied)
```

### 5.2 `proposal.json` — complete schema

**Version 1 (current):**

```json
{
  "schema_version": "1",
  "id":           "string — unique identifier, slug or UUID, URL-safe",
  "title":        "string — one line, imperative, human-readable",
  "status":       "pending | applied | dismissed",
  "created_at":   "string — ISO 8601, UTC, e.g. 2026-07-02T10:00:00Z",
  "summary":      "string — 1-3 sentences describing the purpose",
  "files":        ["list of strings — relative paths (candidates or confirmed)"],
  "diff_preview": "string | null — first 20 lines of unified diff, or null"
}
```

**Required fields (V1):** `id`, `title`, `status`, `created_at`

**Optional fields (V1):** `summary`, `files`, `diff_preview`

**Field contracts:**

| Field | Type | Constraint |
|---|---|---|
| `schema_version` | string | Must be present from V1 onward. Currently `"1"`. |
| `id` | string | Non-empty. URL-safe. Matches parent directory name. |
| `title` | string | Non-empty. Single line. No newlines. |
| `status` | string | One of: `pending`, `applied`, `dismissed`. |
| `created_at` | string | ISO 8601 UTC. Never changes after creation. |
| `summary` | string | May be empty string. No secret values. |
| `files` | list[string] | Relative paths only. No absolute paths. No home dir. |
| `diff_preview` | string or null | Max 20 lines. No secret values. No credentials. |

**What `proposal.json` must never contain:**

- Secret values (API keys, passwords, tokens, connection strings)
- File contents (full source code, SQL migrations, config file bodies)
- Absolute paths outside the project directory
- User credentials or PII
- Data that was not present at proposal generation time

### 5.3 `summary.md` — optional human-readable document

The `summary.md` file is the bridge between the ephemeral `PRProposal` (14 sections,
generated in memory) and the persisted `proposal.json` (minimal, 7 fields).

When AEOS generates a `PRProposal` and the operator saves it, the operator may also
save the full `--output proposal.md` file as `summary.md` in the proposal directory.
This preserves the full reasoning (objective, scope, checklist, rollback notes) for
later reference.

**Format:** Markdown, human-readable, no mandatory structure.
**Who writes it:** The operator, or a future `aeos agent pr save` command.
**Read by:** Human reviewers. Workspace HTML (optional section). Not parsed by AEOS.

### 5.4 `diff.patch` — optional unified diff

The `diff.patch` file is a standard unified diff of the proposed file changes. It is
used for:
- Human review of exact proposed changes before apply
- Optional display in workspace HTML
- Pre-apply integrity check (apply engine verifies the diff still applies cleanly)

**Format:** Standard unified diff (GNU diff / git diff format).
**Who writes it:** The operator (generated separately, e.g. `git diff > diff.patch`).
  OR a future agent that produces diffs deterministically.
**Required for apply?** Deferred decision — see §10.3.

### 5.5 `apply-log.json` — written by Apply Engine only

```json
{
  "proposal_id":     "string — matches parent directory",
  "applied_at":      "ISO 8601 UTC",
  "applied_by":      "string — 'aeos agent pr apply' or 'aeos workspace apply-pr'",
  "aeos_version":    "string — AEOS version at apply time",
  "pre_apply_harden_record_id": "string — MemoryRecord id before apply",
  "steps_applied":   ["list of strings — each step that ran"],
  "steps_skipped":   ["list of strings — steps skipped with reason"],
  "backup_path":     "string | null — path to pre-apply backup",
  "validation_result": "passed | failed | not_run",
  "human_confirmed": true,
  "notes":           "string | null"
}
```

**Immutable.** Once written, `apply-log.json` is never modified.
**Written before apply begins**, then updated with result.
**If apply fails mid-way**, `apply-log.json` reflects the partial state and
`steps_applied` contains only the steps that completed successfully.

### 5.6 Versioning

The `schema_version` field in `proposal.json` enables non-breaking evolution:

| Version | Fields | Notes |
|---|---|---|
| `"1"` (current) | id, title, status, created_at, summary, files, diff_preview | Baseline |
| Future | +evidence_hash, +parent_proposal_id, +tags | To be defined via RFC |

`ProposalRepository._parse_proposal()` must remain backward-compatible with V1 indefinitely.
When V2 fields are added, the parser must continue to read V1 files without error.

**Decision frozen:** The parser uses `raw.get("field", default)` — missing fields
are always silently defaulted, never errors (except for the 4 required fields).

---

## 6. Ownership

The ownership matrix answers: **who is allowed to perform each operation?**

| Operation | Actor | Mechanism | Notes |
|---|---|---|---|
| **Create PRProposal** | AEOS Agent | `generate_pr_proposal()` / `generate_pr_proposal_from_memory()` | Ephemeral, no disk write |
| **Persist to proposal.json** | Human operator | Manual file creation OR future `aeos agent pr save` | Gate 1 — intentional human gate |
| **Read (list)** | AEOS Agent / Human | `ProposalRepository.list()` / `aeos agent pr list` | Read-only |
| **Read (show)** | AEOS Agent / Human | `ProposalRepository.get()` / `aeos agent pr show` | Read-only |
| **Render in Workspace** | AEOS UI Engine | `aeos workspace demo` / `aeos ui project-workspace` | Read-only HTML |
| **Dismiss** | Human operator | Future `aeos agent pr dismiss <id>` | Writes status in proposal.json |
| **Apply** | Human operator | Future `aeos agent pr apply <id>` or `aeos workspace apply-pr <id>` | Gate 3 — explicit |
| **Archive** | Human operator | No dedicated command — dismissed/applied proposals are already preserved | Manual cleanup optional |
| **Delete** | Human operator | Manual `rm -rf ~/.aeos/workspace/proposals/<id>/` | AEOS never auto-deletes |

**What the AEOS Agent may never do:**
- Persist a Proposal without human instruction
- Change a Proposal's status without human instruction
- Apply a Proposal autonomously
- Delete a Proposal or its directory
- Modify a Proposal's `id`, `title`, or `created_at`

---

## 7. Security Contract

### 7.1 Gates in the lifecycle

| Gate | Point in lifecycle | Check | Abort condition |
|---|---|---|---|
| **Context gate** | PRProposal generation | Secret pattern scan on all output fields | Any secret pattern → abort generation |
| **Persistence gate** | proposal.json creation | Field validation on load | Invalid JSON → skip (list) or raise (show) |
| **Apply gate** | Apply Engine entry | Full preconditions check (see §10.2) | Any precondition fails → abort |
| **Backup gate** | Apply Engine pre-write | Backup creation | Backup fails → abort, never write |
| **Confirmation gate** | Apply Engine execution | Explicit human confirmation | No confirmation → abort |

### 7.2 Auditability

Every proposal leaves an audit trail across two storage locations:

**`proposal.json`** — what was proposed, when, in what state.

**`apply-log.json`** — if applied: what ran, when, what was the pre-apply state.

**MemoryRecord sequence** — the MemoryRecord before apply and the MemoryRecord after apply
(regenerated via `aeos reclaim harden` post-apply) together form the delta evidence.

A complete audit of a proposal includes: the original PRProposal output (if saved in
`summary.md`), the `proposal.json`, the `apply-log.json`, and the two MemoryRecords.

### 7.3 Rollback contract

Rollback is always possible for proposals that have not been applied to production.
The rollback path depends on what the proposal contained:

| Proposal type | Rollback mechanism |
|---|---|
| Documentation only | `git revert <commit>` |
| SQL migration (staging) | `supabase migration revert` or restore staging snapshot |
| Governance file update | `git revert` |
| Code change | `git revert <commit>` |
| Production migration | Not allowed via AEOS Proposal — out of scope permanently |

**Contract:** The Apply Engine must write rollback instructions to `apply-log.json`
before executing any step. If rollback is not possible for a given step, that step
must be explicitly flagged and require a second confirmation.

---

## 8. Agent Contract

### 8.1 What agents may do today

| Capability | Command | Notes |
|---|---|---|
| Generate PRProposal | `aeos agent pr-proposal` | Deterministic, ephemeral |
| Generate AgentPlan | `aeos agent plan` | Deterministic, ephemeral |
| List Proposals | `aeos agent pr list` | Read-only |
| Show Proposal | `aeos agent pr show <id>` | Read-only |

### 8.2 What agents may do in future sprints

| Capability | Planned command | Gate required |
|---|---|---|
| Save PRProposal to disk | `aeos agent pr save <id>` | Gate 1 — human confirms save |
| Dismiss a Proposal | `aeos agent pr dismiss <id>` | Gate 2 — human confirms dismiss |
| Apply a Proposal | `aeos agent pr apply <id>` | Gate 3 — explicit confirmation (see §10) |

### 8.3 What agents may never do

These restrictions are permanent. They cannot be lifted by sprint, by flag, or by
model capability.

```
AGENT.01  An agent never opens a GitHub PR autonomously.
AGENT.02  An agent never pushes code to any repository.
AGENT.03  An agent never applies a Proposal without explicit human confirmation.
AGENT.04  An agent never modifies a Proposal's id, title, or created_at.
AGENT.05  An agent never deletes a Proposal or its directory.
AGENT.06  An agent never runs a database migration against a production database.
AGENT.07  An agent never reads .env files or environment secrets.
AGENT.08  An agent never modifies existing MemoryRecords.
AGENT.09  An agent never runs without producing a log entry (apply-log or AIInteractionLog).
AGENT.10  An agent never produces output with applied: true or read_only: false.
```

---

## 9. Workspace Contract

### 9.1 Relationships

```
                     AEOS Ecosystem Relationships

MemoryRecord  ─────── generates ──────► PRProposal (ephemeral)
     │                                       │
     │                                       │ human persists
     │                                       ▼
     │                              Proposal (proposal.json)
     │                                       │
     ▼                                       ▼
  Registry                         ProposalRepository
  (projects.json)                  (read-only store)
     │                                       │
     └─────────────────┬─────────────────────┘
                       │
                       ▼
              Workspace HTML
       (aeos workspace demo / aeos ui project-workspace)
       - Reads MemoryRecords → "Findings" section
       - Reads AgentPlan    → "Recommendations" section
       - Reads PRProposal   → "Suggested PR" section
       - Reads Registry     → project metadata
                       │
                       ▼
            Evidence Pack (9 files)
            (aeos ui evidence-pack)
       - Includes PRProposal as pr-proposal.md
       - Does NOT include proposal.json (that's internal to AEOS)
```

### 9.2 Workspace → Proposal: one-way read

The Workspace reads Proposals (via `PRProposal` regeneration or from persisted
`proposal.json` in the future) but never writes to them. The Workspace is a
read-only view of the current state of a project.

### 9.3 Evidence Pack → Proposal: inclusion rule

The Evidence Pack (`aeos ui evidence-pack`) includes the PRProposal as a markdown
file (`pr-proposal.md`). It does NOT include `proposal.json` — that file is
internal to AEOS's governance layer and does not belong in an evidence pack
delivered to a client or investor.

**The boundary:** Evidence Pack = outward-facing (client/investor). Proposal
directory = inward-facing (operator governance).

### 9.4 Memory ↔ Proposal: the dependency chain

```
aeos reclaim harden → MemoryRecord → generate_pr_proposal_from_memory → PRProposal
                                   ↑
                        No Proposal exists without at least one MemoryRecord.
                        A PRProposal always cites latest_record_id.
                        An apply-log always cites pre_apply_harden_record_id.
```

A Proposal without a valid `latest_record_id` is an invalid Proposal. The Apply
Engine must verify that the cited MemoryRecord still exists before applying.

---

## 10. Apply Engine Contract

This section defines the complete preconditions for `aeos agent pr apply <id>`.
No implementation is specified. Every decision that an implementer would otherwise
need to make is resolved here.

### 10.1 What the Apply Engine is

The Apply Engine is the controlled, human-gated mechanism that executes the
changes described in a Proposal. It is the only AEOS component that may write to
a project directory or a database.

The Apply Engine is not:
- A code generator
- An AI agent
- A migration tool
- A deployment pipeline

It is an **orchestrator that executes a pre-validated, human-approved sequence of
steps** and produces an immutable evidence record of what happened.

### 10.2 Preconditions — all must pass before any write

```
APPLY.PRE.01  Proposal exists: proposal.json is present and parseable
APPLY.PRE.02  Status is pending: status must equal "pending" (never re-apply)
APPLY.PRE.03  MemoryRecord cited in evidence_references exists on disk
APPLY.PRE.04  Project path exists: the target project directory is accessible
APPLY.PRE.05  No apply-log.json exists: prevents double-apply
APPLY.PRE.06  Backup is possible: apply-log.json can be written to the proposal dir
APPLY.PRE.07  ruff, mypy, pytest pass on the project (if Python project)
              OR equivalent quality gate for other project types
APPLY.PRE.08  Human has typed explicit confirmation (not a flag, not --yes)
APPLY.PRE.09  (If diff.patch present) diff applies cleanly to current working tree
APPLY.PRE.10  No uncommitted changes in the project working tree
```

If any precondition fails, the Apply Engine aborts. It writes an `apply-log.json`
with `validation_result: "failed"` and logs which precondition failed.

### 10.3 Apply sequence

```
Step 0:  Write apply-log.json with status "started"
         (Abort if cannot write — disk full, permissions, etc.)

Step 1:  Create pre-apply MemoryRecord snapshot
         (aeos reclaim harden --path <project> --output pre-apply-memory/)
         (Abort if harden fails)

Step 2:  [For each proposed change]:
         2a. Display the specific change to the human
         2b. Human confirms each change individually (or confirms all)
         2c. Execute the change
         2d. Write to apply-log.json: step completed

Step 3:  Run post-apply validation
         (aeos reclaim harden --path <project>)
         (Run quality gates if applicable)

Step 4:  Update proposal.json: status → applied
Step 5:  Update apply-log.json: validation_result, completed_at

Step 6:  Display summary to human
         "N steps applied. M steps skipped. Evidence at <path>."
         "Next: aeos workspace demo --overwrite"
```

### 10.4 Atomicity contract

The Apply Engine must behave atomically at the step level:
- Each step either completes fully or is logged as failed
- Failed steps do not trigger automatic rollback (human decides)
- Partial apply is a valid outcome — `steps_applied` in apply-log.json reflects it

The Apply Engine must NOT attempt full transaction semantics (all-or-nothing).
This is too complex for V1 and creates false confidence. Instead:
- Partial apply is documented
- Rollback is documented in apply-log.json
- Human runs `git revert` or restores backup manually if needed

### 10.5 Decisions frozen for the Apply Engine

These decisions are made here so that MVP-AGENTS-7 or the Apply sprint does not
re-debate them.

| Decision | Choice | Rationale |
|---|---|---|
| Atomicity model | Per-step, not full transaction | Too complex for V1; partial apply + log is safer |
| Human confirmation | Required once per apply run, not per step | Reduces friction while maintaining gate |
| Status update timing | Step 4 only AFTER Step 3 validation passes | Status must reflect verified apply, not just execution |
| Backup strategy | Pre-apply harden snapshot (always) | Makes rollback evidence-backed |
| diff.patch requirement | Optional in V1 — not required | Projects may not have diffs pre-computed |
| Production guard | Apply Engine rejects `production` target | Staging only in V1 — always |
| Double-apply guard | Abort if apply-log.json exists (APPLY.PRE.05) | Idempotency preserved by refusal |
| Re-apply mechanism | Not supported in V1 — new Proposal required | Simpler, cleaner audit trail |

### 10.6 What the Apply Engine never does

```
AE.01  The Apply Engine never runs without an existing proposal.json
AE.02  The Apply Engine never runs against a production database
AE.03  The Apply Engine never runs if apply-log.json already exists
AE.04  The Apply Engine never modifies an existing MemoryRecord
AE.05  The Apply Engine never skips the backup step (APPLY.PRE.06)
AE.06  The Apply Engine never generates new diffs — it applies existing ones
AE.07  The Apply Engine never pushes to a remote git repository
AE.08  The Apply Engine never opens a GitHub PR
AE.09  The Apply Engine never runs without human confirmation (typed, not flagged)
AE.10  The Apply Engine never produces output with applied: true
       before Step 4 (post-validation status update) is complete
```

---

## 11. Summary

### 11.1 Architecture decisions frozen by this document

| # | Decision |
|---|---|
| D1 | `PRProposal` (ephemeral) and `Proposal` (persisted) are two distinct objects. |
| D2 | The transition from PRProposal to Proposal is a human gate (not automatic). |
| D3 | A Proposal is immutable after creation. State changes do not edit fields. |
| D4 | Three terminal states: `pending`, `applied`, `dismissed`. No rollback of state. |
| D5 | `proposal.json` schema V1 defined. `schema_version` field required for forward compatibility. |
| D6 | `apply-log.json` is written before apply begins, updated with result. |
| D7 | Apply Engine uses per-step atomicity, not full transaction semantics. |
| D8 | Apply Engine requires backup (pre-apply harden snapshot) before any write. |
| D9 | Apply Engine requires explicit typed confirmation, not a CLI flag. |
| D10 | Apply Engine never runs against production. Staging only in V1. |
| D11 | `diff.patch` is optional in V1. Apply Engine does not require it. |
| D12 | Evidence Pack contains `pr-proposal.md`, not `proposal.json`. |
| D13 | Deleted proposals: AEOS never auto-deletes. Human deletes manually if desired. |
| D14 | Dismissed proposals are preserved. Dismissal is governance evidence. |

### 11.2 Invariants

All invariants defined in §4 (PROP.01–.08, RO.01–.06, SEC.01–.07, EV.01–.04),
§8 (AGENT.01–.10), and §10 (APPLY.PRE.01–.10, AE.01–.10) are permanent.
They cannot be lifted by sprint, by configuration, or by model capability.

### 11.3 Risks avoided

| Risk | Prevention |
|---|---|
| Apply runs twice (double-apply) | `apply-log.json` existence check (APPLY.PRE.05) |
| Apply runs on a production database | Production guard (AE.02) — permanent |
| State update without validated apply | Status only updated after Step 3 (D8) |
| Evidence gap after apply | apply-log.json + pre-apply snapshot mandatory (D6, D8) |
| Proposal accumulates without review | Persist is a human gate — not automatic (D2) |
| Proposal ID collision | Directory name = ID — filesystem enforces uniqueness |
| Partial apply goes unnoticed | Per-step logging in apply-log.json + steps_applied/steps_skipped |
| Secret in proposal.json | Context gate in PRProposal generation (SEC.01) |
| Proposal edited retroactively | Immutability invariant (D3, PROP.06) |
| Schema drift breaks old proposals | schema_version + backward-compatible parser (§5.6) |

### 11.4 Questions deferred to future sprints

| Question | Deferred to |
|---|---|
| Implement `aeos agent pr save` | MVP-AGENTS-7 or dedicated sprint |
| Implement `aeos agent pr dismiss` | Same as apply sprint |
| Implement `aeos agent pr apply` | Dedicated Apply sprint (post-MVP-AGENTS-7) |
| Add `in_review` state | Deferred to Apply sprint |
| Define diff.patch generation | Apply sprint — how does AEOS generate or verify the diff? |
| Multi-step apply confirmation | V2 — V1 uses single confirmation |
| TTL / expiry for stale proposals | Optional V2 feature |
| Team-level proposal review (multi-user) | V3 — multi-user workspace required first |
| Apply to projects with no MemoryRecord | Out of scope — MemoryRecord always required |

---

## See Also

- [AI-RUNTIME-DOCTRINE.md](AI-RUNTIME-DOCTRINE.md) — AI runtime contract
- [ARCHITECTURE.md](../../ARCHITECTURE.md) — §7 source module structure
- [CONSTITUTION.md](../../CONSTITUTION.md) — §2 core invariants
- [docs/agents/AGENT-ROADMAP.md](../agents/AGENT-ROADMAP.md) — MVP-AGENTS-7/8 planning
- [docs/agents/AGENT-SAFETY-GATES.md](../agents/AGENT-SAFETY-GATES.md) — gate definitions
- `src/aeos/agent/pr_management.py` — Proposal, ProposalRepository, ProposalStatus
- `src/aeos/agent/pr_proposal.py` — PRProposal, generate_pr_proposal_from_memory
- `src/aeos/memory/models.py` — MemoryRecord
