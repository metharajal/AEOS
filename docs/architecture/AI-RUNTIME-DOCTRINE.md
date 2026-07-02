# AEOS AI Runtime Doctrine

**Version:** 1.0
**Status:** PROPOSED
**Date:** 2026-07-02
**Sprint:** MVP-DOCS-ALIGN-1
**Authority:** [CONSTITUTION.md](../../CONSTITUTION.md) §5.3 · [AI-DEVELOPMENT-POLICY.md](../AI-DEVELOPMENT-POLICY.md)

---

## Purpose

This document defines the permanent architectural contract for how AEOS interacts
with AI systems — local or remote. It governs the design of every future AI
integration, every configuration surface, and every agent command.

It is not a feature spec. It does not describe `aeos ai ask`. It does not choose
an implementation. It defines the invariants and the interfaces within which any
implementation must operate.

---

## 1. The Fundamental Distinction

### 1.1 Local-first is a principle, not a dependency

AEOS is **AI local-first**. This means:

> By default, no data leaves the machine. Any departure from this default requires
> explicit human consent, explicit configuration, and an immutable audit record.

This is a **sovereignty principle**, not a dependency declaration.

It does not mean:
- AEOS requires Ollama
- AEOS requires any specific binary
- AEOS requires any specific port
- AEOS requires a running model to function

**AEOS must work offline with zero AI integration.** All diagnostic, governance, and
recovery commands operate without a model. AI is an optional reasoning layer. When
unavailable, AEOS falls back to deterministic rules — not to degraded UX.

### 1.2 Why AEOS must not be Ollama-first

Ollama is the most common local model runner today. It may not be in 2027.

Binding AEOS to Ollama's API (`/api/generate`) creates:

| Risk | Consequence |
|---|---|
| Ollama API changes | AEOS breaks without code change |
| User prefers LM Studio or vLLM | AEOS unusable for them |
| Ollama removed/abandoned | Core AEOS capability disappears |
| Enterprise user requires vLLM | Cannot deploy AEOS internally |
| Edge device without Ollama | Cannot run AEOS agents |

**Current state of `src/aeos/ai/local.py`:**
```python
if config.local.provider != "ollama":
    raise LocalAiError(f"unsupported local provider: {config.local.provider}")
```
This line must not survive MVP-AGENTS-7. It is a temporary limitation, not a doctrine.

### 1.3 The actual principle stack

```
PRINCIPLE (immutable)    →  Local-first, frontier by exception
ABSTRACTION (stable)     →  AIProvider contract (defined in §2)
IMPLEMENTATION (swappable) →  Ollama, LM Studio, vLLM, llama.cpp server, LiteLLM...
```

The principle never changes. The abstraction changes through RFC. The implementation
changes through `aeos.toml` configuration — without touching AEOS code.

---

## 2. The Five Core Abstractions

AEOS defines five stable types for all AI interactions. These types are the
contract. Any runtime, any provider, any future agent must speak these types.

### 2.1 AIProvider

The minimum interface AEOS expects from any AI backend:

```
AIProvider {
  name:      string         # identifier — "ollama", "lm-studio", "vllm", "litellm", ...
  base_url:  string         # HTTP endpoint — "http://localhost:11434"
  api_style: enum           # openai-compatible | ollama-native | custom
  is_local:  bool           # true = no data leaves machine
  requires_auth: bool       # false for local providers, true for frontier
}
```

A provider is valid if it:
1. Accepts HTTP POST requests
2. Returns a text completion
3. Does not read `.env` files
4. Does not log prompt content externally

A provider is **not** required to:
- Speak any specific API format (AEOS adapts)
- Be on a fixed port
- Use any specific model format

### 2.2 AIRouter

The routing logic that selects which provider to use:

```
AIRouter {
  strategy:  enum  # local-only | local-first | frontier-only | manual
  providers: list[AIProvider]
  fallback:  AIProvider | None
  gate:      HumanApprovalGate  # required for any non-local call
}
```

**Routing invariants (non-negotiable):**
- `local-only`: no network call ever. Raises if local unavailable.
- `local-first`: tries local, raises before touching frontier unless explicit.
- Frontier calls: always require `require_human_approval = true` confirmation.
- No silent escalation. No retry-on-failure to frontier. Human decides.

### 2.3 AIContext

What AEOS is allowed to send to a provider:

```
AIContext {
  prompt:   string           # sanitized user/system prompt
  project:  string | None    # project name (not path)
  task:     string           # descriptor — "plan", "propose-pr", "summarize"
  metadata: dict[str, str]   # non-sensitive context (counts, levels, statuses)
}
```

