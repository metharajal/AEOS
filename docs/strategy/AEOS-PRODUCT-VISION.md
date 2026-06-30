# AEOS Product Vision

**Date:** 2026-06-27
**Status:** Strategic — Living Document
**Version:** 0.2

---

## 0. What AEOS Is

**AEOS — AI Engineering Operating System**

AEOS is a **local-first, open-source-first, AI-local-first** agentic engineering system for creating, reclaiming, modernizing, migrating, evolving, and operating digital products with AI.

AEOS transforms an idea, a prototype, an AI-generated project, a monolithic application, or a legacy system into software that is mastered, auditable, portable, maintainable, secure, and sovereign.

AEOS is not only a code generator.
AEOS is not only an audit tool.
AEOS is not only a migration tool.
AEOS is not only an AI development assistant.

AEOS is a layer of technical, architectural, operational, and sovereign mastery above AI tools, no-code, low-code, cloud platforms, open source, and legacy systems.

---

## 0.1 Local-First, Open-Source-First, AI-Local-First Doctrine

### Local-first by default

AEOS must not send code, secrets, `.env` files, business data, database schemas, migration files, logs, or sensitive architecture details to external services by default.

Every AEOS operation runs locally first:

- local repository analysis
- local dependency scanning
- local security and sovereignty checks
- local test execution
- local report generation
- local branch-based execution
- local documentation generation

### Open-source-first

AEOS prefers portable and inspectable building blocks:

- **Database**: PostgreSQL
- **Containerization**: Docker, Docker Compose, Kubernetes when necessary
- **Backend**: FastAPI, Django, NestJS, Spring, Laravel or equivalent open frameworks
- **Identity**: Keycloak, Ory, Authentik or equivalent open-source identity systems
- **Storage**: MinIO or S3-compatible open storage
- **Data layer**: Directus, Hasura, PostgREST, Appwrite or equivalent open-source layers
- **Observability**: open stacks (Prometheus, Grafana, Loki, OpenTelemetry)
- **CI/CD**: portable pipelines (GitHub Actions, GitLab CI, Forgejo, Woodpecker)

AEOS can use cloud providers, but must always document:
- the dependency introduced
- the available open-source alternative
- the lock-in level
- the exit cost
- the sovereignty level achieved

### AI-local-first

AEOS uses local AI models for:
- routine analysis and classification
- planning and decomposition
- documentation generation
- safe refactoring
- code explanation and review

AEOS avoids frontier AI by default.

Frontier AI is used only when:
- local AI is demonstrably insufficient for the task
- the engineer has explicitly authorized the call
- the context has been stripped of secrets and sensitive data
- the output will be verified locally after generation

**Strategic sentence:**

> Local AI by default.
> Frontier AI by exception.
> Human approval for sensitive operations.

---

## 1. Core Thesis

The explosion of AI code generation tools has made it easier than ever to start a digital product. But starting fast and owning what you built are not the same thing.

AEOS exists at the intersection of four forces:
- **AI generates code faster than teams can govern it.**
- **Hosted platforms capture the stack behind every generated project.**
- **Local AI is now capable enough to handle most engineering tasks at near-zero marginal cost.**
- **Organizations with legacy systems have no structured path to modernize safely without vendor capture.**

AEOS is the engineering operating system that bridges all four: it helps you create, reclaim, modernize, migrate, evolve, and operate software products built with AI or inherited from the past — while keeping control of the code, the data, the infrastructure, the models, the costs, and the sovereignty.

**Strategic phrase:**

> Lovable creates fast.
> AEOS governs, reclaims, modernizes, migrates, and operates durably.

**Central phrases — AEOS identity:**

> Lovable is a use case. Reclaim is a rail. AEOS is the full engineering operating system.

> AEOS Core guarantees. AEOS Agents reason. AEOS Memory learns. Humans validate.

---

## Founder Problem Statement

AEOS is born from a concrete problem: building fast with AI is now easy, but owning, evolving, securing, and selling those products as serious software remains difficult.

*AEOS est né d'un problème concret : créer vite avec l'IA est devenu facile, mais posséder, faire évoluer, sécuriser et vendre ces projets comme de vrais produits logiciels reste difficile.*

---

The founder of AEOS is its first target user.

He has built several projects using AI-assisted and no-code web tools. Each time, the starting experience was fast and encouraging. But as projects matured, a recurring set of problems emerged:

**Cost dependency.** Continuing to evolve a project through a frontier AI platform or a web builder means paying per iteration, per feature, per fix. The cost is manageable at the beginning. It becomes a constraint as the product grows.

**Platform capture.** The project lives on Supabase. The auth is managed by an external service. The deployment is tied to Vercel. The data is on infrastructure the founder does not control. Replacing any one of these requires significant re-engineering.

**The serious client question.** When a bank, a government institution, a large enterprise, or a regulated organization asks the following questions, there is no clean answer:

- Where is the data stored?
- Who controls the infrastructure?
- Can this be self-hosted on our own servers?
- Can we exit Supabase or Vercel if needed?
- How can we maintain this without depending on an external AI platform?
- Can you guarantee no data leaves our perimeter?

These are not edge-case questions. They are the standard due diligence of any serious buyer — especially in financial services, public administration, healthcare, and enterprise in markets like Senegal and across Africa where digital sovereignty is both a regulatory and a trust requirement.

**The industrialization gap.** A project built fast is not the same as a project built right. Without tests, without CI, without documentation, without a governance structure, without portability — a fast project is a prototype, not a product. The gap between the two is where most AI-generated projects get stuck.

**The personal cost ceiling.** Continuing to develop on frontier AI platforms indefinitely is not economically viable for independent builders and small teams. Local open-weight models are now capable enough to handle most engineering tasks. But using them requires a structure — a workflow, a routing layer, a governance model — that does not yet exist in a usable form.

---

### The conclusion that led to AEOS

> "I built fast. Now I need to own, master, and industrialize."

This is the founding sentence of AEOS. It defines the product paths that mirror the actual trajectory of a builder — and of an organization:

- **Create** the next project right, with sovereignty and quality from the first commit.
- **Reclaim** existing AI-generated projects: audit, harden, and migrate projects already built with Lovable, Bolt, Replit, Supabase, or similar tools.
- **Modernize** legacy monolithic applications: understand, map, and progressively transform systems that were never built to last.
- **Migrate** toward a target architecture: move from Lovable Cloud to self-hosted, from Firebase to PostgreSQL, from monolith to modular, with controlled agents, tests, and rollback.
- **Evolve** locally with low token dependency: continue developing with local AI models, at near-zero marginal cost.
- **Operate** continuously: audit, secure, optimize, and document the product over time.

AEOS is not a theoretical framework. It is the tool the founder needed and could not find.

AEOS helps create, reclaim, modernize, migrate, evolve, and operate digital products with AI — while keeping technical, economic, and sovereign control.

---

## 2. The Problem

### 2.1 The generation trap

Tools like Lovable, Bolt, Replit, and Cursor let anyone produce a working application in minutes. This is genuinely transformative. But the speed of creation masks a set of structural risks:

**Platform lock-in by default.** A Lovable project ships with Supabase for the database, Supabase Auth for authentication, Supabase Storage for files, and Vercel for hosting. None of these choices are made consciously by the user. They are embedded in the generated scaffold.

**Token cost accumulation.** Every iteration, every feature request, every bug fix through a frontier AI platform costs tokens. For early-stage projects this is manageable. For teams iterating daily on a maturing product, the cost compounds. There is no incentive for the platform to reduce that cost — it is the business model.

**Loss of architectural control.** Generated code is opinionated. The architecture, the data model, the auth flow, and the deployment target are decided by the generator, not the builder. When the product evolves, the team inherits decisions they did not make and cannot easily undo.

**Portability gap.** Most AI-generated projects cannot be cloned to a new machine, set up locally, or deployed to a different provider without significant effort. There is no `docker-compose.yml`, no migration scripts, no `.env.example`, no Dockerfile.

**Security and compliance blindness.** Generated projects rarely include secret scanning, dependency auditing, or supply chain verification. A team shipping fast with Lovable has no native way to know if they committed an API key or if their dependencies have CVEs.

**Industrialization barrier.** Moving from a prototype to a maintainable, testable, governable product is difficult when the starting point is an AI-generated scaffold with no tests, no CI, no documentation conventions, and no quality gates.

### 2.2 The sovereignty gap

Even teams who build from scratch face a version of this problem:
- They reach for Supabase because it is fast, not because it is sovereign.
- They use Clerk because it is easy, not because they own the auth data.
- They deploy to Vercel because the DX is smooth, not because they control the infrastructure.

Each of these choices is individually defensible. Collectively, they create a stack where the team owns the product name but not the product.

### 2.3 The local AI opportunity

In 2024–2025, local open-weight models crossed a practical threshold. A 7B–14B parameter model running on a MacBook can handle:
- Explaining code
- Writing unit tests
- Refactoring functions
- Generating documentation
- Reviewing diffs
- Answering engineering questions

This means 80–90% of daily engineering assistance tasks can be done locally, at zero marginal cost per token, with no data leaving the machine. The remaining 10–20% — complex reasoning, large context, frontier-class tasks — can be selectively routed to frontier providers, with human approval.

No existing tool makes this routing decision explicit, auditable, and configurable.

### 2.4 The legacy and monolith problem

Many organizations — especially in Africa and in regulated markets globally — are not building fast with AI. They are in a different and older problem: a system that runs the business, that nobody fully understands, that costs more every year to maintain, and that every consultant recommends migrating to AWS or Azure — without explaining why, or what that actually changes.

**The monolith trap.** A legacy application is often a monolith: years of undocumented business logic, tightly coupled modules, no tests, no separation of concerns, a dependency chain that only one or two people understand.

