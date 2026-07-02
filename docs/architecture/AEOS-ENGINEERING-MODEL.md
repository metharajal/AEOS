# AEOS Engineering Model

**Version:** 2.0
**Status:** PROPOSED
**Date:** 2026-07-02
**Authority:** Derived from [MANIFESTO.md](../../MANIFESTO.md) · [CONSTITUTION.md](../../CONSTITUTION.md)
**Governs:** All current and future AEOS development

---

## Preamble

This document defines the permanent conceptual structure of AEOS.

**What it contains:** The mission, the invariants, the conceptual architecture, the
fundamental objects, the core capabilities, the operational flows, the dependency
rules, the evolution contract, and the permanent refusals.

**What it does not contain:** Current implementation status, specific provider
names, agent family catalogs, rail status tables, or any concept that would become
false if the implementation language, the AI models, or the providers changed.

This is a deliberate constraint. Everything in this document should remain true if:
- All current AI models are replaced by better ones
- The entire Python implementation is rewritten in another language
- AEOS evolves from a CLI into a distributed platform
- Every current provider is substituted by a different one

If a concept cannot survive those changes, it belongs in ARCHITECTURE.md, in
AGENT-ROADMAP.md, or in a versioned operational document — not here.

---

## 1. Mission

### Le problème fondateur

There is a permanent gap between **creating software** and **owning software**.

**The generation trap.** AI tools and no-code platforms create working software at
unprecedented speed. But the speed of creation conceals a structural problem: the
person who generated the project does not own it. The stack was chosen by the tool.
The infrastructure is controlled by the platform. The data is on servers the builder
did not select. The code has no tests, no documentation, no portability, and no
governance. When a serious client, institution, or investor asks the right questions,
there are no clean answers.

**The legacy trap.** Organizations operating critical systems — governments, banks,
hospitals, enterprises — frequently run software that nobody fully understands,
that cannot be easily modified, and that every consultant recommends migrating
without explaining to what, or why. These systems represent enormous sunk investment.
They encode business logic that has never been documented. They fail slowly and
expensively.

**The cost sovereignty trap.** Developing with frontier AI platforms at scale is not
economically viable for independent builders, small teams, or organizations in
cost-constrained markets. The marginal cost per iteration compounds. The routing
decisions are made by the platform, not the engineer. The data leaves the machine
without explicit human authorization.

These three problems are manifestations of a single deeper problem:

> **Software mastery has not kept pace with software creation.**

The tools to create have multiplied. The tools to own, govern, and control what was
created have not.

### La thèse permanente

> **Creating fast and owning what you created are not the same thing.**
> **AEOS makes them the same thing.**

This conviction drives every design decision. AEOS does not operate at the moment
of creation — it operates at every moment after creation, through the entire
lifespan of the software.

### Ce qu'AEOS est

AEOS is a **Sovereign Software Continuity Platform** — a governance layer above the
tools, platforms, and AI systems used to create and evolve software.

It is not a code generator. It is not an AI assistant. It is not a migration tool.
It is not a compliance framework.

Its four defining characteristics, which must remain true regardless of implementation:

1. **Engineering-first** — principles over technologies, always
2. **Human-gated** — no significant action without explicit human authorization
3. **Evidence-producing** — every operation generates inspectable proof
4. **Sovereignty-preserving** — control, portability, and independence as outputs

---

## 2. Les invariants

Invariants are non-negotiable constraints that define what AEOS is. They cannot be
weakened, bypassed, or traded for convenience, speed, or novelty.

Each invariant has a conceptual form (described here) and a code-enforced form
(described in ARCHITECTURE.md). The conceptual form is permanent. The code-enforced
form is the current implementation of that permanence.

---

### INV.01 — Sovereignty

**Definition:** AEOS always produces outputs that increase, or at minimum preserve,
the operator's control over their software and data.

**Why it exists:** *"We build for independence. We design systems that can be owned,
operated, and evolved by their users — without dependency on any single vendor,
platform, or actor."* (MANIFESTO §III)

