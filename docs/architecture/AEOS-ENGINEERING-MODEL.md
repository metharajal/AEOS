# AEOS Engineering Model

**Version:** 1.0
**Status:** PROPOSED
**Date:** 2026-07-02
**Authority:** Derived from [MANIFESTO.md](../../MANIFESTO.md) · [CONSTITUTION.md](../../CONSTITUTION.md)
**Governs:** All current and future AEOS development

---

## Preamble

This document defines the permanent conceptual structure of AEOS.

It does not describe technologies. It does not reference implementations. It does not
prescribe tools. All technologies, models, providers, and implementations are considered
interchangeable at all times.

This document will remain valid even if, in five years, every model, every runtime,
every provider, and every tool mentioned in other documents has been replaced.

Its authority derives from the MANIFESTO and the CONSTITUTION. It may only be changed
through a formal RFC process that demonstrates consistency with both.

Every future capability, every new engine, every new rail, and every new agent must
demonstrate compatibility with this model before it can be considered for AEOS.

---

## 1. Mission permanente

### 1.1 Le problème fondateur

There is a permanent gap between **creating software** and **owning software**.

This gap manifests in three recurring forms:

**The generation trap.** AI tools and no-code platforms create working software at
unprecedented speed. But the speed of creation conceals a structural problem: the
person who generated the project does not own it. The stack was chosen by the tool.
The infrastructure is controlled by the platform. The data is on servers the builder
did not select. The code has no tests, no documentation, no portability, and no
governance. When a serious client, institution, or investor asks the right questions,
there are no clean answers.

**The legacy trap.** Organizations operating critical systems — governments, banks,
hospitals, enterprises — frequently run software that nobody fully understands, that
cannot be easily modified, and that every consultant recommends migrating without
explaining to what, or why. These systems represent enormous sunk investment. They
encode business logic that has never been documented. They fail slowly and expensively.
The path forward is systematically obscured by vendor capture, cost, and fear.

**The cost sovereignty trap.** Developing with frontier AI platforms at scale is not
economically viable for independent builders, small teams, or organizations in
cost-constrained markets. The marginal cost per iteration compounds. The routing
decisions are made by the platform, not the engineer. The data leaves the machine
without explicit human authorization. Local AI is now capable enough for most
engineering tasks — but there is no structure, no routing model, and no governance
framework for using it responsibly.

These three problems are manifestations of a single deeper problem:

> **Software mastery has not kept pace with software creation.**

The tools to create have multiplied. The tools to own, govern, and control what was
created have not.

### 1.2 La mission permanente

AEOS exists to close the gap between creation and mastery permanently.

Its mission is:

> **To give any person, team, or organization the tools and the discipline to
> understand, control, evolve, and operate their software — regardless of how it
> was created, what tools were used, or what AI systems are available.**

This mission does not depend on any technology. It is valid before AI, during AI,
and after whatever comes after AI.

It is valid for a solo founder with a generated prototype. It is equally valid for
a government agency with a twenty-year-old monolith.

### 1.3 La thèse permanente

AEOS operates from a single founding conviction that drives every design decision:

> **Creating fast and owning what you created are not the same thing.**
> **AEOS makes them the same thing.**

The gap between the two is where AEOS operates. Not at the moment of creation — but
at every moment after creation, through the entire lifespan of the software.

### 1.4 Ce qu'AEOS est — définition permanente

AEOS is a **Sovereign Software Continuity Platform**.

It is an **AI Engineering Operating System** — a layer of engineering mastery above
the tools, platforms, and AI systems used to create and evolve software.

It is not a code generator. It is not an AI assistant. It is not a migration tool.
It is not a compliance framework.

It is the engineering foundation from which software can be created, reclaimed,
modernized, migrated, governed, and operated — under technical, economic, and
sovereign control — regardless of its origin, its current state, or the tools
available at any given time.

Its four defining characteristics, which must remain true regardless of implementation:

1. **Engineering-first**: principles over technologies, always
2. **Human-gated**: no significant action without explicit human authorization
3. **Evidence-producing**: every operation generates inspectable proof
4. **Sovereignty-preserving**: control, portability, and independence as outputs

---

## 2. Les invariants

Invariants are non-negotiable constraints that define what AEOS is. They cannot be
weakened, bypassed, or traded for convenience, speed, or novelty.

They are listed here in their conceptual form. Each has a code-enforced counterpart.

---

### INV.01 — Souveraineté (Sovereignty)

**Definition:** AEOS always produces outputs that increase, or at minimum preserve,
the operator's control over their software and data.

**Role:** Sovereignty is the primary output of every AEOS operation. A command that
produces analysis must produce analysis that helps the operator reduce dependency.
A proposal that suggests changes must propose changes that increase control.

**Why it exists:** The MANIFESTO declares: *"We build for independence. We design
systems that can be owned, operated, and evolved by their users — without dependency
on any single vendor, platform, or actor."* Sovereignty is the operational form of
this conviction.

**Consequences for architecture:** Every capability has an associated sovereignty
measurement. Every engine must be expressible without cloud dependency. Every provider
must be replaceable. No operation may introduce a new vendor dependency without
documenting it, quantifying it, and proposing an exit path.

---

### INV.02 — Continuité logicielle (Software Continuity)

**Definition:** AEOS always produces outputs that increase the long-term
maintainability, understandability, and operability of the software it governs.

**Role:** Continuity is the temporal dimension of sovereignty. It is not enough to
control a project today — AEOS must ensure it remains controllable in five years,
by a different team, with different tools.

**Why it exists:** The CONSTITUTION §2.1 establishes: *"Engineering excellence is
measured by the longevity of what is built, not by the speed at which it was
produced."*

**Consequences for architecture:** Every governance document produced by AEOS must
describe current reality, not aspirational state. Every proposal must include rollback
notes. Every memory record must be human-validated before becoming a learning input.

---

### INV.03 — Local-first

**Definition:** Every AEOS operation runs locally by default, without requiring an
external network connection.

**Role:** Local-first is the operational expression of sovereignty. A system that
requires network access by default surrenders control to the network. AEOS must be
fully functional on an air-gapped machine.

**Why it exists:** *"We refuse to build lock-in by design."* (MANIFESTO §III) A
tool that requires network access to function creates a dependency on external
availability, external pricing, and external data policies.

**Consequences for architecture:** No engine may have a network call as its default
path. Every capability must have a deterministic, offline fallback. External network
calls are exceptions that require explicit configuration, explicit human authorization,
and explicit logging.

---

### INV.04 — IA local-first

**Definition:** AI assistance defaults to locally-running models. Frontier AI —
any model not running on the operator's infrastructure — is used only when local
AI is demonstrably insufficient, with explicit human authorization for each call.

**Role:** AI local-first is the economic and sovereign form of local-first applied
to AI specifically. It ensures that the marginal cost of AI-assisted engineering is
controllable, and that no data leaves the machine without explicit intent.

**Why it exists:** The CONSTITUTION §3.4 and the AI Runtime Doctrine both establish
that AI is a partner, not an authority. Using a frontier provider by default makes
the platform the authority over what happens to the operator's data.

**Consequences for architecture:** The AI routing layer must be configurable per
operation. Local AI is the first path. Frontier AI is the exception path with a
mandatory human gate. The routing decision must be logged permanently.

---

### INV.05 — Fonctionnement hors ligne (Offline Operability)

**Definition:** AEOS must be fully functional without any network access. Every
diagnostic, governance, memory, and planning capability must produce valid output
on a machine with no internet connection.

**Role:** Offline operability is the strongest test of local-first. If a capability
fails without network access, it is not truly local-first.

**Why it exists:** Organizations with the highest security requirements — government,
military, healthcare, regulated finance — operate in environments with strict network
controls. AEOS must serve these environments without compromise.

**Consequences for architecture:** The deterministic fallback is always available.
AI assistance is an enhancement, never a precondition. No capability may require a
network call to produce its baseline output.

