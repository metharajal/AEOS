# AEOS Workspace — Product Philosophy

**Version:** 1.0.0
**Date:** 2026-07-01
**Status:** Strategic — Founding Document
**Governed by:** [CONSTITUTION.md](../../CONSTITUTION.md) · [MANIFESTO.md](../../MANIFESTO.md)
**See also:** [AEOS-MVP-1.0.md](AEOS-MVP-1.0.md) · [AEOS-PRODUCT-VISION.md](AEOS-PRODUCT-VISION.md)

---

## Preamble

This document is not a UI specification.
It does not describe screens, layouts, components, or interactions.

It describes why the AEOS Workspace exists, what it stands for,
how it thinks about software, and what it will become.

Every design decision, every engineering choice, and every product iteration
should be measured against this document.

If something contradicts what is written here, the document wins — unless
the document is changed through deliberate revision.

This is a founding document. It is meant to last.

---

## 1. Why the Workspace Exists

### The CLI solves the wrong problem for half the audience

The AEOS CLI is the authoritative interface. It is fully built, fully tested,
and fully capable of everything AEOS can do today.

But the CLI speaks one language: the language of engineers who live in terminals.

The people who need AEOS most are not always the people who live in terminals.

A CTO at a twelve-person startup decides which systems to migrate, which governance to prioritize,
which technical debt to address before the next enterprise client meeting.
They think in portfolio terms, not in command syntax.

A DSI at a government institution needs to demonstrate to auditors that citizen data
is sovereign, that dependencies are documented, and that the team can maintain the system
without a vendor. They think in compliance terms, not in recovery stages.

A software architect inheriting an AI-generated project needs to understand what exists,
what risks are present, and where to begin. They think in architecture terms,
not in CLI flags.

**The Workspace exists because the CLI was designed to execute. The Workspace is designed to govern.**

### The problem the Workspace solves

The CLI answers: "What should I do next?"
The Workspace answers: "What is happening across my entire portfolio — and am I in control?"

These are different questions. They require different instruments.

The CLI is a scalpel. The Workspace is a control room.

A surgeon uses a scalpel. An air traffic controller uses a control room.
Both are indispensable. Neither replaces the other.

### Why a CTO opens the Workspace every morning

Not to check if the tests passed. That is CI.
Not to read logs. That is monitoring.
Not to write code. That is the IDE.

A CTO opens the Workspace to answer five questions:

1. Do I have any open human gates that need my decision?
2. Has any project drifted from its declared sovereignty posture?
3. Are there governance documents awaiting my review?
4. What did the AI do last night, and does it need my validation?
5. Is the project the client asked about ready for the due diligence call at 10am?

These five questions define the Workspace.
Everything else is secondary.

---

## 2. The Philosophy of the Workspace

### The Workspace is a cockpit

A dashboard shows you information.
A cockpit lets you pilot a system.

The difference is not cosmetic. It is philosophical.

A dashboard assumes the system runs itself and you need to be informed.
A cockpit assumes the system requires a pilot and you need to be equipped.

AEOS takes the second position without apology.

Software does not govern itself.
AI does not make engineering decisions.
Sovereignty does not maintain itself.

The human is the pilot. The Workspace is the cockpit.

### What makes a cockpit different from a dashboard

A cockpit has instruments that reflect the real state of the system — not what the system
thinks you want to see, but what the system actually is.

A cockpit has controls that require deliberate activation. Nothing happens because you
looked at a screen. Things happen because you made a decision.

A cockpit makes the cost of inaction visible. If a human gate has been open for three days,
the Workspace makes that visible — not as an alarm, but as a fact.

A cockpit gives you enough information to make a decision, and not more.
A cockpit that overwhelms its pilot is a cockpit that kills.

### The cockpit doctrine

Every instrument in the Workspace must earn its place.
If it does not help the pilot make a better decision, it does not belong.

Every control in the Workspace must be deliberate.
If it does something automatically, it must tell the pilot exactly what it did.

Every action in the Workspace must produce evidence.
If the pilot approved something, there must be a record of what was approved, when, and why.

This is not a UX preference. It is a constitutional requirement.
CONSTITUTION §6.2: "No authorized modification. No applied state without intent.
No silent frontier escalation. No destructive action without gate."

The cockpit doctrine is the Constitution made visible.

---

## 3. The Magic Moment

### What must happen in under 30 seconds

The user opens the Workspace. They have never seen this project before,
or they haven't looked at it in three weeks.

In under 30 seconds, they must understand:

- **What this project is** — generator, stack, providers, size
- **Where it stands** — current stage, current maturity, current sovereignty level
- **What needs attention** — open human gates, critical risks, missing evidence
- **What changed since last time** — memory delta, new findings, AI activity

Not in a report. Not in a table of metrics. In an instant.

The magic moment is not about information volume.
It is about orientation.

The pilot who enters the cockpit does not need to be told what every instrument means.
They orient instantly — altitude, heading, fuel, anomalies.
Then they fly.

### What the user must feel

Not informed. Oriented.
Not overwhelmed. Equipped.
Not reassured. Honest.

The worst thing a cockpit can do is give the pilot false confidence.
AEOS must never show a green light when the system is not green.

The best thing a cockpit can do is give the pilot an accurate picture of reality —
even when reality is uncomfortable — and the controls to do something about it.

### Why they say "I finally understand my software"

Because for the first time, the software is legible.

Not the code — the code was always there.
But the governance, the sovereignty posture, the dependencies, the risks,
the human decisions that shaped this system — these were invisible.

AEOS makes them visible.

The Workspace is not a tool that generates insight. It is a surface that reveals
what was always true — and gives the pilot a way to act on it.

"I finally understand my software" means:
I know what I depend on.
I know what I control.
I know what I need to decide.
I know what my team has committed to.
I know where I am and where I am going.

---

## 4. The Fundamental Objects

### Workspace

The AEOS Workspace is the entire environment — not a single project view,
but the complete engineering operating system for a person, a team, or an organization.

The Workspace is where the pilot lives.
It persists between sessions. It accumulates memory.
It is the one place where all governed projects are visible together.

A Workspace belongs to a human operator. It reflects their decisions, their policies,
their approved actions, and their accumulated knowledge.

### Portfolio

A Portfolio is the collection of projects visible in a Workspace.

