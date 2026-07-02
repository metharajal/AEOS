# AEOS Sovereignty Model

**Version:** 1.0
**Status:** PROPOSED
**Date:** 2026-07-02
**Type:** Conceptual foundation — no implementation, no technology names
**Governs:** MVP scope, roadmap prioritization, all product decisions

---

## Preamble

This document answers one question:

> **What must an owner control to remain truly master of their digital product throughout its entire life?**

It is not a technical document. It does not describe commands, engines, or providers.
It describes the permanent structure of digital sovereignty — what it is, why it is lost,
and what AEOS must guarantee to restore and maintain it.

Every product decision, every sprint, every new capability must be evaluated against this
model. If a capability does not advance at least one sovereignty guarantee, it should not
be prioritized.

---

## 1. Ce que la souveraineté signifie réellement

Sovereignty is not a technical property. It is a relationship between an owner and their
product.

An owner is sovereign over their product when they can answer four questions at any time,
without consulting the vendor who built it, the platform that hosts it, or the AI that
helped generate it:

**Q1 — Comprendre**
*What does this product do, how does it do it, and why was it built this way?*

**Q2 — Contrôler**
*Can I change it, correct it, or stop it, without asking permission from any external
system?*

**Q3 — Déplacer**
*Can I move it — to different infrastructure, a different team, a different country —
using only documented procedures?*

**Q4 — Prouver**
*Can I demonstrate to any auditor, investor, or regulator that the product operates
as I claim it does?*

A product where even one of these four questions cannot be answered is a product where
sovereignty has been lost, partially or entirely.

### Pourquoi la souveraineté se perd

Sovereignty is not lost suddenly. It erodes. The four most common erosion paths:

**L'érosion par la génération.** A product built by an AI tool or a no-code platform
is operational but not understood. The owner can use it but cannot answer Q1. Sovereignty
was never established.

**L'érosion par la dépendance.** A product that relies on a platform's proprietary
features (authentication, storage, realtime, etc.) cannot be moved. The owner cannot
answer Q3. Sovereignty was captured gradually.

**L'érosion par l'oubli.** A product built by a team that has since left has no
documented decisions, no captured reasoning, no understandable architecture. A new
team cannot answer Q1 or Q4. Sovereignty was lost through attrition.

**L'érosion par l'accumulation.** A product that has grown through years of patches,
dependencies, and undocumented changes has become opaque to its owner. Nobody can
confidently answer Q2. Sovereignty was lost through complexity.

AEOS exists to reverse all four erosion paths.

---

## 2. Les six piliers de la souveraineté

A digital product has six distinct dimensions of sovereignty. Losing control of any
one of them creates a vulnerability that can propagate to the others.

They are not independent. They reinforce each other when strong; they undermine each
other when weak. Data sovereignty without code sovereignty is fragile: you may own
the data but not understand the code that governs access to it. AI sovereignty without
knowledge sovereignty is dangerous: the AI makes recommendations that nobody can
challenge because no decisions were ever documented.

---

### Pilier 1 — Souveraineté du code

**Définition**
The owner can read, understand, modify, test, and run the product's code independently
of the tools, platforms, or teams that originally created it.

**Ce qu'un propriétaire perd s'il ne maîtrise pas ce pilier**
A product whose code cannot be understood cannot be safely changed. A product whose
code cannot be run without a specific tool or credential is held hostage by that tool.
A product with no tests cannot be modified with confidence. Losing code sovereignty
means losing the ability to evolve the product without risk.

**Les quatre sous-dimensions**

| Sous-dimension | Question de contrôle |
|---|---|
| Lisibilité | Any competent engineer can understand this code within a reasonable time |
| Testabilité | Changes can be made with confidence — a test suite catches regressions |
| Portabilité | The code builds and runs without proprietary tools or undocumented secrets |
| Gouvernance | Every significant architectural decision is documented with its reasoning |

**La garantie qu'AEOS doit apporter**
AEOS must measure code sovereignty, classify its gaps, and help restore it. It must
detect AI-generated code that lacks governance, identify missing tests, flag proprietary
build dependencies, and produce governance documentation grounded in evidence — not
in templates.

---

### Pilier 2 — Souveraineté des données