---

### INV.06 — Human-in-the-loop

**Definition:** No significant, irreversible, or destructive action is taken without
explicit human authorization. AI proposals are exactly that — proposals. Humans decide.

**Role:** Human-in-the-loop is the accountability mechanism. It ensures that the
human who validates an action owns that action — regardless of how it was produced.

**Why it exists:** The MANIFESTO §II: *"Human judgment, human ethics, and human
accountability cannot be delegated to any system — artificial or otherwise."* The
CONSTITUTION §3.4 establishes that AI shall never perform irreversible actions
without explicit human authorization.

**Consequences for architecture:** Action Levels 3 and above require documented human
gates. No agent, no engine, and no interface bypasses a gate. The `applied: false`
invariant is code-enforced: nothing is applied until a human explicitly triggers
application. There is no `--force-apply` flag.

---

### INV.07 — Auditabilité (Auditability)

**Definition:** Every significant AEOS operation leaves a permanent, inspectable,
immutable evidence record. Nothing happens without a trace.

**Role:** Auditability is the proof mechanism. It allows any observer — human or
external auditor — to reconstruct what happened, when, why, and what the result was.

**Why it exists:** The CONSTITUTION §2.7: *"History is an engineering asset. It
shall never be rewritten to hide mistakes."* Evidence is how AEOS demonstrates that
its invariants were respected.

**Consequences for architecture:** Every engine produces an evidence artifact. Every
proposal cites the evidence that justifies it. Every apply operation produces an
apply log before it begins. Evidence is never retroactively altered or deleted.

---

### INV.08 — Reproductibilité (Reproducibility)

**Definition:** Every AEOS environment and every AEOS output can be reproduced by
any person, on any machine, using only documented inputs and documented procedures.

**Role:** Reproducibility is the foundation of collaboration and long-term sustainability.
A system that cannot be reproduced cannot be maintained.

**Why it exists:** The CONSTITUTION §2.6: *"Any contributor shall be able to recreate
the engineering environment using the documented process."*

**Consequences for architecture:** AEOS outputs are deterministic given the same inputs.
Non-deterministic outputs (AI-generated content) are always marked as such and always
require human review. Environment setup requires no personal knowledge, no oral
tradition, no undocumented local state.

---

### INV.09 — Sécurité by design (Security by Design)

**Definition:** Security is an architectural property, not a feature. Every AEOS
component is designed to minimize attack surface, handle failures safely, and never
expose sensitive data.

**Role:** Security by design means that security is not added after the fact — it is
present in every design decision.

**Why it exists:** The CONSTITUTION §2.5 and §6.2 establish six absolute safety
requirements: no secret exposure, no unauthorized modification, no applied state
without intent, no silent AI escalation, no destructive action without gate, no
autonomous production change.

**Consequences for architecture:** Secret values never appear in any output, log, or
transmitted context. The context sanitization gate is mandatory and non-bypassable.
Read-only is the design default for all diagnostic capabilities.

---

### INV.10 — Standards ouverts (Open Standards)

**Definition:** AEOS prefers open standards, open formats, and open interfaces in
all its outputs, configurations, and provider contracts.

**Role:** Open standards ensure that AEOS outputs are interoperable, inspectable,
and independent of proprietary tooling. A project governed by AEOS must be readable
by anyone without a license to a specific tool.

**Why it exists:** The MANIFESTO §III: *"We believe that openness and sovereignty
are not opposites."* Proprietary formats create the exact dependency AEOS exists to
eliminate.

**Consequences for architecture:** Configuration formats are standard text formats
(TOML, JSON, Markdown). AI context uses documented HTTP interfaces. All evidence is
serializable to human-readable formats. No governance document requires a proprietary
reader.

---

### INV.11 — Modularité (Modularity)

**Definition:** Every AEOS engine, capability, and provider is independently deployable,
independently testable, and independently replaceable without affecting others.

**Role:** Modularity prevents the accumulation of hidden coupling. It ensures that
replacing one component does not require understanding the whole system.

**Why it exists:** The CONSTITUTION §5.3: *"Engines are the bounded, testable units
of AEOS functionality. Each engine has a single, clearly defined scope. Dependencies
between engines are explicit and directed. Circular dependencies are not permitted."*

**Consequences for architecture:** The dependency graph is a directed acyclic graph.
Every module declares its dependencies. No module depends on its callers. Side effects
are documented at module boundaries. Every safety invariant is enforced internally,
not delegated to the caller.

---

### INV.12 — Portabilité (Portability)

**Definition:** Every project governed by AEOS can be moved to a different machine,
a different provider, and a different team — using only its documented artifacts.

**Role:** Portability is the test of sovereignty. A project that cannot be moved is
a project that is captured.

**Why it exists:** The CONSTITUTION §5.3: *"AEOS is infrastructure-independent. No
engine requires a cloud account, a hosted service, or an external network connection
by default."*

**Consequences for architecture:** Every AEOS scaffold includes portability artifacts
(containerization, migration scripts, environment documentation). Every audit measures
portability as a first-class metric. A project cannot reach the `sovereign` maturity
level without demonstrating portability.

---

### INV.13 — Absence de verrouillage fournisseur (No Vendor Lock-in)

**Definition:** AEOS never creates a dependency on a specific vendor, platform, tool,
or AI provider that is not documented, not quantified, and not paired with a documented
exit path.

**Role:** No-lock-in is the permanent application of sovereignty across all technical
choices. Every dependency is a potential capture. Every dependency must be documented.

**Why it exists:** The MANIFESTO §III: *"We refuse to build lock-in by design."* The
CONSTITUTION establishes that all providers are replaceable by architectural definition.

**Consequences for architecture:** Every provider used by AEOS is defined by a contract
(interface), not by a specific implementation. Any provider that satisfies the contract
can be substituted. Lock-in is always explicit, documented, and paired with exit options.

---

### INV.14 — Read-only par défaut · Applied: false

**Definition:** All diagnostic, analysis, and planning operations are non-destructive
by default. `read_only: true` is the default state. `applied: false` is the invariant
of every non-apply operation.

**Role:** These two invariants are the machine-readable expression of the human gate.
They appear in every output surface as a constant reminder that the operator must
explicitly act to cause any change.

**Why it exists:** The CONSTITUTION §6.2 makes these absolute: they cannot be
overridden by configuration, agent behavior, or any interface. They are code-enforced
and test-verified.

**Consequences for architecture:** Every output carries its governance flags. Every
engine that might theoretically have side effects must prove it has none in read-only
mode. Tests explicitly verify that diagnostic operations leave no trace on the
audited project.

---

### INV.15 — Evidence obligatoire (Mandatory Evidence)

**Definition:** Every significant AEOS operation — diagnostic, proposal, apply, or
governance action — produces an evidence artifact before declaring completion. No step
is complete without evidence. No proposal exists without citing evidence.

**Role:** Mandatory evidence prevents the decoupling of action from proof. It ensures
that claims made by AEOS are always backed by inspectable records.

**Why it exists:** The CONSTITUTION §5.1: *"Evidence production is a design requirement.
Every operation that produces a result must produce that result in a form that is
inspectable, serializable, and auditable."*

**Consequences for architecture:** The Evidence Engine is not optional. It is invoked
by every other engine at step completion. Evidence is produced before status is updated.
A step that cannot produce evidence has not completed.

---

## 3. Les couches permanentes

AEOS is organized into eight conceptual layers. Dependencies flow downward only:
a layer may use the layers below it, never the layers above it.

