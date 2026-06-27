# AEOS Product Vision

**Date:** 2026-06-27
**Status:** Strategic — Living Document
**Version:** 0.1

---

## 1. Core Thesis

The explosion of AI code generation tools has made it easier than ever to start a digital product. But starting fast and owning what you built are not the same thing.

AEOS exists at the intersection of three forces:
- **AI generates code faster than teams can govern it.**
- **Hosted platforms capture the stack behind every generated project.**
- **Local AI is now capable enough to handle most engineering tasks at near-zero marginal cost.**

AEOS is the engineering operating system that bridges all three: it helps you create, reclaim, evolve, and modernize software products built with AI — while keeping control of the code, the data, the infrastructure, the models, the costs, and the sovereignty.

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

This is the founding sentence of AEOS. It defines three product paths that mirror the actual trajectory of a builder:

- **Path A — Build from scratch**: start the next project right, with sovereignty and quality from the first commit.
- **Path B — Reclaim existing AI-generated projects**: audit, harden, and migrate projects already built with Lovable, Bolt, Replit, Supabase, or similar tools.
- **Path C — Evolve locally with low token dependency**: continue developing with local AI models, at near-zero marginal cost, with frontier reserved for the genuinely complex tasks.
- **Path D — Modernize and migrate existing applications**: audit, map, and guide the progressive modernization of legacy monolithic systems — without promising magic automation.

AEOS is not a theoretical framework. It is the tool the founder needed and could not find.

A fourth path has emerged since: many organizations — especially in Africa — are not building from scratch. They are sitting on legacy monolithic systems they do not fully understand, cannot easily maintain, and cannot afford to migrate incorrectly. Path D addresses this reality.

AEOS helps create, reclaim, modernize, and evolve digital products with AI — while keeping technical, economic, and sovereign control.

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

---

## 3. The Four AEOS Product Paths

---

### Path A — Build from Scratch

> Start clean. Build right. Own everything from day one.

For founders, freelancers, and teams who want to build a digital product with AI assistance and maintain full engineering control from the first commit.

**What AEOS provides:**

- **Project scaffold** with explicit architecture: source layout, test structure, CI pipeline, documentation conventions, governance directory.
- **Conscious stack choices**: database, auth, storage, and hosting are explicit decisions, not embedded defaults. AEOS prompts for them and generates portable infrastructure.
- **Quality gates from day one**: ruff, mypy, pytest, and sovereignty check are wired into the CI pipeline before the first feature is written.
- **Local-first AI assistance**: `aeos ai ask` routes engineering questions to a local model by default. Frontier is opt-in, with human approval.
- **Sovereignty by design**: no Supabase dependency, no Vercel lock-in, no secret exposure — enforced by `aeos sovereignty check` in CI.

**Future commands on this path:**

```
aeos init <project> --type saas        # scaffold a full-stack sovereign project
aeos blueprint create                  # generate architecture blueprint
aeos architecture plan                 # propose stack (db/auth/storage/hosting)
aeos quality                           # run all quality gates
aeos sovereignty check                 # verify no external lock-in
aeos ai ask "How should I model users in this schema?"
```

**Outcome:** A project that can be moved to any machine, deployed to any provider, and maintained by any engineer — without depending on the platform that generated it.

---

### Path B — Reclaim Existing AI-Generated Projects

> You built fast. Now build right.

For teams who used Lovable, Bolt, Replit, Cursor, or similar tools and now face the consequences: a working prototype with no architecture, no tests, no portability, and a stack they did not choose.

**What AEOS provides:**

- **Audit layer**: `aeos sovereignty check` scans the project for Supabase, Firebase, Clerk, Vercel, and other hosted dependencies.
- **Dependency map**: understand exactly what the project depends on, at which layer (database, auth, storage, hosting, AI, MCP).
- **Risk classification**: findings are categorized by severity (OK / WARNING / ERROR) with concrete recommendations.
- **Migration plan**: `aeos sovereignty migrate-plan` generates a step-by-step roadmap to replace hosted dependencies with self-hostable alternatives.
- **Portability hardening**: AEOS identifies missing Dockerfile, missing migrations, missing `.env.example`, and guides the team to add them.
- **Security sweep**: detect committed secrets, vulnerable dependencies, insecure base images.