**What AIContext must never contain:**
- Secret values (API keys, tokens, passwords, connection strings)
- File contents (source code, SQL migrations, config files)
- `.env` keys or values
- User credentials or PII
- Full file paths that reveal system topology

**What AIContext may contain:**
- Aggregate counts from MemoryRecord (`findings_summary: {critical: 3, ...}`)
- Sovereignty level (1–5), project maturity level
- Action plan structure (task names, priorities, types — not implementation details)
- MemoryRecord metadata (project name, audit date, provider names — not values)

The sanitization rule is simple: **anything a human would be comfortable publishing
on GitHub can be in AIContext**. Anything else cannot.

### 2.4 AIResponse

What AEOS receives back from a provider:

```
AIResponse {
  text:          string       # completion text — always a string, never binary
  provider_used: string       # name of the provider that produced this
  model_used:    string       # model identifier as reported by the provider
  is_local:      bool         # true = no external call was made
  latency_ms:    int          # round-trip time
}
```

**AIResponse invariants:**
- `text` is always read-only. AEOS never applies a response directly.
- `is_local = false` is always logged (see AIInteractionLog).
- A response carries `read_only: true · applied: false` at every output surface.

### 2.5 AIInteractionLog

Every AI call — local or frontier — produces an immutable log entry:

```
AIInteractionLog {
  id:            string       # UUID
  timestamp:     ISO 8601
  provider:      string       # AIProvider.name
  is_local:      bool
  task:          string       # AIContext.task
  project:       string | None
  prompt_hash:   string       # SHA-256 of prompt (not the prompt itself)
  response_hash: string       # SHA-256 of response (not the response itself)
  latency_ms:    int
  human_approved: bool        # true if frontier + confirmation required
  applied:       bool         # always false — human applies
}
```

**Why prompt hash, not prompt:** AEOS logs that a call happened and can verify integrity.
It does not store prompts in logs (they may contain project structure). The hash is
enough to detect tampering.

---

## 3. Provider Ecosystem

### 3.1 Role of each tool

AEOS does not choose between these tools. It defines an adapter interface that all
of them can satisfy.

| Tool | Role in AEOS ecosystem | API surface used by AEOS |
|---|---|---|
| **Ollama** | Local model runner — pull, run, manage models | OpenAI-compatible: `POST /v1/chat/completions` (preferred) or native `POST /api/generate` |
| **LM Studio** | Local model runner with GUI — useful for non-technical users | OpenAI-compatible: `POST /v1/chat/completions` |
| **vLLM** | High-throughput local/self-hosted inference — enterprise, team | OpenAI-compatible: `POST /v1/chat/completions` |
| **llama.cpp server** | Lightweight, edge-deployable server — minimal footprint | OpenAI-compatible: `POST /v1/chat/completions` (recent versions) |
| **LiteLLM** | Proxy/gateway that translates between providers — unified endpoint | OpenAI-compatible: `POST /v1/chat/completions` |
| **OpenWebUI** | GUI for local models — not a provider, uses Ollama/OpenAI under the hood | Not called directly by AEOS |
| **AnythingLLM** | Knowledge base + model orchestration — adds RAG and memory on top of any backend | OpenAI-compatible: `POST /v1/chat/completions` if configured as proxy |

### 3.2 The OpenAI-compatible API as convergence point

All major local model runtimes now expose an OpenAI-compatible HTTP API:

| Tool | Default port | OpenAI endpoint |
|---|---|---|
| Ollama | 11434 | `http://localhost:11434/v1/chat/completions` |
| LM Studio | 1234 | `http://localhost:1234/v1/chat/completions` |
| vLLM | 8000 | `http://localhost:8000/v1/chat/completions` |
| llama.cpp server | 8080 | `http://localhost:8080/v1/chat/completions` |
| LiteLLM proxy | 4000 | `http://localhost:4000/v1/chat/completions` |
| AnythingLLM (API mode) | 3001 | `http://localhost:3001/api/openai/chat/completions` |

**Architectural consequence:**

> AEOS local AI providers should converge on the OpenAI-compatible API format.
> This is not because OpenAI is the standard — it is because every major local
> runtime has adopted this format as a lingua franca. Using it means AEOS can
> support all runtimes with one adapter instead of N adapters.

The current frontier adapter (`src/aeos/ai/frontier.py`) already does this correctly.
The local adapter (`src/aeos/ai/local.py`) must be refactored to match the same
pattern when MVP-AGENTS-7 is implemented.

### 3.3 Ollama native API vs OpenAI-compatible