**The lift-and-shift illusion.** Moving to cloud without changing architecture solves exactly one problem (hardware maintenance) while making everything else worse: more expensive, still monolithic, still undocumented, now dependent on a foreign cloud vendor.

**The cost blindspot.** Organizations with legacy systems rarely know the real cost: developer time, maintenance, opportunity cost of features not shipped, risk cost of the system failing.

---

## 3. The Five AEOS Use Cases

---

### A. New Build — Create a new project correctly

> Start clean. Build right. Own everything from day one.

For founders, freelancers, and teams who want to build a digital product with AI assistance and maintain full engineering control from the first commit.

**What AEOS provides:**

- **Project scaffold** with explicit architecture: source layout, test structure, CI pipeline, documentation conventions, governance directory.
- **Conscious stack choices**: database, auth, storage, and hosting are explicit decisions, not embedded defaults.
- **Quality gates from day one**: ruff, mypy, pytest, and sovereignty check are wired into the CI pipeline before the first feature is written.
- **Local-first AI assistance**: `aeos ai ask` routes engineering questions to a local model by default. Frontier is opt-in, with human approval.
- **Sovereignty by design**: no Supabase dependency, no Vercel lock-in, no secret exposure — enforced by `aeos sovereignty check` in CI.

**Examples:**
GovTech · mairie digitale · SaaS FinOps · CRM métier · portail citoyen · application bancaire · plateforme interne · outil administratif

**Future commands:**

```
aeos new <project> --type saas        # scaffold a full-stack sovereign project
aeos blueprint create                  # generate architecture blueprint
aeos architecture plan                 # propose stack (db/auth/storage/hosting)
aeos quality                           # run all quality gates
aeos sovereignty check                 # verify no external lock-in
aeos ai ask "How should I model users in this schema?"
```

**Outcome:** A project that can be moved to any machine, deployed to any provider, and maintained by any engineer — without depending on the platform that generated it.

---

### B. Reclaim — Reclaim a project generated elsewhere

> You built fast. Now build right.

For teams who used Lovable, Bolt, Replit, Cursor, or similar tools and now face the consequences: a working prototype with no architecture, no tests, no portability, and a stack they did not choose.

**What AEOS provides:**

- **Generator detection**: identify Lovable, Bolt, Replit, and similar tools from repository signals.
- **Provider dependency map**: understand exactly what the project depends on, at which layer (database, auth, storage, hosting, AI, MCP).
- **Control map**: what is controlled, what is external, what is inferred, what is missing.
- **Risk classification**: findings are categorized by severity (OK / WARNING / ERROR) with concrete recommendations.
- **Exit options**: always five paths, from securing in place to full sovereign rebuild.
- **Portability hardening**: identify missing Dockerfile, missing migrations, missing `.env.example`.
- **Security sweep**: detect committed secrets, vulnerable dependencies.

**Commands:**

```
aeos reclaim inspect --path <project>       # read-only intelligence report
aeos reclaim plan --path <project>          # structured exit roadmap (future)
aeos supabase check --path <project>        # Supabase-specific audit
aeos security check --path <project>        # secret and security scan
aeos sovereignty check --path <project>     # external dependency audit
aeos report --path <project>                # full aggregated report
```

**Outcome:** A Lovable or Bolt project that can be understood, maintained, migrated, and deployed without the originating platform — transformed into a governable engineering asset.

---

### C. Modernize — Modernize monolithic and legacy applications

> You did not build with AI. You inherited something that was never built to last.

For organizations — enterprises, public institutions, SMEs — that have existing monolithic applications they need to understand, maintain, modernize, or migrate, without being captured by a cloud migration vendor.

**What AEOS provides:**

- **Legacy inspection**: `aeos modernize inspect` scans the project structure, detects languages, frameworks, database connectors, and external dependencies.
- **Dependency mapping**: `aeos modernize map` generates a structured map of the application's layers — what calls what, what depends on what.
- **Modernization planning**: `aeos modernize plan` generates a progressive roadmap for breaking the monolith — without requiring a full rewrite.
- **Migration readiness**: `aeos modernize readiness` assesses whether the application is ready for container-based or cloud deployment.
- **Containerization plan**: guide toward Docker/Kubernetes progressively.
- **FinOps alignment**: identify cost optimization opportunities — unused dependencies, over-provisioned services, unmetered external calls.

**The AEOS principle on this path:**

> Audit first. Understand before you move. Recommend before you automate.

AEOS does not rewrite the application. It does not apply automatic migrations. It does not make architecture decisions autonomously. It gives the team the visibility they need to make those decisions with evidence.

**Important:** AEOS does not automatically recommend microservices. It recommends the right strategy:
- Keep the monolith but secure it
- Modularize progressively
- Containerize
- Extract certain modules
- Expose APIs
- Migrate progressively
- Rebuild only when necessary

**Future commands:**

