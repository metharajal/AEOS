# AEOS Research Backlog — Local-first Sovereignty

**Date:** 2026-06-27
**Status:** Backlog / Research
**Branch:** main (post Sprint 2M)

---

## Context

AEOS is a local-first, sovereign, agentic, and governed AI Engineering Operating System.

After Sprint 2M (Sovereignty Check MVP), AEOS can detect external platform dependencies, portability gaps, and basic security signals in a project. This backlog documents the next layer of strategic themes, research signals, and proposed future sprints.

This document is a living research note. It consolidates signals from:
- xigh GitHub repositories (open-weight-models, herbert-rs, llm-copy-bench, DevSecOps tooling)
- Research on local-first AI agent frameworks
- Local coding agents and Ollama-based workflows
- Trivy / supply chain security patterns
- Self-hosted Supabase alternatives (SelfDB, Postbase, Pocketbase)
- AI readiness and project maturity scoring patterns
- Zero-trust agent governance frameworks

---

## Why This Matters for AEOS

AEOS is not just a CLI tool. It is the operating foundation for engineering teams who want to:
- Build without mandatory dependence on hosted AI platforms
- Own their data and their stack
- Operate in air-gapped, regulated, or cost-constrained environments
- Maintain full auditability of what AI does in their codebase

Sprint 2M established the first static audit layer. The themes below represent the next frontier: deeper sovereignty detection, security hardening, agent governance, and project maturity scoring.

---

## Research Sources

| # | Source | Theme |
|---|--------|-------|
| 1 | xigh/open-weight-models | Sovereign Model Catalog |
| 2 | xigh/herbert-rs, llama.cpp runtimes | Local Runtime Abstraction |
| 3 | Trivy, Gitleaks, Snyk, distroless | Security & Supply Chain Check |
| 4 | xigh/llm-copy-bench | AI Model Evaluation |
| 5 | Somi, local-first agent frameworks | Agent Governance |
| 6 | local-cli, Ollama coding agents | Local Coding Agent patterns |
| 7 | SelfDB, Postbase, Pocketbase | Supabase Exit Plan |
| 8 | Workstream, AI readiness scoring | AI Readiness / Maturity Score |
| 9 | Agyn, zero-trust agent platforms | Zero-trust Agent Runtime |

---

## Strategic Themes

---

### 1. Sovereign Model Catalog

**Inspiration:** xigh/open-weight-models — a curated list of open-weight models with commercial licenses, hardware profiles, and capability categorizations.

**Why useful for AEOS:**

AEOS Sprint 2J hardcoded `llama3.2` via Ollama as the default local model. There is no mechanism to validate whether the chosen model is:
- Genuinely open-weight (weights publicly available)
- Commercially usable (license permits product use)
- Appropriate for the hardware (RAM / VRAM requirements)
- Aligned with sovereignty principles (no usage telemetry, no cloud dependency)

A model with a non-commercial license used in a product is a sovereignty and legal risk, analogous to depending on Supabase without an exit plan.

**Possible future commands:**
```
aeos model list                    # list known sovereign models
aeos model list --filter license=apache2
aeos model inspect llama3.2        # show license, size, requirements
aeos ai doctor --check-model       # validate model sovereignty
```

**Candidate models to catalog (MVP):**
- `llama3.2` (Meta Llama 3.2 Community License — commercial use allowed)
- `mistral-7b` (Apache 2.0)
- `phi-3-mini` (MIT)
- `qwen2.5-coder` (Apache 2.0)
- `codestral` (non-commercial — flag as WARNING)
- `gpt-4o` (OpenAI API — flag as frontier/non-sovereign)

**Priority:** High — AI sovereignty is incomplete without model license awareness.

---

### 2. Local Runtime Abstraction

**Inspiration:** xigh/herbert-rs — Rust-based local inference primitives. References to llama.cpp, candle, vLLM, LM Studio, OpenAI-compatible local endpoints.

**Why useful for AEOS:**

`ask_local_ai()` in Sprint 2J targets Ollama's `/api/generate` endpoint specifically. If Ollama is unavailable, changes its API, or is not the right tool for a given environment, AEOS has no fallback.

True local sovereignty means the engineering system is not dependent on any single inference runtime.

**Possible future commands / config:**
```toml
[ai.local]
provider = "lmstudio"          # or "llamacpp" | "vllm" | "ollama" | "custom"
base_url = "http://localhost:1234"
api_style = "openai-compatible"  # or "ollama-native"
```

```
aeos ai doctor --runtime          # detect available local runtimes
```

