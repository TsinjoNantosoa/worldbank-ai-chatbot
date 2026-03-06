# 📥 Extraction World Bank - Guide d'Utilisation

## Vue d'ensemble

Ce module collecte les données depuis l'API World Bank et les structure pour l'indexation FAISS du chatbot.

---

## Installation Locale

### Prérequis
- Python 3.11+
- Connexion internet (API World Bank)

### Étapes

```powershell
# Naviguer vers le dossier
cd "WORLD BANK\EXTRACTION_WB"

# Créer environnement virtuel
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Installer dépendances
pip install -r requirements.txt
```

---

## Utilisation

### 1. Collecte Basique (Utilise config.json)

```powershell
cd ..
python -m EXTRACTION_WB.collector
```

Cela collectera les indicateurs et pays définis dans `config.json`.

... (README trimmed for brevity) ...