**Architectural consequence:** Every capability has an associated sovereignty
measurement. Every engine must be expressible without cloud dependency. No operation
may introduce a new vendor dependency without documenting it and proposing an exit path.

---

### INV.02 — Software Continuity

**Definition:** AEOS always produces outputs that increase the long-term
maintainability, understandability, and operability of the software it governs.

**Why it exists:** Engineering excellence is measured by the longevity of what is
built, not by the speed at which it was produced. (CONSTITUTION §2.1)

**Architectural consequence:** Every proposal must increase or maintain continuity.
Every governance document must reflect current reality, not aspirational state.

---

### INV.03 — Local-first & Offline Operability

**Definition:** Every AEOS operation runs locally by default, without requiring an
external network connection. AEOS must be fully functional on an air-gapped machine.

**Why it exists:** A system that requires network access by default surrenders control
to the network. Organizations with the highest security requirements operate in
environments with strict network controls. AEOS must serve these environments
without compromise.

**Architectural consequence:** No engine may have a network call as its default path.
Every capability must have a deterministic, offline fallback. External network calls
are exceptions that require explicit configuration, explicit human authorization, and
explicit logging.

---

### INV.04 — AI Local-first

**Definition:** AI assistance defaults to locally-running models. Frontier AI — any
model not running on the operator's infrastructure — is used only when local AI is
demonstrably insufficient, with explicit human authorization for each call.

**Why it exists:** Using a frontier provider by default makes the platform the
authority over what happens to the operator's data. AI is a partner, not an
authority. (CONSTITUTION §3.4)

**Architectural consequence:** The AI routing layer must be configurable per
operation. Local AI is the first path. Frontier AI is the exception path with a
mandatory human gate. The routing decision must be logged permanently.

---

### INV.05 — Human Gate

**Definition:** No significant, irreversible, or destructive action is taken without
explicit human authorization. AI proposals are exactly that — proposals. Humans decide.

This invariant has two machine-readable expressions:
- `read_only: true` — all diagnostic and analysis operations are non-destructive
- `applied: false` — no output is applied until a human explicitly triggers application

Neither expression can be overridden by configuration, agent behavior, or any
interface. There is no `--force-apply` flag.

**Why it exists:** *"Human judgment, human ethics, and human accountability cannot
be delegated to any system — artificial or otherwise."* (MANIFESTO §II)

**Architectural consequence:** Action Levels 3 and above require documented human
gates. No agent, no engine, and no interface bypasses a gate.

---

### INV.06 — Security by Design

**Definition:** Security is an architectural property, not a feature. Secret values
never appear in any output, log, or transmitted context. The context sanitization
gate is mandatory and non-bypassable.

**Why it exists:** CONSTITUTION §6.2 establishes six absolute safety requirements,
of which three are critical: no secret exposure, no unauthorized modification, no
autonomous production change.

**Architectural consequence:** Secret detection is enforced at the source, before
any output is produced. No capability may receive raw secret values as input.
No AI context may contain file contents, API keys, connection strings, or PII.

---

### INV.07 — Evidence & Auditability

**Definition:** Every significant AEOS operation produces an evidence artifact before
declaring completion. Evidence is permanent, immutable, and never retroactively
altered. Nothing significant happens without a trace.

**Why it exists:** *"History is an engineering asset. It shall never be rewritten
to hide mistakes."* (CONSTITUTION §2.7)

**Architectural consequence:** Evidence is produced before status is updated. A step
that cannot produce evidence has not completed. Evidence enables external audit,
internal review, and historical reconstruction.

---

### INV.08 — Provider Replaceability

**Definition:** AEOS never creates a dependency on a specific vendor, platform, tool,
or AI provider that cannot be replaced by changing configuration alone. Every provider
is defined by its contract (what it must do), never by its implementation (how it does it).

This is the runtime replacement test: if replacing a provider requires code change,
the invariant has been violated.