**Future commands on this path:**

```
aeos onboard                           # onboard existing project into AEOS
aeos project inspect                   # inspect project structure
aeos sovereignty check                 # detect external dependencies
aeos sovereignty migrate-plan          # generate migration roadmap (read-only)
aeos security check                    # detect security gaps
aeos supply-chain check                # audit dependencies, licenses, SBOM
aeos harden                            # guided hardening checklist
```

**Outcome:** A Lovable or Bolt project that can be understood, maintained, migrated, and deployed without the originating platform — transformed into a governable engineering asset.

---

### Path C — Evolve Locally with Low Token Dependency

> Let local AI do 90% of the work. Reserve frontier for the rest.

For teams who want to continue evolving their product with AI assistance without paying frontier token costs for every routine engineering task.

**What AEOS provides:**

- **Local-first routing**: `aeos ai ask` defaults to the configured local model (Ollama, LM Studio, llama.cpp). Frontier is only called when explicitly requested or when local fails and the user approves.
- **Human approval gates**: `require_human_approval = true` in `aeos.toml` ensures no silent frontier fallback. The engineer always knows when a frontier model is being used.
- **Model sovereignty**: AEOS helps the team choose a local model that is genuinely open-weight, commercially usable, and appropriate for their hardware.
- **Future agent runtime**: local coding agents that can read files, write code, run tests, and propose commits — all on a dedicated git branch, with human review before merge.
- **Runtime flexibility**: AEOS abstracts the local inference runtime. Teams can switch from Ollama to LM Studio or llama.cpp without changing their workflow.

**Cost structure this enables:**

| Task | Today | With AEOS |
|------|-------|-----------|
| Explain this function | Frontier ($) | Local (free) |
| Write unit test | Frontier ($) | Local (free) |
| Refactor module | Frontier ($) | Local (free) |
| Review diff | Frontier ($) | Local (free) |
| Architect new feature | Frontier ($) | Frontier (human-approved) |
| Debug complex regression | Frontier ($) | Frontier (human-approved) |

**Future commands on this path:**

```
aeos ai ask "Write a test for this function"     # local by default
aeos ai ask "..." --provider frontier            # explicit frontier
aeos ai ask "..." --provider auto                # local first, frontier fallback (with approval)
aeos ai doctor                                   # check local model availability
aeos model list                                  # browse sovereign model catalog
aeos agent run --local "add pagination to API"   # sandboxed local coding agent
aeos code task --local                           # local-first engineering task
aeos review --local                              # local code review
```

**Outcome:** A team that can iterate on their product continuously, at near-zero token cost, with frontier AI reserved for the tasks that genuinely require it — and with full transparency about when frontier is used.

---

### Path D — Modernize and migrate existing applications

> You did not build with AI. You inherited something that was never built to last.

For organizations — enterprises, public institutions, SMEs — that have existing monolithic applications they need to understand, maintain, modernize, or migrate, without being captured by a cloud migration vendor or a consulting firm charging by the day.

**The problem this path addresses:**

Many organizations in Africa and in regulated markets globally are not in the "building fast with AI" problem. They are in a different and older problem: they have a system that runs the business, that nobody fully understands, that costs more every year to maintain, and that every consultant recommends migrating to AWS or Azure — without explaining why, or what that actually changes.

**The monolith trap.** A legacy application is often a monolith: a single codebase with years of undocumented business logic, tightly coupled modules, no tests, no separation of concerns, and a dependency chain that only one or two people understand. Touching one part breaks another. Adding a feature takes months. The original developers are gone.

**The "lift and shift" illusion.** The most common migration recommendation is to move the application to a cloud provider — AWS, Azure, GCP — without changing the architecture. This is called "lift and shift." It solves exactly one problem (hardware maintenance) while making everything else worse: the application is now more expensive (cloud billing replaces owned infrastructure), still monolithic, still undocumented, and now dependent on a foreign cloud vendor that can change pricing or terms at any time. Organizations in Senegal, Côte d'Ivoire, or Morocco that "migrated to the cloud" often find themselves paying three to five times more than before, for the same system, with the same problems, and less control.