Ollama's native API (`POST /api/generate`) and OpenAI-compatible API (`POST /v1/chat/completions`)
coexist on the same server. AEOS should prefer the OpenAI-compatible endpoint:

- It uses the same code path as frontier providers
- It is forward-compatible with other runtimes
- It supports multi-turn conversations natively (messages array)
- It is tested by a larger community

The native Ollama API may be used as a fallback if the user configures
`api_style = "ollama-native"` in `aeos.toml`. This is an explicit opt-in,
not the default.

### 3.4 AnythingLLM — not a dependency, a valid adapter

AnythingLLM provides value that AEOS does not and should not replicate:
- Document ingestion and RAG (retrieval-augmented generation)
- Persistent workspace memory at the model level
- Multi-user team access
- GUI for non-technical users

AEOS may route to AnythingLLM as a local provider when the user configures it.
The integration is: **AEOS → AnythingLLM OpenAI-compatible API → any backend model**.

AnythingLLM is not a core dependency. AEOS must not require it. AEOS must not
hard-code its port or its API path.

### 3.5 LiteLLM — the multiplexer

LiteLLM is a proxy that translates between 100+ providers using OpenAI-compatible
input. For users who want to switch models without reconfiguring AEOS, LiteLLM is
the right tool:

```
AEOS → LiteLLM (localhost:4000) → [Ollama | LM Studio | vLLM | Claude | OpenAI ...]
```

This architecture keeps AEOS configuration stable while the underlying model
changes. AEOS only needs to know the LiteLLM endpoint.

---

## 4. Configuration Model

### 4.1 `aeos.toml` is the single source of truth

All AI runtime configuration lives in `aeos.toml` at the project or global level.
No environment variable is read to determine routing behavior. Environment variables
are only used for secrets (API keys), never for routing decisions.

```toml
[ai]
mode                  = "local-first"     # local-only | local-first | frontier-only
frontier_allowed      = false             # default: false in sovereign mode
require_human_approval = true             # never false

  [ai.local]
  provider      = "openai-compatible"     # openai-compatible | ollama-native | custom
  base_url      = "http://localhost:11434" # any local endpoint
  default_model = "llama3.2"             # model identifier

  [ai.frontier]
  provider      = "openai-compatible"
  base_url_env  = "AEOS_FRONTIER_BASE_URL"
  api_key_env   = "AEOS_FRONTIER_API_KEY"
  model_env     = "AEOS_FRONTIER_MODEL"
```

### 4.2 What is configurable

| Setting | Who sets it | Can be changed without code |
|---|---|---|
| `ai.local.provider` | `aeos.toml` | Yes |
| `ai.local.base_url` | `aeos.toml` | Yes |
| `ai.local.default_model` | `aeos.toml` | Yes |
| `ai.mode` | `aeos.toml` | Yes |
| `frontier_allowed` | `aeos.toml` | Yes |
| `require_human_approval` | `aeos.toml` | Yes, but never below `true` by default |
| Frontier API key | environment variable | Yes |
| Which local runtime | `aeos.toml` | Yes — this is the whole point |

### 4.3 What is not configurable

| Setting | Why fixed |
|---|---|
| `applied: false` for all AI responses | Core invariant — code-enforced |
| `read_only: true` on all AI output surfaces | Core invariant — code-enforced |
| Human gate before frontier call | Safety invariant — not overridable |
| No secrets in AIContext | Privacy invariant — not overridable |
| No file contents in AIContext | Privacy invariant — not overridable |

### 4.4 Offline mode

When `ai.mode = "local-only"` and no local provider is reachable, AEOS:
1. Does not call any remote endpoint
2. Does not error the CLI (unless the user explicitly ran `aeos ai ask`)
3. Falls back to deterministic output for all agent commands
4. Logs: `local AI unavailable — operating in deterministic mode`

This is not a degraded state. Deterministic output is the baseline. AI is
an enhancement layer, never a dependency for correctness.

---

## 5. Security Rules — Universal, All Providers

These rules apply regardless of provider, regardless of whether the call is local
or frontier, regardless of user configuration.

### 5.1 The context sanitization gate

Before any prompt is constructed:

1. **Secret scan**: if any known secret pattern is detected in the proposed
   context, the call is aborted. The user sees: `AI context rejected: secret
   pattern detected. Review your context before escalating.`
2. **File content check**: if the context includes raw file content (source code,
   SQL, config), the call is aborted. Only metadata and summaries are allowed.
3. **PII scan**: basic PII patterns (email, phone, national ID formats) are flagged.
   The call is rejected if detected.

The gate cannot be disabled. It is not a warning. It is a hard stop.