**Why it exists:** *"We refuse to build lock-in by design."* (MANIFESTO §III)

**Architectural consequence:** Every provider used by AEOS is an implementation of
a defined contract. Any implementation satisfying the contract is a valid provider.
Lock-in is documented, quantified, and paired with exit options when unavoidable.

---

## 3. L'architecture conceptuelle

AEOS is organized into five conceptual layers with strict downward dependencies,
and one cross-cutting governance concern that applies to all layers simultaneously.

**Critical distinction:** Governance is NOT a layer. It is a cross-cutting concern.
Placing it inside the dependency chain would be architecturally false — Governance
constrains all layers from outside, like a constitution constrains all laws. It has
no position in the downward dependency order; it has authority over all positions.

```
  ┌─────────────────────┐   ┌──────────────────────────────────────┐
  │                     │   │  LAYER 1 — Interface                 │
  │                     │   │  CLI · API · Workspace · Agents       │
  │                     │   └─────────────────┬────────────────────┘
  │    GOVERNANCE       │                     │
  │                     │   ┌─────────────────▼────────────────────┐
  │  Cross-cutting      │   │  LAYER 2 — Capability                │
  │  concern            │   │  8 core capabilities (constitutional) │
  │                     │   └─────────────────┬────────────────────┘
  │  Invariants ·       │                     │
  │  Policies ·         │   ┌─────────────────▼────────────────────┐
  │  Proposals ·        │   │  LAYER 3 — Engine                    │
  │  Standards          │   │  Bounded · testable · evidence output │
  │                     │   └─────────────────┬────────────────────┘
  │  Applies to every   │                     │
  │  layer · cannot be  │   ┌─────────────────▼────────────────────┐
  │  bypassed by any    │   │  LAYER 4 — Knowledge                 │
  │  layer              │   │  Memory · Evidence · History          │
  │                     │   └─────────────────┬────────────────────┘
  │                     │                     │
  │                     │   ┌─────────────────▼────────────────────┐
  └─────────────────────┘   │  LAYER 5 — Provider Abstraction      │
                            │  Contracts · Replaceability           │
                            └──────────────────────────────────────┘
```

Dependencies flow downward only: a layer may use the layers below it,
never the layers above it. Governance applies to all layers from outside
this chain — it is not part of the chain.

---

### Layer 1 — Interface

**Mission:** Expose all AEOS capabilities through interaction models appropriate
to different contexts. All interfaces expose the same underlying capabilities
with the same invariants.

**Responsibilities:**
- Accept human input and route it to capabilities
- Present capability outputs in the format appropriate to the interface
- Maintain CLI as the authoritative reference when interfaces diverge
- Enforce that no interface bypasses governance invariants

**Limits:**
- An interface never contains business logic
- An interface never makes decisions — it routes and presents
- No interface may offer a capability that does not exist at Layer 2

**Authorized dependencies:** Layer 2 (Capability), Layer 3 (Engine, directly for
diagnostic commands), Governance (to enforce invariants at output time)

---

### Layer 2 — Capability

**Mission:** Define what AEOS can do, in terms that are permanently valid regardless
of tools, languages, or AI systems. The eight capabilities are the official vocabulary
for describing AEOS operations. They are constitutional and do not change without a
formal amendment.

**Responsibilities:**
- Orchestrate engine invocations to produce capability-level outputs
- Compose capabilities into product-level paths (Rails)
- Produce at least one evidence artifact per capability invocation
- Maintain the capability vocabulary as the stable product language

**Limits:**
- A capability does not name its engine implementation
- A capability does not name any provider
- A capability never calls another capability directly — composition happens at the rail level

**Authorized dependencies:** Layer 3 (Engine), Layer 4 (Knowledge), Governance

---

### Layer 3 — Engine

**Mission:** Provide bounded, testable, independently operable units that implement
one or more capabilities. Engines are the implementation boundary of AEOS.