Governance is the horizontal constant: its invariants apply at every layer and cannot
be bypassed by any layer.

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1 — Interface                                            │
│  How humans and systems interact with AEOS                      │
│  CLI · API · Workspace · Agents                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│  LAYER 2 — Rail Orchestration                                   │
│  How capabilities are organized into product-level paths        │
│  Build · Reclaim · Modernize · Migrate · Operate                │
│  Security · Sovereignty · Agents · Memory                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│  LAYER 3 — Capabilities                                         │
│  What AEOS can do, independently of implementation              │
│  Discover · Assess · Recover · Transform · Continue             │
│  Govern · Operate · Learn                                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│  LAYER 4 — Engines                                              │
│  Bounded, testable units that implement capabilities            │
│  Each engine: single scope · read-only default · evidence output│
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│  LAYER 5 — Knowledge                                            │
│  What AEOS remembers and how it accumulates validated learning  │
│  Memory · Evidence · History                                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│  LAYER 6 — Governance                                           │
│  What rules AEOS enforces unconditionally                       │
│  Policy · Invariants · Standards · Proposals · Playbooks        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│  LAYER 7 — AI Orchestration                                     │
│  How AEOS routes to AI, sanitizes context, and logs interaction │
│  AIRouter · AIContext · AIResponse · AIInteractionLog           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│  LAYER 8 — Provider Abstraction                                 │
│  What interface any external system must expose to AEOS         │
│  AIProvider · StorageProvider · IdentityProvider · etc.         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│  PROVIDERS (replaceable implementations)                        │
│  Any system that satisfies a provider contract                  │
│  Interchangeable. Never known to upper layers by name.          │
└─────────────────────────────────────────────────────────────────┘
```

### Layer 1 — Interface

**Mission:** Expose all AEOS capabilities to humans and systems through interaction
models appropriate to different contexts. All interfaces expose the same underlying
capabilities with the same invariants.

**Responsibilities:**
- Accept human input and translate it into capability invocations
- Present capability outputs in the format appropriate to the interface
- Enforce that no interface bypasses the invariants defined in Layer 6
- Maintain CLI as the authoritative reference when interfaces diverge

**Limits:**
- An interface never contains business logic
- An interface never makes decisions — it routes and presents
- No interface may offer a capability that does not exist in the engine layer

**Authorized dependencies:** Layer 2 (Rail Orchestration), Layer 4 (Engines directly for
diagnostic commands), Layer 6 (Governance, to enforce invariants at output time)

---

### Layer 2 — Rail Orchestration

**Mission:** Organize capabilities into product-level paths that correspond to the
real journey of a software project. Rails are the user-visible organization of AEOS.

**Responsibilities:**
- Define coherent paths through capabilities (e.g., Reclaim = Discover + Assess + Recover)
- Maintain the sequential stage model for each rail where ordering matters
- Document which capabilities each rail combines and in what order
- Ensure that no rail bypasses the capability layer by calling engines directly

**Limits:**
- Rails do not contain implementation logic — they orchestrate capabilities
- A rail does not have its own state — state lives in Knowledge (Layer 5)
- Rails are additive: a new rail must not break existing rail behavior

**Authorized dependencies:** Layer 3 (Capabilities), Layer 5 (Knowledge, to read context),
Layer 6 (Governance, to enforce gates and policies)

---

### Layer 3 — Capabilities

**Mission:** Define what AEOS can do, in terms that are permanently valid regardless
of the tools, languages, or AI systems available.

The eight capabilities are the official vocabulary for describing AEOS operations.
They are constitutional (CONSTITUTION §1.4). They do not change without a
Constitutional amendment.

| Capability | Purpose |
|---|---|
| **Discover** | Understand what exists: structure, dependencies, providers, generators, risks |
| **Assess** | Evaluate current state: control map, security posture, sovereignty level, maturity |
| **Recover** | Bring a project to a controlled, secure, portable, and governable state |
| **Transform** | Move a project toward a target architecture in controlled, tested, reversible steps |
| **Continue** | Resume or sustain development under controlled AI assistance |
| **Govern** | Define, enforce, and maintain standards, decisions, and policies |
| **Operate** | Monitor, audit, and maintain projects over time |
| **Learn** | Accumulate validated knowledge from operations and human-confirmed outcomes |

**Responsibilities:**
- Each capability has a precisely defined scope that does not expand without RFC
- Capabilities are composable: a rail may invoke multiple capabilities in sequence
- Each capability invocation produces at minimum one evidence artifact

**Limits:**
- A capability does not name its engine implementation
- A capability does not name any provider
- A capability description remains valid regardless of the implementation technology

**Authorized dependencies:** Layer 4 (Engines), Layer 5 (Knowledge), Layer 6 (Governance)

---

### Layer 4 — Engines

**Mission:** Provide bounded, testable, independently operable units that implement
one or more capabilities. Engines are the implementation units of AEOS.

**Responsibilities:**
- Enforce their own safety invariants internally (not delegated to callers)
- Produce structured, serializable output for every operation
- Default to read-only behavior and explicitly declare when writes are required
- Produce evidence at step completion before updating any status

**Limits:**
- An engine has a single, clearly defined scope
- An engine never calls another engine directly — dependency is always upward
- An engine never knows which interface invoked it
- An engine never names a specific AI provider or implementation

**Authorized dependencies:** Layer 5 (Knowledge), Layer 6 (Governance invariants),
Layer 7 (AI Orchestration, via abstract interface only)

---

### Layer 5 — Knowledge

**Mission:** Accumulate, store, and retrieve the validated learning that AEOS
generates over time — locally, immutably, without cloud dependency.

**Responsibilities:**
- Store audit results as immutable, human-validated records
- Maintain the audit history and timeline for each project
- Produce comparison and trend outputs from historical records
- Ensure that knowledge never includes secret values or raw file contents

**Limits:**
- Knowledge is never updated autonomously — human validation is required
- Knowledge is local-first: no cloud sync by default
- Knowledge accumulates but never makes decisions — it informs
- An inference from knowledge is a proposal, not an action

**Authorized dependencies:** Layer 6 (Governance, for validation gates)

---

### Layer 6 — Governance

**Mission:** Define, communicate, and enforce the non-negotiable rules that apply
to every layer of AEOS without exception.

Governance is the horizontal invariant layer. It does not have a single place in
the dependency chain — it is applied at every layer. Every engine, every capability,
every interface, and every provider interaction must satisfy the governance layer.

**Responsibilities:**
- Maintain and enforce the 15 invariants defined in §2
- Define the Proposal lifecycle and its invariants
- Define the Standards hierarchy (MANIFESTO → CONSTITUTION → Standards → Playbooks)
- Produce governance documents as first-class engineering artifacts
- Maintain the Policy objects that define what may never be violated

**Limits:**
- Governance does not implement capabilities — it constrains them
- A governance rule that cannot be enforced in code is not an invariant — it is a guideline
- Governance documents must reflect current reality, not aspirational state

**Authorized dependencies:** Layer 5 (Knowledge, to produce evidence-backed governance)

---

### Layer 7 — AI Orchestration

**Mission:** Provide the routing, sanitization, logging, and gate mechanism for
all AI interactions — local or frontier — in a provider-agnostic, auditable way.

**Responsibilities:**
- Route AI requests to the appropriate provider based on configured strategy
- Sanitize context before any AI call (secret gate, file content gate, PII gate)
- Enforce the human approval gate before any frontier AI call
- Log every AI interaction (by hash, never by raw content)
- Provide deterministic fallback when no AI provider is available

**Limits:**
- AI Orchestration never knows what the response will be used for
- AI Orchestration never applies any AI response — it only routes and logs
- AI Orchestration never names a specific provider in its routing logic
- The sanitization gates cannot be disabled by configuration

**Authorized dependencies:** Layer 8 (Provider Abstraction)

---

### Layer 8 — Provider Abstraction

**Mission:** Define the minimum contract that any external system must satisfy to
be used by AEOS. The abstraction layer makes providers interchangeable.

**Responsibilities:**
- Define provider contracts (interfaces, not implementations)
- Guarantee that the replacement of any provider requires only configuration change,
  not code change (the runtime replacement test)
- Document which contract each family of providers must satisfy

**Limits:**
- Provider Abstraction never knows which concrete provider is in use at runtime
- Provider Abstraction never contains business logic
- The abstraction contract for a provider family is stable — providers must adapt
  to AEOS's contract, not the reverse

**Authorized dependencies:** Providers (Layer 9, via the defined contract only)

---

## 4. Les objets fondamentaux

These are the core business objects of AEOS. They are technology-independent. Their
definition must remain valid regardless of implementation language or storage technology.

### Project

The fundamental unit of AEOS governance. A Project is a codebase and its associated
governance artifacts, registered within AEOS scope.

| Property | Description |
|---|---|
| Identity | A unique name and associated metadata |
| Scope | A codebase directory and its governance documents |
| State | A measured maturity level and sovereignty level |
| History | An accumulation of MemoryRecords over time |
| Policy | The policies that apply to this project |

A Project is what AEOS governs. Everything else is produced in service of a Project.

---

### Workspace

The multi-surface, read-only presentation of a Project's current state, produced
for human consumption.

| Property | Description |
|---|---|
| Content | Derived from MemoryRecords, Evidence, Proposals, and Agent Plans |
| Nature | Always read-only — a view, never an editor |
| Surfaces | CLI output · static HTML · API response · Agent summary |
| Freshness | Regenerated on demand — never auto-updated |

The Workspace is the artifact a human reviews before making a decision. It is the
bridge between machine analysis and human judgment.

---

### MemoryRecord

An immutable, validated snapshot of a single AEOS audit run. The fundamental unit
of the Knowledge layer.

| Property | Description |
|---|---|
| Content | Aggregate counts and status labels — never raw values, never secrets |
| Immutability | A MemoryRecord is never modified after creation |
| Validation | Human-validated before being used as learning input |
| Scope | One audit run, one project, one point in time |

MemoryRecords are the foundation of AEOS's learning. The timeline of MemoryRecords
for a project is its engineering history.

---

### Evidence

A durable, inspectable proof that a step or capability has been exercised. Evidence
is produced before a step is marked complete.

| Property | Description |
|---|---|
| Timing | Written before status is updated (never retroactively) |
| Immutability | An evidence artifact is never altered after creation |
| Content | What was done, when, with what result, by what mechanism |
| Scope | One step, one operation, one moment in time |

Evidence is the machine-readable answer to "prove it." It enables external audit,
internal review, and historical reconstruction.

---

### Proposal

The contract between machine analysis and human action. A structured, evidence-backed
recommendation that a human must validate before anything is executed.

| Property | Description |
|---|---|
| Origin | Generated deterministically from MemoryRecords by an Agent |
| Nature | Always read-only until a human triggers application |
| Invariants | `read_only: true · applied: false · human validation required` always present |
| Persistence | Stored locally as a governance record |
| Lifecycle | pending → applied or pending → dismissed (terminal states, no rollback) |
| Immutability | A Proposal's content never changes after creation |

The full Proposal lifecycle is defined in the Proposal Lifecycle Contract.

---

### Workflow

An ordered, gate-defined sequence of steps that implements a capability arc. Workflows
are the operational form of a Rail.

| Property | Description |
|---|---|
| Structure | Ordered steps with defined inputs, outputs, and evidence requirements |
| Gates | Human approval points that must be passed before the next step begins |
| Rollback | Every destructive step has a documented rollback path |
| Evidence | Each step produces evidence before the next step begins |

Workflows are implemented in Playbooks. They are the operational bridge between
strategy (Rails) and execution (Engines).

---

### Policy

A non-negotiable rule enforced by the system at all times, under all conditions.
Policies cannot be disabled by configuration or bypassed by interface choice.

| Property | Description |
|---|---|
| Enforcement | Code-enforced and test-verified — not conventional |
| Scope | Applies across all layers, all interfaces, all providers |
| Change process | Policies may only be changed through the Constitutional amendment process |
| Examples | No secret in output · No applied: true without human gate · No silent AI escalation |

Policies are the machine-readable form of invariants. Every invariant defined in §2
has one or more corresponding policies.

---

### Context

The sanitized, secret-free, file-content-free information provided to any AI provider.
Context is the boundary between AEOS internal state and external AI systems.

| Property | Description |
|---|---|
| Content | Aggregate counts, status labels, metadata — never raw values |
| Sanitization | Mandatory secret gate and file content gate before construction |
| Scope | One AI interaction request |
| Logging | Logged by hash after sanitization (never by content) |

Context is the mechanism by which AEOS can use AI assistance without surrendering
data sovereignty. The sanitization gate is the last enforcement point before any
data leaves the machine.

---

### Knowledge

The accumulated body of validated findings, patterns, and corrections that AEOS
has stored from human-confirmed operations.

| Property | Description |
|---|---|
| Accumulation | Grows over time through human-validated audit results |
| Validation | Human confirmation is required before a result enters Knowledge |
| Use | Informs future proposals and plans — never makes autonomous decisions |
| Storage | Local-first, no cloud sync by default |

Knowledge is what makes AEOS more accurate over time. It is the memory of what was
true, confirmed by a human, at a specific point in time.

---

### Provider

Any replaceable external capability that AEOS uses to perform its operations. A
Provider is always defined by its contract (interface), never by its implementation.

| Property | Description |
|---|---|
| Identity | A named capability family (AI, Storage, Identity, etc.) |
| Definition | A contract defining required inputs, outputs, and behaviors |
| Replaceability | Any Provider that satisfies the contract can replace any other |
| Independence | A Provider never knows how AEOS uses its output |

Providers are the interchangeable layer. Changing a Provider requires only configuration
change — no code change (the runtime replacement test).

---

### Agent

A bounded, specialized AI assistant that operates within AEOS invariants to accomplish
a defined scope of engineering tasks.

| Property | Description |
|---|---|
| Scope | Precisely defined — no agent has a general mandate |
| Invariants | Agents do not bypass Core invariants — ever |
| Output | Always a Proposal or an Evidence artifact — never a direct apply |
| Accountability | Human validates every significant Agent output |

Agents reason. They do not decide. Every Agent output that results in a system change
passes through a human gate first.

---

### Task

A discrete, traceable unit of work with defined input, output, and evidence.

| Property | Description |
|---|---|
| Traceability | Every Task has an identifiable owner and a start/end timestamp |
| Output | A Task produces a documented artifact or a status update |
| Evidence | Completion requires evidence of the output produced |
| Gate | Tasks at Action Level 3+ require human approval to close |

Tasks are the smallest unit of work that AEOS tracks. They compose into Workflows.

---

## 5. Les capacités fondamentales

The eight core capabilities define what AEOS does, permanently and independently of
implementation. They are the official vocabulary for describing AEOS operations.

Each capability operates at one or more Action Levels (see §8). Each capability
produces at least one evidence artifact. Each capability is provider-agnostic: it
specifies what must happen, not which tool performs it.

---

### Discover

**Purpose:** Understand what exists in a software project before making any decision
about what to do with it.

**What it produces:** Structure map · dependency inventory · provider identification ·
generator detection · risk zone identification · unknown control zones

**Key principle:** Discover is always read-only, always non-destructive, always the
first step in any rail engagement. No action is taken before discovery is complete.

**Scale:** From a single file to an entire organization's portfolio.

---

### Assess

**Purpose:** Evaluate the current state of a project against defined standards of
control, security, sovereignty, and maturity.

**What it produces:** Control map · security posture · sovereignty level · maturity
level · finding classification · production readiness verdict

**Key principle:** Assessment produces evidence, not action. Every finding is classified
and cited. The Assessment does not propose remediation — it describes the gap between
current state and target state.

---

### Recover

**Purpose:** Bring a fragile, captured, or ungoverned project back to a controlled,
secure, portable, and governable state through a structured sequence of validated steps.

**What it produces:** Recovery plan · governance baseline · portability artifacts ·
security remediation · RLS hardening proposals · migration readiness

**Key principle:** Recovery is staged. Each stage has preconditions, defined actions,
evidence requirements, human gates, and rollback paths. No stage begins without
completing the previous stage's gates.

---

### Transform

**Purpose:** Move a project from one architecture to another — controlled, tested,
and reversible — with full evidence at every step.

**What it produces:** Migration plan · transformation roadmap · backup verification ·
dry-run results · rollback procedures · post-migration evidence

**Key principle:** Transform never applies anything without a backup, a dry-run,
a rollback path, and explicit human approval. "Apply first, fix later" is not a
pattern AEOS supports.

---

### Continue

**Purpose:** Resume or sustain active development of a project under controlled AI
assistance — local AI first, frontier by exception, with branch and PR discipline.

**What it produces:** Development workflow documentation · AI routing configuration ·
context filtering rules · local AI assistance · PR proposals · apply proposals

**Key principle:** Continue is the ongoing mode. It is not a one-time operation.
Every development session under Continue follows the same routing model: local AI
first, human-gated frontier escalation when needed.

---

### Govern

**Purpose:** Define, enforce, and maintain the engineering standards, architectural
decisions, security policies, sovereignty policies, and AI usage policies that ensure
long-term mastery of a project.

**What it produces:** ARCHITECTURE.md · DECISIONS.md · SECURITY.md · SOVEREIGNTY.md ·
AI-DEVELOPMENT-POLICY.md · Standards · Playbooks · ADRs · Proposals · Evidence

**Key principle:** Governance documents must reflect current reality. A governance
document that describes aspirational state is misleading, not governing. AEOS produces
governance from evidence, not from hope.

---

### Operate

**Purpose:** Monitor, audit, and maintain projects over time — detecting drift,
enforcing quality gates, and generating periodic evidence reports.

**What it produces:** Drift detection reports · periodic audit results · quality gate
status · MemoryRecord timeline · sovereignty drift alerts · AI cost audit

**Key principle:** Operate is continuous. It is not a milestone. A project enters
Operate mode and stays there. Evidence accumulates. Drift is detected early, before
it becomes a crisis.

---

### Learn

**Purpose:** Accumulate validated knowledge from AEOS operations and human-confirmed
outcomes — in local, controlled memory — to make future operations faster, more
accurate, and more consistent.

**What it produces:** MemoryRecords · knowledge base updates · pattern improvements ·
accuracy improvements in future Assessments and Plans

**Key principle:** Learning is human-validated. An inference from un-validated data
is a hypothesis, not knowledge. Every knowledge update requires a human to confirm
that the source is correct before it influences future operations.

---

## 6. Les familles de Providers

A Provider Family defines a type of external capability that AEOS may use. AEOS
defines the contract for each family. Any implementation that satisfies the contract
is a valid provider for that family.

AEOS never names a specific provider as required. Specific implementations are
configuration choices, not architectural dependencies.

---

### AI Provider

**Contract:** Accept a sanitized text prompt. Return a text completion. Support
offline detection (is the provider available?). Not require secret values in the
prompt.

**Sub-families:**
- Local AI Provider: runs on operator infrastructure, no data leaves the machine
- Frontier AI Provider: requires network access, explicit human authorization

**Contract invariants:**
- No AI Provider receives secret values, raw file contents, or PII
- Every AI Provider interaction is logged (by hash, not by content)
- Every frontier AI Provider call requires explicit human gate

---

### Coding Agent Provider

**Contract:** Accept a structured task description and context. Execute bounded
coding tasks within a defined scope. Produce a diff or a Proposal, never a direct apply.

**Contract invariants:**
- A Coding Agent Provider never pushes to remote repositories
- A Coding Agent Provider never applies to production without a human gate
- A Coding Agent Provider never reads secret values

---

### Embedding Provider

**Contract:** Accept text. Return a numeric vector representation. Support offline
operation or clearly declare online dependency.

**Use in AEOS:** Knowledge retrieval, semantic similarity for project pattern matching.

---

### Vector Store Provider

**Contract:** Store and retrieve vector embeddings with associated metadata. Support
local-first storage.

**Use in AEOS:** Future semantic memory and pattern retrieval.

---

### Knowledge Provider

**Contract:** Store, index, and retrieve structured documents. Support offline operation.

**Use in AEOS:** Documentation retrieval, standards lookup, project knowledge base.

---

### Source Control Provider

**Contract:** Provide read/write access to a versioned code repository. Support
branching, committing, and diff generation via a documented interface.

**Contract invariants:**
- AEOS never pushes to a protected branch without explicit human authorization
- AEOS never force-pushes without explicit human authorization

---

### Identity Provider

**Contract:** Authenticate and authorize users. Support standard open identity protocols.

**Contract invariants:**
- AEOS never stores credentials — it delegates authentication to the provider
- Credentials never appear in AEOS output or logs

---

### Storage Provider

**Contract:** Store and retrieve files or objects by key. Support local-first storage.
Provide portable data formats (no proprietary binary formats).

---

### Search Provider

**Contract:** Accept a query. Return ranked results from an indexed corpus. Support
both semantic and full-text modes.

---

## 7. Les familles d'Agents

Agent Families define the roles that AI agents play within AEOS. Each role has a
defined scope, a defined output type, and defined constraints. No agent may exceed
its defined scope.

Every agent family is independent of the AI model or runtime used to implement it.

---

### Planning Agent

**Role:** Break complex engineering work into safe, reversible, testable steps.
Produce structured plans with evidence references.

**Output:** AgentPlan · step sequence · risk assessment

**Constraints:** A Planning Agent never executes steps — it only proposes them.

---

### Discovery Agent

**Role:** Analyze project structure, dependencies, providers, and architecture to
produce a complete understanding of what exists.

**Output:** Structure map · dependency inventory · provider identification

**Constraints:** Read-only. No modification of the analyzed project.

---

### Architecture Agent

**Role:** Propose target architectures based on current state, constraints, and
sovereignty goals. Evaluate architectural options.

**Output:** Architecture proposals · trade-off analysis · recommendation with evidence

**Constraints:** Proposes only — never decides. Human approves every architectural choice.

---

### Security Agent

**Role:** Audit secret exposure, permission policies, dependency vulnerabilities,
and supply chain risks.

**Output:** Security findings · risk classification · remediation proposals

**Constraints:** Read-only. Never displays secret values. Never names a secret value.

---

### Coding Agent

**Role:** Implement specific, bounded code changes within a defined scope, under
explicit human direction.

**Output:** Diff · Proposal · branch with committed changes

**Constraints:** Never pushes to production. Never applies without human gate.
Every change is proposable before it is applied.

---

### Review Agent

**Role:** Review code, proposals, architecture, and governance documents against
defined standards.

**Output:** Review report · findings · checklist completion status

**Constraints:** Review output is advisory. Human accepts or rejects each finding.

---

### Testing Agent

**Role:** Generate and execute tests to verify behavior, prevent regression, and
validate invariants.

**Output:** Test suite · coverage report · test results

**Constraints:** Test execution is read-only. Test generation produces a Proposal
that a human merges.

---

### Documentation Agent

**Role:** Generate, update, and maintain governance documents, architecture records,
and evidence reports from validated sources.

**Output:** Governance documents · ADRs · evidence reports · READMEs

**Constraints:** Documentation generation produces a Proposal. Human reviews and
merges. Governance documents reflect evidence, not aspirations.

---

### Migration Agent

**Role:** Plan and orchestrate migrations between architectures, platforms, or data
stores, with backup verification, dry-run, and rollback path at every step.

**Output:** Migration plan · backup verification report · dry-run result · rollback procedure

**Constraints:** Never applies a migration without backup, dry-run, and explicit human
confirmation. Never applies to production without explicit human authorization.

---

### Governance Agent

**Role:** Enforce engineering standards, generate ADRs, manage decision records, and
maintain the Standards hierarchy.

**Output:** Standards compliance report · ADR proposals · decision records

**Constraints:** Governance enforcement is advisory in read-only mode. Enforcement
actions (blocking a merge, requiring a gate) are subject to human override.

---

### Memory Agent

**Role:** Store validated audit results, corrections, and decisions in local Knowledge.
Retrieve relevant historical context for current operations.

**Output:** MemoryRecord updates · knowledge retrieval results

**Constraints:** Never updates Memory without human-validated input. Memory updates
cite their source and validation date.

---

### Orchestrator Agent

**Role:** Route tasks to the appropriate specialized agent. Manage the sequence of
agent invocations within a Workflow. Enforce the routing doctrine (local AI first,
frontier by exception).

**Output:** Task routing decisions · escalation requests · workflow progress reports

**Constraints:** The Orchestrator never bypasses human gates. When a gate is required,
the Orchestrator stops and asks — it never proceeds autonomously.

---

## 8. Les rails du produit

Rails are the user-facing product paths. Each rail combines multiple capabilities
to address a distinct phase of the software lifecycle.

| Rail | Purpose | Core Capabilities | Status |
|---|---|---|---|
| **Build** | Start new projects correctly, with sovereignty and quality from day one | Continue · Govern | MVP |
| **Reclaim** | Audit, harden, and recover AI-generated or no-code projects | Discover · Assess · Recover | Production |
| **Modernize** | Understand and progressively transform monolithic or legacy applications | Discover · Assess · Transform | Planned |
| **Migrate** | Move from one architecture to another — controlled, tested, reversible | Transform · Recover | Planned |
| **Operate** | Continuous audit, security, optimization, and documentation | Operate · Assess | Planned |
| **Security** | Cross-cutting security verification — always read-only | Assess · Govern | Production (partial) |
| **Sovereignty** | Detect, measure, and reduce external platform dependency | Assess · Govern | Production (partial) |
| **Agents** | Cross-cutting task execution with specialized AI agents | All | Evolving |
| **Memory** | Local, controlled knowledge accumulation about projects and audits | Learn | Production |

**Rail principles:**
- A rail is not a feature — it is an organized path through capabilities
- A rail may engage capabilities in any order, but must follow their preconditions
- A rail does not bypass safety invariants
- A new rail must map to at least one existing capability before it can be added

---

## 9. Les grands flux

The primary operational flows of AEOS. These flows describe how objects move through
layers and what happens at each transition. They are independent of implementation.

---

### Flux 1 — Recovery Arc (Reclaim → Govern → Continue)

The standard path for an AI-generated or fragile project entering AEOS governance.

```
Existing project (ungoverned)
        │
        │  Discover + Assess
        ▼
