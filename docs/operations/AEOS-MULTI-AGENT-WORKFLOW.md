# AEOS Multi-Agent Workflow

**Version :** 2026-06-29
**Auteur :** AEOS Operations / ChatGPT (CTO) + Claude Code (Execution)
**Statut :** Document vivant — référence obligatoire pour tout agent travaillant sur AEOS

---

## 1. Pourquoi ce document existe

AEOS est développé par plusieurs agents IA travaillant en parallèle sur des périmètres distincts. Sans protocole explicite, ce modèle multi-agent génère des risques : perte de contexte, conflits de branches, violations de sécurité, décisions prises en dehors de la source de vérité.

Ce document définit :

- le rôle précis de chaque agent
- la source de vérité unique
- le protocole obligatoire avant chaque tâche
- les règles interdites non négociables
- les checks obligatoires avant toute PR

---

## 2. Les agents et leurs rôles

### 2.1 ChatGPT — CTO Stratégique

**Rôle :** Architecte produit et arbitre de priorités.

Responsabilités :
- Définir la vision produit et les objectifs de sprint
- Arbitrer les trade-offs entre rails, entre agents, entre risques
- Rédiger les specs de sprint et les décisions d'architecture
- Prioriser le backlog et valider les changements structurants
- Relire les résultats de sprint et proposer les ajustements
- Formuler les prompts agents pour les tâches complexes

Contraintes :
- Ne touche pas le code directement
- Ne commit pas, ne crée pas de PR
- Opère uniquement via des instructions transmises à Claude Code ou Codex

---

### 2.2 Claude Code — Exécution Locale Principale

**Rôle :** Bras armé local du développement AEOS.

Responsabilités :
- Exécuter les sprints sur la machine de développement locale
- Lire, écrire et modifier les fichiers du repo AEOS
- Lancer les commandes shell : `git`, `uv`, `pytest`, `ruff`, `mypy`
- Créer les branches, commits et PRs
- Respecter les contraintes de sécurité définies par le CTO
- Maintenir la cohérence entre le contexte de la conversation et l'état du repo

Contraintes :
- Travaille uniquement dans le repo local `~/Development/AEOS`
- Ne modifie jamais les projets clients sans instruction explicite
- Ne lit jamais `.env`
- Propose avant d'agir sur tout changement sensible

---

### 2.3 Codex — Tâches Parallèles Isolées

**Rôle :** Agent cloud pour les tâches autonomes à faible risque.

Responsabilités :
- Prendre en charge des tâches isolées en parallèle (documentation, tests unitaires, refactorings limités)
- Créer des PRs autonomes dans des branches dédiées
- Travailler sur des périmètres clairement délimités sans affecter `main`
- Réduire la charge sur Claude Code pour les tâches répétitives ou mécaniques

Contraintes :
- Ne modifie jamais de fichiers sensibles (secrets, configuration de production, projets clients) sans validation humaine explicite
- N'accède pas aux secrets ni aux variables d'environnement
- Opère uniquement dans des branches préfixées `codex/`
- Toute PR Codex doit être relue par un humain avant merge
- Ne prend jamais de décision architecturale sans validation CTO

---

### 2.4 IA Locale (Ollama) — Souveraineté et Analyse Privée

**Rôle :** Couche de traitement local-first pour protéger la confidentialité des données.

Responsabilités :
- Analyse privée de fichiers et de code sans envoi vers un modèle cloud
- Pré-audit local avant tout traitement par un modèle externe
- Classification locale de la sensibilité des données
- Routage intelligent : décider ce qui peut partir vers le cloud vs ce qui reste local
- Fondation future pour la mémoire locale AEOS (contexte, patterns, diagnostics)

Contraintes :
- Par défaut, aucun code sensible n'est envoyé à un modèle externe
- Les modèles cloud (ChatGPT, Claude API, Codex) ne reçoivent que ce qui est explicitement autorisé
- L'IA locale est le gardien de la doctrine `AI-LOCAL-FIRST`
- N'est pas un outil de remplacement pour les modèles frontier sur les tâches complexes — c'est un filtre et une couche de souveraineté

---

### 2.5 Antigravity — Laboratoire Agentique Futur

**Rôle :** Espace d'expérimentation contrôlée pour les patterns agentiques avancés.

Responsabilités (futures) :
- Expérimenter de nouveaux patterns d'orchestration multi-agent
- Tester des pipelines agentiques autonomes dans un environnement isolé
- Explorer les cas d'usage avancés : agents en boucle, memory augmentée, planification multi-step

Contraintes actuelles :
- **Pas un outil de production pour AEOS aujourd'hui**
- Utilisable uniquement quand les gates AEOS (validation humaine, mémoire, auditabilité) seront suffisamment matures
- Toute expérimentation Antigravity est isolée du repo principal
- Ne merge jamais directement dans `main` sans revue complète et validation CTO

---

## 3. La source de vérité

**L'état d'AEOS est défini par GitHub, pas par un contexte de chat.**