```
aeos modernize inspect --path ./legacy-app      # inspect legacy project structure
aeos modernize map --path ./legacy-app          # generate dependency map
aeos modernize plan --path ./legacy-app         # step-by-step modernization roadmap
aeos modernize readiness --path ./legacy-app    # assess readiness for container/cloud
aeos modernize extract-module --name billing    # extract a specific module
aeos modernize containerize --path ./legacy-app # containerization plan
aeos cloud-cost check --path ./legacy-app       # estimate structural cost of lift-and-shift
aeos finops check --path ./legacy-app           # identify cost optimization opportunities
```

**The organizations this path serves:**

- A government agency running a monolithic Java application built in 2008, maintained by a single vendor, with no documentation and no tests.
- A bank whose core banking system is a decade-old PHP monolith running on physical servers, never containerized.
- An NGO with a donor management system built in Access and VBA, with no exit plan and no one who understands the full data model.
- A telecoms operator whose internal operations portal is a mix of Perl scripts, Oracle procedures, and undocumented APIs.

None of these organizations need more AI features. They need clarity, structure, and a progressive path forward they can execute with their own teams.

**Outcome:** An organization that understands what it has, knows what it costs, and has a clear phased roadmap to modernize — without a big-bang rewrite, without vendor capture, and without losing the business logic that makes their system work.

---

### D. Migrate — Migrate toward a target architecture

> You know where you are. AEOS helps you get where you need to be.

For teams who need to move from one architecture to another — from Lovable Cloud to self-hosted, from Firebase to PostgreSQL, from monolith to modular — with controlled agents, tests, and rollback.

**What AEOS provides:**

- **Migration plan**: structured, phased plan from current state to target architecture.
- **Branch-based execution**: all migration work happens in isolated branches, never directly on production.
- **Test-first approach**: no migration step executes without passing tests.
- **Evidence report**: every migration action is logged, documented, and auditable.
- **Rollback readiness**: every destructive step has a defined rollback path.
- **Multi-target support**: Supabase Cloud → self-hosted, Firebase → PostgreSQL, Vercel → VPS, monolith → modular, on-premise → container/cloud.

**Migration examples:**
- Lovable Cloud → own Supabase Cloud project
- Lovable Cloud → self-hosted Supabase
- Lovable Cloud → PostgreSQL + FastAPI / NestJS / Django
- Supabase → pure PostgreSQL
- Firebase → PostgreSQL
- Vercel → Cloudflare / VPS / Kubernetes / sovereign cloud
- On-premise monolith → Docker / Kubernetes
- Legacy → modular architecture

**Future commands:**

```
aeos migrate --from lovable --to postgres-open-backend --path <project>
aeos migrate --from monolith --to modular-architecture --path ./legacy-app
aeos migrate --to sovereign-stack --mode agentic
aeos migrate plan --path <project>          # generate migration plan (read-only)
aeos migrate execute --step 1 --branch      # execute one step in isolated branch
aeos migrate test --step 1                  # run tests for migration step
aeos migrate report --path <project>        # evidence report
aeos migrate rollback --step 1              # rollback one migration step
```

**Outcome:** A controlled, tested, documented migration from the current architecture to the target — without breaking production, with evidence at every step.

---

### E. Evolve / Operate — Evolve and control over time

> Build with AI without accumulating invisible debt.

For teams who want to continue evolving their product continuously, at near-zero token cost, with frontier AI reserved for the tasks that genuinely require it — and with full control over time.

**What AEOS provides:**

- **Local-first routing**: `aeos ai ask` defaults to the configured local model. Frontier is only called when explicitly requested.
- **Human approval gates**: `require_human_approval = true` ensures no silent frontier fallback.
- **Continuous audit**: periodic sovereignty, security, and quality checks integrated into CI.
- **Drift detection**: AEOS detects when a project drifts from its target architecture.
- **Feature evolution**: add features, refactor, reduce debt, improve security, reduce costs, replace providers.
- **Periodic reports**: `aeos operate report` produces a full audit report at any point.

**Cost structure this enables:**

| Task | Without AEOS | With AEOS |
|------|-------------|-----------|
| Explain this function | Frontier ($) | Local (free) |
| Write unit test | Frontier ($) | Local (free) |
| Refactor module | Frontier ($) | Local (free) |
| Review diff | Frontier ($) | Local (free) |
| Architect new feature | Frontier ($) | Frontier (human-approved) |
| Debug complex regression | Frontier ($) | Frontier (human-approved) |

**Commands:**

```
aeos ai ask "Write a test for this function"     # local by default
aeos ai ask "..." --provider frontier            # explicit frontier
aeos evolve --task "add citizen complaint workflow"
aeos operate check                               # full sovereignty + security audit
aeos operate report                              # periodic report
aeos agent run --local "add pagination to API"   # sandboxed local coding agent
aeos model list                                  # browse sovereign model catalog
```

**Outcome:** A team that can iterate continuously, at near-zero token cost, with frontier AI reserved for the genuinely complex tasks — and with full transparency about when frontier is used.

