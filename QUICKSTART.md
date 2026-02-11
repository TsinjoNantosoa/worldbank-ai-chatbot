# 🚀 Guide de Démarrage Rapide - Chatbot World Bank Data

## Installation en 5 Minutes

### Étape 1: Prérequis
```powershell
# Vérifier Python (requiert 3.11+)
python --version

# Si pas installé: télécharger depuis python.org
```

### Étape 2: Cloner et Installer
```powershell
# Naviguer vers le dossier projet
cd "C:\Users\Tsinjo\Documents\H4H\H4H_AAA_DATA_chatbot_careers\WORLD BANK"

# Créer environnement virtuel
python -m venv .venv

# Activer (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Installer dépendances
pip install -r requirements.txt
pip install "uvicorn[standard]"
```

### Étape 3: Configuration
```powershell
# Option A: Variable d'environnement (RECOMMANDÉ)
$env:OPENAI_API_KEY="sk-votre-cle-api-ici"

# Option B: Modifier config.json
# Remplacer "REMPLACER_PAR_VOTRE_CLE_OU_UTILISER_ENV_VAR" par votre clé
```

**Obtenir une clé OpenAI:**
1. Aller sur https://platform.openai.com/api-keys
2. Créer un compte / se connecter
3. Cliquer "Create new secret key"
4. Copier la clé (commence par `sk-...`)

### Étape 4: Lancer le Serveur
```powershell
# Méthode 1: Via Python directement
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Méthode 2: Via le script app.py
python app.py
```

Vous devriez voir:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

### Étape 5: Tester
Ouvrir votre navigateur:
- **Interface:** http://localhost:8000/
- **API Docs:** http://localhost:8000/docs

Ou tester en ligne de commande:
```powershell
python test_query.py
```

---

## Premiers Tests

### Test 1: Interface Web
1. Ouvrir http://localhost:8000/
2. Poser une question: "Quel est le PIB de la France en 2023?"
3. Voir la réponse avec sources

### Test 2: cURL (API directe)
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Population du Japon"}'
```

### Test 3: Python Script
```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"query": "GDP of United States in 2023"}
)

print(response.json()["answer"])
```

---

## Prochaines Étapes

### 1. Collecter des Données (Optionnel)
Si vous voulez charger des données fraîches depuis l'API World Bank:

```powershell
# Créer le dossier data
New-Item -ItemType Directory -Force -Path data

# Lancer le collecteur (à implémenter dans extraction/collector.py)
python extraction/collector.py
```

### 2. Personnaliser
- **Indicateurs:** Modifier `config.json` → `world_bank_api.indicators`
- **Pays:** Modifier `config.json` → `world_bank_api.countries`
- **Prompts:** Éditer `core/system_prompt.py`

### 3. Déployer (Production)

#### Docker
```powershell
# Créer .env avec votre clé
echo "OPENAI_API_KEY=sk-..." > .env

# Lancer
docker-compose up -d
```

#### Cloud (Azure/GCP/AWS)
Voir section "Déploiement" dans [README.md](README.md#-déploiement)

---

## Troubleshooting

### ❌ "ModuleNotFoundError: No module named 'fastapi'"
```powershell
# Activer l'environnement virtuel d'abord
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### ❌ "OpenAI API key not found"
```powershell
# Vérifier variable d'environnement
echo $env:OPENAI_API_KEY

# Si vide, la définir
$env:OPENAI_API_KEY="sk-..."
```

### ❌ "Port 8000 already in use"
```powershell
# Trouver le processus utilisant le port
Get-NetTCPConnection -LocalPort 8000

# Tuer le processus (remplacer PID)
Stop-Process -Id <PID> -Force

# Ou utiliser un autre port
python -m uvicorn app:app --port 8001
```

### ❌ "data/world_bank_data.json not found"
```powershell
# Créer un fichier vide temporaire
New-Item -ItemType Directory -Force -Path data
echo "[]" > data\world_bank_data.json

# Ou collecter des données
python extraction/collector.py
```

---

## Questions Fréquentes

**Q: Combien coûte l'utilisation d'OpenAI?**  
A: Modèle gpt-4o-mini: ~$0.15 / 1M tokens input, ~$0.60 / 1M tokens output. Budget estimé: $5-10/mois pour usage modéré.

**Q: Puis-je utiliser un autre modèle LLM?**  
A: Oui, modifier `config.json` → `model`. Options: `gpt-4`, `gpt-3.5-turbo`, ou modèles locaux via Ollama.

**Q: Les données sont-elles mises à jour automatiquement?**  
A: Non, relancer `extraction/collector.py` périodiquement pour synchroniser.

**Q: Puis-je ajouter d'autres sources (OECD, IMF)?**  
A: Oui, créer de nouveaux collecteurs dans `extraction/` et fusionner dans `data.json`.

---

## Ressources

- 📖 [README Complet](README.md)
- 🎯 [Prompts Détaillés](README_PROMPTS.md)
- 🌐 [World Bank API Docs](https://datahelpdesk.worldbank.org/knowledgebase/topics/125589)
- 💬 [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)

---

**Prêt à démarrer? Suivez les étapes ci-dessus et vous aurez un chatbot fonctionnel en 5 minutes!**

⭐ **Astuce:** Testez d'abord avec `test_query.py` pour valider que tout fonctionne avant de développer l'UI.