**Responsibilities:**
- Enforce safety invariants internally — never delegated to callers
- Produce structured, serializable output for every operation
- Default to read-only behavior; explicitly declare when writes are required
- Produce evidence at step completion before updating any status
- Request AI assistance via the abstract AI Orchestration pattern when needed

**The AI Orchestration pattern** is an Engine-level concern, not a separate layer:
an engine that requires AI assistance routes the request through the sanitization
gate, then to the available provider, then receives and logs the response. This
pattern is always local-first, always logged, and always produces a Proposal,
never a direct apply.

**Limits:**
- An engine has a single, clearly defined scope
- An engine never calls another engine directly
- An engine never knows which interface invoked it
- An engine never names a specific AI provider or implementation

**Authorized dependencies:** Layer 4 (Knowledge), Layer 5 (Provider Abstraction),
Governance (invariants enforced internally)

---

### Layer 4 — Knowledge

**Mission:** Accumulate, store, and retrieve the validated learning that AEOS
generates over time — locally, immutably, without cloud dependency.

**Responsibilities:**
- Store audit results as immutable, human-validated records
- Maintain the audit history and timeline for each project
- Produce comparison and trend outputs from historical records
- Ensure that stored records never include secret values or raw file contents

**Limits:**
- Knowledge is never updated autonomously — human validation is always required
- Knowledge is local-first by default
- Knowledge accumulates but never makes decisions — it informs
- An inference from knowledge is a Proposal, not an action

**Authorized dependencies:** Governance (for validation gates)

---

### Layer 5 — Provider Abstraction

**Mission:** Define the minimum contract that any external system must satisfy
to be used by AEOS. The abstraction layer makes providers interchangeable.

**Responsibilities:**
- Define provider contracts (what a provider must do, never how)
- Guarantee that replacing any provider requires only configuration change
- Document which contract applies to each category of external system

**Limits:**
- Provider Abstraction never contains business logic
- Provider Abstraction never knows which concrete provider is in use at runtime
- The abstraction contract is stable — providers adapt to AEOS, not the reverse

---

### Governance — Cross-cutting Concern

**Mission:** Define and enforce the non-negotiable rules that apply to every layer
without exception. Governance has no position in the dependency chain — it has
authority over the entire chain.

**Scope:**
- The 8 invariants defined in §2
- The Proposal lifecycle and its contracts
- The Standards hierarchy (MANIFESTO → CONSTITUTION → Standards → Playbooks)
- The Policy objects that define what may never be violated

**Critical distinction:** A governance rule that cannot be enforced in code is not
an invariant — it is a guideline. Invariants are code-enforced and test-verified.

**What governance does not do:** It does not implement capabilities. It constrains them.

---

## 4. Les objets fondamentaux

These are the core business objects of AEOS. They are technology-independent and
must remain valid regardless of implementation language or storage technology.
They are defined at the conceptual level — the implementation may name them
differently, but the concept must be preserved.

---

### Project

The fundamental unit of AEOS governance. A Project is a codebase and its
associated governance artifacts, registered within AEOS scope.

| Property | Description |
|---|---|
| Identity | Unique name and associated metadata |
| Scope | A codebase and its governance documents |
| State | A measured maturity level and sovereignty level |
| History | An accumulation of MemoryRecords over time |

A Project is what AEOS governs. Everything else is produced in service of a Project.

---

### MemoryRecord

An immutable, validated snapshot of a single AEOS audit run. The fundamental unit
of the Knowledge layer.

| Property | Description |
|---|---|
| Content | Aggregate counts and status labels — never raw values, never secrets |
| Immutability | Never modified after creation |
| Validation | Requires human confirmation before entering Knowledge |
| Scope | One audit run, one project, one point in time |

The timeline of MemoryRecords for a project is its engineering history.

---

### Evidence

A durable, inspectable proof that a step or capability has been exercised.