### 5.2 The frontier consent protocol

Every frontier call follows this sequence — no exceptions:

```
1. AEOS constructs AIContext
2. AEOS runs context sanitization gate
3. AEOS displays: "This call will be sent to [provider] at [url]. Review:"
4. AEOS shows: task, project name, summary of what's in context (not the prompt)
5. AEOS asks: "Type 'yes' to confirm, anything else to cancel:"
6. User types 'yes'
7. AEOS logs: AIInteractionLog entry with timestamp and prompt hash
8. AEOS sends the request
9. AEOS displays: response with 'read_only: true · applied: false' footer
10. AEOS logs: response hash, latency
```

Steps 3–6 cannot be skipped via flag. There is no `--yes` or `--force` flag for
frontier escalation. The two-action requirement (explicit flag + explicit confirmation)
is permanent.

### 5.3 Local call logging

Local calls are logged too — in AIInteractionLog — but without the consent prompt.
The log exists for auditability, not surveillance. The user can inspect their own
interaction history at `~/.aeos/ai/interaction-log.jsonl`.

### 5.4 Model output is never applied

No matter what a model says, AEOS never applies the output directly. Every AI
response:
- Is displayed to the human
- Is saved to a file if `--output` is specified
- Carries `read_only: true · applied: false` in the output
- Requires a separate human action to use

There is no `--apply` flag. There is no "apply this response to my codebase" mode.

---

## 6. Future Commands That Will Use This Layer

These commands are planned, not yet implemented. They define what the AI runtime
layer must support.

| Command | AI layer role | Provider tier |
|---|---|---|
| `aeos agent plan --model llama3` | Route to local model for plan enrichment | Local only |
| `aeos agent plan --escalate` | Route to frontier with consent protocol | Frontier with gate |
| `aeos ai ask <prompt>` | Direct AI interaction, fully controlled | Local-first |
| `aeos ai doctor` | Check which providers are reachable | Diagnostic only |
| `aeos reclaim summarize --project` | Summarize MemoryRecord findings | Local-first |
| `aeos modernize analyze --path` | Reason about legacy codebase structure | Local-first |

None of these commands should require a specific runtime. They should work with any
provider that satisfies the AIProvider contract.

### 6.1 What `aeos ai ask` must be

When `aeos ai ask` is implemented, it must:
- Accept `--provider local|frontier|auto`
- Accept `--model <name>`
- Accept `--project <name>` for context injection (sanitized MemoryRecord summary)
- Never accept `--context-file` (file contents not allowed in context)
- Display the response with `read_only: true · applied: false`
- Log the interaction in AIInteractionLog
- Fail cleanly if no provider is reachable

It must not:
- Automatically use frontier if local fails (without explicit user instruction)
- Remember conversation history in a persistent session (stateless by default)
- Execute any command or apply any change based on model output

---

## 7. The Runtime Replacement Test

A new AI runtime must be adoptable by changing `aeos.toml` only — no AEOS code
change required. This is the **runtime replacement test**.

To pass the test, any new runtime must expose:

```
POST {base_url}/v1/chat/completions
Content-Type: application/json

{
  "model": "<model-name>",
  "messages": [{"role": "user", "content": "<prompt>"}],
  "stream": false
}

→ 200 OK
{
  "choices": [{
    "message": {
      "content": "<response-text>"
    }
  }]
}
```

This is the OpenAI chat completions format. Every runtime listed in §3.1 supports
this format. Any future runtime that does not support it requires a custom adapter
registered in `aeos.toml [ai.local] api_style = "custom"`.

The replacement test passes when:
1. User installs new runtime (e.g., vLLM)
2. User edits `aeos.toml`: `base_url = "http://localhost:8000"` and `default_model = "mistral"`
3. `aeos agent plan` uses the new runtime without any AEOS update

For runtimes that do not speak OpenAI-compatible format, `api_style = "custom"`
in `aeos.toml` signals that an adapter must be registered. The custom adapter
handles the format translation; the AIProvider contract above remains the same.
The choice of OpenAI-compatible format is a pragmatic convergence point, not an
obligation. AEOS must never reject a provider solely because it uses a different
HTTP format.

---

## 8. Decisions Required Before MVP-AGENTS-7

These decisions are deferred. The doctrine defines the options; the implementation
sprint chooses between them.