Understanding (MemoryRecord created)
        │
        │  Recover (staged: governance → secrets → database → tests → portability)
        ▼
Controlled project (maturity: controlled → portable)
        │
        │  Govern (produce standards, decisions, policies)
        ▼
Governed project (maturity: sovereign)
        │
        │  Continue (local AI, branch + PR discipline, proposals)
        ▼
Operating project (ongoing: Operate + Learn)
```

---

### Flux 2 — Audit → Proposal → Human Gate

The atomic loop that underlies every AEOS operation that may result in a change.

```
MemoryRecords (existing validated knowledge)
        │
        │  Agent reads
        ▼
Analysis (deterministic or AI-assisted)
        │
        │  Evidence cited
        ▼
PRProposal (ephemeral, 14-section, rich)
        │
        │  Human reviews
        ▼
        ├─── Discard → stop
        │
        └─── Persist → Proposal (governance record, status: pending)
                │
                │  Human validates
                ▼
                ├─── Dismiss → Proposal (status: dismissed, preserved)
                │
                └─── Apply → Apply Engine
                                │
                                │  Pre-apply evidence
                                │  Human confirms
                                │  Step execution
                                │  Post-apply evidence
                                ▼
                           Proposal (status: applied)
                           New MemoryRecord created
```

---

### Flux 3 — Knowledge Accumulation

How AEOS learns over time.

```
Audit run → Raw findings
        │
        │  Human reviews findings
        ▼