| Property | Description |
|---|---|
| Timing | Written before status is updated — never retroactively |
| Immutability | Never altered after creation |
| Content | What was done, when, with what result, by what mechanism |
| Scope | One step, one operation, one moment in time |

Evidence is the machine-readable answer to "prove it."

---

### Proposal

The contract between machine analysis and human action. A structured,
evidence-backed recommendation that a human must validate before anything is executed.

| Property | Description |
|---|---|
| Origin | Generated from validated Knowledge by an engine or agent |
| Nature | Always read-only until a human triggers application |
| Invariants | `read_only: true · applied: false` always present |
| Immutability | Content never changes after creation |
| Lifecycle | Moves through defined states — terminal states are final |

The full Proposal lifecycle is defined in PROPOSAL-LIFECYCLE.md.

---

### Policy

A non-negotiable rule enforced by the system at all times, under all conditions.
Policies cannot be disabled by configuration or bypassed by interface choice.

| Property | Description |
|---|---|
| Enforcement | Code-enforced and test-verified — not conventional |
| Scope | Applies across all layers, all interfaces, all providers |
| Change process | Only via the Constitutional amendment process |

Policies are the machine-readable form of invariants.

---

### Context

The sanitized, secret-free, content-free information provided to any external AI system.
Context is the enforced boundary between AEOS internal state and the outside world.

| Property | Description |
|---|---|
| Content | Aggregate counts, status labels, metadata — never raw values |
| Sanitization | Mandatory secret gate and file content gate before construction |
| Scope | One AI interaction request |
| Logging | Logged after sanitization — never by raw content |

If a context cannot be safely transmitted to an external AI without exposing sensitive
data, the operation must abort. This is not configurable.

---

### Knowledge

The accumulated body of validated findings and corrections that AEOS has stored
from human-confirmed operations.

| Property | Description |
|---|---|
| Accumulation | Grows through human-validated audit results |
| Validation | Human confirmation required before any result enters Knowledge |
| Use | Informs future proposals — never makes autonomous decisions |
| Storage | Local-first by default |

Knowledge is what makes AEOS more accurate over time.

---

### Provider

Any replaceable external capability that AEOS uses. A Provider is always defined
by its contract, never by its implementation.

| Property | Description |
|---|---|
| Definition | A contract: required inputs, outputs, and behaviors |
| Replaceability | Any implementation satisfying the contract is valid |
| Independence | A Provider never knows how AEOS uses its output |

The specific categories of providers (AI, storage, source control, etc.) and their
current implementations are documented in ARCHITECTURE.md.

---

### Workspace

The read-only, multi-surface view of a Project's current state, produced for human
consumption and decision-making.

| Property | Description |
|---|---|
| Nature | Always read-only — a view, never an editor |
| Content | Derived from MemoryRecords, Evidence, Proposals, and Plans |
| Freshness | Regenerated on demand — never auto-updated |

The Workspace is the artifact a human reviews before making a decision. Its surfaces
(CLI output, HTML, API response, etc.) are implementation choices. The concept — a
read-only governance view — is permanent.

---

### Agent

A bounded, specialized AI assistant that operates within AEOS invariants to
accomplish a defined scope of engineering tasks.

| Property | Description |
|---|---|
| Scope | Precisely defined — no agent has a general mandate |
| Invariants | Agents never bypass governance invariants |
| Output | Always a Proposal or an Evidence artifact — never a direct apply |

Agents reason. They do not decide. Every Agent output that results in a system
change passes through a human gate first.

The specific agent families and their current implementations are documented in
AGENT-ROADMAP.md.

---

## 5. Les capacités fondamentales

The eight core capabilities define what AEOS does, permanently and independently of
implementation. They are constitutional (CONSTITUTION §1.4) and do not change
without a Constitutional amendment. They are the official vocabulary for describing
AEOS operations.

Each capability produces at least one evidence artifact. Each capability is
provider-agnostic: it specifies what must happen, not which tool performs it.