| Decision | Options | Constraint |
|---|---|---|
| Default local API style | `openai-compatible` (preferred) vs `ollama-native` (current) | Prefer openai-compatible for multi-runtime support |
| `local.py` refactor scope | Full rewrite vs adapter pattern on top of current code | Must pass runtime replacement test after change |
| Interaction log location | `~/.aeos/ai/` vs project-level | Prefer global to avoid leaking project paths |
| Log format | JSONL (append-only, auditable) vs SQLite | JSONL preferred: plain text, no binary, git-inspectable |
| Conversation statefulness | Stateless (safe) vs stateful session | Stateless by default in V1 |
| `aeos ai doctor` output | JSON vs terminal table | Must work offline (only checks local provider availability) |
| AnythingLLM integration | Documented as valid adapter vs explicit CLI support | Documented only in V1 — no special code |
| LiteLLM integration | Documented as valid adapter vs bundled proxy | Documented only in V1 — user manages LiteLLM |

---

## 9. What This Doctrine Prevents

Each of these is a possible future mistake that this document preemptively blocks.

| Risk | Prevention |
|---|---|
| AEOS requires `ollama pull` before first use | `ai.mode = "local-only"` fails gracefully, deterministic fallback |
| AEOS hardcodes `localhost:11434` | `base_url` is configurable in `aeos.toml` |
| AEOS ships Ollama or downloads models | No bundled model, no model download — user manages runtime |
| AEOS agents auto-apply model suggestions | `applied: false` invariant enforced in all output surfaces |
| AEOS sends MemoryRecord files to frontier | AIContext type forbids file contents |
| A convenience `--force-frontier` flag ships | Consent protocol cannot be bypassed by flag |
| AEOS becomes an AnythingLLM wrapper | AnythingLLM is one valid adapter; it has no special code path |
| AEOS logs full prompts | AIInteractionLog stores hashes, never prompt text |
| AEOS fails without any AI runtime | Deterministic fallback is always available |
| A sprint ships "Ollama integration" that blocks LM Studio users | Runtime replacement test is the acceptance criterion |

---

## 10. Invariant Summary

These invariants are permanent. They cannot be changed by configuration, by sprint,
by user request, or by model capability.

```
AI.01  AEOS functions without any AI runtime (deterministic fallback always available)
AI.02  Local-first means sovereignty, not a dependency on a specific binary
AI.03  No data leaves the machine without explicit human consent
AI.04  No secret value enters any AIContext (hard gate, not a warning)
AI.05  No raw file content enters any AIContext
AI.06  No AI response is applied without a separate explicit human action
AI.07  All AI interactions are logged (prompt hash + response hash + provider)
AI.08  Frontier escalation requires two user actions: explicit flag + typed confirmation
AI.09  The local provider is configurable in aeos.toml without code change
AI.10  The runtime replacement test must pass for any new provider
```

---

## 11. Supported Provider Matrix

| Provider | API style | Local | Auth required | Status |
|---|---|---|---|---|
| Ollama | openai-compatible (preferred) or ollama-native | Yes | No | Current (via code change in MVP-AGENTS-7) |
| LM Studio | openai-compatible | Yes | No | Supported via config |
| vLLM | openai-compatible | Yes / self-hosted | Optional | Supported via config |
| llama.cpp server | openai-compatible (recent versions) | Yes | No | Supported via config |
| LiteLLM proxy | openai-compatible | Yes (local proxy) | Depends on backend | Supported via config |
| AnythingLLM | openai-compatible (API mode) | Yes | Optional | Supported via config |
| OpenWebUI | Not called directly | — | — | Not a provider — GUI layer |
| Claude (Anthropic) | openai-compatible via `base_url` | No (frontier) | Yes (env var) | Frontier, consent required |
| OpenAI | openai-compatible | No (frontier) | Yes (env var) | Frontier, consent required |
| Any other OpenAI-compatible API | openai-compatible | Depends | Depends | Supported via config |

---

## See Also

- [CONSTITUTION.md](../../CONSTITUTION.md) — AI routing invariants §5.3
- [AI-DEVELOPMENT-POLICY.md](../AI-DEVELOPMENT-POLICY.md) — development-time AI policy
- [docs/agents/LOCAL-AI-ASSISTANT-POLICY.md](../agents/LOCAL-AI-ASSISTANT-POLICY.md) — agent-level AI policy
- [docs/agents/FRONTIER-AI-ESCALATION.md](../agents/FRONTIER-AI-ESCALATION.md) — frontier escalation protocol
- [docs/agents/AGENT-ROADMAP.md](../agents/AGENT-ROADMAP.md) — MVP-AGENTS-7 (Ollama), MVP-AGENTS-8 (Frontier Escalation)
- [aeos.toml](../../aeos.toml) — current AEOS AI configuration
- `src/aeos/ai/` — current AI module implementation