**Définition**
The owner controls where data lives, who can access it, how it can be migrated, and
how it can be exported — independently of any platform, database vendor, or SaaS provider.

**Ce qu'un propriétaire perd s'il ne maîtrise pas ce pilier**
Data that lives on a platform the owner does not control is not owned — it is rented.
Access control enforced only at the application layer is one deployment away from
catastrophic exposure. A schema that cannot be migrated is a permanent dependency on
the current database provider. A product without data portability cannot be sold,
audited, or regulated.

**Les quatre sous-dimensions**

| Sous-dimension | Question de contrôle |
|---|---|
| Localisation | I know exactly where each piece of data lives and who controls that infrastructure |
| Contrôle d'accès | Access is enforced at the data level, not only at the application level |
| Portabilité | The data can be migrated to a different system using documented, tested procedures |
| Traçabilité | Every schema change is documented, versioned, and reversible |

**La garantie qu'AEOS doit apporter**
AEOS must audit data sovereignty: inspect access control policies, classify data
storage by sovereignty level, detect undocumented schema evolution, verify migration
scripts exist and are tested, and flag when data lives on infrastructure the owner
does not control.

---

### Pilier 3 — Souveraineté de l'IA

**Définition**
The owner controls which AI systems reason about their product, what information those
systems receive, and can replace any AI system without modifying their product's code.

**Ce qu'un propriétaire perd s'il ne maîtrise pas ce pilier**
A product developed with AI assistance where the AI has seen source code, secrets, or
business logic without explicit consent has lost confidentiality sovereignty — regardless
of the AI provider's terms of service. A product that cannot function when one AI
provider is unavailable, expensive, or deprecated has lost operational sovereignty over
its development process.

**Les quatre sous-dimensions**

| Sous-dimension | Question de contrôle |
|---|---|
| Confidentialité | No sensitive data reaches any AI system without explicit, logged authorization |
| Remplaçabilité | Any AI system can be substituted by changing configuration, not code |
| Local-first | AI assistance defaults to locally-running systems; external AI is the explicit exception |
| Traçabilité | Every AI interaction is logged by reference — the reasoning is auditable, not hidden |

**La garantie qu'AEOS doit apporter**
AEOS must enforce the confidentiality gate before any AI call, verify that providers are
replaceable by the runtime replacement test, default all AI routing to local-first, log
every AI interaction, and demonstrate that the product can be operated and developed
without any external AI provider.

---

### Pilier 4 — Souveraineté de l'infrastructure

**Définition**
The owner can provision, operate, and migrate their product's infrastructure independently,
using documented procedures, without proprietary tooling or undocumented credentials.

**Ce qu'un propriétaire perd s'il ne maîtrise pas ce pilier**
A product whose infrastructure cannot be reproduced is permanently fragile. A single
engineer departure or a single platform outage can make the product unrecoverable. A
product on infrastructure with undocumented pricing models faces unpredictable costs.
A product that cannot be moved to a different region or provider cannot satisfy
regulatory or sovereignty requirements.

**Les quatre sous-dimensions**

| Sous-dimension | Question de contrôle |
|---|---|
| Documentabilité | The infrastructure can be fully described and reproduced from documentation alone |
| Indépendance | Each infrastructure dependency is documented with an exit path |
| Reproductibilité | A new environment can be provisioned from scratch using only documented procedures |
| Mesurabilité | External dependencies are inventoried and quantified (their cost and risk assessed) |

**La garantie qu'AEOS doit apporter**
AEOS must inventory all infrastructure dependencies, measure the sovereignty level of
each (on the 1-5 scale), flag undocumented dependencies, generate infrastructure
documentation from reality, and propose exit paths for captured dependencies.

---

### Pilier 5 — Souveraineté de la connaissance

**Définition**
The decisions, reasoning, and history behind the product are documented, preserved,
and accessible independently of the people who made them — in formats that survive
team turnover, tool changes, and time.

**Ce qu'un propriétaire perd s'il ne maîtrise pas ce pilier**
Knowledge sovereignty is the most invisible loss. A team that built a product and then
left takes its knowledge with them. The next team faces an opaque system — they know
what it does, not why. Without documented decisions, every change risks breaking
something whose purpose was never written down. Without an audit trail, the product
cannot be regulated, sold, or handed over.