A CTO sees their company's portfolio: five products, two internal tools, one legacy migration.
A consulting firm sees their client portfolio: twelve projects at various stages of recovery.
A solo founder sees their portfolio of one.

The Portfolio is the highest-level view.
It answers the question: "What is the state of everything I am responsible for?"

A Portfolio does not aggregate metrics. It reveals posture.
The question is not "how many tests are passing?" — it is "which projects are sovereign
and which are exposed?"

**Relationship:** A Workspace contains one or more Portfolios.
A Portfolio contains one or more Projects.

### Project

A Project is a software system under AEOS governance.

It has a name, a stack, a generator (if applicable), a set of providers,
a sovereignty level, a project maturity, and a recovery arc.

The Project is the fundamental unit of the Workspace.
Everything else — stages, evidence, memory, governance, migration — lives inside a Project.

A Project is not a repository. A repository is an implementation detail.
A Project is a software system: its architecture, its dependencies, its governance posture,
its history, and its future.

**Relationship:** A Project belongs to a Portfolio. A Project has Memory, Architecture,
Governance, Recovery, Migration, Sovereignty, Evidence, and a Timeline.

### Memory

Memory is the accumulated, validated audit history of a Project.

Every time AEOS audits a project, a MemoryRecord is created.
Every time a human validates a finding or approves an action, it is recorded in Memory.
Every decision — to migrate, to defer, to harden, to accept risk — is a Memory entry.

Memory is not a log. Logs record what happened.
Memory records what was understood and validated.

Memory makes each session richer than the last.
The first time you run `aeos reclaim harden`, you discover your project.
The tenth time, you measure your progress.

Memory is local. It belongs to the project and the team. It never leaves.

**Relationship:** A Project has one Memory. Memory contains a Timeline of MemoryRecords.
Each MemoryRecord is associated with a Stage, an Evidence set, and zero or more Decisions.

### Architecture

Architecture is the declared structure of a Project:
its components, its dependencies, its providers, its data flows, and the decisions that shaped it.

Architecture in AEOS is not the actual code structure.
It is the governed, documented, human-reviewed understanding of the code structure.

The difference is critical. Code changes daily.
Architecture is what the team has agreed to understand and maintain.

Architecture is always a document, never inferred automatically.
AEOS can generate an architecture draft. Humans review and validate it.
Only after human review does it become the Project's Architecture.

**Relationship:** A Project has one declared Architecture. Architecture contains Components,
Dependencies, Providers, and Decision references.

### Governance

Governance is the set of documents and policies that define how a Project is managed.

In AEOS, Governance is concrete: ARCHITECTURE.md, DECISIONS.md, SECURITY.md,
SOVEREIGNTY.md, AI-DEVELOPMENT-POLICY.md, aeos.toml, RECOVERY.md.
These seven documents are required by CONSTITUTION §5.5.

Governance is not compliance. Compliance is governance done for regulators.
Governance is done for the team — to make engineering decisions explicit,
to make knowledge transferable, and to make the project auditable by its own members.

A project without governance is a project that depends on people's memories.
People leave. Memories fade. Governance persists.

**Relationship:** A Project has one Governance set. Governance contains required Documents,
each with a status (present, missing, outdated, under review).

### Recovery

Recovery is the arc from fragile to sovereign — the ten-stage process that takes a project
from its current ungoverned state to a state of full engineering control.

Recovery is not a one-time event. It is a progression.
Each stage has preconditions, actions, human gates, evidence requirements, and a rollback path.

A project enters Recovery when it is discovered to be fragile, ungoverned, or captured.
A project exits Recovery when it reaches `sovereign` maturity — when it can survive,
be transferred, be audited, and be evolved without external dependency.

Recovery is the story of a project. It is the journey, not the destination.

**Relationship:** A Project has one Recovery arc. Recovery contains ten Stages,
each with a status (pending, ready, in progress, done, blocked), Evidence, and Human Gates.

### Migration

Migration is a planned, human-approved transition from one architecture to another.

In MVP 1.0, Migration is a plan: source architecture, target architecture, backup requirement,
dry-run analysis, rollback SQL, sovereignty delta, human validation.

In V2, Migration is also an execution: the controlled apply of the validated plan,
with backup confirmation, Level 4 human gate, step-by-step monitoring, and evidence at each step.

Migration is never automatic. It is never silent. It is never irreversible without a rollback path.

**Relationship:** A Project may have zero or one active Migration. A Migration has a Plan,
a Status (draft, reviewed, approved, executing, complete, rolled back), and an Evidence set.

### Sovereignty

Sovereignty is the measured independence of a Project from external platforms and vendors.

AEOS defines five sovereignty levels:
- Level 1: Controlled Productivity — cloud-hosted, secured and documented
- Level 2: Personal Cloud Control — own cloud accounts, full dashboard access
- Level 3: Managed Open Source — open-source backends, self-manageable
- Level 4: Self-Hosted — on-premise or controlled infrastructure
- Level 5: Full Sovereign Stack — zero dependency on foreign platforms

Sovereignty is not ideology. It is measurement.
A project at Level 1 is not wrong. It is honest about its posture.
A project claiming Level 4 without documentation is not sovereign — it is unverified.

AEOS measures sovereignty. It does not impose a target.
The target is chosen by the pilot based on client requirements, regulation, and risk tolerance.

**Relationship:** A Project has a declared Sovereignty Level and a Sovereignty Posture document.
Sovereignty is re-assessed at each audit. The Timeline shows sovereignty progression.

### Evidence

Evidence is the artifact that proves a Stage or action was completed.

Evidence is not a checkbox. Evidence is a reference to an inspectable, auditable artifact:
a file, a git commit, a test result, a backup record, a human approval timestamp.

AEOS generates evidence at every operation. Humans confirm evidence at every stage.

Evidence is the foundation of trust. A project that cannot produce evidence for its
governance claims is a project with claims, not governance.

**Relationship:** Each Stage has required Evidence items. Each MemoryRecord contains
an Evidence summary. Evidence can be referenced from Governance documents and Decisions.

### Timeline

The Timeline is the chronological view of all audits, decisions, and validated actions
for a Project.

The Timeline is the project's history — not the git history, which is the code's history.
The Timeline is the engineering governance history: what was understood, what was decided,
what was approved, how the project evolved.