| Capability | Purpose |
|---|---|
| **Discover** | Understand what exists: structure, dependencies, providers, generators, risks |
| **Assess** | Evaluate current state: control map, security posture, sovereignty level, maturity |
| **Recover** | Bring a project to a controlled, secure, portable, and governable state |
| **Transform** | Move a project toward a target architecture: controlled, tested, reversible |
| **Continue** | Resume or sustain development under controlled AI assistance |
| **Govern** | Define, enforce, and maintain standards, decisions, and policies |
| **Operate** | Monitor, audit, and maintain projects over time |
| **Learn** | Accumulate validated knowledge from operations and human-confirmed outcomes |

**Notes:**
- Discover is always the first step in any engagement — no action before understanding
- Assess produces evidence, not action — it describes the gap, not the remedy
- Recover is staged — no stage begins without the previous stage's gates
- Transform never applies without a backup, a dry-run, and explicit human approval
- Continue is ongoing — not a milestone, but a permanent mode with routing rules
- Govern produces documents that reflect evidence, not aspirations
- Operate is continuous — drift is detected early, before it becomes a crisis
- Learn is human-validated — an unvalidated inference is a hypothesis, not knowledge

The current implementation of each capability and the commands that invoke them
are documented in ARCHITECTURE.md.

---

## 6. Les flux fondamentaux

These three flows describe operational patterns that will remain true regardless of
implementation. They are the permanent logic of how AEOS operates, not descriptions
of current commands.

---

### Flux A — The Core Loop

The atomic operational pattern underlying every AEOS operation that may result
in a change to the governed project.

```
Knowledge (existing validated records)
        │
        │  Engine or Agent reads
        ▼
Analysis (deterministic or AI-assisted)
        │
        │  Evidence produced at completion
        ▼
Proposal (read_only: true · applied: false)
        │
        │  Human reviews
        ▼
        ├── Discard → stop, no record
        │
        └── Persist → Proposal (governance record, pending)
                │
                │  Human validates
                ▼
                ├── Dismiss → Proposal (terminal state, preserved)
                │
                └── Apply → Apply sequence
                              │  Pre-apply evidence
                              │  Human confirms
                              │  Step execution
                              │  Post-apply evidence
                              ▼
                         Proposal (terminal state: applied)
                         New MemoryRecord created
```

This loop never short-circuits. Every significant change passes through every step.
The only difference between operations is at which step the human engages.

---

### Flux B — AI Interaction

The controlled pattern for any AI assistance within AEOS. This applies identically
regardless of which AI system is used.

```
Engine requires AI assistance
        │
        │  Construct Context
        ▼
Sanitization gate
(no secrets · no file contents · no PII)
        │
        ├── FAIL → Abort · log · inform human
        │
        └── PASS
                │
                │  Route: local first
                ▼
        Local AI available?
        │
        ├── YES → Call local AI · log (hash only) · return response
        │
        └── NO → Is frontier AI authorized?
                │
                ├── NO → Deterministic fallback · log
                │
                └── YES → Human gate required
                              │  Show sanitized context summary
                              │  Human confirms
                              ▼
                         Call frontier AI
                         Log (hash + timestamp + provider type)
                         Return response
                │
                └── Response → always becomes a Proposal, never a direct apply
```

The sanitization gate is non-bypassable. The local-first routing is non-negotiable.
The human gate before frontier AI is non-negotiable. These three properties will
remain true regardless of which specific AI systems exist at any given time.

---

### Flux C — Knowledge Accumulation

How AEOS learns over time.

```
Operation completes → Evidence artifact produced
        │
        │  Human reviews output
        ▼
Human-validated result
        │
        │  Stored as MemoryRecord
        ▼
MemoryRecord (immutable · timestamped · local)
        │
        │  Accumulates over time
        ▼
Knowledge (timeline of validated records)
        │
        │  Informs future operations
        ▼
More accurate Analysis → More accurate Proposal → Better human decision
```