**Les quatre sous-dimensions**

| Sous-dimension | Question de contrôle |
|---|---|
| Décisions | Every significant architectural, security, and product decision is documented with its reasoning |
| Preuves | Every significant operation produces an inspectable, immutable record |
| Mémoire | The product's history — its evolution, its findings, its corrections — is preserved locally |
| Transmission | A new team can understand and operate the product using only documented artifacts |

**La garantie qu'AEOS doit apporter**
AEOS must produce governance documents grounded in audit evidence (not templates),
preserve an immutable timeline of MemoryRecords, capture decisions as ADRs with
evidence references, and ensure that all knowledge artifacts are stored locally and
independent of AEOS itself.

---

### Pilier 6 — Souveraineté opérationnelle

**Définition**
The owner can detect, correct, and prevent sovereignty degradation over time — independently,
continuously, without dependence on the original development team or any external service.

**Ce qu'un propriétaire perd s'il ne maîtrise pas ce pilier**
Sovereignty is not a state — it is a continuous effort. Without operational sovereignty,
every change to the codebase, every new dependency, and every team change is an opportunity
for undetected erosion. A product that was sovereign at launch can lose sovereignty
silently within weeks through accumulated drift.

**Les quatre sous-dimensions**

| Sous-dimension | Question de contrôle |
|---|---|
| Détection | Sovereignty degradation is detected before it becomes a crisis |
| Recovery | Any sovereignty loss can be corrected through a documented, executable procedure |
| Continuité | The product can be operated and maintained by a different team, immediately |
| Mesure | Sovereignty levels are quantified and trending — improvement is measurable |

**La garantie qu'AEOS doit apporter**
AEOS must detect sovereignty drift between audit states, alert when sovereignty level
decreases, provide executable recovery workflows for each pillar, quantify progress
across the sovereignty lifecycle, and produce operational continuity artifacts.

---

## 3. Les garanties AEOS par pilier — couverture actuelle

This section maps each guarantee to what the current product covers and what remains
genuinely absent. The goal is an honest gap analysis, not an inventory of features.

**Legend:** ✅ Covered · ⚠️ Partial · ❌ Absent

---

### Pilier 1 — Code

| Garantie | État | Note |
|---|---|---|
| Detect AI-generated code lacking governance | ✅ | `reclaim inspect` classifies generators |
| Detect missing or inadequate tests | ⚠️ | Detection exists; adequacy scoring absent |
| Detect proprietary build dependencies | ⚠️ | Partial — dependency audit exists, build portability not verified |
| Produce evidence-backed governance documentation | ❌ | Scaffold exists but produces templates, not evidence-backed documents |
| Measure code sovereignty level | ⚠️ | Findings exist; aggregated verdict absent |

**Verdict:** Measurement is partial. Governance production is absent.

---

### Pilier 2 — Données

| Garantie | État | Note |
|---|---|---|
| Inspect data access control (RLS, permissions) | ✅ | `supabase rls harden` covers this |
| Classify data storage by sovereignty level | ⚠️ | Sovereignty check covers external services, not data specifically |
| Detect undocumented schema evolution | ❌ | Not implemented |
| Verify migration scripts exist and are testable | ❌ | Not implemented |
| Produce schema and data portability documentation | ❌ | Not implemented |
| Verify backup existence and verifiability | ❌ | Not implemented |

**Verdict:** Access control (RLS) covered. Everything else is absent.

---

### Pilier 3 — IA

| Garantie | État | Note |
|---|---|---|
| Enforce confidentiality gate before AI calls | ✅ | `ai/router.py` gate exists |
| Route AI locally by default | ✅ | `aeos ai ask` defaults to local |
| Require explicit authorization for external AI | ✅ | `require_human_approval` flag |
| Verify provider replaceability by configuration | ⚠️ | Architecture supports it; one hardcoded provider check remains |
| Log every AI interaction by reference | ❌ | Not implemented |
| Demonstrate offline operation without AI | ❌ | Fallback exists but not verified or demonstrated |

**Verdict:** The core doctrine is implemented. Verification and demonstration are absent.