The Timeline enables measurement: sovereignty went from Level 1 to Level 3 in six weeks.
The Timeline enables audit: every decision has a timestamp, an actor, and a rationale.
The Timeline enables handoff: a new team member can read the Timeline and understand
not just what the code does, but why the system is the way it is.

**Relationship:** A Project has one Timeline. The Timeline contains MemoryRecords, Decisions,
Human Gate approvals, and Migration events, in chronological order.

### Agent

An Agent is a specialized AI collaborator with a bounded scope, operating under human approval gates.

AEOS defines 14 specialized agents: Discovery, Architecture, Planning, Database, Backend,
Frontend, Legacy, Refactoring, Security, DevOps, Test, Evidence, Memory, and Local AI Orchestrator.

An Agent does not decide. An Agent proposes.
An Agent does not act on production. An Agent acts in branches, under human gates.
An Agent does not access secrets. An Agent accesses what it needs, stripped of sensitive data.

In the Workspace, Agent activity is visible, auditable, and controllable.
The pilot can see what every agent proposed, what was accepted, and what was modified
before acceptance.

**Relationship:** Agents operate within Capabilities. Agents are configured through Policies.
Agent actions are gated by Human Gates. Agent outputs are recorded in Memory.

### Stage

A Stage is a discrete phase in the Recovery arc.

AEOS defines ten stages: stage_0_baseline through stage_9_sovereign_operating_mode.

Each Stage has:
- A name and description
- Preconditions (what must be true before this stage begins)
- Actions (what AEOS and the team do)
- Human gates (where human approval is required)
- Evidence requirements (what must exist to declare the stage complete)
- A rollback path (what to do if the stage needs to be undone)
- A memory record type (what is captured when the stage completes)
- Associated agents (which agents assist in this stage)

A Stage is not a checkbox on a roadmap. It is a structured commitment with preconditions
and evidence. A Stage that cannot produce its evidence requirements is not complete.

**Relationship:** Recovery contains ten Stages. Each Stage belongs to one or more Capabilities.
Each Stage has Evidence, Human Gates, and optional Agent participation.

### Capability

A Capability is one of the eight core functions of AEOS:
Discover · Assess · Recover · Transform · Continue · Govern · Operate · Learn.

Capabilities are not features. They are engineering disciplines.

Discover: understand what exists.
Assess: evaluate the current state.
Recover: bring fragile systems to control.
Transform: move to a new architecture.
Continue: develop with AI under sovereignty constraints.
Govern: define and enforce standards.
Operate: maintain over time.
Learn: accumulate validated knowledge.

A Capability is exercised through Stages and Engines.
In the Workspace, Capabilities provide the organizing vocabulary for what AEOS can do.

**Relationship:** Capabilities are implemented by Engines and exercised through Stages.
Capabilities map to Rails: the Reclaim Rail exercises Discover, Assess, and Recover.

### Policy

A Policy is a declared rule governing how AEOS behaves in a specific context.

Policies govern:
- AI routing: which tasks go local, which go frontier, what requires human approval
- Data handling: what can be sent to which provider, what must never leave the machine
- Sovereignty: the target level, the acceptable dependencies, the exit strategies
- Agent behavior: what agents can propose, what they cannot do
- Migration: what constitutes a valid backup, what rollback is required

Policies are declared in `aeos.toml` and in governance documents.
They are not preferences. They are engineering contracts.

A Policy cannot be overridden by an agent. A Policy can be changed by a human.
Every Policy change is a Decision and is recorded in Memory.

**Relationship:** Policies govern Agents, AI Routing, and Migration behavior.
Policies are stored in aeos.toml and referenced in Governance documents.

### Human Gate

A Human Gate is a point in a workflow where AEOS stops and requires explicit human approval
before proceeding.

Human Gates exist because some actions are irreversible, high-risk, or require
engineering judgment that no automated system should provide.

Human Gates are not friction. They are the architecture of accountability.
CONSTITUTION §3.4: "AI shall never perform irreversible engineering actions without
explicit human authorization."

In the Workspace, Human Gates are first-class objects.
Every open Human Gate is visible. Every approved Human Gate is auditable.
No Human Gate can be bypassed, overridden, or auto-approved.

The pilot must always know: what gates are open, what they are gating, and what
the consequence of approval or refusal is.

**Relationship:** Human Gates appear within Stages, Migration steps, and Agent actions.
Human Gate approvals are recorded in Memory with a timestamp and actor.

### Risk

A Risk is a classified finding that requires attention or a decision.

AEOS classifies risks into four levels: critical, high, medium, low.

A critical risk is a finding that must be addressed before the project can proceed.
A high risk is a finding that should be addressed in the next stage.
A medium risk is a finding that is documented and tracked.
A low risk is a finding that is acknowledged and deferred.

A risk is not a bug. A bug is a code defect.
A risk is an engineering posture finding: exposed secrets, missing portability assets,
undocumented dependencies, unenforced RLS, absent governance.

**Relationship:** Risks are produced by audits (Discovery and Assessment capabilities).
Risks are classified in Evidence reports. Risks are tracked in the Recovery arc.

### Decision

A Decision is a recorded choice, its context, rationale, and consequence.

Every significant engineering choice in AEOS becomes a Decision:
the choice to use a specific provider, to defer a stage, to accept a risk,
to approve a migration, to adopt a policy, to change an architecture.

CONSTITUTION §2.3: "Every important engineering decision shall be explicit.
Assumptions must be documented. Architectural decisions must be recorded."

A Decision is not a log entry. A log records what happened.
A Decision records what was understood, what was considered, what was chosen, and why.

Decisions are the living record of engineering judgment.
They are the difference between a team that knows its system and a team that inherited it.

**Relationship:** Decisions are stored in DECISIONS.md and in Memory.
Decisions are linked to Stages, Human Gates, and Architecture changes.

---

## 5. The Unit of the Product

### The answer: the Project

The Workspace is organized around Projects.

Not stages. Not agents. Not sovereignty levels. Not evidence. Projects.

Here is why.

Every other object in AEOS exists within the context of a Project.
Stages are stages of a Project's recovery.
Evidence proves a Project's stage completion.
Memory is a Project's history.
Governance is a Project's declared standards.
Sovereignty measures a Project's independence.
Migration is a Project's architectural transition.

Remove the Project and nothing else has meaning.

The AEOS Workspace is a project governance system — not a process manager,
not an AI orchestrator, not a sovereignty calculator.
It governs software projects. Projects are its reason for existing.