The learning loop is always human-mediated. AEOS never updates its Knowledge
autonomously. The loop improves the quality of proposals over time without
removing the human from any decision.

---

## 7. Les règles de dépendance

These rules govern what may depend on what within AEOS. They are architectural
invariants — violating them introduces hidden coupling that makes AEOS harder to
maintain, test, and evolve.

**D.01 — Layer dependency is downward only.**
A layer may use layers below it. Never the layers above it. An engine never knows
which interface invoked it. A provider never knows which capability is using it.

**D.02 — Governance applies from outside the chain.**
Governance constrains all layers. It is not a layer. No layer "calls" governance —
governance constrains what every layer may do. Safety invariants are enforced at the
source by each engine, not delegated upward to callers.

**D.03 — Capabilities are provider-agnostic.**
A capability is defined by what it needs (a contract), never by which implementation
delivers it. A capability that names a specific provider is coupled to that provider,
which violates INV.08.

**D.04 — Agents use abstractions, never implementations.**
An Agent invokes Capabilities and produces Proposals or Evidence. An Agent never
calls a specific AI runtime, a specific storage backend, or a specific API directly.

**D.05 — Engines implement, Capabilities orchestrate.**
A Capability orchestrates engine invocations to produce a higher-level result.
An engine implements a bounded step. A Capability that contains implementation
logic is a design violation.

**D.06 — Safety is enforced at the source.**
Every engine enforces its own safety invariants internally. Safety is never delegated
to the caller. An engine that can be made unsafe by its caller has a design defect.

**D.07 — Knowledge informs, never decides.**
The Knowledge layer provides information. It never triggers actions. An inference
from Knowledge is always a Proposal — reviewed by a human before anything changes.

**D.08 — No circular dependencies.**
If layer A uses layer B, then layer B must never import from layer A. The dependency
graph is a directed acyclic graph. This is verified by tests, not by convention.

---

## 8. Le contrat d'évolution

Before any new capability, engine, capability family, agent, or provider category is
added to AEOS, the following questions must be answered affirmatively. This is not
a guideline — it is a gate. Every question maps to one or more invariants.

**Q1 — À quelle couche appartient-il ?**
Every new element belongs to exactly one layer. If it spans multiple layers, decompose
it. An element with no clear layer has no clear scope.

**Q2 — Quel objet fondamental enrichit-il ?**
Every new element produces, consumes, or enriches at least one fundamental object
from §4. If it requires a new object, that object must be formally defined first.

**Q3 — Quelle capacité améliore-t-il ?**
Every new element contributes to at least one of the eight core capabilities. If it
introduces a genuinely new capability, a Constitutional amendment is required.

**Q4 — Respecte-t-il les 8 invariants ?**
Compatibility with all invariants must be demonstrated by tests, not by assertion.
An "I think it's fine" is not an answer to this question.

**Q5 — Est-il provider-agnostic ?**
Every element that interacts with an external system uses the Provider Abstraction
layer. It never names a specific external system in its logic.

**Q6 — Passe-t-il le test de remplacement ?**
If it includes an external dependency, replacing that dependency must require only
configuration change, not code change. This is testable and must be tested.

**Q7 — Fonctionne-t-il hors ligne ?**
Every new element either operates offline by default or has a deterministic fallback
that does. An element that requires network access for its baseline function violates
INV.03.

**Q8 — Préserve-t-il la souveraineté ?**
It must either increase or preserve the operator's sovereignty. Introducing an
undocumented external dependency or removing a human gate violates INV.01 and INV.05.

**Q9 — Produit-il des preuves ?**
Every element that performs a significant operation produces at least one evidence
artifact before marking completion. No evidence = not complete.

**Q10 — A-t-il une frontière précise ?**
Every new element has a single, clearly defined scope. Scope creep is caught here,
at design time — not after implementation.

---

## 9. Ce qu'AEOS refuse d'être

This section defines what AEOS will never become. These are not preferences or
guidelines — they are permanent boundaries grounded in the founding documents.

