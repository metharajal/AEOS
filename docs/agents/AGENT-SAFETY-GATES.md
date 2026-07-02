# AEOS Agent Safety Gates

**Version:** 1.0
**Sprint:** MVP-AGENTS-1
**Status:** RATIFIED

---

## Core Principle

> Agent proposes. AEOS verifies. Human validates.

No agent action in AEOS bypasses all three stages. If any stage is missing,
the action does not proceed.

---

## Mandatory Gates — Ordered

Every agent run passes through these gates in sequence. A failure at any gate
terminates the agent run and returns a structured error with the gate name and
reason.

### Gate 1 — Environment Integrity

Before any agent reads project data, AEOS verifies:

| Check | Pass condition | Failure action |
|-------|---------------|----------------|
| Registry exists | `~/.aeos/projects.json` present | Abort · suggest `aeos workspace init` |
| Registry readable | Valid JSON | Abort · suggest manual inspection |
| Registry `read_only: true` | Flag present and true | Abort · log anomaly |
| Registry `local_only: true` | Flag present and true | Abort · log anomaly |
| No `.env` in scope | No `.env` file referenced in context | Abort · log violation |

### Gate 2 — Project Scope

Before an agent accesses a specific project:

| Check | Pass condition | Failure action |
|-------|---------------|----------------|
| Project registered | Name in `~/.aeos/projects.json` | Abort · suggest `aeos project register` |
| `memory_dir` exists | Directory on disk | Abort · log missing dir |
| `memory_dir` contains MemoryRecords | At least one `.json` file | Warn · continue with empty set |
| Project `read_only: true` | Flag present and true | Abort · log anomaly |

### Gate 3 — Context Sanitisation

Before any data is loaded into the agent's context window:

| Check | Pass condition | Failure action |
|-------|---------------|----------------|
| No secrets in payload | No `.env` content, no tokens, no keys | Abort · log field names |
| No file contents | Only metadata fields, not raw file text | Strip · log |
| No connection strings | No DSN, JDBC, or similar | Strip · log |
| Context size within limit | Under configured token budget | Truncate · log |

### Gate 4 — Output Review

Before any agent output is written to disk or displayed:

| Check | Pass condition | Failure action |
|-------|---------------|----------------|
| Output contains no secrets | Pattern-matched against known secret formats | Strip · warn |
| Output marked read-only | Contains `read_only: true · applied: false` | Append marker |
| Output does not include SQL | No executable `ALTER`, `DROP`, `INSERT` | Strip · warn |
| Output is structured | Valid Markdown or JSON | Reject unstructured output |

### Gate 5 — Human Validation

Before any recommendation becomes actionable:

| Check | Pass condition | Failure action |
|-------|---------------|----------------|
| Human has reviewed output | Explicit acknowledgement required | Block apply |
| Human has typed `--apply` | No implicit apply mode | Block apply |
| Evidence record written | Audit trail exists before apply | Block apply |

---

## Forbidden Files

The following files must never be read by any agent, at any time, under any
circumstance:

```
.env
.env.local
.env.production
.env.staging
.env.test
.envrc
secrets.json
credentials.json
*.pem
*.key
*.p12
*.pfx
id_rsa
id_ed25519
~/.ssh/*
~/.aws/credentials
~/.config/gcloud/credentials.db
```

If an agent receives a path that resolves to one of these files, it must:
1. Refuse to read the file
2. Log the attempted path (not the content)
3. Return an explicit error to the caller
4. Not silently skip or ignore — the refusal must be visible

---

## Forbidden Operations

The following operations are forbidden regardless of agent capability or user
instruction:

| Operation | Why |
|-----------|-----|
| `exec()`, `subprocess`, `os.system()` | Arbitrary code execution |
| `open(..., 'w')` on client project files | Write to client scope |
| SQL `ALTER`, `DROP`, `CREATE`, `INSERT`, `UPDATE`, `DELETE` | Migration apply |
| `git commit`, `git push` without human `--apply` | Autonomous commit |
| `requests.get/post` without explicit user opt-in | Network call |
| `json.loads(.env content)` | Secret parsing |
| Modifying `~/.aeos/projects.json` | Registry mutation |
| Modifying any `MemoryRecord` file | Evidence corruption |

---

## Conditions for PR Proposal Generation

An agent may generate a PR description (never open the PR) when:

1. Gate 1–5 have all passed
2. The human has explicitly requested a PR proposal
3. The proposal contains only: title, body, checklist — no code diffs
4. The proposal is marked `read_only: true · applied: false`
5. The proposal references specific evidence files for every claim
6. The human reviews and explicitly runs `gh pr create` themselves

An agent must never call `gh pr create` autonomously.

---

## Conditions for Refusing a Request

An agent must refuse and explain when:

| Condition | Required response |
|-----------|-----------------|
| Request involves reading `.env` | "Refused: secrets are outside agent scope." |
| Request involves writing to client files | "Refused: agents are read-only in AEOS." |
| Request asks to apply a migration | "Refused: migrations require human `--apply`." |
| Request asks to commit autonomously | "Refused: commits require human confirmation." |
| Request asks to send data to external API without consent | "Refused: network call requires explicit opt-in." |
| Context payload would include secrets | "Refused: context sanitisation failed." |
| Project not registered in AEOS | "Refused: project not in registry — run `aeos project register`." |

The refusal message must:
- Be explicit and non-apologetic
- Name the specific policy violated
- Suggest the correct human-controlled alternative
- Be logged in the agent evidence trail

---

## Logs and Evidence Expected

Every agent run produces a structured log entry containing:

```json
{
  "timestamp": "2026-07-02T00:00:00Z",
  "agent_type": "local-analyst",
  "model": "local/ollama/llama3",
  "project": "my-project",
  "gates_passed": ["env-integrity", "project-scope", "context-sanitisation"],
  "gates_failed": [],
  "context_fields_included": ["status", "findings_count", "audit_date"],
  "context_fields_excluded": [],
  "output_type": "recommendation-list",
  "secrets_detected_and_stripped": 0,
  "human_decision": null,
  "applied": false,
  "read_only": true
}
```

This log is written before the output is shown to the human. It is immutable
once written. It is never deleted by subsequent runs.

---

## Summary: The Three-Stage Rule

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   AGENT PROPOSES   →   AEOS VERIFIES   →   HUMAN VALIDATES │
│                                                         │
│   (Gates 1–3)          (Gate 4)            (Gate 5)    │
│                                                         │
│   No stage can be skipped.                              │
│   No stage can be automated away.                       │
│   Human validation is always the final gate.            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```
