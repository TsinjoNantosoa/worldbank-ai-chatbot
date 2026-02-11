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

### 2. Collecte Personnalisée

```powershell
# Spécifier indicateurs
python -m EXTRACTION_WB.collector \
  --indicators NY.GDP.MKTP.CD SP.POP.TOTL SL.UEM.TOTL.ZS

# Spécifier pays
python -m EXTRACTION_WB.collector \
  --countries FRA DEU USA JPN CHN

# Plage de dates
python -m EXTRACTION_WB.collector \
  --date-range 2015:2023

# Combiner tout
python -m EXTRACTION_WB.collector \
  --indicators NY.GDP.MKTP.CD SP.POP.TOTL \
  --countries FRA DEU \
  --date-range 2018:2023 \
  --output data/custom_output.json
```

### 3. Exemple Complet

```powershell
python -m EXTRACTION_WB.collector \
  --indicators NY.GDP.MKTP.CD SP.POP.TOTL EN.ATM.CO2E.PC \
  --countries USA FRA DEU GBR JPN CHN IND BRA \
  --date-range 2010:2023
```

---

## Utilisation Docker

### Build Image

```powershell
cd "WORLD BANK\EXTRACTION_WB"
docker build -t wb-extraction -f Dockerfile ..
```

### Run Once

```powershell
docker run --rm \
  -v ${PWD}/../data:/app/data \
  -v ${PWD}/../config.json:/app/config.json:ro \
  wb-extraction
```

### Docker Compose (Collecte Unique)

```powershell
cd "WORLD BANK\EXTRACTION_WB"
docker-compose up wb-extraction
```

### Docker Compose (Collecte Planifiée - Cron)

```powershell
# Démarre service cron (collecte hebdomadaire)
docker-compose --profile cron up -d wb-extraction-cron

# Voir logs
docker-compose logs -f wb-extraction-cron
```

---

## Configuration

### Fichier `config.json`

```json
{
  "world_bank_api": {
    "base_url": "https://api.worldbank.org/v2",
    "indicators": [
      "NY.GDP.MKTP.CD",    // PIB
      "SP.POP.TOTL",       // Population
      "SL.UEM.TOTL.ZS",    // Chômage
      "EN.ATM.CO2E.PC"     // Émissions CO2
    ],
    "countries": [
      "USA", "FRA", "DEU", "GBR", "JPN", "CHN", "IND", "BRA"
    ],
    "date_range": "2000:2023",
    "per_page": 1000,
    "rate_limit_delay_seconds": 0.2
  }
}
```

### Indicateurs Disponibles

Recherchez codes indicateurs sur: https://data.worldbank.org/indicator

**Exemples populaires:**

| Code | Description |
|------|-------------|
| `NY.GDP.MKTP.CD` | PIB (USD courants) |
| `SP.POP.TOTL` | Population totale |
| `SL.UEM.TOTL.ZS` | Taux chômage (%) |
| `EN.ATM.CO2E.PC` | Émissions CO2/hab |
| `SE.PRM.ENRR` | Taux scolarisation primaire |
| `SH.DYN.MORT` | Mortalité infantile |
| `SI.POV.DDAY` | Pauvreté (<$2.15/jour) |

---

## Structure Output

Le fichier `data/world_bank_data.json` généré a cette structure:

```json
{
  "metadata": {
    "collection_date": "2026-02-11T12:00:00",
    "date_range": "2000:2023",
    "indicators_count": 3,
    "countries_count": 5
  },
  "categories": [
    {
      "category": "indicator_NY.GDP.MKTP.CD",
      "name": "GDP (current US$)",
      "description": "GDP at purchaser's prices...",
      "source": "World Bank",
      "pages": [
        {
          "url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.CD?locations=FRA",
          "content": "Indicator: GDP (current US$)...",
          "metadata": {
            "country_code": "FRA",
            "country_name": "France",
            "indicator_code": "NY.GDP.MKTP.CD",
            "data_points_count": 24,
            "latest_year": "2023",
            "latest_value": 2782000000000
          }
        }
      ]
    }
  ]
}
```

---

## Logs & Monitoring

### Logs Console

Les logs sont affichés en temps réel:

```
2026-02-11 12:00:00 - INFO - Initialized WorldBankCollector...
2026-02-11 12:00:01 - INFO - Step 1/3: Fetching indicators metadata...
2026-02-11 12:00:05 - INFO - [1/3] Processing NY.GDP.MKTP.CD
2026-02-11 12:00:30 - INFO - ✅ Done! Collected 3 categories
```

### Logs Docker

```powershell
docker-compose logs -f wb-extraction
```

---

## Troubleshooting

### ❌ "Connection refused" / Timeout

```powershell
# Vérifier connectivité API
curl "https://api.worldbank.org/v2/country?format=json&per_page=1"

# Si proxy requis, configurer
set HTTP_PROXY=http://proxy:8080
set HTTPS_PROXY=http://proxy:8080
```

### ❌ "No data collected"

- Vérifier codes indicateurs/pays valides
- Agrandir plage dates (`--date-range 1990:2023`)
- Certains indicateurs n'ont pas de données récentes

### ❌ "Rate limit exceeded"

Augmenter délai dans `config.json`:

```json
"rate_limit_delay_seconds": 0.5  // au lieu de 0.2
```

---

## Maintenance

### Mise à Jour Régulière

Planifier collecte mensuelle/hebdomadaire:

**Windows Task Scheduler:**
```powershell
# Créer tâche planifiée (dimanche 2h)
schtasks /create /tn "WBDataCollect" /tr "python C:\...\EXTRACTION_WB\collector.py" /sc weekly /d SUN /st 02:00
```

**Docker Cron:**
Utiliser `docker-compose --profile cron up -d`

### Nettoyage

```powershell
# Supprimer anciennes collectes
Remove-Item data\world_bank_data.json.bak

# Reset complet
Remove-Item data\*.json
python -m EXTRACTION_WB.collector  # Recollecte fraîche
```

---

## API World Bank - Ressources

- **Documentation:** https://datahelpdesk.worldbank.org/knowledgebase/topics/125589
- **Browse Indicators:** https://data.worldbank.org/indicator
- **API Explorer:** https://api.worldbank.org/v2/
- **Licence:** CC BY 4.0 (attribution requise)

---

## Support

Pour problèmes:
1. Vérifier logs
2. Tester requête API manuellement (curl)
3. Consulter README principal du projet

---

**Prochaine étape:** Une fois données collectées, lancer le chatbot principal avec ces données indexées.

Voir: [../README.md](../README.md)
