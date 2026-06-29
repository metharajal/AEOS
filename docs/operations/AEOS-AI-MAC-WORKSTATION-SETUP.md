# AEOS AI Mac Workstation Setup

**Version :** 2026-06-29  
**Auteur :** AEOS Operations  
**Branche :** sprint3f/memory-layer-mvp

---

## 1. Objectif

Ce guide permet de reconstruire de zéro une workstation Mac complète pour le projet AEOS.  
Il couvre l'IA locale, le développement Python/Node, les audits clients, les outils DevOps et la reprise de projets existants sur un nouveau Mac.

---

## 2. Principes fondamentaux

| Principe | Description |
|---|---|
| **LOCAL-FIRST** | Tout ce qui peut tourner localement doit tourner localement. |
| **OPEN-SOURCE-FIRST** | Préférer les outils open-source éprouvés. |
| **AI-LOCAL-FIRST** | Les modèles IA doivent tourner localement par défaut (Ollama). Le frontier AI (Claude, GPT) est réservé aux cas où le local est insuffisant. |
| **FRONTIER AI ONLY WHEN NECESSARY** | Ne pas envoyer de données sensibles à un LLM cloud sans justification explicite. |
| **NO SECRETS COPIED BLINDLY** | Ne jamais copier un `.env` sans lecture et rotation préalable. |
| **NO .ENV WITHOUT REVIEW** | Chaque `.env` doit être inspecté manuellement avant usage sur une nouvelle machine. |
| **GITHUB AS SOURCE OF TRUTH** | Le code source vit sur GitHub. La machine locale est un poste de travail, pas une sauvegarde. |
| **UV SYNC RECREATES PYTHON ENV** | `uv sync` suffit à recréer l'environnement Python. Pas besoin de copier `.venv`. |
| **DOCKER + OLLAMA = LOCAL RUNTIME** | Docker et Ollama forment les fondations du runtime local pour les services et les modèles IA. |

---

## 3. Installation système minimale

### 3.1 Xcode Command Line Tools

```bash
xcode-select --install
```

### 3.2 Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew --version
# Homebrew 6.0.4+
```

### 3.3 Git

```bash
brew install git
git --version
# git version 2.50.1+
```

### 3.4 GitHub CLI

```bash
brew install gh
gh auth login
gh auth status
# ✓ Logged in to github.com as metharajal
```

### 3.5 uv (gestionnaire Python)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version
# uv 0.11.24+
```

### 3.6 VS Code

Télécharger depuis https://code.visualstudio.com/  
Version cible : 1.126.0+

```bash
code --version
```

### 3.7 Claude Code

```bash
npm install -g @anthropic-ai/claude-code
claude --version
# 2.1.187+
```

---

## 4. Tooling Python / AEOS

### 4.1 Cloner AEOS

```bash
mkdir -p ~/Development
cd ~/Development
git clone https://github.com/metharajal/AEOS.git
cd AEOS
```

### 4.2 Créer et activer l'environnement Python

```bash
uv sync
source .venv/bin/activate
```

> Ne jamais copier un `.venv` d'une autre machine. `uv sync` recrée l'environnement proprement à partir de `pyproject.toml`.

### 4.3 Vérifier AEOS

```bash
uv run aeos --version
uv run aeos doctor
```

### 4.4 Qualité de code

```bash
ruff check .
ruff format --check .
mypy src
pytest
```

---

## 5. Tooling Node

### 5.1 Node.js

```bash
brew install node
node --version
# v24.18.0+
npm --version
# 11.16.0+
```

### 5.2 pnpm

```bash
npm install -g pnpm
pnpm --version
# 11.9.0+
```

### 5.3 Bun (optionnel)

Bun est optionnel. À installer uniquement si un projet client le requiert explicitement.

```bash
curl -fsSL https://bun.sh/install | bash
bun --version
```

---

## 6. Docker / DevOps

### 6.1 Docker Desktop

Télécharger depuis https://www.docker.com/products/docker-desktop/

```bash
docker --version
# Docker version 29.5.3+
docker compose version
# Docker Compose version v5.1.4+
docker info
```

### 6.2 Outils Kubernetes et Infrastructure

```bash
brew install kubectl helm k9s terraform trivy argocd jq yq tree
```

Vérifications :