**Runtimes to support (roadmap):**
- Ollama (current, Sprint 2J)
- LM Studio (OpenAI-compatible, port 1234)
- llama.cpp server (OpenAI-compatible)
- vLLM (OpenAI-compatible)
- Custom OpenAI-compatible endpoint (catch-all)

**Priority:** Medium — Ollama is stable and widely adopted. Abstraction is important for long-term resilience but not urgent.

---

### 3. Security & Supply Chain Check

**Inspiration:** Trivy (container + filesystem scanning), Gitleaks (secret detection in git history), Snyk (dependency CVE scanning), distroless base images.

**Why useful for AEOS:**

Sprint 2M detects sovereignty gaps (hosted platforms, portability). The next layer is security: a project can be sovereign but still insecure. Specific gaps not covered by Sprint 2M:

- **Secret leak in git history**: `.env` with real secrets may have been committed and then removed, but it lives in git history. Gitleaks-style scanning detects this.
- **Vulnerable dependencies**: `package.json` or `pyproject.toml` may pin packages with known CVEs.
- **Insecure container base images**: `FROM ubuntu:latest` is not reproducible and may be outdated.
- **No SBOM**: Without a Software Bill of Materials, supply chain integrity cannot be verified.
- **IaC misconfigurations**: Terraform, Kubernetes, or Docker Compose files may expose insecure defaults.

**Possible future commands:**
```
aeos security check               # static security audit (no network)
aeos security check --json
aeos supply-chain check           # SBOM, license audit, pinned versions
```

**MVP detection rules (static, no network):**
- Scan git log for `+<PATTERN>=` where PATTERN matches sensitive var names (Gitleaks-inspired, read-only)
- Detect `FROM ubuntu:latest` or `FROM node:latest` in Dockerfile (non-pinned base images)
- Detect unpinned dependencies (`"^1.0.0"` or `"*"` in package.json)
- Detect missing `.dockerignore`
- Detect missing `COPY --chown` in Dockerfile (privilege escalation risk)

**Security constraints (unchanged from Sprint 2M):**
- Never read real secret values from git history
- Only report commit SHAs, file names, line patterns (not values)
- No network calls to CVE databases in MVP

**Priority:** High — natural extension of Sprint 2M. Shares `SovereigntyFinding` / `SovereigntyCheckResult` model.

---

### 4. Lovable / Supabase Exit Plan

**Inspiration:** SelfDB, Postbase, Pocketbase — self-hosted alternatives to Supabase. Research on projects generated by Lovable, Bolt, and Replit that depend on Supabase for database, auth, storage, and realtime.

**Why useful for AEOS:**

Sprint 2M can detect that a project uses Supabase. The next step is to help the user understand what a migration to a sovereign stack would look like, concretely.

A Supabase project typically depends on:
- **Database**: Supabase-hosted PostgreSQL
- **Auth**: Supabase Auth (GoTrue)
- **Storage**: Supabase Storage
- **Realtime**: Supabase Realtime (Elixir Phoenix)
- **Edge Functions**: Supabase Edge (Deno)

Sovereign alternatives:
- **Database**: Local PostgreSQL + docker-compose
- **Auth**: Keycloak, Ory Hydra, Lucia, Better Auth (self-hosted)
- **Storage**: MinIO (S3-compatible, self-hosted)
- **Realtime**: Soketi (Pusher-compatible, self-hosted)

**Possible future commands:**
```
aeos sovereignty migrate-plan       # generate migration roadmap (no auto-apply)
aeos sovereignty migrate-plan --from supabase --to local
```

**MVP output (read-only, no modification):**
```
Migration Plan: Supabase → Sovereign Stack

Database:
  Detected: @supabase/supabase-js
  Recommendation: Add docker-compose.yml with postgres:16
  Migration: export schema with pg_dump, apply locally

Auth:
  Detected: Supabase Auth via supabase.auth.*
  Recommendation: Replace with Lucia or Better Auth
  Migration: abstract auth adapter, swap provider

Storage:
  Detected: Supabase Storage via supabase.storage.*
  Recommendation: Use MinIO (S3-compatible)
  Migration: update storage client to aws-sdk/client-s3
```

**Priority:** Medium — depends on Sprint 2M findings being mature. High value for Lovable/Bolt users.

---

### 5. AI Model Evaluation

**Inspiration:** xigh/llm-copy-bench — benchmarks measuring the copy fidelity of LLMs: can a model reproduce a UUID, a YAML block, a file path, a hash, or a masked secret without hallucinating?