| Source | Ce qu'elle contient |
|---|---|
| **GitHub — `main`** | L'état officiel, validé et auditable du projet |
| **Commits** | L'historique des décisions et des changements |
| **Pull Requests** | La traçabilité des revues et validations |
| **Tests** | La preuve que le code fonctionne |
| **`docs/strategy/`** | La vision produit et les rails |
| **`docs/operations/`** | Les guides opérationnels et le protocole agent |

**Règle fondamentale :** Un contexte de chat, une mémoire d'agent, ou un fichier local non commité ne sont PAS la source de vérité. Si ce n'est pas dans GitHub, ce n'est pas officiel.

---

## 4. Protocole obligatoire avant chaque tâche agent

Avant de commencer tout travail sur AEOS, tout agent (Claude Code, Codex, Antigravity, ou autre) doit exécuter ce protocole dans l'ordre.

### 4.1 Lecture des documents de contexte

Lire ces documents dans cet ordre :

1. `docs/strategy/AEOS-PRODUCT-VISION.md`
2. `docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md`
3. `docs/operations/AEOS-AI-MAC-WORKSTATION-SETUP.md`
4. `docs/operations/AEOS-CTO-HANDOFF.md`
5. `docs/operations/AEOS-SPRINT-LOG.md`
6. `docs/operations/AEOS-NEXT-ACTIONS.md`
7. `docs/operations/AEOS-MULTI-AGENT-WORKFLOW.md` ← ce document

### 4.2 Actions post-lecture

Après la lecture, l'agent doit :

1. **Résumer l'état actuel** : branche active, sprint en cours, derniers commits structurants
2. **Confirmer la branche** : quelle branche est active, est-elle à jour avec `origin/main`
3. **Proposer un plan** : liste des fichiers à modifier, actions à effectuer, commandes à lancer
4. **Attendre validation** si le changement est sensible (modification de code Python, migration, changement d'architecture, toucher un projet client)

### 4.3 Prompt de démarrage standard

```
Before doing any work on AEOS, read:

* docs/strategy/AEOS-PRODUCT-VISION.md
* docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md
* docs/operations/AEOS-AI-MAC-WORKSTATION-SETUP.md
* docs/operations/AEOS-CTO-HANDOFF.md
* docs/operations/AEOS-SPRINT-LOG.md
* docs/operations/AEOS-NEXT-ACTIONS.md
* docs/operations/AEOS-MULTI-AGENT-WORKFLOW.md

Then:

* summarize the current state (branch, active sprint, last structural commits)
* confirm the active branch and its sync status with origin/main
* propose a plan before modifying any file
* wait for human validation if the change is sensitive
* never read .env
* never display secrets
* never touch client projects unless explicitly instructed
* never apply migrations without explicit gate
* never contact a database
* never confuse AEOS with a Reclaim tool or a Lovable clone
```

---

## 5. Règles interdites — non négociables

Ces règles s'appliquent à tous les agents sans exception.

| Règle | Description |
|---|---|
| **Ne jamais lire `.env`** | Ni l'afficher, ni le copier, ni le transmettre |
| **Ne jamais afficher de secrets** | Clés API, tokens, mots de passe, credentials |
| **Ne jamais modifier un projet client** | `ma-mairie-digitale` et tout autre projet client sont hors scope sans instruction explicite |
| **Ne jamais appliquer une migration** | `supabase db push`, `apply_migration` ou équivalent sont interdits sans gate humain explicite |
| **Ne jamais contacter une base de données** | Pas de connexion Supabase, PostgreSQL, ou autre sans demande explicite |
| **Ne jamais faire de correction destructive** | Pas de `git reset --hard`, pas de suppression de fichiers sans confirmation |
| **Ne jamais confondre AEOS** | AEOS n'est pas un simple outil Reclaim, ni un clone de Lovable — c'est un AI Engineering Operating System complet |

---

## 6. Checks obligatoires avant PR

Avant toute Pull Request, les commandes suivantes doivent passer sans erreur :

```bash
# Synchroniser les dépendances
uv sync --extra dev --extra test

# Vérifier la qualité du code
uv run ruff check .

# Vérifier le formatage
uv run ruff format --check .

# Vérifier les types
uv run mypy src

# Lancer les tests
uv run pytest

# Vérifier l'état du repo
git status
```

**Aucune PR ne doit être créée si l'un de ces checks échoue.**

---

## 7. Modèle opérationnel final

```
ChatGPT conseille.
Le repo se souvient.
Claude Code exécute localement.
Codex travaille en parallèle sur des PRs isolées.
L'IA locale protège la souveraineté.
Antigravity expérimente.
GitHub prouve.
L'humain valide.
```

Ce modèle garantit :
- **Continuité** : l'état AEOS est toujours récupérable depuis GitHub
- **Sécurité** : les données sensibles ne quittent pas l'environnement local sans autorisation
- **Souveraineté** : aucun vendor lock-in sur un agent ou un modèle IA
- **Traçabilité** : chaque décision est documentée et chaque changement est dans Git
- **Autonomie humaine** : aucune action destructrice sans gate humain explicite

---

## 8. Historique des mises à jour

| Date | Mise à jour |
|---|---|
| 2026-06-29 | Création initiale — sprint3f3/multi-agent-operating-model |