```bash
kubectl version --client
helm version
k9s version
terraform --version
trivy --version
argocd version --client
jq --version
yq --version
tree --version
```

---

## 7. IA locale (Local AI)

### 7.1 Ollama — outil recommandé (AEOS AI-LOCAL-FIRST)

Ollama est l'outil principal pour exécuter des LLM localement dans AEOS.  
Son intégration CLI reproductible en fait la référence pour tout développement IA local.

**Installation via Homebrew :**

```bash
brew install ollama
```

Ou via le script officiel :

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Démarrage du service :**

```bash
ollama serve &
```

**Vérifications :**

```bash
ollama --version
ollama list
```

**Modèles recommandés pour AEOS :**

```bash
ollama pull llama3.2
ollama pull mistral
ollama run llama3.2
```

### 7.2 LM Studio (complémentaire, non recommandé pour AEOS)

LM Studio peut exister comme outil complémentaire à titre personnel.  
Cependant, **AEOS doit privilégier Ollama** pour toute intégration IA locale :

- Ollama est CLI-first et scriptable.
- Ollama est reproductible entre machines via `brew install` ou `curl`.
- LM Studio est une application GUI sans équivalent CLI fiable pour l'automatisation.

---

## 8. Cloud / Provider CLIs

### 8.1 Supabase CLI — recommandé

Installé et requis pour tous les projets utilisant Supabase comme backend.

```bash
brew install supabase/tap/supabase
supabase --version
# 2.108.0+
supabase login
```

### 8.2 Vercel CLI — optionnel

À installer uniquement si le projet déploie sur Vercel.

```bash
npm install -g vercel
vercel --version
```

### 8.3 AWS CLI — optionnel

À installer uniquement si le projet utilise des services AWS.

```bash
brew install awscli
aws --version
aws configure
```

---

## 9. Reprise AEOS sur un nouveau Mac

Séquence complète pour reprendre le travail AEOS from scratch :

```bash
mkdir -p ~/Development
cd ~/Development
git clone https://github.com/metharajal/AEOS.git
cd AEOS
uv sync
source .venv/bin/activate
uv run aeos --version
git status
```

Vérifications supplémentaires :

```bash
git log --oneline -5
uv run aeos doctor
pytest
```

---

## 10. Reprise projets clients

### 10.1 Cloner le projet client

```bash
mkdir -p ~/aeos-client-audits
cd ~/aeos-client-audits
git clone https://github.com/metharajal/ma-mairie-digitale.git
cd ma-mairie-digitale
```

### 10.2 Règles strictes sur les secrets

```bash
# Vérifier que .env n'est pas tracké
git ls-files .env

# Vérifier l'état du dépôt
git status
```

> **Ne jamais copier `.env` aveuglément d'une ancienne machine.**  
> Inspecter le fichier, vérifier chaque variable, effectuer une rotation des secrets si nécessaire.

### 10.3 Relancer l'analyse AEOS

```bash
cd ~/Development/AEOS
source .venv/bin/activate
uv run aeos reclaim harden --project ~/aeos-client-audits/ma-mairie-digitale
```

---

## 11. Sécurité secrets / .env

### Règles strictes

- **Ne jamais afficher `.env` dans un terminal partagé ou enregistré.**
- **Ne jamais copier les secrets sans rotation préalable.**
- **Ne jamais committer `.env` dans Git.**

### Vérifications avant de commencer à travailler

```bash
# Vérifier que .env n'est pas dans l'index Git
git ls-files .env
# → aucun résultat attendu

# Vérifier l'état du dépôt
git status

# Vérifier que .env est dans .gitignore
grep '.env' .gitignore
```

### Convention de référence

Chaque projet doit avoir un `.env.example` avec des placeholders :

```
# .env.example
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
OPENAI_API_KEY=sk-...
```

> Si des secrets ont été commités dans l'historique Git, traiter cela comme un incident de sécurité :  
> rotation immédiate des clés concernées, puis nettoyage de l'historique (`git filter-branch` ou BFG Repo Cleaner).

---

## 12. Validation finale sur un nouveau Mac

Checklist complète avant de commencer à travailler :

