# AEOS Research Backlog — xigh Repositories Inspirations

**Date:** 2026-06-27
**Status:** Backlog / Research
**Source:** https://github.com/xigh?tab=repositories

---

## Context

This note consolidates research signals identified from the xigh GitHub repositories that are relevant to the AEOS roadmap.

AEOS is a local-first, sovereign AI Engineering Operating System. The goal of this research is to identify useful technical ideas and patterns from external sources, assess their alignment with AEOS sovereignty principles, and propose future sprint candidates.

No code is implemented here. This is a design and backlog document.

---

## Identified Resources and AEOS Inspirations

---

### 1. open-weight-models

**Source:** xigh repository focused on cataloging open-weight AI models with commercial-friendly licenses.

**What it covers:**
- Curated list of open-weight language models
- License classification (Apache 2.0, MIT, Llama Community License, etc.)
- Capability categorization (code, reasoning, instruction-following, multilingual)
- Model size and hardware requirements
- Benchmark references

**What it inspires for AEOS:**

AEOS currently supports a single default local model (`llama3.2` via Ollama). There is no mechanism for a user to discover which open-weight models are compatible with sovereign deployment.

A future **Sovereign Model Catalog** would allow AEOS to:
- Recommend models based on hardware constraints and use case
- Flag models with restrictive licenses (non-commercial, research-only)
- Validate that the chosen model is genuinely open-weight and self-hostable
- Integrate this information into `aeos ai doctor` or a dedicated `aeos model list` command

**Alignment with sovereignty:**
High. Using a model with a non-commercial license while building a product is a sovereignty risk. AEOS should be able to warn about this the same way it warns about Supabase or Clerk.

---

### 2. herbert-rs / Local Inference Engines

**Source:** xigh projects around Rust-based local inference and lightweight model runners.

**What it covers:**
- Rust implementations of local inference primitives
- Alternatives to full Ollama stack
- Inspiration for lightweight, embedded inference runtimes
- Patterns for wrapping llama.cpp, candle, or similar backends

**What it inspires for AEOS:**

AEOS Sprint 2J hardcoded Ollama as the only local provider (`provider = "ollama"`). This is a practical starting point but creates a soft dependency on a single runtime.

A future **Local Runtime Abstraction** would allow AEOS to:
- Support multiple local inference backends: Ollama, llama.cpp (via CLI or API), LM Studio, vLLM, custom OpenAI-compatible endpoints
- Decouple `aeos ai ask --provider local` from Ollama specifically
- Allow `aeos.toml` to specify `provider = "lmstudio"` or `provider = "llamacpp"` or `provider = "custom"`
- Keep a single interface (`ask_local_ai`) that dispatches to the right backend

**Alignment with sovereignty:**
High. True local sovereignty means not depending on any single inference stack. If Ollama is unavailable or has licensing changes, AEOS should route to an alternative without breaking the user's workflow.

---

### 3. DevSecOps — Trivy / Gitleaks / Snyk / Distroless

**Source:** xigh projects and references to container scanning, secret detection, and minimal base images.

**What it covers:**
- Trivy: container image vulnerability scanning
- Gitleaks: secret detection in git history
- Snyk: dependency vulnerability scanning
- Distroless / minimal base images: reduced attack surface

**What it inspires for AEOS:**

Sprint 2M added a static sovereignty check focused on external platform dependencies and portability. The next natural extension is a **Security and Supply Chain Check** covering:

- Secret scanning beyond env examples: scan git history for committed secrets (inspired by Gitleaks)
- Container image audit: detect non-distroless base images, known vulnerable base image versions (inspired by Trivy)
- Dependency audit: detect packages with known CVEs in package.json or pyproject.toml
- Supply chain: detect packages fetched from non-standard registries or with no pinned versions

This would extend `aeos sovereignty check` or introduce a new `aeos security check` command.

**Security constraints (unchanged):**
- Never read real secret values
- Only report names, locations, and patterns
- No network calls to external vulnerability databases in MVP

**Alignment with sovereignty:**
High. A truly sovereign project must also be secure. A container built on a vulnerable base image or a codebase with leaked secrets is not sovereign.

---

### 4. llm-copy-bench

**Source:** xigh benchmark project evaluating the ability of language models to faithfully reproduce structured content (IDs, hashes, YAML, commands, paths).