---

## 4. The Six AEOS Modes

AEOS is organized around six primary modes, each corresponding to a phase in the lifecycle of a digital product:

| Mode | Command | Purpose |
|------|---------|---------|
| **New Build** | `aeos new` | Create a new project correctly from the first commit |
| **Reclaim** | `aeos reclaim` | Reclaim a project generated elsewhere |
| **Modernize** | `aeos modernize` | Modernize a monolithic or legacy application |
| **Migrate** | `aeos migrate` | Migrate toward a target architecture |
| **Evolve** | `aeos evolve` | Evolve a product with AI assistance |
| **Operate** | `aeos operate` | Supervise, audit, secure, and optimize over time |

These six modes cover the complete lifecycle of a digital product — from first commit to long-term operation — under engineering control.

---

## 5. The Agentic Core

AEOS is designed to work with specialized agents. Each agent has a defined scope, reads before it writes, and never acts without human approval on destructive operations.

**Discovery Agent**
Analyzes repo, files, dependencies, providers, architecture, risks.

**Architecture Agent**
Proposes target architecture based on current state and constraints.

**Planning Agent**
Breaks work into safe, reversible, testable steps.

**Database Agent**
Analyzes schemas, migrations, RLS, exports, imports, seeds.

**Backend Agent**
Migrates or reconstructs APIs, services, edge functions, background jobs.

**Frontend Agent**
Adapts the interface to new backends and APIs.

**Legacy Agent**
Analyzes monoliths, modules, dependencies, coupling points.

**Refactoring Agent**
Proposes extraction, modularization, and cleanup strategies.

**Security Agent**
Verifies secrets, Git history, RLS, permissions, auth — read-only, never displays values.

**DevOps Agent**
Creates Dockerfile, docker-compose, CI/CD pipelines, deployment configurations.

**Test Agent**
Generates and runs non-regression tests before and after each migration step.

**Evidence Agent**
Produces proofs, reports, decisions, and audit logs at every step.

**Local AI Orchestrator**
Selects local models for each task. Routes all analysis, planning, and documentation tasks locally first. Decides when frontier fallback is genuinely justified. Minimizes external context. Strips secrets and sensitive data before any frontier call. Logs all frontier usage. Requires explicit human approval for any operation involving sensitive data.

---

## 6. Controlled Agentic Principle

AEOS automates extensively, but never without control.

Every significant action follows this sequence:

```
analyze → propose → simulate → implement in branch → test → report → ask approval → merge/deploy
```

**Non-negotiable rules:**

- No secret displayed — AEOS only reports variable names and presence, never values.
- No push without explicit validation.
- No destructive migration without backup.
- No production change without human confirmation.
- No deletion without rollback path.
- No deployment without evidence report.
- No architecture change without human approval.
- No risky execution without sandbox or dedicated branch.
- No frontier AI call without explicit approval when sensitive data is involved.
- No external call by default — local execution is the baseline.
- No code, schema, secret, or business data sent externally unless explicitly approved.
- Local verification required after any frontier-generated output before use.

These rules apply equally to agents and to direct CLI commands.

---

## 7. Sovereignty Levels

AEOS proposes multiple sovereignty levels. It does not impose a single path. The right level depends on cost, timeline, available expertise, criticality, client requirements, and regulation.

**Level 1 — Controlled Productivity**
Stay on Lovable / Supabase / Vercel, but secure and document everything.
Rotate exposed keys. Add .gitignore protection. Enable RLS. Add .env.example.

**Level 2 — Personal Cloud Control**
Migrate to your own Supabase, Vercel, Cloudflare accounts.
You own the project. Full Dashboard access. Direct billing. Minimal migration effort.

**Level 3 — Managed Open Source**
PostgreSQL, Directus, Hasura, Appwrite, Keycloak, MinIO.
Open source, self-manageable, portable.

**Level 4 — Self-Hosted**
Supabase self-hosted, PostgreSQL, custom backend, self-hosted auth and storage, observability.
Data on-premises or on controlled infrastructure.

**Level 5 — Full Sovereign Stack**
Controlled infrastructure, sovereign cloud, national VPS, micro-cloud, Kubernetes, backups, BCP/DRP.
Zero dependency on foreign platforms. Maximum compliance. Maximum portability.

AEOS helps choose the right level based on:
- Cost and timeline
- Available engineering capacity
- Level of criticality
- Client and regulatory requirements
- Sovereignty and data residency
- Security and auditability
- Maintenance burden

---

## 8. Target Users

**Independent founders and solo builders**
- Building a SaaS, internal tool, or digital product with AI
- No dedicated engineering team
- Budget-conscious: frontier token costs matter
- Appreciate speed but need durability

**Freelancers and agencies**
- Take on AI-generated projects from clients who used Lovable, Bolt, or Replit
- Need to audit, harden, and maintain code they did not write
- Need to explain and justify technical decisions to non-technical clients