**The cost blindspot.** Most organizations with legacy systems do not know the real cost of their application. They know the server cost. They do not know the developer time cost, the maintenance cost, the opportunity cost of features not shipped, or the risk cost of the system going down. Without a clear cost picture, modernization decisions are made on intuition, not on evidence.

**What AEOS provides on Path D:**

AEOS does not promise automatic modernization. It provides structured, static analysis to help teams understand what they have before deciding what to do next.

- **Legacy inspection**: `aeos legacy inspect` scans the project structure, detects languages, frameworks, database connectors, and external dependencies.
- **Dependency mapping**: `aeos legacy map` generates a visual or structured map of the application's layers — what calls what, what depends on what, what is shared vs. isolated.
- **Modernization planning**: `aeos modernization plan` generates a progressive roadmap for breaking the monolith into independently deployable modules — without requiring a full rewrite.
- **Migration readiness**: `aeos migration readiness` assesses whether the application is ready for a container-based or cloud deployment — and what must be done first (add tests, document APIs, isolate database access, add health checks).
- **Cloud cost readiness**: `aeos cloud-cost check` estimates the structural cost implications of a lift-and-shift migration, and identifies which components should be rearchitected before moving.
- **FinOps alignment**: `aeos finops check` identifies cost optimization opportunities — unused dependencies, over-provisioned services, missing resource limits, unmetered external API calls.

**The AEOS principle on Path D:**

> Audit first. Understand before you move. Recommend before you automate.

AEOS does not rewrite the application. It does not apply automatic migrations. It does not make architecture decisions autonomously. It gives the team the visibility they need to make those decisions with evidence — and the structure to execute them progressively.

**Future commands on this path:**

```
aeos legacy inspect                    # inspect legacy project structure
aeos legacy map                        # generate dependency map
aeos modernization plan                # step-by-step modernization roadmap
aeos migration readiness               # assess readiness for container/cloud move
aeos cloud-cost check                  # estimate structural cost of lift-and-shift
aeos finops check                      # identify cost optimization opportunities
```

**The organizations this path serves:**

- A government agency in Senegal running a monolithic Java application built in 2008, maintained by a single vendor, with no documentation and no tests.
- A bank in Abidjan whose core banking system is a decade-old PHP monolith that runs on physical servers and has never been containerized.
- An NGO in Nairobi with a donor management system built in Access and VBA, with no exit plan and no one who understands the full data model.
- A telecoms operator whose internal operations portal is a mix of Perl scripts, Oracle procedures, and undocumented APIs — and whose modernization was "estimated at $2M" by a consulting firm.

None of these organizations need more AI features. They need clarity, structure, and a progressive path forward that they can execute with their own teams.

**Outcome:** An organization that understands what it has, knows what it costs, and has a clear, phased roadmap to modernize — without a big-bang rewrite, without a vendor dependency, and without losing the business logic that makes their system work.

---

## 4. Target Users

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

---

## 5. Why AEOS Can Be Different

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

---

## 6. Startup Positioning

**English:**
> AEOS is the control layer for AI-built software.

**Français:**
> AEOS est la couche de contrôle des logiciels construits avec l'IA.

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

## 7. Roadmap Implications

The following strategic themes flow directly from this vision:

**Deepening sovereignty detection (Path B)**
- Source code scanning for vendor patterns (not just package.json)
- Hardcoded URL detection
- Recursive env file scanning
- `sovereignty.toml` for accepted risks

**Lovable / Supabase Exit Plan (Path B)**
- Generate concrete migration plan from detected dependencies
- PostgreSQL local setup via docker-compose
- Self-hosted auth (Keycloak, Ory, Lucia)
- Self-hosted storage (MinIO)

**Security & Supply Chain Check (Paths A, B)**
- Secret scan in git history (names only, no values)
- Vulnerable dependency detection
- Non-pinned base image detection
- SBOM generation

**Sovereign Model Catalog (Path C)**
- Embedded catalog of open-weight models with license classification
- Hardware requirement profiles
- Integration with `aeos ai doctor`

