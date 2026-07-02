# AEOS Local AI Assistant Policy

**Version:** 1.0
**Sprint:** MVP-AGENTS-1
**Status:** RATIFIED

---

## Product Positioning

> AEOS ne donne pas le contrôle à l'IA.
> AEOS rend l'ingénierie assistée par IA contrôlable.

AEOS occupies a distinct category from general-purpose AI coding assistants.
Where tools like Cursor, Copilot, or autonomous agents act on your codebase
without a guaranteed human checkpoint, AEOS treats AI as a **diagnostic layer**
that surfaces recommendations for human review — never as an executor.

The target user is a CTO or senior engineer who needs to:
- Understand the state of a recovered or audited codebase
- Receive prioritised, evidence-backed recommendations
- Retain full decision authority before any change is applied

AI assistance in AEOS is a **lens**, not a hand.

---

## Doctrine: Local-First AI

Every AI capability in AEOS defaults to local execution. Network calls to
frontier models (Claude, GPT-4, Gemini, etc.) are a controlled exception,
never the default, and require explicit human opt-in with data disclosure.

This doctrine protects:
- Client confidentiality (no project data leaves the machine by default)
- Auditability (all AI outputs are logged locally before any action)
- Sovereignty (the CTO controls what the AI sees and when)
- Compliance (no inadvertent transmission of regulated data)

Local AI stack preference order:
1. Deterministic Python analysis (no AI)
2. Locally-served open model (Ollama, LM Studio, or similar)
3. On-device model (Apple MLX, llama.cpp)
4. Frontier AI via explicit escalation (see `FRONTIER-AI-ESCALATION.md`)

---

## Role of AI Agents in AEOS

AI agents in AEOS are **read-only analysts**. Their role is to:

- Read MemoryRecords and audit findings
- Identify patterns across projects in the registry
- Draft summaries, risk narratives, and prioritised recommendation lists
- Propose PR descriptions and human-gate responses
- Flag anomalies that deterministic checks cannot detect

They do **not**:
- Write code to disk
- Apply migrations
- Commit changes
- Push branches
- Register or deregister projects
- Modify MemoryRecords
- Access credentials or environment variables

---

## What an Agent CAN Do

| Category | Permitted action |
|----------|-----------------|
| **Analysis** | Read MemoryRecords (counts, status, metadata) |
| **Analysis** | Read registry metadata (project names, types, paths) |
| **Analysis** | Read generated workspace HTML for audit trail |
| **Summarisation** | Draft human-readable summaries of findings |
| **Recommendations** | Propose ordered action lists with evidence references |
| **PR proposals** | Draft PR description text for human review |
| **Human gates** | Draft human-gate response text for human approval |
| **Diagnostics** | Interpret `workspace doctor` output |
| **Risk narrative** | Explain what a finding means in business terms |

---

## What an Agent CANNOT Do

The following actions are **permanently forbidden** regardless of user
instruction, model capability, or workflow context:

| Category | Forbidden action |
|----------|-----------------|
| **Secrets** | Read any `.env` file |
| **Secrets** | Read any secret, key, token, or credential |
| **Secrets** | Include secrets in any prompt or context payload |
| **Secrets** | Log secrets to any file or output stream |
| **Apply** | Execute SQL migrations |
| **Apply** | Write to any client project file |
| **Apply** | Commit code without explicit human `--apply` flag |
| **Apply** | Push to any remote branch autonomously |
| **Apply** | Modify MemoryRecords |
| **Apply** | Register or remove projects from the registry |
| **Network** | Contact external APIs without explicit user opt-in |
| **Network** | Transmit project file contents to any external service |
| **Scope** | Operate outside the registered project set |
| **Scope** | Access filesystem paths outside defined project roots |

---

## Secrets Policy

**No secret ever enters an AI context window.**

A secret is defined as any value that, if disclosed, would grant access to a
system or dataset not otherwise accessible. This includes:

- API keys, tokens, passwords, passphrases
- Database connection strings (even without passwords)
- Private keys (SSH, GPG, TLS)
- Session cookies or OAuth tokens
- Contents of `.env`, `.env.local`, `.env.production`, or equivalent files
- Contents of `secrets.json`, `credentials.json`, or equivalent files

AEOS enforces this by:
1. Never importing or reading `.env` files in any module
2. Constructing AI context payloads exclusively from MemoryRecord metadata
3. Explicitly stripping any string that matches common secret patterns before
   sending to any AI model
4. Logging what was sent (not the values, only the field names) for audit

---

## Read-Only by Default

All AI agent operations in AEOS carry the same read-only guarantee as the
workspace commands:

```
read_only: true  ·  applied: false  ·  human validation required
```

This appears in every AI-generated output, every recommendation file, and
every PR proposal. It is not optional and cannot be overridden by the model.

An AI agent that produces output claiming `applied: true` without an explicit
human `--apply` command has violated this policy.

---

## No Autonomous Apply

No AI agent in AEOS applies changes without an explicit, separate human
command. The workflow is always:

```
Agent proposes → AEOS validates → Human reviews → Human applies
```

There is no shortcut. There is no "auto-apply" mode. There is no "trust level"
that bypasses this gate. Even if the model is confident, even if the
recommendation is obvious, the human applies.

This is not a limitation. It is the product.

---

## Human Validation Required

Every AI-generated recommendation surfaces as a reviewable artifact:
- A Markdown file in the workspace
- A proposed PR description in the terminal
- A list of suggested commands the human must run explicitly

The human can reject, modify, or approve any recommendation. AEOS records the
decision (accept / reject / modify) in the evidence trail.

No recommendation is considered complete until the human has explicitly
responded to it.

---

## Evidence Required

Every AI agent action that affects workspace state must produce an evidence
record containing:
- Timestamp
- Agent type and model used (local or frontier)
- Input summary (field names only, no secret values)
- Output summary
- Human decision (accept / reject / modify)
- Applied: true/false

This record is stored in the project's evidence directory and is never deleted
by subsequent agent runs.

---

## Memory Integration Rules

AI agents may read MemoryRecords. They may never write them.

Permitted reads:
- `status` field (e.g. `harden_complete`, `risk_level`)
- `findings_count` fields (critical, important, manual)
- `project_name`, `audit_date`, `last_seen`
- `read_only`, `local_only` flags

Forbidden reads:
- Any field containing a file path that leads to `.env` or secrets
- Any raw file content embedded in a MemoryRecord
- Any field whose value is a credential or connection string

If a MemoryRecord contains unexpected fields that look like secrets, the agent
must refuse to process the record and log a warning.

---

## Summary

| Principle | Rule |
|-----------|------|
| Local-first | Prefer local model; frontier AI by exception only |
| Read-only | Agents never write to project files or MemoryRecords |
| No autonomous apply | Human `--apply` required for every state change |
| No secrets | No secret ever enters any AI context |
| Evidence | Every agent action produces an auditable evidence record |
| Human authority | Human decision is final and cannot be bypassed |
| Reversibility | Every agent output is reviewable before application |