**Small and medium product teams (2–10 engineers)**
- Moved fast in early stages, now need to industrialize
- Have a prototype with technical debt and no governance
- Want to add quality gates, tests, CI, and documentation without starting over

**CTOs and technical leads**
- Responsible for architectural decisions and team standards
- Need visibility into what the stack depends on and what can go wrong
- Need to enforce sovereignty and security policies across projects

**Organizations with sovereignty requirements**
- Public sector, healthcare, finance, defense adjacents
- Cannot use US-hosted AI platforms for certain data
- Need on-premise or air-gapped deployment
- Need auditability and data residency guarantees

**African and emerging market teams**
- Building digital products with limited infrastructure budget
- Frontier AI costs are prohibitive at scale
- Local-first AI is not just a preference but an economic necessity
- Sovereignty from global platforms aligns with national digital sovereignty goals

**Enterprises and public institutions with legacy systems**
- Running monolithic applications built years or decades ago
- Need to understand, maintain, modernize without vendor capture
- Cannot afford a big-bang rewrite
- Need a phased, evidence-based modernization path

---

## 9. Why AEOS Can Be Different

Most tools in this space optimize for speed of generation. AEOS optimizes for durability of ownership.

| Principle | What it means in practice |
|-----------|--------------------------|
| **Local-first** | The default path never touches a frontier model. Every frontier call is explicit and logged. |
| **Sovereignty-first** | Every check, every recommendation, every generated scaffold is designed to minimize dependency on external platforms. |
| **Cost-control-first** | 90% of engineering tasks can be done locally for free. AEOS makes that 90% accessible and reliable. |
| **Human approval** | No agent, no frontier call, no destructive action happens without the engineer explicitly authorizing it. |
| **Audit before automation** | AEOS checks before it acts. `sovereignty check` runs before `migrate-plan`. `security check` runs before `harden`. |
| **No silent frontier fallback** | `auto` mode with `require_human_approval = true` stops and asks. It never silently escalates to frontier. |
| **No secret exposure** | AEOS never reads, logs, or displays real secret values. It only reports variable names and presence. |
| **Portability** | Every scaffold AEOS generates can be moved to any machine or provider. |
| **Governance** | Every project has a governance directory, every AI decision has a rationale, every agent action has an audit log. |
| **Quality gates** | No code leaves the project without passing ruff, mypy, and pytest. This is not optional — it is the default. |
| **Read-only by default** | Audit commands never modify the audited project. Inspect before you act. |
| **Evidence at every step** | Every migration, every agent action, every check produces an auditable record. |

---

## 10. Startup Positioning

**English:**
> AEOS is the control layer for AI-built software.

**Français:**
> AEOS est la couche de maîtrise des logiciels construits, repris, modernisés et migrés avec l'IA.

**Strategic phrases:**

> AEOS transforms a digital project into a mastered software asset.

> Create cleanly.
> Reclaim lucidly.
> Modernize without breaking.
> Migrate without losing control.
> Evolve with AI without invisible debt.

**Competitive positioning:**

| Tool | Role | Relationship to AEOS |
|------|------|---------------------|
| Lovable / Bolt / Replit | Generate fast | AEOS is what you use after |
| Cursor / Claude Code | AI coding assistant | AEOS is the governance wrapper |
| Supabase / Firebase | Hosted backend | AEOS helps you escape or replace |
| Vercel / Netlify | Hosted deployment | AEOS ensures you can deploy elsewhere |
| Trivy / Gitleaks | Security scanning | AEOS integrates these as checks |
| Ollama / LM Studio | Local inference runtime | AEOS abstracts and governs them |

AEOS does not compete with generators. It complements them. The relationship is:

> **Lovable creates. AEOS governs.**

---

## 11. Roadmap Implications

The following strategic themes flow directly from this vision, organized by use case:

### Rail A — New Build

- `aeos new` scaffold with sovereign defaults
- Backend, frontend, database, auth, infrastructure generators
- Sovereign templates
- Tests and CI by default
- `aeos blueprint create` for full-stack sovereign scaffolding
- Stack selection: DB, auth, storage, hosting
- Architecture decision records (ADRs) generated at scaffold time

### Rail B — Reclaim

- `aeos reclaim inspect` — generator and provider detection, control map, exit options
- `aeos reclaim plan` — structured exit roadmap
- Provider dependency map
- Secret scan in git history (names only, no values)
- Sovereignty detection deepening: source code scanning for vendor patterns
- Lovable / Supabase exit plan: PostgreSQL local via docker-compose, self-hosted auth, self-hosted storage

### Rail C — Modernize

- `aeos modernize inspect` — legacy project structure scan
- `aeos modernize map` — dependency map
- `aeos modernize plan` — module extraction and strangler pattern roadmap
- `aeos modernize readiness` — container/cloud readiness assessment
- `aeos cloud-cost check` — lift-and-shift cost estimation
- `aeos finops check` — cost optimization opportunities

### Rail D — Migrate

