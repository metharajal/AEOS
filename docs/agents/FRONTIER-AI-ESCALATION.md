# AEOS Frontier AI Escalation Policy

**Version:** 1.0
**Sprint:** MVP-AGENTS-1
**Status:** RATIFIED

---

## Principle

> Local AI first. Frontier AI last resort.

Frontier AI models (Claude, GPT-4, Gemini, Mistral-via-API, and equivalents)
are powerful but carry inherent risks for a local-first platform: data leaves
the machine, inference costs accumulate, and the user loses control of what
the model does with their context.

AEOS treats frontier AI as an exception, not a default.

---

## Frontier AI by Exception Only

Frontier model invocation in AEOS requires all of the following:

1. The local model (or deterministic analysis) has explicitly failed to produce
   an actionable result
2. The user has typed an explicit escalation command (e.g. `--escalate` flag)
3. AEOS has displayed a data disclosure warning and the user has confirmed
4. The context payload has been sanitised and reviewed
5. The escalation has been logged before the API call is made

If any condition is unmet, AEOS does not call the frontier model.

---

## When to Escalate

Frontier escalation is appropriate when:

| Scenario | Reason |
|----------|--------|
| Local model cannot interpret a complex multi-file dependency graph | Task exceeds local model capability |
| Risk narrative requires synthesis across 50+ findings | Context length exceeds local model window |
| Human-gate response requires nuanced legal or compliance framing | Domain expertise that local model lacks |
| PR description requires precise understanding of RLS policy intent | Requires frontier reasoning |
| User explicitly requests a second opinion on a risk assessment | Human-initiated quality check |

In all cases, the escalation is initiated by the user, not triggered
automatically by the agent.

---

## When to NEVER Escalate

Frontier escalation is **permanently forbidden** in the following situations:

| Situation | Why |
|-----------|-----|
| Context payload contains any `.env` value | Secret would leave the machine |
| Context contains database connection strings | Credential exposure |
| Context contains private key material | Catastrophic if logged by provider |
| User has not explicitly consented | Violates local-first doctrine |
| The task can be completed by deterministic analysis | Unnecessary data exposure |
| The task can be completed by a local model | Unnecessary data exposure |
| The project is under NDA or active legal matter | Regulatory risk |
| The escalation would transmit patient, financial, or government data | Compliance risk |

When in doubt, do not escalate. A wrong recommendation from a local model that
the human can correct is safer than a correct recommendation from a frontier
model that exposed client data.

---

## Data Forbidden in Escalation Payloads

The following categories of data are never included in any payload sent to a
frontier model:

| Category | Examples |
|----------|---------|
| Secrets | API keys, passwords, tokens, private keys |
| Environment variables | Any `.env` file content, `process.env` values |
| Connection strings | PostgreSQL DSN, Redis URL, JDBC strings |
| Personal data | Names, emails, phone numbers, national IDs |
| Financial data | Card numbers, IBAN, transaction records |
| Health data | Patient records, diagnoses, prescription data |
| Government data | Tax IDs, permit numbers, citizen records |
| Legal documents | Contracts, NDAs, litigation records |
| Raw source code | File contents that may contain embedded secrets |
| Client-identifiable metadata | Project names that identify a client without consent |

What CAN be sent:
- MemoryRecord metadata (counts, status strings, audit dates)
- Anonymised finding descriptions (e.g. "3 RLS policies missing")
- Generic architectural patterns (e.g. "multi-tenant SaaS with Supabase")
- Human-written summaries that the user has reviewed before sending

---

## Minimum Anonymisation Before Escalation

Before any payload reaches a frontier model, AEOS applies:

1. **Secret strip** — regex scan for known secret patterns; any match aborts
   the escalation with an explicit error
2. **Path anonymisation** — absolute file paths replaced with relative
   equivalents or redacted entirely
3. **Project name review** — user confirms whether the project name may be
   transmitted; offer to substitute a codename
4. **Content truncation** — payload capped at configured token limit; excess
   context is summarised locally, not transmitted raw
5. **Field allowlist** — only explicitly permitted MemoryRecord fields are
   included; all others are stripped

The sanitised payload is shown to the user for review before transmission.

---

## Human Validation Before Sending

The escalation workflow is:

```
1. User requests escalation (explicit --escalate flag)
   ↓
2. AEOS builds sanitised context payload
   ↓
3. AEOS displays payload summary to user:
   "About to send to [model]: [field list]. No secrets detected.
    Project name will be transmitted as: [name or codename]."
   ↓
4. User types: yes / no
   ↓ (yes)
5. AEOS logs escalation record (timestamp, model, fields)
   ↓
6. API call made
   ↓
7. Response displayed — marked read_only: true · applied: false
   ↓
8. Human reviews and decides
```

The user can abort at step 4 with no data transmitted.

---

## Mandatory Traceability

Every frontier escalation produces an immutable evidence record:

```json
{
  "timestamp": "2026-07-02T00:00:00Z",
  "escalation_id": "esc-2026-07-02-001",
  "model": "claude-sonnet-4-6",
  "provider": "anthropic",
  "project_codename": "project-alpha",
  "context_fields_sent": ["status", "findings_count", "audit_date"],
  "secrets_detected": 0,
  "user_confirmed": true,
  "response_received": true,
  "applied": false,
  "read_only": true,
  "human_decision": null
}
```

This record is written to the project's evidence directory before the API call
is made. It is immutable. It is never deleted.

If the API call fails, the record is updated with `response_received: false`
and the error code. No retry is made without explicit user instruction.

---

## Local AI Stack Reference

AEOS prefers the following local inference options (in order):

| Option | Type | Privacy | Cost | Capability |
|--------|------|---------|------|-----------|
| Deterministic Python | No model | Perfect | Free | Limited |
| Ollama (local server) | Open model | Machine-local | Free | Good |
| Apple MLX | On-device | Device-local | Free | Good |
| llama.cpp | On-device | Device-local | Free | Good |
| LM Studio | Local GUI | Machine-local | Free | Good |
| Frontier API | Remote | Leaves machine | Paid | Best |

AEOS escalates to frontier only after local options have been exhausted or
explicitly bypassed by the user.

---

## Summary

| Rule | Detail |
|------|--------|
| Local first | Default to deterministic analysis or local model |
| Explicit consent | User must type the escalation command |
| Data disclosure | AEOS shows what will be sent before sending |
| No secrets | Escalation aborts if any secret is detected |
| Anonymisation | Paths, names, and content sanitised before transmission |
| Traceability | Evidence record written before API call |
| Human decision | Frontier output is a proposal, never an apply |
| Immutable log | Escalation records are never modified or deleted |