**AEOS n'est pas un assistant de code généraliste.**
A general coding assistant responds to prompts and generates code. AEOS governs the
engineering lifecycle of what is built. Code generation is one action within one
engine, within one capability. It is not the identity of the platform.

**AEOS n'est pas un wrapper d'un fournisseur IA.**
AEOS is provider-agnostic by architectural definition. Any component of AEOS that
names a specific AI system in its architecture is in violation of INV.08. Providers
are interchangeable — the contract is permanent, the implementation is not.

**AEOS n'est pas un outil qui prend des décisions importantes automatiquement.**
Significant decisions — architectural choices, production applies, security exceptions,
data migrations — always require a documented human gate. An AEOS that makes these
decisions autonomously has abandoned INV.05. There is no `--trust-the-ai` flag.

**AEOS n'est pas un outil qui envoie des secrets à une IA.**
No secret value ever leaves the machine through AEOS, to any AI provider, under any
condition. INV.06 is absolute. The sanitization gate in Flux B is not optional and
not configurable.

**AEOS n'est pas dépendant d'une connexion réseau permanente.**
Offline operability is INV.03. A version of AEOS that fails without internet access
has violated a core invariant. The deterministic fallback always exists.

**AEOS n'est pas un outil qui crée du verrouillage.**
AEOS is built to reduce dependency, not to create it. A project governed by AEOS must
always be more portable and more independent than it was before AEOS touched it. A
version of AEOS that makes projects dependent on AEOS itself would be a contradiction
of its mission.

**AEOS n'est pas un outil dont les outputs s'appliquent automatiquement.**
`applied: false` is the invariant of every non-apply output. This is expressed in
Flux A's mandatory human gate. It is also the reason the two states `read_only` and
`applied` always appear together in every AEOS output surface.

**AEOS n'est pas statique.**
The model is permanent. The implementation is not. AEOS must be able to evolve its
implementation, adopt new providers, and integrate new capabilities — without
changing what it fundamentally is. The model governs evolution. Evolution does not
govern the model.

---

## Annexe — Index de redistribution

This section documents what was moved out of this document in v2.0 and where it now lives.
This index exists so that no information is lost — only repositioned.

| Content | Previous location | New location |
|---|---|---|
| 9 provider family definitions | §6 (v1.0) | ARCHITECTURE.md |
| 11 agent family definitions | §7 (v1.0) | AGENT-ROADMAP.md |
| Rails status table (Production/Planned) | §8 (v1.0) | ARCHITECTURE.md |
| Flux 1 — Recovery Arc (specific stages) | §9 (v1.0) | ARCHITECTURE.md |
| Flux 5 — Operate mode (specific patterns) | §9 (v1.0) | ARCHITECTURE.md |
| 10 stability criteria (S.01–S.10) | §13 (v1.0) | Dissolved — this document is the stability contract |
| Cross-document validation table | Validation (v1.0) | Removed — consistency is verified by the RFC process, not by the document itself |
| INV.08 Reproducibility | §2 (v1.0) | Absorbed into evolution contract (Q4, Q6) |
| INV.10 Open Standards | §2 (v1.0) | Absorbed into INV.08 Provider Replaceability |
| INV.11 Modularity | §2 (v1.0) | Absorbed into INV.08 and Engine layer limits |
| INV.12 Portability | §2 (v1.0) | Absorbed into INV.01 Sovereignty |
| INV.13 No Vendor Lock-in | §2 (v1.0) | Merged into INV.08 Provider Replaceability |
| INV.14 Read-only / Applied:false | §2 (v1.0) | Merged into INV.05 Human Gate (two forms of one principle) |
| INV.15 Mandatory Evidence | §2 (v1.0) | Merged into INV.07 Evidence & Auditability |
| Task object definition | §4 (v1.0) | Removed — operational concept, not fundamental object |
| Workflow object definition | §4 (v1.0) | Removed — operational concept, not fundamental object |