---

### Pilier 4 — Infrastructure

| Garantie | État | Note |
|---|---|---|
| Inventory all external dependencies | ✅ | `sovereignty check` produces inventory |
| Measure sovereignty level per dependency (1-5) | ✅ | Sovereignty levels 1-5 are measured |
| Flag undocumented external dependencies | ✅ | `reclaim inspect` detects these |
| Produce infrastructure documentation from evidence | ❌ | Not implemented |
| Propose exit paths for captured dependencies | ❌ | Not implemented |
| Verify infrastructure reproducibility | ❌ | Not implemented |

**Verdict:** Measurement is solid. Documentation and actionability are absent.

---

### Pilier 5 — Connaissance

| Garantie | État | Note |
|---|---|---|
| Preserve immutable audit timeline (MemoryRecords) | ✅ | `memory` rail is fully functional |
| Produce evidence artifacts per operation | ✅ | Evidence engine produces artifacts |
| Capture decisions as ADRs with evidence references | ❌ | Not implemented |
| Write governance documents into the governed project | ❌ | Not implemented |
| Ensure knowledge artifacts are independent of AEOS | ✅ | Local JSON files, readable without AEOS |

**Verdict:** Memory and evidence are strong. Decision capture and governance injection are absent.

---

### Pilier 6 — Opérationnel

| Garantie | État | Note |
|---|---|---|
| Generate recovery plan | ✅ | `reclaim recovery plan` is functional |
| Execute recovery stages with human gates | ❌ | Plan exists; execution is manual |
| Detect sovereignty drift between states | ❌ | `memory compare` exists but no alerting |
| Quantify sovereignty progression | ⚠️ | Timeline exists; progression scoring absent |
| Produce operational continuity documentation | ❌ | Not implemented |

**Verdict:** Planning is strong. Execution and continuous monitoring are absent.

---

## 4. Synthèse des gaps par pilier

| Pilier | Couverture actuelle | Gap principal | Impact sur la mission |
|---|---|---|---|
| Code | Measurement partial | No evidence-backed governance | Cannot prove mastery |
| Données | Access control only | Schema, migration, portability absent | Partial sovereignty only |
| IA | Doctrine implemented | Replaceability unverified, logging absent | Promise undemonstrated |
| Infrastructure | Measurement solid | No actionable documentation | Measurement without remedy |
| Connaissance | Memory strong | No governance injection, no ADRs | Learning without documentation |
| Opérationnel | Planning strong | No execution, no drift detection | Plans without action |

**The structural gap:**
AEOS currently measures and plans well. It cannot yet execute or continuously maintain.
The product stops exactly at the moment where the user must act. The gap is not about
understanding — it is about controlled action.

---

## 5. Roadmap MVP reconstruite par souveraineté

The roadmap below is rebuilt exclusively from the sovereignty model. Each sprint must
advance at least one pillar's guarantee from absent or partial to covered.

**Critère d'entrée d'un sprint :** *Does this advance a sovereignty guarantee or only add a capability?*

**Règle de priorité :** Pillars where measurement exists but action is absent are
prioritized — they have the highest conversion ratio (build on what exists, close the gap).

---

### Sprint S-1 — Fermer la boucle de souveraineté du code
**Pilier : Code + Connaissance**

The single most impactful sprint. Produce evidence-backed governance documents IN the
governed project, based on real audit findings — not templates. This is the first time
AEOS can say: "this project is governed." It advances both Code sovereignty (governance
documentation) and Knowledge sovereignty (governance injection).

**Garanties à couvrir :**
- Code: Produce evidence-backed governance documentation ❌ → ✅
- Knowledge: Write governance documents into the governed project ❌ → ✅

**Dépendance :** Requires human-gated execution — Apply Engine must exist first.
Split into two sub-sprints if needed: Apply Engine (S-1a), then Governance Injection (S-1b).

---

### Sprint S-2 — Démontrer la souveraineté IA de bout en bout
**Pilier : IA**

The AI sovereignty pillar is the most visible promise and the most under-verified.
This sprint closes the replaceability gap, adds AI interaction logging, and verifies
that AEOS operates fully without any external AI. The goal is not new features —
it is making existing features provably correct.

