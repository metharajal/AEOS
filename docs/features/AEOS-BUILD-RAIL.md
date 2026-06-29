# AEOS Build Rail

**Version :** Sprint 4A — 2026-06-30  
**Statut :** MVP livré — `aeos build plan` disponible  
**Rail :** Build

---

## 1. Rôle du rail Build

Le rail Build est le point d'entrée de tout **nouveau projet AEOS-native**.

Son rôle n'est pas de générer un prototype rapidement. Son rôle est de structurer un
projet avec contrôle, souveraineté, sécurité, architecture, documentation et portabilité
**dès le premier commit**.

> **Build ne signifie pas prototype rapide.**
> Build signifie projet contrôlé dès le départ.

La différence avec Lovable n'est pas la vitesse. La différence est la propriété.

---

## 2. Différence avec Lovable

| Dimension | AEOS Build | Lovable |
|---|---|---|
| Architecture | Explicite, choisie par l'humain, documentée | Défauts intégrés (Supabase, Vercel) |
| Base de données | Choix documenté : PostgreSQL, Supabase, MySQL | Supabase par défaut |
| Auth | Choix documenté : Keycloak, Supabase, Clerk | Supabase Auth par défaut |
| Sécurité | Gate CI dès le premier commit | Non incluse |
| Tests | Structure scaffoldée, CI câblée | Non inclus |
| Documentation | ADR, governance, .env.example | Minimal |
| Portabilité | Dockerfile, docker-compose, migrations | Non incluse |
| Souveraineté | Audit CI par défaut | Non incluse |
| Lock-in | Explicite et documenté si présent | Implicite et invisible |

Lovable est un **use case** d'AEOS (Reclaim Rail). Build est un **rail séparé**.

---

## 3. Commande `aeos build plan`

### Usage

```bash
aeos build plan --name <project_name> --type <project_type> --stack <stack>
aeos build plan --name <project_name> --type <project_type> --stack <stack> --json
```

### Exemple

```bash
aeos build plan --name civic-portal --type web-app --stack nextjs-supabase
```

### Types acceptés (MVP)

| Type | Description |
|---|---|
| `web-app` | Application web (frontend + backend) |
| `api` | Service API (REST, GraphQL) |
| `internal-tool` | Outil interne (backoffice, ops) |

### Stacks acceptées (MVP)

| Stack | Description |
|---|---|
| `nextjs-supabase` | Next.js + Supabase BaaS |
| `nextjs-postgres` | Next.js + PostgreSQL auto-hébergé |
| `fastapi-postgres` | FastAPI + PostgreSQL |
| `generic` | Stack non définie — à préciser avant scaffolding |

---

## 4. Sortie texte

```
── Build Plan ───────────────────────────────────────────

── Project Identity ─────────────────────────────────────
  name:  civic-portal
  type:  web-app
  stack: nextjs-supabase

── Architecture Summary ─────────────────────────────────
  Next.js frontend with Supabase BaaS (auth, database, storage).
  API routes in Next.js App Router. RLS required on all Supabase tables.

── Suggested Folder Structure ───────────────────────────
  src/app/
  src/components/
  src/lib/
  supabase/migrations/
  ...

── Required Governance Files ────────────────────────────
  README.md
  ARCHITECTURE.md
  .env.example
  .gitignore
  docs/DECISIONS.md

── Security Baseline ────────────────────────────────────
  • No .env committed — .gitignore must include .env from day one
  • Secrets only through environment variables — never hardcoded
  • Auth boundaries documented in ARCHITECTURE.md before any code
  • Least privilege by default — minimum permissions for every service account
  • RLS required on all Supabase tables — no table without a policy
  • Supabase anon key must never grant write access without RLS

── Sovereignty Baseline ─────────────────────────────────
  • Local development must work without cloud dependencies
  • Database portability documented — schema must be exportable
  • External providers identified and documented in ARCHITECTURE.md
  • Exit strategy required before first production deploy
  • Supabase is an external provider — document migration path to self-hosted Postgres
  • Supabase Auth is an external dependency — document auth portability

── Testing Baseline ─────────────────────────────────────
  • Unit tests for all business logic
  • Integration tests for API routes and data layer
  • CI quality gate — tests must pass before merge
  • End-to-end tests recommended before production deploy

── Deployment Baseline ──────────────────────────────────
  • Local run command required — project must run locally before cloud deploy
  • Dockerfile recommended for reproducible deployments
  • Cloud provider not hardcoded — all endpoints via environment variables
  • CI/CD pipeline must not contain cloud credentials in code
  • Local run: npm run dev + Supabase local emulator (supabase start)
  • Supabase project URL must be in .env — not hardcoded

── Recommended Next Steps ───────────────────────────────
  1. Run aeos build scaffold to generate the folder structure (coming soon)
  2. Create ARCHITECTURE.md with component diagram
  3. Fill .env.example with all required variables
  4. Set up CI pipeline with quality gate
  5. Document auth boundaries before writing any code
  6. Run aeos reclaim harden after first commit to audit sovereignty
  7. Set up Supabase local dev environment before adding RLS

Read-only — no project created, no files modified.
  read_only: true  ·  applied: false
```