**Why useful for AEOS:**

AEOS will eventually use local models for agentic tasks: editing files, generating config, running commands. A model that hallucinates file paths or corrupts YAML is not safe for sovereign engineering use.

Before trusting a model with engineering tasks, AEOS should be able to evaluate it locally:

**Evaluation categories (inspired by llm-copy-bench):**
- Copy fidelity: can the model reproduce a UUID without modification?
- YAML integrity: can the model output valid YAML that parses correctly?
- Command safety: does the model reproduce shell commands faithfully?
- Secret masking: does the model avoid completing masked values?
- Path accuracy: does the model preserve file paths, dots, slashes, extensions?
- Instruction following: does the model follow structured output instructions?

**Possible future commands:**
```
aeos ai eval                        # run local evaluation suite
aeos ai eval --model llama3.2
aeos ai eval --category copy-fidelity
aeos ai eval --json
```

**Output:**
```
AI Model Evaluation
Model:  llama3.2 (via ollama)

copy-fidelity     PASS   (10/10 UUID reproductions exact)
yaml-integrity    PASS   (8/10 YAML outputs valid)
command-safety    WARN   (2/10 commands slightly altered)
instruction-follow PASS  (9/10 structured outputs compliant)

Overall: WARN
```

**Priority:** Medium — gated on having a working local model. Useful before enabling agentic workflows.

---

### 6. Agent Governance

**Inspiration:** Somi (local-first agent frameworks), local-cli Ollama coding agents, Agyn (zero-trust agent platforms).

**Why useful for AEOS:**

AEOS will eventually support agentic workflows: reading files, writing code, running commands, creating commits. Without governance, an agent can:
- Overwrite files without human review
- Run destructive commands
- Access sensitive files
- Commit secrets to git

Key patterns from research:
- **Git isolation**: agents should work on a dedicated branch, never directly on main
- **Sandbox**: agents should not have access to the host filesystem beyond the project directory
- **Human approval gates**: destructive operations require explicit confirmation
- **Audit log**: every agent action must be recorded (what, when, why, result)
- **Least privilege**: agents receive only the permissions needed for the specific task
- **Zero-trust**: no agent action is trusted by default, each must be authorized

**Possible future commands:**
```
aeos agent run "add unit test for user.py"    # sandboxed, on branch
aeos agent log                                # show audit log
aeos agent config                             # show governance settings
```

**aeos.toml governance config (proposal):**
```toml
[agent]
enabled = false                    # disabled by default
require_human_approval = true      # always confirm before write/run
sandbox_mode = "git-branch"        # or "none" | "docker"
max_file_writes = 5                # per session
allow_shell = false                # no shell execution without explicit opt-in
audit_log = "logs/agent.jsonl"
```

**Priority:** Medium-Low for near term. High strategic importance — defines the agentic architecture contract.

---

### 7. AI Readiness / Project Maturity Score

**Inspiration:** Workstream AI readiness scoring patterns, engineering command center concepts.

**Why useful for AEOS:**

`aeos sovereignty check` and `aeos ai doctor` each produce binary OK/WARNING/ERROR findings per item. There is no aggregate view of a project's readiness for AI-assisted engineering.

A future **AI Readiness Score** would:
- Aggregate findings across all AEOS checks
- Produce a score from 0–100 (or a tiered label: NOT READY / BASIC / SOVEREIGN / PRODUCTION)
- Identify the top 3 actions to improve the score
- Be exportable as JSON for CI dashboards

**Scoring dimensions:**
- AI configuration (local-first, human approval, model sovereignty)
- Project structure (README, governance, tests, CI)
- Security (no leaked secrets, no vulnerable packages)
- Portability (Dockerfile, migrations, env example)
- Sovereignty (no hosted dependencies, self-hostable)
- Agent readiness (governance config, audit log, sandbox)

**Possible future commands:**
```
aeos score                          # compute AI readiness score
aeos score --json
aeos score --explain               # show dimension breakdown
```

**Priority:** Low for near term — requires other checks to be mature first. High value for CTO dashboards and team onboarding.

---

## Proposed Future Sprints

| Sprint | Name | Source Inspiration | Priority |
|--------|------|--------------------|----------|
| 2N | Sovereignty Check — Enhanced Detection | Sprint 2M + Supabase patterns | High |
| 2O | Security Check | Gitleaks, Trivy | High |
| 2P | Supply Chain Check | Trivy, Snyk, SBOM | High |
| 2Q | Sovereign Model Catalog | xigh/open-weight-models | High |
| 2R | Lovable / Supabase Exit Plan | SelfDB, Pocketbase | Medium |
| 2S | Local Runtime Abstraction | xigh/herbert-rs, llama.cpp | Medium |
| 2T | AI Model Evaluation | xigh/llm-copy-bench | Medium |
| 2U | Agent Governance MVP | Somi, Agyn, local-cli | Medium |
| 2V | AI Readiness Score | Workstream | Low |