### Why not stages?

Stages are the path, not the destination.
A stage matters because it moves a Project forward.
Organizing the Workspace around stages would make AEOS a recovery checklist.
AEOS is not a checklist. It is an operating system for software ownership.

### Why not sovereignty?

Sovereignty is a measurement, not a purpose.
A project that achieves sovereignty Level 4 has achieved it in service of something:
a client requirement, a regulatory mandate, a risk mitigation.
Organizing the Workspace around sovereignty would make AEOS an ideology machine.
AEOS is not ideological. It is pragmatic.

### Why not agents?

Agents are means, not ends.
No pilot thinks of their cockpit as an "agent management system."
Agents serve the project. The project serves the team. The team serves the mission.

### The implication

Every view in the Workspace starts with a Project or Portfolio.
Every action in the Workspace is taken in the context of a Project.
Every memory, every evidence, every decision is attached to a Project.

The navigation of the Workspace follows: **Portfolio → Project → Everything else.**

---

## 6. The Main Views of the Workspace

### Portfolio Overview

**Role:** The map. The first thing the pilot sees.

The Portfolio Overview shows all governed projects in one place.
Each project is represented as a card or row showing:
sovereign state, current stage, open human gates, critical risks, and last audit date.

The Portfolio Overview is not a status dashboard. It is a triage surface.
The pilot scans it and immediately understands: where is my attention needed?

No metric. No graph. No trend. Just posture.

The Portfolio Overview is the answer to: "What is the state of everything I am responsible for?"

---

### Project Workspace

**Role:** The cockpit per project. The deepest view.

Once the pilot enters a specific Project, they are in the Project Workspace.
This is the full control environment for one project: its architecture, its recovery arc,
its memory, its governance, its open human gates, its AI activity.

The Project Workspace is persistent between sessions.
The pilot leaves, comes back, and the cockpit remembers where they were —
not literally, but because the Memory is always there.

The Project Workspace is not a page with tabs. It is an integrated environment
where every object is linked to every other. A risk links to its evidence.
Evidence links to a stage. A stage links to its human gates.
A human gate links to the agent that proposed the action.

Everything is connected. Nothing is isolated.

---

### Architecture Explorer

**Role:** Understand the structure.

The Architecture Explorer renders the declared architecture of a project:
its components, its dependencies, its providers, its data flows.

It does not show the code. It shows what the team has agreed to understand
about the code — the governed architecture, not the actual implementation.

The Architecture Explorer is where a new team member starts.
It is where an architect validates that the documented architecture matches their mental model.
It is where a CTO demonstrates to a client: "This is what we have. This is what we control."

The Architecture Explorer is read-only. It reflects what has been declared and reviewed.
Changes to the architecture are Decisions — and Decisions go through human review.

---

### Recovery Center

**Role:** Progress through stages.

The Recovery Center shows the full ten-stage arc for a project,
with the current state of each stage: pending, ready, in progress, complete, blocked.

For each stage, the pilot can see:
- What is required before this stage can begin
- What actions are associated with this stage
- Which human gates are open
- What evidence is required for completion
- What agents are available to assist

The Recovery Center is where recovery work happens — not where recovery is tracked.
The distinction matters. Tracking produces overhead. Working produces progress.

The pilot does not fill in a form saying "stage 2 complete." The pilot reviews the evidence
for stage 2, confirms it is valid, and approves the stage. AEOS records the completion.

---

### Governance Center

**Role:** Manage governance documents and decisions.

The Governance Center shows the seven required governance documents for a project
and their current status: present, missing, outdated, under review.

For each document, the pilot can:
- See the current content
- Review and approve a proposed update
- See when it was last validated and by whom
- See which decisions it references

The Governance Center is also where Decisions are managed.
Every ADR, every DEC, every significant choice is visible here — with its context,
its rationale, and its consequences.

The Governance Center is the answer to: "Do I own my project's knowledge?"

---

### Migration Center

**Role:** Plan, validate, and (in V2) execute migration.

The Migration Center shows the migration posture of a project:
current architecture, target architecture, readiness assessment, and migration plan.

In MVP 1.0, the Migration Center shows the plan:
backup requirements, dry-run analysis, rollback SQL, sovereignty delta projected.

The pilot reviews the plan, asks questions, documents their decision, and approves
the migration strategy. The execution waits for V2.

In V2, the Migration Center becomes the execution surface:
the pilot sees each step of the migration, its status, its evidence,
and can approve or halt at any human gate.

The Migration Center is the answer to: "Am I ready to move — and do I know what will happen?"

---

### Memory Timeline

**Role:** Understand the history.

The Memory Timeline shows every audit, every decision, every human gate approval,
every agent action for a project — in chronological order.

The Timeline is not a log. Logs are operational. The Timeline is historical.
It answers: "How did this project become what it is today?"

The Timeline enables sovereignty measurement over time:
"Six months ago, this project had exposed secrets and no governance.
Today, it is at sovereignty Level 3. Here are the decisions that made that happen."

The Timeline is the project's biography. Every serious project deserves one.

---

### Evidence Explorer

**Role:** Prove progress.

The Evidence Explorer shows the evidence associated with each stage and each decision.

Every claim in AEOS must be backed by evidence.
The Evidence Explorer is where the pilot verifies: "Is this real?"

For each stage: what evidence was required, what evidence was produced,
and who confirmed it. If evidence is missing, it is shown as missing — not hidden.

The Evidence Explorer is the answer to: "Can I defend this project's posture
to a client, an auditor, or an investor?"

---

### AI Collaboration View

**Role:** Govern AI usage.

The AI Collaboration View shows everything the AI did for this project:
what was proposed, what was approved, what was rejected, what was modified before approval,
how much went to local AI, how much went to frontier, and what frontier was authorized for.

The pilot can configure AI routing policy here:
which tasks route to local, which require explicit approval before frontier escalation,
which data must never be sent externally.

The AI Collaboration View is the answer to: "Is my team using AI responsibly?
Do I know what data left the machine? Who approved it?"

It is not a usage dashboard. It is an accountability surface.

---

### Human Gates View

**Role:** Process pending approvals.

The Human Gates View shows every open human gate across all projects in the portfolio.

This is the most important operational view.
Every human gate is a decision waiting to be made.
Some are urgent (migration approval before a client call).
Some are routine (governance document review).
Some are critical (frontier AI authorization for sensitive context).