---

## 5. Sortie JSON (`--json`)

```json
{
  "command": "build plan",
  "read_only": true,
  "applied": false,
  "project_name": "civic-portal",
  "project_type": "web-app",
  "stack": "nextjs-supabase",
  "architecture_summary": "Next.js frontend with Supabase BaaS...",
  "folder_structure": ["src/app/", "src/components/", ...],
  "governance_files": [
    "README.md",
    "ARCHITECTURE.md",
    ".env.example",
    ".gitignore",
    "docs/DECISIONS.md"
  ],
  "security_baseline": [...],
  "sovereignty_baseline": [...],
  "testing_baseline": [...],
  "deployment_baseline": [...],
  "recommended_next_steps": [...]
}
```

---

## 6. Garanties read-only

| Garantie | Statut |
|---|---|
| Aucun projet créé | ✓ |
| Aucun fichier modifié | ✓ |
| `read_only: true` dans la sortie JSON | ✓ |
| `applied: false` dans la sortie JSON | ✓ |
| Aucun `.env` lu | ✓ |
| Aucun secret affiché | ✓ |
| Aucun appel réseau | ✓ |
| Aucun appel IA externe | ✓ |
| Aucun Docker build | ✓ |
| Aucun npm install / uv init | ✓ |

---

## 7. Limites du MVP (Sprint 4A)

- `aeos build plan` produit un plan — il ne génère pas de fichiers.
- Aucun code applicatif n'est généré.
- Les stacks disponibles sont limitées à 4 (nextjs-supabase, nextjs-postgres,
  fastapi-postgres, generic).
- Les types sont limités à 3 (web-app, api, internal-tool).
- La commande est statique — elle n'inspecte pas de projet existant.

---

## 8. Étapes futures possibles

| Commande | Objectif |
|---|---|
| `aeos build scaffold` | Générer la structure de dossiers et fichiers governance |
| `aeos build review` | Auditer un projet en cours de construction |
| `aeos build generate` | Générer des composants avec contrôle humain |
| `aeos build apply` | Appliquer une action avec gate humain explicite |

Chaque étape future restera soumise aux invariants AEOS :
- `read_only: true` par défaut
- `applied: false` jusqu'à validation humaine explicite
- Aucun secret lu ou affiché
- Aucun appel frontier AI sans autorisation

---

## 9. Architecture interne

```
src/aeos/build/
  __init__.py        — exports publics
  planner.py         — BuildPlan, create_build_plan(), build_plan_to_dict()

src/aeos/cli.py      — commande aeos build plan
tests/unit/
  test_build_planner.py  — 18 tests
```

### Public API

```python
from aeos.build import (
    BuildPlan,
    VALID_TYPES,
    VALID_STACKS,
    create_build_plan,
    build_plan_to_dict,
    validate_project_type,
    validate_stack,
)

plan = create_build_plan("civic-portal", "web-app", "nextjs-supabase")
d = build_plan_to_dict(plan)
```

---

## Voir aussi

- [`docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md`](../strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md)
- [`docs/features/AEOS-MEMORY-LAYER.md`](AEOS-MEMORY-LAYER.md)
- [`docs/features/AEOS-RECLAIM-HARDEN.md`](AEOS-RECLAIM-HARDEN.md)