---

### Sprint 2N — Enhanced Sovereignty Check

Deepen Sprint 2M detection with:
- Source code scanning (detect `supabase.createClient(` in JS/TS files)
- Hardcoded URL detection (`*.supabase.co`, `*.firebaseapp.com`)
- Recursive `.env.*` scanning
- `sovereignty.toml` for accepted risks / exclusions
- CI enforcement mode (exit 1 on WARNING with `--strict`)

### Sprint 2O — Security Check

Static security audit:
- Git history scan for secret patterns (names only, not values)
- Non-pinned base images in Dockerfile
- Missing `.dockerignore`
- Command: `aeos security check [--json]`

### Sprint 2P — Supply Chain Check

- Unpinned dependency versions
- License audit (detect non-commercial licenses in dependencies)
- Basic SBOM generation
- Command: `aeos supply-chain check [--json]`

### Sprint 2Q — Sovereign Model Catalog

- Embedded catalog of open-weight models with license classification
- `aeos model list`, `aeos model inspect <name>`
- Integration with `aeos ai doctor` to warn on non-commercial model licenses

### Sprint 2R — Lovable / Supabase Exit Plan

- Detect Supabase patterns in Sprint 2M findings
- Generate a concrete migration roadmap (read-only, no auto-apply)
- Command: `aeos sovereignty migrate-plan [--from supabase]`

### Sprint 2S — Local Runtime Abstraction

- Decouple `ask_local_ai()` from Ollama
- Add `provider = "lmstudio"` and `provider = "custom"` to `aeos.toml`
- Detect available runtimes in `aeos ai doctor`

### Sprint 2T — AI Model Evaluation

- Local benchmark suite: copy fidelity, YAML integrity, instruction following
- Command: `aeos ai eval [--model <name>] [--json]`
- Produces PASS / WARN / FAIL per category

### Sprint 2U — Agent Governance MVP

- Define agent governance config in `aeos.toml`
- Implement `require_human_approval` gate for agent actions
- Implement audit log (`logs/agent.jsonl`)
- Command: `aeos agent config`, `aeos agent log`

### Sprint 2V — AI Readiness Score

- Aggregate all AEOS check findings into a single score
- Command: `aeos score [--json] [--explain]`
- Export-ready for CI dashboards

---

## Out of Scope for Now

The following are intentionally deferred beyond the near-term roadmap:

- Automatic migration from Supabase to PostgreSQL (code modification)
- Automatic removal of hosted dependencies
- Network calls to CVE databases or vulnerability registries
- Online registry of sovereign vs. non-sovereign packages
- FinOps scoring or cost analysis
- Graphical interface or web dashboard
- Streaming AI responses
- Multi-agent orchestration
- Remote deployment automation
- Integration with CI/CD pipelines beyond static checks

---

## Recommended Next Priority

After Sprint 2M, the recommended sequence is:

**1. Sprint 2N — Enhanced Sovereignty Check (immediate)**

Sprint 2M detects packages and env var names. It does not scan source code. A Supabase project that uses `supabase.createClient()` in TypeScript would not be detected unless the package is in `package.json`. Source code scanning is the highest-value next step with the lowest implementation cost — it reuses the same static analysis pattern.

**2. Sprint 2O/2P — Security & Supply Chain Check (short term)**

Security is the natural companion to sovereignty. A project can be dependency-free from Supabase but still leak secrets in git history or use a vulnerable base image. The `SovereigntyFinding` / `SovereigntyCheckResult` model from Sprint 2M can be reused directly.

**3. Sprint 2Q — Sovereign Model Catalog (short term)**

AI sovereignty is incomplete without model license awareness. This is a pure data + logic sprint (no network calls, no API) and fits the AEOS quality model perfectly.

**4. Sprint 2S — Local Runtime Abstraction (medium term)**

This enables AEOS to survive Ollama API changes or environment constraints. It is important for production resilience but not urgent while Ollama remains stable.

**5. Agent Governance (long term)**

Agent capabilities must be built on a solid governance foundation. This sprint is deferred until the static audit layer (2N–2Q) is mature and the team has validated the static-first approach.