The Human Gates View is the answer to: "What needs my decision right now?"

The pilot can filter by project, by urgency, by gate type.
They can review the proposed action, see the context, and approve or reject.
Every approval is recorded in Memory with a timestamp.

---

### Risk Register

**Role:** Prioritize attention.

The Risk Register shows all classified risks across the portfolio:
critical, high, medium, low — with the projects they belong to and the stages they block.

The Risk Register is not an alarm system. It is a prioritization tool.

A CTO scanning the Risk Register knows: "I have two critical risks on Project A.
They are blocking stage 2. Before I do anything else today, I need to address those."

Every risk has a remediation path. The Risk Register shows not just the problem
but the next action to address it.

---

## 7. The Vital Information

### Tier 1 — Always visible, never hidden

These are the instruments that must be on-screen at all times.
If the pilot cannot see them, the cockpit has failed.

**1. Open Human Gates** — How many decisions are waiting for me right now?
If this number is greater than zero, it is shown prominently.
A human gate that has been open for 48 hours requires escalation visibility.

**2. Critical Risks** — How many critical risks exist across my portfolio?
Critical means: blocking progress, exposing secrets, or putting client data at risk.
This number must never be hidden in a submenu.

**3. Sovereignty Level per Project** — At a glance, where does each project stand?
Not as a number — as a posture: secured, governed, portable, sovereign, drifting.

**4. Current Stage per Project** — Where is each project in its recovery arc?
The pilot must see at a glance: this project is at stage_2, this one is blocked at stage_4.

### Tier 2 — Visible on demand, surfaced when relevant

**5. Missing Governance** — Which required documents are absent or outdated?
Surfaced automatically when a project is selected or when a due diligence event is imminent.

**6. Evidence Health** — For the current stage: is evidence complete, partial, or missing?
Shown within the Recovery Center, not on the Portfolio Overview.

**7. AI Activity** — What did AI agents do recently? What is pending confirmation?
Shown in the AI Collaboration View, surfaced as a notification when approval is needed.

**8. Pending Reviews** — Governance documents or architecture proposals awaiting review.
Shown in the Governance Center, surfaced in the Human Gates View.

**9. Migration Readiness** — Is this project ready to migrate? What is blocking it?
Shown in the Migration Center, surfaced in the Project Workspace summary.

**10. Memory Delta** — How has this project changed since the last audit?
Shown in the Memory Timeline, surfaced as a summary when the Project Workspace is opened.

### Tier 3 — Available, not surfaced automatically

**11. Technical Debt Summary** — The accumulation of accepted risks and deferred stages.
Available in the Evidence Explorer and Recovery Center.

**12. Dependency Map** — The full tree of external dependencies and their sovereignty impact.
Available in the Architecture Explorer.

**13. Frontier AI Usage** — Frequency, cost, and context of frontier AI calls.
Available in the AI Collaboration View.

**14. Audit History** — Full chronological audit record.
Available in the Memory Timeline.

---

## 8. The Main Actions

Listed in descending frequency — what the pilot does most to least often:

| Rank | Action | Context |
|---|---|---|
| 1 | Review and approve an open human gate | Human Gates View — daily |
| 2 | Review a governance document proposal | Governance Center — weekly per project |
| 3 | Check open risks for a project | Risk Register — daily |
| 4 | Check the portfolio sovereignty overview | Portfolio Overview — daily |
| 5 | Review evidence for a completed stage | Recovery Center — per stage |
| 6 | Compare two memory records | Memory Timeline — after each audit |
| 7 | Review AI activity and approve pending actions | AI Collaboration View — daily |
| 8 | Update AI routing policy | AI Collaboration View — monthly or on-demand |
| 9 | Import a new project into AEOS | Portfolio Overview — on project onboarding |
| 10 | Mark a stage as ready and approve entry | Recovery Center — per stage |
| 11 | Review the migration plan for a project | Migration Center — before client call |
| 12 | Approve the migration strategy | Migration Center — on decision |
| 13 | Review architecture changes | Architecture Explorer — after significant work |
| 14 | Validate a Decision record | Governance Center — after architectural choice |
| 15 | Configure sovereignty target for a project | Settings / Governance Center |
| 16 | Export an evidence report | Evidence Explorer — for client or auditor |
| 17 | Set frontier AI authorization for a task | AI Collaboration View |
| 18 | Review and update sovereignty policy | Governance Center / Settings |
| 19 | Run a manual audit | Recovery Center / Portfolio |
| 20 | Archive a completed migration | Migration Center |

### The actions that must never require more than two steps

1. Reviewing an open human gate
2. Checking the current sovereignty level of a project
3. Finding the most critical risk in the portfolio

If any of these requires more than two actions, the cockpit has failed.

---

## 9. The Users

### Solo Founder

**Who:** Builds a SaaS or internal tool, usually alone or with one engineer.
Used Lovable or Bolt to start. Now pitching to their first enterprise client.

**What they expect from the Workspace:**
Speed and clarity. They have fifteen minutes before the client call.
They need to understand their project's posture instantly.
They need to know what to say when the client asks about data sovereignty.

The Workspace must speak in plain terms: "Your project is at sovereignty Level 1.
This means your data is on Supabase. You can explain this. Here is how."

**What they do not need:**
Complexity. Jargon. Dashboards they do not understand.
The solo founder is not a governance expert — they are a builder who needs
to become credible to a serious buyer.

---

### CTO — Early-Stage Startup

**Who:** Technical lead of a startup with three to twenty engineers.
Responsible for architecture, quality, and technical due diligence.

**What they expect from the Workspace:**
Portfolio visibility. Governance control. Human gate management.
They want to know: "Which of my projects is ready for the enterprise deal?
Which one needs work before the audit in three weeks?"

The Workspace must give them a portfolio view that answers these questions
without having to open every project.

**What they value most:**
The investor demo surface. The evidence export. The sovereignty progression timeline.
These are the artifacts that make or break a deal.

---

### Software Architect

**Who:** Principal or staff engineer responsible for architecture decisions.
Often inheriting a project or reviewing a migration plan.

**What they expect from the Workspace:**
Depth. The Architecture Explorer. The Decision log. The evidence chain.

They want to validate: "Is the documented architecture accurate?
Do the decisions make sense given what the code actually does?
Is the migration plan technically sound?"