- `aeos migrate plan` — migration plan from current to target
- Branch-based agentic execution
- Tests and rollback at every step
- Evidence report
- Multi-target: Lovable → Supabase, Firebase → PostgreSQL, monolith → modular

### Rail E — Evolve / Operate

- `aeos evolve` — feature evolution with AI agents
- `aeos operate` — continuous audit
- Sovereignty and security drift detection
- `aeos operate report` — periodic audit report
- AI Readiness Score: `aeos score` command

### Rail F — Local AI Runtime

- Local model configuration and selection (`aeos.toml`)
- Local model routing: Ollama, LM Studio, llama.cpp, vLLM, custom endpoints
- Local-first task execution for all routine operations
- Frontier fallback only with explicit human approval
- Privacy-preserving context selection (strip secrets before any external call)
- Model capability evaluation (`aeos ai eval`)
- Sovereign model catalog with license classification (`aeos model list`)
- `aeos ai doctor` — local runtime health check
- Frontier usage audit log

### Rail G — Agents Rail (all rails)

Agents are not a separate product. They are transversal capabilities available across all rails.

- Agent config in `aeos.toml`
- Human approval gate for agent actions
- Git branch isolation for agent work
- Audit log (`logs/agent.jsonl`)
- Local AI Orchestrator routing all tasks locally first
- Frontier escalation only when justified, logged, and approved
- 14 specialized agents: Discovery, Architecture, Planning, Database, Backend, Frontend, Legacy, Refactoring, Security, DevOps, Test, Evidence, Memory, Local AI Orchestrator

Agent governance invariants (code-enforced, untouchable by agent behavior):
- Every agent reads before it writes
- No agent takes a destructive action without human approval
- No agent calls frontier AI with `.env` content, secrets, or sensitive business data
- No agent updates Memory without a human-validated result

### Rail H — Security Rail (cross-cutting)

Security verification that runs inside Reclaim, Modernize, and Operate rails automatically.
Always read-only. Always non-destructive.

- Secret detection in Git history (names only, never values)
- Dependency vulnerability scanning
- RLS policy analysis
- Auth configuration review
- Supply chain risk detection
- `aeos security check --path <project>`

Invariant: AEOS never displays a secret value. All findings reference `file:line`, never `file:line:value`.

### Rail I — Memory Rail (cross-cutting)

Local, controlled knowledge accumulation about projects, audits, and engineering decisions.

- Audit results and findings history
- Human-validated corrections
- Project-specific rules and invariants
- Dependency maps and portability scores over time
- Migration decisions and their outcomes

The controlled learning loop:
```
audit result → human review → validated correction → rule update → local memory
test result  → human review → pattern validation  → rule reinforcement → local memory
```

Memory is local only. No cloud sync. Memory updates require human validation.
Memory feeds future audits, not future decisions autonomously.

**See also:** [`docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md`](AEOS-PRODUCT-RAILS-AND-AGENTS.md) — full nine-rail matrix, agent governance rules, Build Rail discipline, and what AEOS must not become.

---

## 12. What AEOS Is Not

**Not a simple LLM wrapper.**
AEOS is not a thin client over the OpenAI API. It is an engineering operating system with opinions about sovereignty, quality, governance, and cost.

**Not a clone of Lovable.**
AEOS does not generate applications from a natural language prompt. It governs, audits, reclaims, modernizes, migrates, and evolves applications — including those generated by Lovable.

**Not just a scanner.**
`aeos sovereignty check` is a starting point, not the product. AEOS generates migration plans, scaffolds sovereign replacements, and assists local development — not just detects problems.

**Not a platform that locks users in.**
Every AEOS command is a local CLI. There is no cloud service, no account, no usage-based billing, no telemetry, no required external dependency. AEOS is a tool you own.

**Not a tool that pushes toward frontier by default.**
Frontier AI is treated as an exception, not the default. Every frontier call is explicit, logged, and requires human approval.

**Not a replacement for human engineering judgment.**
AEOS assists, audits, and governs. It does not make architectural decisions autonomously. Human approval is a first-class feature, not a fallback.

**Not a tool that forces full sovereignty.**
AEOS proposes five sovereignty levels. Staying on Supabase Cloud is a valid option. The goal is informed choice, not ideological purity.

---

## 13. North Star

> AEOS must allow a person, a small team, or an organization to create, reclaim, modernize, migrate, evolve, and operate serious digital products with AI — without losing technical, economic, or sovereign control.

This means:
- A solo founder can build a production-ready SaaS without Supabase, without Vercel, and without paying per-token for every coding task.
- A freelancer can take over a Lovable project, understand it fully, harden it, and maintain it without depending on the original platform.
- A small team in Dakar, Lagos, or Nairobi can build and evolve a digital product using local AI models, with frontier AI reserved for the truly complex tasks — at a cost they control.
- A CTO can enforce sovereignty, security, and quality standards across every project in the organization, through a CLI that runs in CI and on every developer's machine.
- A government agency or enterprise sitting on a decade-old monolith can understand what it has, know what it costs, and receive a concrete phased roadmap to modernize — without a big-bang rewrite, without vendor capture, and without losing the business logic that runs the organization.

