# AEOS CTO Handoff

**Version :** 2026-06-29
**Auteur :** AEOS Operations / ChatGPT (CTO) + Claude Code (Execution)
**Statut :** Document vivant — à mettre à jour à chaque décision structurante

---

## Documents à lire avant toute reprise

Tout agent ou collaborateur reprenant le travail sur AEOS doit lire ces documents dans l'ordre :

1. `docs/strategy/AEOS-PRODUCT-VISION.md`
2. `docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md`
3. `docs/operations/AEOS-AI-MAC-WORKSTATION-SETUP.md`
4. `docs/operations/AEOS-CTO-HANDOFF.md` ← ce document
5. `docs/operations/AEOS-SPRINT-LOG.md`
6. `docs/operations/AEOS-NEXT-ACTIONS.md`
7. `docs/operations/AEOS-MULTI-AGENT-WORKFLOW.md`

---

## 1. Vision AEOS

**AEOS** est un **AI Engineering Operating System** — un système d'exploitation pour ingénierie logicielle augmentée par l'IA.

AEOS n'est pas un outil. C'est une plateforme d'agents, de rails et de mémoire qui permet à des équipes humaines de produire, auditer, sécuriser et opérer des systèmes logiciels avec l'IA comme copilote systématique.

### Positionnement

> **Lovable is a use case. Reclaim is a rail. AEOS is the full engineering operating system.**

- **Lovable** génère des interfaces à partir de prompts. C'est un cas d'usage parmi d'autres.
- **Reclaim** est un rail AEOS : il audite, sécurise et harden des projets existants.
- **AEOS** orchestre l'ensemble : Build, Reclaim, Modernize, Migrate, Operate, Security, Sovereignty, Agents, Memory.

### Garanties centrales

> **AEOS Core guarantees. AEOS Agents reason. AEOS Memory learns. Humans validate.**

- **Core** : des commandes reproductibles, déterministes, auditables.
- **Agents** : des agents IA qui raisonnent sur le contexte, proposent, planifient.
- **Memory** : un système de mémoire local-first qui apprend des diagnostics passés.
- **Humans** : aucune action destructrice sans gate humain explicite.

---

## 2. Doctrine

| Principe | Description |
|---|---|
| **LOCAL-FIRST** | Tout ce qui peut tourner localement doit tourner localement. |
| **OPEN-SOURCE-FIRST** | Préférer les outils open-source éprouvés. |
| **AI-LOCAL-FIRST** | Les modèles IA tournent localement par défaut (Ollama). Le frontier AI est réservé aux cas où le local est insuffisant. |
| **FRONTIER AI ONLY WHEN NECESSARY** | Ne pas envoyer de données sensibles à un LLM cloud sans justification explicite. |
| **NO SECRETS COPIED BLINDLY** | Ne jamais copier un `.env` sans lecture et rotation préalable. |
| **GITHUB AS SOURCE OF TRUTH** | Le code vit sur GitHub. La machine locale est un poste de travail, pas une sauvegarde. |
| **GATE BEFORE APPLY** | Aucune correction automatique sans validation humaine intermédiaire. |
| **OUTPUT BEFORE WRITE** | Toujours produire en `/tmp` ou `--output` avant d'écrire dans le repo. |

---

## 3. Rails produit

| Rail | Description |
|---|---|
| **Build** | Scaffolding de projets AEOS-native (Python, Supabase, Lovable). |
| **Reclaim** | Audit, sécurisation et hardening de projets existants. |
| **Modernize** | Mise à niveau de bases de code legacy. |
| **Migrate** | Migration de bases de données, de cloud, d'architectures. |
| **Operate** | Monitoring, alerting, runbooks automatisés. |
| **Security** | RLS, secrets, OWASP, audit de surface d'attaque. |
| **Sovereignty** | Contrôle de la stack : pas de vendor lock-in, IA locale, données souveraines. |
| **Agents** | Orchestration d'agents IA spécialisés par rail. |
| **Memory** | Mémoire locale-first des diagnostics, décisions et patterns appris. |

---

## 4. Rôles des agents

### ChatGPT — CTO / Product Architect / Strategy

- Définit la vision produit et les priorités.
- Rédige les specs de sprint et les décisions d'architecture.
- Arbitre les trade-offs entre rails et entre agents.
- Ne touche pas le code directement.

### Claude Code — Exécution locale

- Exécute les sprints en local sur la machine de développement.
- Lit, écrit et modifie les fichiers du repo AEOS.
- Lance les commandes shell (git, uv, pytest, ruff, mypy).
- Crée les branches, commits et PRs.
- Respecte les contraintes de sécurité définies par le CTO.