The Workspace must give them tools to interrogate the system deeply —
not just see its surface.

**What they do not need:**
Simplified summaries. The architect tolerates complexity;
what they cannot tolerate is inaccuracy.

---

### Engineering Manager

**Who:** Manages a team of three to ten engineers.
Responsible for process, code quality, and governance adoption.

**What they expect from the Workspace:**
Review queue management. Governance document status.
Human gate tracking. Stage progress per project.

The Engineering Manager is the person who processes the most human gates.
The Workspace must make their review work efficient:
clear queue, clear context for each gate, clear approval path.

**What they value most:**
The Human Gates View. The Governance Center. The Recovery Center.

---

### DSI (Direction des Systèmes d'Information)

**Who:** Senior executive responsible for IT systems at a large organization.
May not be technical but is accountable for system risk, compliance, and sovereignty.

**What they expect from the Workspace:**
Portfolio sovereignty status at a glance.
Evidence they can show to auditors.
A clear answer to: "What systems are sovereign? What is our exposure?"

The DSI does not run commands. The DSI makes decisions based on what they see.
The Workspace must present sovereignty posture clearly, without requiring
technical knowledge to interpret it.

**What they value most:**
The Portfolio Overview. The Evidence export. The Sovereignty progression timeline.
The answer to: "Can I show this to a regulator?"

---

### Public Institution

**Who:** Technology director or IT lead at a government agency, municipality,
or public institution. Building or inheriting digital public infrastructure.

**What they expect from the Workspace:**
Compliance documentation. Data residency proof. Exit strategy evidence.
Sovereignty Level 4 or 5 visibility and documentation.

Public institutions often work under specific regulations: data must not leave the country,
specific infrastructure must be used, every change must be audited.

The Workspace must make these requirements visible and demonstrable.
"Here is our sovereignty posture. Here is the evidence. Here is the exit strategy."

**What they value most:**
Regulatory-grade audit trails. Sovereignty documentation. Evidence exports.
The ability to say: "We can demonstrate compliance."

---

### Consulting Firm

**Who:** Agency or independent contractor managing multiple client projects.
Often inheriting AI-generated projects from clients who used Lovable or Bolt.

**What they expect from the Workspace:**
Multi-client portfolio management. Quick project onboarding.
Evidence generation for client reports. Governance baseline in under an hour.

A consulting firm charges for governance work. The Workspace must make
governance work fast, evidence-rich, and professionally presentable.