**Garanties à couvrir :**
- IA: Verify provider replaceability ⚠️ → ✅
- IA: Log AI interactions by reference ❌ → ✅
- IA: Demonstrate offline operation ❌ → ✅

---

### Sprint S-3 — Souveraineté des données : au-delà du contrôle d'accès
**Pilier : Données**

The data sovereignty pillar has the largest gap: RLS coverage exists but schema
documentation, migration traceability, and portability are absent. A product whose
data is inaccessible to the business after a provider failure has not achieved
sovereignty regardless of code quality.

**Garanties à couvrir :**
- Données: Detect undocumented schema evolution ❌ → ✅
- Données: Verify migration scripts exist and are testable ❌ → ✅
- Données: Produce schema documentation from evidence ❌ → ✅

---

### Sprint S-4 — Souveraineté de la connaissance : les décisions capturées
**Pilier : Connaissance**

Memory records exist. Evidence exists. But decisions are not captured. A product whose
MemoryRecords show "what happened" but not "why it was decided" has incomplete knowledge
sovereignty. This sprint adds ADR generation from audit evidence, making the governance
record complete.

**Garanties à couvrir :**
- Knowledge: Capture decisions as ADRs with evidence references ❌ → ✅

---

### Sprint S-5 — Souveraineté opérationnelle : de la planification à l'exécution
**Pilier : Opérationnel**

The recovery plan is excellent. The stages are defined. But no stage can be executed
under human control today. This sprint makes recovery operational: guided, gated,
executable. It also adds the first drift detection — the trigger for the recovery
workflow.

**Garanties à couvrir :**
- Opérationnel: Execute recovery stages with human gates ❌ → ✅
- Opérationnel: Detect sovereignty drift between states ❌ → ✅

---

### Sprint S-6 — Souveraineté de l'infrastructure : de l'inventaire à l'action
**Pilier : Infrastructure**

The infrastructure inventory is strong. But inventory without documentation and without
exit paths is a measurement without remedy. This sprint produces infrastructure
sovereignty documents from evidence: what exists, what it costs in dependency terms,
and how to migrate away from each dependency.

**Garanties à couvrir :**
- Infrastructure: Produce infrastructure documentation from evidence ❌ → ✅
- Infrastructure: Propose exit paths for captured dependencies ❌ → ✅

---

### Sprint S-7 — Souveraineté opérationnelle : score et progression
**Pilier : Opérationnel + tous les piliers**

By sprint S-6, all pillars have at least one guarantee covered. This sprint synthesizes
everything into a sovereign score — a single, measurable, communicable metric that
aggregates all six pillars. The score answers the CTO's question: "where am I, and
where was I six months ago?"

**Garanties à couvrir :**
- Opérationnel: Quantify sovereignty progression ⚠️ → ✅
- All pillars: Aggregate pillar scores into a sovereign verdict

---

## 6. Le MVP de souveraineté

**A product is at MVP sovereignty when a developer or CTO, starting from an unknown
project, can demonstrate the following to any auditor, investor, or regulator:**

1. This project is understood — it has documented architecture, decisions, and history.
2. This project is controlled — access to code and data is governed at the appropriate level.
3. This project can be moved — the infrastructure is documented and the dependencies have exit paths.
4. This project can be proven — every significant decision has evidence.
5. This project can be developed further — with AI assistance that is local, replaceable, and audited.
6. This project's sovereignty can be maintained — drift is detected and recovery is executable.

**Current honest position:** statements 1, 3, 4, and 5 are partial. Statements 2 and 6 are
mostly absent. MVP is S-1 through S-5.

---

## 7. La vraie catégorie

A tool that simply "reclaims projects" has many competitors — code auditors, migration
consultants, security scanners, technical debt analyzers.

A platform that **guarantees digital sovereignty across six pillars** — code, data, AI,
infrastructure, knowledge, and operations — permanently, locally, with human gates at
every significant action — is a different category.

The distinction is not in what the tool measures. It is in what the tool **guarantees**.

Measurement without action is a report. Measurement with controlled, evidence-backed,
human-gated action is sovereignty.

That is what AEOS is building. Not the report. The guarantee.