| Composant | Commande de vérification | Statut attendu |
|---|---|---|
| Homebrew | `brew --version` | ✓ 6.0.4+ |
| GitHub CLI | `gh auth status` | ✓ Logged in as metharajal |
| uv | `uv --version` | ✓ 0.11.24+ |
| Python | `python --version` | ✓ 3.14+ |
| Docker | `docker --version` | ✓ 29.5.3+ |
| Docker Compose | `docker compose version` | ✓ v5.1.4+ |
| Supabase CLI | `supabase --version` | ✓ 2.108.0+ |
| Ollama | `ollama --version` | ✓ installé (sinon : `brew install ollama`) |
| VS Code | `code --version` | ✓ 1.126.0+ |
| Claude Code | `claude --version` | ✓ 2.1.187+ |
| AEOS cloné | `ls ~/Development/AEOS` | ✓ présent |
| AEOS Python env | `uv run aeos --version` | ✓ version affichée |
| AEOS tests | `pytest` | ✓ tous verts |
| Client audits | `ls ~/aeos-client-audits` | ✓ dossier présent |
| Secrets exposés | `git ls-files .env` | ✓ aucun résultat |

---

## 13. Inventaire de référence — Mac actuel (2026-06-29)

### Installé

| Outil | Version |
|---|---|
| macOS | 26.3 (arm64) |
| Homebrew | 6.0.4 |
| Git | 2.50.1 |
| GitHub CLI | 2.95.0 (connecté : metharajal) |
| uv | 0.11.24 |
| Python (via uv) | 3.14.6 |
| Node.js | v24.18.0 |
| npm | 11.16.0 |
| pnpm | 11.9.0 |
| Docker | 29.5.3 |
| Docker Compose | v5.1.4 |
| Supabase CLI | 2.108.0 |
| VS Code | 1.126.0 |
| Claude Code | 2.1.187 |
| kubectl | ✓ |
| helm | ✓ |
| k9s | ✓ |
| terraform | ✓ |
| trivy | ✓ |
| argocd | ✓ |
| jq | ✓ |
| yq | ✓ |
| tree | ✓ |
| AEOS repo | ~/Development/AEOS |
| Client project | ~/aeos-client-audits/ma-mairie-digitale |

### Absent — à installer sur nouveau Mac

| Outil | Priorité | Commande |
|---|---|---|
| Ollama | **Recommandé** (AI-LOCAL-FIRST) | `brew install ollama` |

### Optionnel selon les projets

| Outil | Condition |
|---|---|
| Vercel CLI | Projets déployés sur Vercel |
| AWS CLI | Projets utilisant des services AWS |
| Bun | Projets Node.js qui requièrent Bun explicitement |

---

## 14. Troubleshooting

### Problème 1 — Ancien dossier AI-Foundation-Kit ouvert dans VS Code

**Symptôme :** VS Code affiche le mauvais workspace. Le terminal affiche un prompt `ai-foundation-kit` au lieu de `AEOS`.

**Solution :**

1. Fermer VS Code.
2. Ouvrir VS Code en pointant sur le bon dossier :

```bash
code ~/Development/AEOS
```

---

### Problème 2 — Ancien `.venv` avec mauvais `VIRTUAL_ENV`

**Symptôme :** `VIRTUAL_ENV` pointe vers un ancien chemin (`ai-foundation-kit`, `~/.venv`, etc.).  
`uv run` ou `python` utilisent le mauvais interpréteur.

**Solution :**

```bash
cd ~/Development/AEOS
rm -rf .venv
uv sync
source .venv/bin/activate
python --version
which python
# → doit afficher ~/Development/AEOS/.venv/bin/python
```

---

### Problème 3 — Prompt shell affiche l'ancien projet

**Symptôme :** Le prompt affiche `ai-foundation-kit` au lieu de `AEOS` ou du répertoire courant.

**Cause :** L'environnement virtuel d'un ancien projet est toujours actif dans la session shell.

**Solution :**

```bash
deactivate
cd ~/Development/AEOS
source .venv/bin/activate
```

---

### Problème 4 — Caches `__pycache__` corrompus ou obsolètes

**Symptôme :** Erreurs d'import inattendues, tests échouent sans raison apparente après un changement d'environnement.

**Solution :**

```bash
cd ~/Development/AEOS
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
uv sync
pytest
```

---

*Document généré le 2026-06-29 — à mettre à jour à chaque changement majeur d'environnement.*