### Codex (optionnel) — Tâches parallèles / PRs isolées / Cloud agents

- Peut prendre en charge des tâches isolées en parallèle (documentation, tests, refactoring).
- Opère dans des branches dédiées sans affecter main.
- Ne doit pas accéder aux secrets ou aux projets clients sans gate explicite.
- Toute PR Codex doit être relue par un humain avant merge.

### IA Locale (Ollama) — Souveraineté et analyse privée

- Analyse privée de fichiers et de code sans envoi vers un modèle cloud.
- Pré-audit local avant tout traitement par un modèle externe.
- Gardien de la doctrine `AI-LOCAL-FIRST` : aucun code sensible vers le cloud par défaut.
- Fondation future pour la mémoire locale AEOS.

### Antigravity (futur) — Expérimentation agentique

- Réservé à l'expérimentation de nouveaux patterns agentiques.
- Ne doit pas être utilisé en production sans validation AEOS.
- Pas un outil principal pour AEOS aujourd'hui — utilisable seulement quand les gates seront matures.

---

## 5. Règles de sécurité — non négociables

1. **Ne jamais lire `.env`** — ni l'afficher, ni le copier.
2. **Ne jamais afficher de secrets** — clés API, tokens, mots de passe.
3. **Pas d'apply sans gate** — toute correction automatique doit être proposée, validée, puis appliquée.
4. **Pas de connexion Supabase sans demande explicite** — ne pas déclencher `supabase db push`, `apply_migration` ou équivalent sans instruction directe.
5. **Ne pas toucher les projets clients** — `ma-mairie-digitale` et tout autre projet client sont hors scope sauf instruction explicite.
6. **Rotation des secrets avant copie** — si un `.env` doit être transféré sur une nouvelle machine, rotation préalable obligatoire.
7. **Historique Git traité séparément** — si un secret a été commité, c'est un incident : rotation immédiate + nettoyage d'historique.

---

## 6. État actuel de AEOS (2026-06-29)

### Branche principale
`main` — propre, à jour, CI verte.

### Commits structurants récents

| Commit | Description |
|---|---|
| `2e868ee` | Merge PR #33 — sprint3f/memory-layer-mvp |
| `5f2c1ed` | docs(operations): AI Mac workstation setup |
| `7139b77` | feat(memory): Memory Layer MVP — local-first diagnostic record store |
| `d438805` | Merge PR #32 — sprint3e/reclaim-remediation-plan |
| `aa4d5d6` | feat(reclaim): add remediation plan to harden output |

### Fonctionnalités actives dans AEOS CLI

- `aeos inspect` — audit de sécurité projet
- `aeos reclaim harden` — hardening avec plan de remédiation et `--output`
- `aeos memory` — Memory Layer MVP (à consolider, voir AEOS-NEXT-ACTIONS.md)

### Structure du repo

```
src/aeos/
  cli.py          ← point d'entrée CLI
  reclaim/        ← rail Reclaim
  memory/         ← Memory Layer MVP (store, models, __init__)
docs/
  features/       ← specs fonctionnelles
  operations/     ← guides opérationnels (ce dossier)
  research/       ← recherches et exploration
  strategy/       ← vision produit et rails
tests/
  unit/           ← tests unitaires (dont test_memory_store.py)
```

---

## 7. État actuel de ma-mairie-digitale (2026-06-29)

- Projet client : `~/aeos-client-audits/ma-mairie-digitale`
- Audité via `aeos reclaim harden`
- Plan de remédiation généré
- `.env` non tracké (vérifié)
- **Aucune modification depuis l'audit** — projet intact

---

## 8. Décisions structurantes

| Date | Décision | Raison |
|---|---|---|
| 2026-06-29 | Ollama = runtime IA local recommandé | AI-LOCAL-FIRST doctrine |
| 2026-06-29 | Vercel CLI / AWS CLI / Bun = optionnels | Pas de dépendance forcée |
| 2026-06-29 | `uv sync` = seule méthode de recréation d'env Python | Reproductibilité garantie |
| 2026-06-29 | Memory Layer MVP mergé dans main | Fondation pour AEOS Agents |
| 2026-06-29 | `--output` sur toutes les commandes write | Gate avant écriture repo |
| 2026-06-29 | GitHub = source de vérité unique | Pas de dépendance à l'état local |
| 2026-06-29 | Workflow multi-agent documenté | Continuité, sécurité, souveraineté entre agents |