Human-validated result
        │
        │  Memory Agent stores
        ▼
MemoryRecord (immutable, validated)
        │
        │  Accumulates over time
        ▼
Knowledge (timeline of MemoryRecords)
        │
        │  Informs future
        ▼
More accurate Plan → More accurate Proposal → Better human decisions
```

---

### Flux 4 — AI Interaction (any AI-assisted operation)

The controlled path for any AI call within AEOS.

```
Capability invocation requiring AI assistance
        │
        │  Build AIContext
        ▼
Context sanitization gate
(secret check · file content check · PII check)
        │
        ├── FAIL → Abort, log, inform human
        │
        └── PASS
                │
                │  Route: local first
                ▼
        Local AI Provider available?
        │
        ├── YES → Call local AI, log (hash), return AIResponse
        │
        └── NO → Is frontier allowed?
                │
                ├── NO → Deterministic fallback, log
                │
                └── YES → Human gate required
                                │
                                │  Display sanitized context summary
                                │  Human types confirmation
                                ▼
                        Call frontier AI
                        Log (hash + provider + timestamp)
                        Return AIResponse
                │
                └── AIResponse → Proposal (never direct apply)
```

---

### Flux 5 — Operate (Continuous Mode)

How AEOS maintains sovereignty over an operating project.

```
Scheduled or triggered audit
        │
        │  Discover + Assess
        ▼