The measure of AEOS success is not the number of users or the amount of code generated.

It is the number of engineering teams who can truthfully say:

> **"We own our stack. We control our costs. We trust our tools."**

---

## 14. Total Sovereign Recovery

### The promise

> **From generated prototype to sovereign software.**
> *De prototype généré à logiciel souverain maîtrisé.*

AEOS does not stop at:

- scanning a project;
- auditing findings;
- generating a report;
- applying a one-off fix.

AEOS accompanies a client from a generated, fragile, or dependent project all the way to software that is mastered, secured, migratable when necessary, maintainable, operable, and developable over time — with local AI by default, frontier AI by exception only.

The full recovery arc covers:

| Phase | What AEOS provides |
|---|---|
| Understanding | Stack inspection, architecture map, zones of control and unknown |
| Secret sovereignty | Secret exposure detection, .gitignore verification, rotation plan |
| Architecture documentation | ARCHITECTURE.md, aeos.toml, dependency map |
| Governance | DECISIONS.md, SECURITY.md, SOVEREIGNTY.md, AI policy |
| Database / RLS hardening | RLS policy analysis, SQL proposals, human review gates |
| Testing | Smoke tests, test baseline, regression safety net |
| CI / CD | Quality gate pipeline, branch protection, CI wiring |
| Local execution | Local run documentation, Dockerfile, docker-compose |
| Portability | Schema versioning, migration export, reversible deployment |
| Migration (when necessary) | Backup → dry-run → rollback plan → human validation → tests |
| Local AI continuation | Local-first development, filtered context, human approval gates |
| Sovereign operation | Continuous audit, drift detection, periodic AEOS reports |

---

### Progressive sovereignty

> Sovereignty is a staged recovery process, not a single action.

A project does not become sovereign in one step. AEOS defines a progressive maturity model:

| Level | Label | What it means |
|---|---|---|
| `weak` | Fragile | No documentation, exposed secrets, no portability, no tests |
| `partial` | Partial | Some documentation, secrets addressed, limited portability |
| `controlled` | Controlled | Governance in place, secrets rotated, RLS hardened, CI active |
| `portable` | Portable | Local run possible, Dockerfile present, migrations versioned |
| `sovereign` | Sovereign | Full data control, exit strategies defined, local AI running, periodic audits active |

The target is always `sovereign`. The path is always progressive. No single step achieves sovereignty — every stage moves the project forward on the maturity axis.

> **Distinction with Section 7:** These maturity levels measure the **project's recovery state** —
> how controlled, governed, and portable it is. They are distinct from the provider sovereignty
> levels in Section 7 (Controlled Productivity → Full Sovereign Stack), which measure the
> cloud infrastructure dependency level. A project can be `controlled` (governance in place,
> secrets rotated, RLS hardened) while still running on Supabase Cloud (Section 7 Level 1).
> Both axes matter; they are complementary, not interchangeable.

---

### Dimensions of sovereignty

| Dimension | What it covers |
|---|---|
| **Code sovereignty** | Code is readable, owned, and maintainable without the originating platform |
| **Data sovereignty** | Data is controlled, exportable, and hosted on infrastructure you choose |
| **Secret sovereignty** | No credentials exist in Git history; rotation policy is active |
| **Deployment sovereignty** | The project is deployable without a specific cloud account or third-party CI |
| **Architecture sovereignty** | Every architectural decision is documented and reversible |
| **AI sovereignty** | No frontier AI is used without explicit approval; local AI handles routine tasks |
| **Knowledge sovereignty** | Architecture, decisions, and history are documented and human-readable |
| **Operational sovereignty** | The team can audit, maintain, and evolve the product without external dependency |

---

### AEOS is not a chatbot. AEOS is not a blind autonomous agent.

> AEOS is a controlled agentic operating system for sovereign software recovery, continuation, and operation.

> AEOS Core guarantees.
> AEOS Agents reason.
> AEOS Memory learns.
> Humans validate.

This doctrine applies equally during recovery, continuation, and operation:

- Agents propose actions — humans decide which to apply.
- Every sensitive step has a human gate.
- Every completed step produces evidence.
- Memory records what was validated, not what was inferred.

AEOS is not Reclaim only. Reclaim is the entry point. Total Sovereign Recovery is the destination.

---

**Vision finale :**

> AEOS creates, reclaims, modernizes, migrates, evolves, and operates software:
> with AI agents · primarily locally · with open-source-first building blocks · under human control · with tests, evidence, portability, and sovereignty.

> Créer.
> Reprendre.
> Moderniser.
> Migrer.
> Évoluer.
> Opérer.
>
> Avec des agents IA.
> Sous contrôle humain.
> Avec preuves, tests, portabilité et souveraineté.