**What they value most:**
The Portfolio Overview (across clients). The Evidence Explorer.
The Recovery Center (to show clients their project's progress).
The time-to-first-governance-PR metric.

---

## 10. The UX Principles

These are non-negotiable. They apply to every view, every action, every decision
in the design of the AEOS Workspace.

### Evidence First

Never show a claim without evidence.
If a project's sovereignty is Level 3, show what makes it Level 3.
If a risk is classified as critical, show what finding produced that classification.

The pilot must always be able to ask "why?" and get an answer that references
a real artifact — a file, a commit, a test result, a human approval.

### Human Always in Control

Nothing happens without explicit pilot action.
No background task. No silent migration. No auto-approved gate.

The cockpit can propose. The cockpit can highlight. The cockpit can recommend.
The cockpit cannot act.

### Explain Before Acting

Every action that produces a consequence must first explain what will happen.
"Running this audit will create a MemoryRecord for this project."
"Approving this gate will allow the agent to generate the governance PR."

The explanation is not a warning. It is information the pilot needs to act with confidence.

### Every Decision is Traceable

Every approval, every rejection, every configuration change is recorded.
The pilot must be able to say: "Who approved this? When? What context did they have?"

Traceability is not surveillance. It is the foundation of accountability.

### Local First

By default, no data leaves the machine.
Memory is local. Evidence is local. Architecture is local. Decisions are local.

If something is shared — an evidence export, a frontier AI call, a governance document
sent to a client — the pilot knows it, approves it, and the action is recorded.

### Progressive Disclosure

The Portfolio Overview shows the minimum needed.
The Project Workspace shows more.
The Evidence Explorer shows everything.

The pilot controls depth. The Workspace does not overwhelm at the surface
and does not hide complexity when it is needed.

### Zero Hidden Automation

If AEOS did something, it is visible.
If an agent proposed something, it is visible.
If a policy was applied, it is visible.
If data was routed to frontier AI, it is visible.

There are no invisible processes. The cockpit is always honest about what happened.

### Propose, Never Impose

AEOS generates proposals. Humans generate decisions.

The agent generates an architecture draft. The pilot reviews and approves.
AEOS generates a migration plan. The pilot validates and authorizes.
AEOS classifies a risk as critical. The pilot decides how to respond.

Proposing is not weakening. It is the architecture of trust.

### Context Carries

Every session knows what the previous session established.
Memory makes each interaction richer than the last.

The pilot should never have to re-explain what they know.
The Workspace should never forget what has been validated.

### Confidence Builds Gradually

The first audit produces discoveries. Discoveries produce risks.
Risks produce a recovery plan. The plan produces governance.
Governance produces evidence. Evidence produces trust.

The Workspace does not claim trust before it is earned.
It builds confidence incrementally — through evidence, through approval,
through progress measured against declared stages.

---

## 11. What the Workspace Must Never Become

### Not Jira

Jira manages tasks. AEOS governs software.

A task is ephemeral. It is created, assigned, completed, forgotten.
An engineering decision is permanent. It is made, recorded, referenced, and evolved.

The Workspace does not have sprints, backlogs, or velocity metrics.
It has stages, evidence, and sovereignty progression.

If the Workspace begins to look like a task manager,
something has gone wrong in its design.

### Not GitHub

GitHub hosts and versions code. AEOS governs the engineering posture above the code.

The Workspace does not show diffs. It does not show pull request discussions.
It does not show commit histories or file trees.

It shows what the team has agreed to understand about the code —
the Architecture, the Decisions, the Governance, the Sovereignty.

If the Workspace begins to look like a code repository viewer,
it has confused the implementation with the governance layer.

### Not an IDE

An IDE is where code is written. The Workspace is where software is governed.

The Workspace does not have a code editor.
It does not have syntax highlighting, autocomplete, or debugging tools.

If a pilot feels they need to write code inside the Workspace,
they should open their editor. The Workspace is not a replacement for engineering tools.
It is the surface above them.

### Not a KPI Dashboard

KPI dashboards show metrics that feel important but measure nothing real.

"52 tests passing." "98% coverage." "7 open PRs." "Code quality: A+"

These are real measurements in the right context. They are not governance.

The Workspace does not show vanity metrics.
It shows posture: sovereign or exposed, governed or fragile, ready or blocked.

If the Workspace begins to accumulate numbers without engineering meaning,
something has gone wrong.

### Not a Chatbot

The Workspace is not a conversational interface.
The pilot does not chat with AEOS. The pilot governs with AEOS.

There is a role for natural language in AEOS — in agent interactions,
in asking questions about a project, in generating proposals.

But the Workspace itself is not a chat window.
The cockpit is not a chat window.

If the primary mode of interaction in the Workspace is typing messages,
the cockpit metaphor has been abandoned.

### Not a DevOps Console

The Workspace is not Kubernetes Dashboard. It is not Grafana. It is not Datadog.

It does not show CPU usage, memory consumption, request latency, or deployment logs.
These are operational concerns, not governance concerns.

Operations Engine data may inform the Workspace — sovereignty drift,
quality gate failures — but the Workspace is not an infrastructure monitoring tool.

If the Workspace starts showing deployment pipelines or server metrics,
it has confused engineering governance with infrastructure operations.

### Not a Wizard

A wizard asks "what do you want to do?" and leads the pilot through predefined steps.

AEOS does not ask where the pilot wants to go.
AEOS shows them where they are — and lets them decide.

The pilot may be at stage_0 because they want to be.
The pilot may be at sovereignty Level 1 because it is the right choice for their context.
The pilot may have accepted a risk that a wizard would flag as "must fix."

AEOS governs. It does not prescribe.

If the Workspace begins to tell the pilot what they should do
without reference to their stated goals and policies,
it has become paternalistic — and paternalism is the death of sovereignty.

### Not a Replacement for Engineering Judgment

The Workspace amplifies judgment. It does not replace it.

Every insight the Workspace surfaces exists to help the pilot make a better decision.
Not to make the decision for them.

If the Workspace is making engineering decisions autonomously —
even small ones, even "obviously right" ones —
it has crossed a line that must not be crossed.

The Constitution says it plainly: "AI may assist, recommend, analyze, generate, or verify.
It shall never own accountability."

The Workspace must enforce this doctrine, not quietly undermine it.

---

## 12. The AEOS Cockpit

### The metaphor, taken seriously

A modern aircraft cockpit is designed around one principle:
give the pilot an accurate picture of reality, the controls to change it,
and enough time to make decisions.

Not: show the pilot what they want to see.
Not: automate the difficult decisions.
Not: create work that does not need to exist.

An accurate picture. The controls. Enough time.

This is exactly what the AEOS Workspace aspires to.

### What it means to pilot software

A pilot does not fly the aircraft by checking dashboards.
A pilot flies by maintaining awareness, making decisions, and executing them precisely.

In AEOS terms:

**Awareness** is knowing the sovereignty posture of every project,
the open human gates, the critical risks, and the progress through recovery stages.

**Decision** is approving a governance proposal, authorizing a migration plan,
configuring an AI routing policy, or accepting a risk with documented rationale.

**Execution** is the result of a human decision — an approved PR merged,
a stage marked complete, a migration authorized, an agent action confirmed.

The Workspace makes awareness possible.
It presents decisions clearly.
It records execution with evidence.

### The system is living

A software project under AEOS governance is not a static artifact.
It changes. It audits run. Memory accumulates. Sovereignty shifts.
Risks emerge. Human gates open. Agents propose. Stages advance.

The Workspace reflects a living system.

This means the Portfolio Overview is never the same twice.
This means the pilot must check it regularly to remain oriented.
This means the Workspace is not something you set up and forget —
it is something you use to pilot a system that never stops moving.

### The relationship between the pilot and the system

The pilot controls the system through deliberate action.
The system reports to the pilot through honest instruments.
The agents assist the pilot under human-gated boundaries.
The memory accumulates so the pilot can build on what was validated.

This is the cockpit.

No silent action. No hidden state. No autonomous execution.
Every instrument is honest. Every control requires intent. Every action leaves evidence.

The pilot who uses the AEOS Workspace does not ask:
"What did the AI do while I was away?"
They ask: "What happened while I was away?"

And the Workspace answers: exactly this, proven by this evidence, approved by this person.

### Why this matters beyond UX

The cockpit doctrine is not a UX preference.
It is a philosophical position about the relationship between humans and AI systems.

AEOS is built on the belief that AI must augment engineering judgment,
not replace it. That sovereignty is a right, not a compliance checkbox.
That accountability cannot be delegated, no matter how good the AI becomes.

The Workspace is where these beliefs become daily practice.

Every human gate that appears in the Workspace says: "This matters. You decide."
Every evidence requirement that must be confirmed says: "Prove it. Don't assume."
Every sovereignty level that is displayed says: "This is real. Not aspirational."

The cockpit makes philosophy concrete.

---

## 13. Vision at Five Years

### When all the engines are present

In five years, AEOS is a complete engineering operating system.

Every capability is live: Discover · Assess · Recover · Transform · Continue ·
Govern · Operate · Learn.

Every engine is production-ready: Discovery · Assessment · Recovery ·
Transformation · Continuation · Governance · Operations · Memory · Evidence · AI Routing.

The Workspace reflects all of them — not as a feature catalog,
but as a coherent system that the pilot navigates fluently.

### What the pilot sees

They open the Workspace and see their portfolio.
Fifty projects. Some sovereign. Some in recovery. Some operating.
Some being built from scratch with AEOS scaffolding.
Some legacies being modernized. Some in active migration.

They scan the Portfolio Overview in ten seconds:
two open human gates. One critical risk on Project F. Project B is at sovereignty Level 4.
Project G just completed stage_7 migration readiness.

They spend the next thirty minutes on decisions:
approve the governance PR for Project A, review the migration plan for Project D,
configure the AI routing policy for the new project added last week.

Then they close the Workspace and go to their engineering work.
The system continues. Memory accumulates. Agents assist within their bounds.
The next morning, the pilot returns and the Workspace shows exactly what happened.

### Recover

In five years, Recovery is the standard onboarding path for any new project:
AI-generated, legacy, or inherited. Every project that enters AEOS governance
goes through the recovery arc. Every stage has evidence. Every completion is validated.

The pilot does not manage recovery manually. They govern it.
They see the progress. They approve the stages. They validate the evidence.
The Recovery Center becomes the standard tool for any organization
that needs to demonstrate that its software systems are under engineering control.

### Govern

In five years, Governance is not a startup practice — it is a standard.

Organizations that adopt AEOS Standards have a common vocabulary
for what it means for a software project to be governed.
The AEOS Constitution is recognized as a reference document
for software engineering governance, like ISO 27001 for information security.

The Workspace makes compliance with AEOS Standards visible and verifiable.
A project that meets all seven governance requirements shows a green governance status.
An auditor can ask: "Show me your AEOS governance status" and the pilot exports
the evidence report in under a minute.

### Migrate

In five years, Migration is fully automated within human-gated boundaries.

The Migration Center shows not just the plan but the execution:
step by step, with real-time evidence, backup confirmation, and rollback availability.

The pilot approves the start. AEOS executes under full visibility.
The pilot can halt at any point. The rollback is always ready.

Migration is no longer the terrifying event it was before AEOS.
It is a governed, evidenced, reversible process — executed by the system
under the authority of the pilot.

### Continue

In five years, Continue is the standard development workflow
for any team that values sovereignty.

Local AI handles 80-90% of routine engineering tasks.
Frontier AI is explicitly authorized for complex reasoning.
Every AI contribution is proposed as a PR, reviewed by a human, and merged with intention.

The AI Collaboration View shows the full picture:
what was done locally, what went to frontier, what was approved, what was modified.

No team using AEOS can say "we don't know what the AI did."
They always know. They always approved.

### Own

Ownership is the destination.

In five years, a project that has been through the full AEOS arc —
recovery, governance, migration, continuation — has reached a state that was once
only achievable by the largest engineering teams:

It can be understood by anyone on the team.
It can be transferred without knowledge loss.
It can be audited by any serious buyer.
It can be maintained without external dependency.
It can be evolved with AI at near-zero marginal cost.
It can survive the departure of its original team.

This is what AEOS means by sovereignty. Not a flag. A state.

### Agents

In five years, Agents are the execution layer of the Workspace.

Every major capability is backed by a specialized agent:
Discovery Agent, Architecture Agent, Planning Agent, Database Agent,
Backend Agent, Security Agent, DevOps Agent, Evidence Agent.

Agents do not act autonomously. They act under human gates.
But what they accomplish within those gates is extraordinary:
a complete architecture review in minutes, a migration plan in hours,
a governance baseline in a day.

The Workspace makes agent coordination visible:
which agent is working on what, what it has proposed, what awaits approval.

The pilot governs the agents. The agents accelerate the work.
The Workspace makes both possible.

### Workspace

In five years, the Workspace is the product.

The CLI remains the authoritative interface — the engine room, not the bridge.
The Workspace is the bridge: where the pilot governs the entire system.

The Workspace is available on any device, locally hosted by default,
with optional team collaboration for organizations that want it.

It is the interface through which a solo founder, a CTO, a DSI, and a government
technology director all access the same engineering operating system —
each from their own perspective, each with their own portfolio,
each with the same fundamental guarantee: they are in control.

### Memory

In five years, Memory is the most valuable artifact in the Workspace.

Every project has a complete, validated history:
every audit, every decision, every agent action, every human approval.

Memory makes knowledge transferable.
A new team member joins and reads the Timeline for their project:
not just what the code does, but why every significant decision was made,
what risks were accepted, what migrations were planned, what sovereignty was achieved.

Memory makes AEOS irreplaceable — not through lock-in,
but because the accumulated knowledge is genuinely valuable
and exists nowhere else.

### Transformation

In five years, Transformation handles the most complex scenarios:
legacy monolith modernization, full stack migration, architecture evolution.

The Workspace coordinates multi-step transformations across months,
maintaining the evidence trail through every phase,
surfacing the human gates at each decision point.

A transformation that previously required a consulting firm and six months
can be planned, governed, and executed by a team of three in six weeks —
with full evidence, full rollback capability, and full sovereignty.

### Operations

In five years, Operations is the continuous governance layer.

Sovereignty drift is detected automatically and surfaced in the Workspace.
Quality gates are monitored and anomalies are reported.
Periodic audit reports are generated and presented for human review.

The pilot does not manage operations manually. They govern it.
They see what changed. They review what AEOS flagged. They approve the response.

The system operates. The pilot governs. This is the AEOS model.

### Certification

In five years, AEOS introduces software certification.

A project that meets all AEOS Standards and maintains its governance posture
can carry the AEOS Compliant designation — a verifiable signal
that the project meets a defined engineering governance standard.

This is not a marketing badge. It is a verifiable claim:
specific governance documents present and validated,
specific sovereignty posture documented and auditable,
specific quality gates passing on specific dates.

The Workspace generates the certification evidence.
The certification is renewed through continuous compliance.

This is the trajectory from a product to a standard.

### Ecosystem

In five years, AEOS is not just a product. It is an ecosystem.

Third-party Standards and Playbooks extend the AEOS governance model
for specific industries: finance, healthcare, government, defense.

Tools integrate with the AEOS Memory layer: IDE extensions,
CI pipelines, code review tools that produce AEOS-compatible evidence.

Organizations share Playbooks and Standards across the ecosystem —
making the accumulated governance knowledge of the AEOS community
available to every team that adopts it.

The Workspace is the surface through which the ecosystem is navigated:
discovering community Standards, adopting Playbooks, contributing evidence patterns.

This is the final vision:

Not a product that governs software.
A platform on which the engineering governance of software is built.

---

## Closing Statement

The AEOS Workspace will be built over years.
It will be designed, iterated, challenged, and improved.

But the philosophy expressed in this document does not iterate.

The cockpit metaphor endures.
The pilot is always in control.
Evidence precedes claims.
Every action leaves a trace.
Sovereignty is measured, not assumed.
AI assists, humans decide.

These are not design preferences.
They are the constitutional commitments of AEOS
made visible in a product interface.

The Workspace will change. These principles will not.

---

*This document was written before any wireframe, mockup, or prototype existed.
It is the foundation from which the Workspace will be built.*

*AEOS Workspace Vision — v1.0.0 — 2026-07-01*