New MemoryRecord
        │
        │  Compare with previous MemoryRecord
        ▼
Drift report (sovereignty drift? Security regression? New dependencies?)
        │
        ├── No drift → Log, continue
        │
        └── Drift detected → Evidence report + Human notification
                                │
                                │  Human reviews
                                ▼
                        Decision: accept drift or remediate?
                                │
                                ├── Accept → Document decision (ADR)
                                │
                                └── Remediate → Recovery Arc (Flux 1)
```

---

## 10. Les règles de dépendance

These rules govern what may depend on what within AEOS. They are architectural
invariants. Violating them introduces hidden coupling that makes AEOS harder to
maintain, test, and evolve.

### D.01 — Layer dependency is downward only

A layer may use the layers below it in the dependency stack. A layer may never use
the layers above it. This prevents circular dependency and keeps the system composable.

```
VALID:    Interface → Engine (Interface calls Engine)
INVALID:  Engine → Interface (Engine should never know its caller)
```

### D.02 — Providers know nothing about capabilities

A Provider (AI, Storage, Identity, etc.) never knows which AEOS capability is using
it. Providers are pure infrastructure. They implement a contract and return a result.
The capability that invokes them interprets the result.

```
VALID:    Capability calls Provider via abstract contract
INVALID:  Provider adjusts behavior based on which capability called it
```

### D.03 — Capabilities know nothing about specific providers

A capability is defined in terms of what it needs (the Provider contract), never in
terms of which specific implementation delivers it. A capability that names a specific
provider is coupled to that provider — which violates the replaceability requirement.

```
VALID:    Capability calls AI Orchestration Layer with a Context
INVALID:  Capability calls "the local Ollama server at localhost:11434"
```

### D.04 — Agents use abstractions, never implementations

An Agent invokes Capabilities and receives Context objects. An Agent never calls a
specific AI runtime, a specific storage backend, or a specific API directly.

```
VALID:    Planning Agent asks the Orchestrator for an AI response to a Context
INVALID:  Planning Agent calls a specific AI model API directly
```

### D.05 — Workflows orchestrate, Engines implement

A Workflow defines the sequence and the gates. An Engine implements the individual
step. A Workflow that contains implementation logic is a design violation.

```
VALID:    Recovery Workflow calls Assess Engine, then Recover Engine, with gates
INVALID:  Recovery Workflow contains logic for reading RLS policies
```

### D.06 — Safety invariants are enforced at the source

Every Engine enforces its own safety invariants. Safety is never delegated to the
caller. An Engine that can be made unsafe by its caller has a design defect.

```
VALID:    Assessment Engine enforces "no secret values in output" internally
INVALID:  Assessment Engine relies on the Interface to filter secret values
```

### D.07 — Knowledge informs, never decides

The Knowledge layer provides information. It never makes decisions. An inference
from Knowledge is a proposal, not an action. Any use of Knowledge that bypasses
a human decision point violates this rule.

```
VALID:    Planning Agent reads MemoryRecord, produces a Plan (proposal)
INVALID:  Memory Engine automatically applies a correction based on historical data
```

### D.08 — No layer imports from a higher layer

Circular dependencies are forbidden. If layer A uses layer B, then layer B must
never import from layer A or any layer above layer A in the stack.

---

## 11. Les règles d'évolution

Before any new capability, engine, rail, agent family, or provider family is added
to AEOS, the following questions must be answered affirmatively. This is not a
guideline — it is a gate.

---

**Q1: À quelle couche appartient-il ?**
Every new element must be assigned to exactly one layer in the model (§3). If it
spans multiple layers, it must be decomposed into components, each belonging to
one layer.

**Q2: Quel objet métier enrichit-il ?**
Every new element must enrich, produce, or consume at least one of the fundamental
objects defined in §4. If it creates a new object, that object must be formally
defined and added to §4 via RFC before the element can be added.

**Q3: Quelle capacité améliore-t-il ?**
Every new element must contribute to at least one of the eight core capabilities
defined in §5. A new rail must map to at least two capabilities. A new engine must
implement at least one capability. If it introduces a new capability, that capability
requires a Constitutional amendment.

**Q4: Respecte-t-il tous les invariants ?**
Every new element must be demonstrated to be compatible with all 15 invariants
defined in §2. Compatibility is demonstrated by tests, not by assertion.

**Q5: Est-il provider-agnostic ?**
Every new element that interacts with an external system must use the Provider
Abstraction layer. It must not name a specific external system in its logic.
If it requires a new provider family, that family must be formally defined in §6.

**Q6: Est-il remplaçable ?**
If the new element includes an external dependency (AI, storage, search, etc.), that
dependency must satisfy the runtime replacement test: changing the dependency
requires only configuration change, not code change.

**Q7: Fonctionne-t-il hors ligne ?**
Every new element must either operate offline by default, or must have a deterministic
fallback that operates offline. An element that requires network access for its
baseline function violates INV.03 and INV.05.

**Q8: Préserve-t-il la souveraineté ?**
Every new element must either increase or preserve the operator's sovereignty. An
element that introduces an undocumented external dependency, reduces portability,
or removes a human gate from the apply path violates INV.01 and INV.06.

**Q9: Produit-il des preuves ?**
Every new element that performs a significant operation must produce at least one
evidence artifact before marking the operation complete. A new engine that produces
no evidence artifact violates INV.07 and INV.15.

**Q10: A-t-il une frontière claire ?**
Every new element must have a precisely defined scope. Scope creep — adding
responsibilities that belong to another layer, another engine, or another capability —
is a design defect that must be resolved at design time, not after implementation.

---

## 12. Ce qu'AEOS refuse d'être

This section is not advisory. It defines what AEOS will never become, regardless
of market pressure, user request, or technological opportunity. Every refusal in
this section is grounded in the founding documents.

---

**AEOS n'est pas un IDE.**
An Integrated Development Environment centers the development workflow. AEOS governs
the engineering outcomes of that workflow. The distinction is permanent. AEOS provides
analysis, proposals, and governance artifacts. It does not replace the development
environment.

**AEOS n'est pas un simple assistant de code.**
A coding assistant responds to prompts and generates code. AEOS governs the entire
lifecycle of a software product — creation, recovery, modernization, migration,
operation, learning. Code generation is one action within one agent, within one
capability. It is not the identity of the platform.

**AEOS n'est pas un wrapper d'un fournisseur IA particulier.**
AEOS is provider-agnostic by definition. Any component of AEOS that names a specific
AI system in its architecture is in violation of the model. AI providers are
interchangeable implementations of the AIProvider contract.

**AEOS n'est pas un générateur de code sans gouvernance.**
Speed of code generation is not a value AEOS optimizes for. What AEOS optimizes for
is the longevity, portability, and sovereignty of what is generated. A project generated
in one minute that cannot be understood, maintained, or migrated in one year is a
failed project, regardless of how fast it was created.

**AEOS n'est pas dépendant d'un cloud.**
AEOS must be fully deployable on a local machine, without cloud accounts, without SaaS
subscriptions, and without network access. Any capability that requires a cloud provider
to function must provide a local alternative. If no local alternative exists, the
capability must declare its dependency explicitly and offer a documented exit path.

**AEOS n'est pas un outil qui crée du verrouillage fournisseur.**
AEOS is built to reduce dependency, not to create it. An AEOS-governed project must
always be more portable, more understandable, and more independent than it was before
AEOS touched it. A version of AEOS that makes projects dependent on AEOS itself would
be a contradiction of its mission.

**AEOS n'est pas un outil qui prend des décisions importantes automatiquement.**
Significant decisions — architectural choices, production applies, security exceptions,
data migrations — always require a documented human gate. An AEOS that makes these
decisions autonomously has abandoned its founding principle. The MANIFESTO declares
that human judgment, human ethics, and human accountability cannot be delegated to
any system.

**AEOS n'est pas un outil nécessitant une connexion permanente.**
Offline operability is an invariant. A tool that requires always-on connectivity
excludes organizations with limited or controlled network access — precisely the
organizations in Africa and in regulated markets for which AEOS is built.

**AEOS n'est pas un outil qui envoie des secrets à une IA.**
No secret value ever leaves the machine through AEOS, to any AI provider, under any
condition. This is INV.09 and it is absolute. A version of AEOS that sends `.env`
contents, API keys, connection strings, or sensitive business data to an AI provider
has violated its core security invariant.

**AEOS n'est pas un outil dont les outputs s'appliquent automatiquement.**
`applied: false` is the invariant of all diagnostic and analytical outputs. There is
no auto-apply mode. There is no `--trust-the-ai` flag. Every change requires an
explicit human action to apply.

---

## 13. Les critères de stabilité

These are the elements that must not change before AEOS 1.0. They represent the
stable foundation on which everything else is built. Changing any of them before
1.0 would invalidate assumptions made throughout the platform.

---

**S.01 — Les huit capacités fondamentales**
Discover · Assess · Recover · Transform · Continue · Govern · Operate · Learn

These are constitutional (CONSTITUTION §1.4). Adding a ninth requires Constitutional
amendment. Renaming any of them breaks the official vocabulary used across all
documents. They must remain stable until 1.0.

**S.02 — Les 15 invariants**
All invariants defined in §2 — especially `read_only: true`, `applied: false`,
no secret exposure, no silent AI escalation, and mandatory human gates at Level 3+ —
must remain non-negotiable until 1.0 and beyond. These are the trust foundation.

**S.03 — Les quatre interfaces et la primauté du CLI**
CLI · API · Workspace · Agents, with CLI as authoritative reference. Adding a fifth
interface before 1.0 would fragment the implementation effort. The CLI primacy rule
must not change.

**S.04 — Les trois systèmes de niveaux**
Action Levels (0–5) · Project Maturity (weak → sovereign) · Sovereignty Levels (1–5)
These three axes together form the measurement system for AEOS. Changing them before
1.0 would invalidate existing MemoryRecords and all comparisons between them.

**S.05 — Le Proposal Lifecycle Contract**
The lifecycle defined in the Proposal Lifecycle Contract — including the 14 frozen
decisions, the terminal states, the apply preconditions, and the apply sequence — must
not change before 1.0. The Apply Engine implementation must satisfy this contract.

**S.06 — L'abstraction IA (AIProvider contract)**
The AIProvider, AIRouter, AIContext, AIResponse, and AIInteractionLog abstractions
defined in the AI Runtime Doctrine must not change before 1.0. Implementations change.
The abstraction must be stable.

**S.07 — La doctrine humain-en-boucle**
The human gate at every significant transition must not be weakened before 1.0. The
gate may be refined (better UX, clearer prompts) but never removed. An AEOS 1.0 that
auto-applies changes without a human gate has abandoned its identity.

**S.08 — Les neuf rails**
The nine rails represent the full product lifecycle. They must not be collapsed or
renamed before 1.0. New rails may be added (with the evolution rules from §11) but
existing rails must not be removed.

**S.09 — La règle de remplacement des Providers**
The runtime replacement test — any Provider is replaceable by changing configuration,
not code — must not be compromised before 1.0. Any change that tightly couples AEOS
to a specific external system violates this stability criterion.

**S.10 — L'auto-application**
AEOS applies its own standards to itself. AEOS has its own ARCHITECTURE.md, its own
aeos.toml, its own governance documents, its own quality gates, and its own memory.
This is not a nice-to-have — it is the strongest proof of principle the platform can
offer. Before 1.0, AEOS must continue to govern itself using its own tooling.

---

## Validation

This section verifies consistency between this Engineering Model and the founding
documents. Any real contradiction is explicitly flagged.

### Cohérence avec le MANIFESTO

| MANIFESTO principle | Model expression | Status |
|---|---|---|
| Technology is a means, never an end | §1.1 (problem statement), §2 (invariants), §12 (refusals) | ✅ |
| Complexity is the enemy of agency | INV.11 (modularity), §11 (evolution rules), §3 (layer limits) | ✅ |
| Human agency cannot be delegated | INV.06 (human-in-the-loop), §7 (agent constraints), §12 (refusals) | ✅ |
| Openness and sovereignty are not opposites | INV.10 (open standards) + INV.01 (sovereignty) as co-invariants | ✅ |
| We build for independence | INV.13 (no vendor lock-in), §6 (provider families), §11.Q6 (replaceability) | ✅ |
| Quality is a discipline at every decision | §11 (10 evolution questions), §13 (stability criteria) | ✅ |
| We build for the engineer maintaining this in 5 years | §13.S01–S10, §14 preamble, document scope | ✅ |

**No contradictions identified.**

---

### Cohérence avec la CONSTITUTION

| CONSTITUTION section | Model expression | Status |
|---|---|---|
| §1.1 — Sovereign Software Continuity Platform | §1.4 (identity definition) | ✅ |
| §1.4 — Eight core capabilities | §5 (exact eight capabilities preserved) | ✅ |
| §1.5 — Platform engines | Layer 4, §3 (bounded, testable, evidence output) | ✅ |
| §1.6 — Three level systems | §13.S04 (stability criterion), referenced in §8 (Action Levels) | ✅ |
| §1.7 — Four platform interfaces | Layer 1, §13.S03 (stability criterion) | ✅ |
| §2.1 — Engineering first | §1.3 (founding conviction), §11 (evolution rules) | ✅ |
| §2.4 — Human accountability | INV.06, §4.Agent, §7.Orchestrator | ✅ |
| §3.4 — AI autonomy boundaries | INV.06, §12 (refusals) | ✅ |
| §5.1 — Read-only default | INV.14, §3.Layer 4 | ✅ |
| §5.3 — Engine architecture | Layer 4, D.06 (safety enforced at source) | ✅ |
| §6.2 — Six absolute safety requirements | INV.09 + INV.06 + INV.14 together capture all six | ✅ |
| §7.1 — Standards hierarchy | §3.Layer 6 (Governance layer) | ✅ |

**No contradictions identified.**

---

### Cohérence avec ARCHITECTURE.md

ARCHITECTURE.md describes the current technical implementation. This Engineering
Model operates at a higher level of abstraction. Consistency is expected but the
two documents serve different purposes.

| ARCHITECTURE.md element | Model expression | Status |
|---|---|---|
| Four platform interfaces | Layer 1, §13.S03 | ✅ |
| Ten platform engines | Layer 4 (abstract, not enumerated here by name) | ✅ |
| Nine product rails | §8 (exact nine rails preserved) | ✅ |
| Three level systems | §13.S04 | ✅ |
| Core doctrine | §1.4 (four defining characteristics) | ✅ |

**One clarification (not a contradiction):** ARCHITECTURE.md §7 describes module-level
implementation. This model does not. The model is above the implementation layer by
design. Both documents are valid at their respective levels of abstraction.

---

### Cohérence avec AI-RUNTIME-DOCTRINE.md

| Doctrine element | Model expression | Status |
|---|---|---|
| Local-first ≠ Ollama-first | INV.03, INV.04, §6.AI Provider family | ✅ |
| 10 AI invariants (AI.01–AI.10) | INV.03, INV.04, INV.05, INV.06, INV.09, INV.14 | ✅ |
| AIProvider contract | §6.AI Provider family, Layer 8 | ✅ |
| Runtime replacement test | §11.Q6, INV.13, §13.S09 | ✅ |
| Offline operability | INV.05 | ✅ |
| Frontier requires explicit gate | INV.04, Flux 4 | ✅ |

**No contradictions identified.**

---

### Cohérence avec PROPOSAL-LIFECYCLE.md

| Lifecycle element | Model expression | Status |
|---|---|---|
| PRProposal vs Proposal (two objects) | §4.Proposal | ✅ |
| Human gate between them (intentional) | INV.06, Flux 2 | ✅ |
| Immutability | INV.07, §4.Proposal | ✅ |
| Three terminal states | §4.Proposal | ✅ |
| Apply Engine preconditions | Flux 2 (apply path), §13.S05 | ✅ |
| Mandatory evidence | INV.15, §4.Evidence, Flux 2 | ✅ |

**No contradictions identified.**

---

### Cohérence avec AEOS-MVP-1.0.md

| MVP-1.0 element | Model expression | Status |
|---|---|---|
| Reclaim → Govern → Continue arc | Flux 1 (Recovery Arc) | ✅ |
| Nine rails | §8 | ✅ |
| Local AI first, frontier by exception | INV.04, Flux 4 | ✅ |
| Human gate for every apply | INV.06, Flux 2 | ✅ |
| Evidence at every stage | INV.15, §4.Evidence | ✅ |

**One clarification (not a contradiction):** AEOS-MVP-1.0.md scopes the Workspace
to V2. This model treats Workspace as a permanent interface concept (Layer 1), with
current implementation as static HTML and future implementation as interactive GUI.
No contradiction — the model is above the implementation scope.

---

### Cohérence avec la vision souveraine, local-first, IA local-first, provider-agnostic

| Principle | Primary model expression |
|---|---|
| Sovereign | INV.01, §1.2, §8 (Sovereignty Rail), §12 |
| Local-first | INV.03, INV.05, Layer 7 (offline fallback) |
| AI local-first | INV.04, §6 (AI Provider family), Flux 4 |
| Provider-agnostic | INV.13, §6, §10 (dependency rules), §11.Q5-Q6 |

All four principles are present as invariants, as architectural rules, and as refusals.
They are mutually reinforcing: sovereignty requires local-first; local-first requires
AI local-first; AI local-first requires provider-agnostic design.

---

## Conclusion

This Engineering Model is the conceptual foundation of AEOS.

It does not describe code. It does not describe tools. It does not privilege any
technology. It will remain valid even when every technology referenced in every other
document has been replaced.

Its stability comes from the same source as the MANIFESTO and the CONSTITUTION:
not from the tools it describes, but from the principles it embodies.

> "No tool is permanent.
> No framework is eternal.
> Principles endure."
> — AI Engineering Manifesto

This document is the architecture of principles for a platform that exists to ensure
that the people who build software remain its owners, its masters, and its stewards —
today, in five years, and beyond.