**What it covers:**
- Measuring copy fidelity of LLMs: can the model reproduce an exact string without hallucinating?
- Test cases: UUIDs, API keys (masked), file paths, YAML blocks, shell commands, hashes
- Evaluation methodology for local models

**What it inspires for AEOS:**

AEOS will eventually need a way to evaluate local models before trusting them in agentic or engineering workflows. A model that hallucinates file paths or corrupts YAML output is not suitable for sovereign engineering use.

A future **AI Model Evaluation** sprint would allow AEOS to:
- Run a local benchmark suite against the configured model
- Test copy fidelity, instruction following, structured output (JSON/YAML)
- Produce a simple sovereignty score: `PASS / WARN / FAIL` per test category
- Integrate as `aeos ai eval` or `aeos model eval`

**Alignment with sovereignty:**
Medium-High. A sovereign system must be able to trust its own tools. Evaluating the local model before use reduces the risk of silent corruption in generated code, config, or documentation.

---

## Proposed Future Sprints

| Sprint | Name | Inspiration | Priority |
|--------|------|-------------|----------|
| 2N | Security & Supply Chain Check | Gitleaks, Trivy, Snyk | High |
| 2O | Sovereign Model Catalog | open-weight-models | High |
| 2P | Local Runtime Abstraction | herbert-rs, llama.cpp | Medium |
| 2Q | AI Model Evaluation | llm-copy-bench | Medium |
| 2R | Lovable/Supabase Migration Plan | Sprint 2M sovereignty findings | Medium |

---

## Priority Rationale

**Sprint 2N — Security & Supply Chain Check (High)**

Sprint 2M introduced sovereignty detection. The natural next layer is security: secrets in git history, vulnerable dependencies, and insecure container images. This extends the existing `sovereignty check` pattern and fits squarely within the static analysis philosophy established in Sprint 2M.

**Sprint 2O — Sovereign Model Catalog (High)**

AEOS positions itself as local-first. Without a way to validate that the chosen model is open-weight and commercially usable, the AI sovereignty guarantee is incomplete. Users need guidance on which models are safe to use in production.

**Sprint 2P — Local Runtime Abstraction (Medium)**

Ollama is the current only supported runtime. Abstracting the runtime is important for long-term resilience but is not urgent while Ollama remains stable and widely adopted.

**Sprint 2Q — AI Model Evaluation (Medium)**

Evaluating models is useful but requires having a model available locally. This sprint is gated on a working local setup, which makes it lower priority for MVP validation.

**Sprint 2R — Lovable/Supabase Migration Plan (Medium)**

This sprint would use the sovereignty check findings from Sprint 2M to generate concrete migration plans. It depends on Sprint 2M being fully validated and is a natural follow-up.

---

## Out of Scope for Immediate Sprints

The following are intentionally deferred and not planned for the near term:

- Automatic migration from Supabase to PostgreSQL
- Automatic removal of hosted dependencies from code
- Integration with external vulnerability databases (CVE lookup)
- Online registry of sovereign vs. non-sovereign packages
- Scoring system or sovereignty index
- FinOps analysis
- UI or graphical interface
- Agentic remediation workflows
- Remote deployment tooling

---

## Alignment with AEOS Sovereignty Principles

| Principle | Covered by these inspirations |
|-----------|-------------------------------|
| Local-first AI | Open-weight catalog, local runtime abstraction, model evaluation |
| No silent frontier calls | Model evaluation validates local model fitness before use |
| No secret exposure | Security check extends Sprint 2M secret detection |
| Portable by default | Container scanning, distroless images, supply chain audit |
| No mandatory external dependency | Runtime abstraction removes Ollama as a hard requirement |
| Auditable | All proposed checks remain static, read-only, and reproducible |

---

## Notes

- All proposed sprints must maintain the existing quality constraints: stdlib only, no network calls in check commands, no secret display, ruff + mypy + pytest quality gate.
- The sovereignty check extension in Sprint 2N should reuse `SovereigntyFinding` and `SovereigntyCheckResult` from Sprint 2M.
- The model catalog in Sprint 2O should be embedded in AEOS (not fetched from a remote registry) for Sprint MVP.
- All new commands must follow the established CLI pattern: sub-app + command + optional `--json`.