**Local Runtime Abstraction (Path C)**
- Support Ollama, LM Studio, llama.cpp, vLLM, custom endpoints
- Runtime-agnostic `ask_local_ai()`
- Runtime detection in `aeos ai doctor`

**AI Model Evaluation (Path C)**
- Local benchmark suite: copy fidelity, YAML integrity, instruction following
- `aeos ai eval` command
- PASS / WARN / FAIL per evaluation category

**Agent Governance MVP (Paths A, C)**
- Agent config in `aeos.toml`
- Human approval gate for agent actions
- Git branch isolation for agent work
- Audit log (`logs/agent.jsonl`)

**Product Blueprint (Path A)**
- `aeos blueprint create` for full-stack sovereign scaffolding
- Stack selection: DB, auth, storage, hosting
- Architecture decision records (ADRs) generated at scaffold time

**Local Development Agent (Path C)**
- `aeos agent run --local` with sandbox and branch isolation
- File read/write, test execution, commit proposal
- Human review gate before any merge

**AI Readiness Score (Paths A, B, C)**
- Aggregate score across all AEOS checks
- `aeos score` command
- Export to JSON for CI dashboards and team reporting

**Legacy Project Inspector (Path D)**
- Static scan of existing monolithic application structure
- Language, framework, and database connector detection
- `aeos legacy inspect` command

**Monolith Dependency Map (Path D)**
- Structured map of application layers and inter-module dependencies
- Identification of shared vs. isolated components
- `aeos legacy map` command

**Modernization Plan Generator (Path D)**
- Progressive roadmap for decomposing a monolith
- Phased recommendations: isolate, extract, containerize, decouple
- `aeos modernization plan` command

**Cloud Cost Readiness Check (Path D)**
- Structural cost estimation for lift-and-shift migration
- Identification of components requiring rearchitecture before cloud move
- `aeos cloud-cost check` command

**FinOps Integration (Path D)**
- Cost optimization opportunity detection
- Unused dependencies, over-provisioned services, unmetered external calls
- `aeos finops check` command
- Future: integration with Costit for cloud spend visibility

---

## 8. What AEOS Is Not

**Not a simple LLM wrapper.**
AEOS is not a thin client over the OpenAI API. It is an engineering operating system with opinions about sovereignty, quality, governance, and cost.

**Not a clone of Lovable.**
AEOS does not generate applications from a natural language prompt. It governs, audits, and evolves applications — including those generated by Lovable.

**Not just a scanner.**
`aeos sovereignty check` is a starting point, not the product. AEOS will eventually generate migration plans, scaffold sovereign replacements, and assist local development — not just detect problems.

**Not a platform that locks users in.**
Every AEOS command is a local CLI. There is no cloud service, no account, no usage-based billing, no telemetry, no required external dependency. AEOS is a tool you own.

**Not a tool that pushes toward frontier by default.**
Frontier AI is treated as an exception, not the default. Every frontier call is explicit, logged, and requires human approval. AEOS is designed to make frontier unnecessary for routine engineering tasks.

**Not a replacement for human engineering judgment.**
AEOS assists, audits, and governs. It does not make architectural decisions autonomously. Human approval is a first-class feature, not a fallback.

---

## 9. North Star

> AEOS must allow a person, a small team, or an organization to build, reclaim, evolve, and modernize serious digital products with AI — without losing technical, economic, or sovereign control.

This means:
- A solo founder can build a production-ready SaaS without Supabase, without Vercel, and without paying per-token for every coding task.
- A freelancer can take over a Lovable project, understand it fully, harden it, and maintain it without depending on the original platform.
- A small team in Dakar, Lagos, or Nairobi can build and evolve a digital product using local AI models, with frontier AI reserved for the truly complex tasks — at a cost they control.
- A CTO can enforce sovereignty, security, and quality standards across every project in the organization, through a CLI that runs in CI and on every developer's machine.
- A government agency or enterprise sitting on a decade-old monolith can understand what it has, know what it costs, and receive a concrete phased roadmap to modernize — without a big-bang rewrite, without vendor capture, and without losing the business logic that runs the organization.

The measure of AEOS success is not the number of users or the amount of code generated.

It is the number of engineering teams who can truthfully say:

> **"We own our stack. We control our costs. We trust our tools."**
