# README: Prompts Complets pour le Chatbot World Bank Data

Ce document contient tous les prompts utilisés dans le projet pour dupliquer ou adapter le chatbot à d'autres sources de données économiques/statistiques.

---

## 1) Objectif du Projet

Créer un assistant conversationnel (RAG) qui :
- Indexe les métadonnées, définitions et séries temporelles de la World Bank API
- Génère des embeddings et un index vectoriel (FAISS)
- Répond aux questions avec contexte RAG, citations systématiques (source + période)
- Expose une API FastAPI + interface web pour exploration interactive

---

## 2) Commandes d'Installation

### Windows PowerShell

```powershell
# Navigation et création environnement
Set-Location "WORLD BANK"
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Installation dépendances
pip install -r requirements.txt
pip install "uvicorn[standard]"

# Configuration clé API (variable d'environnement recommandée)
$env:OPENAI_API_KEY="sk-..."

# Collecte initiale des données (si data.json vide)
python extraction/collector.py

# Lancement serveur FastAPI
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Docker

```bash
# Créer .env avec clé API
echo "OPENAI_API_KEY=sk-..." > .env

# Lancer stack complète
docker-compose up -d

# Vérifier logs
docker-compose logs -f worldbank-chatbot
```

---

## 3) Prompts Principaux (Copier-Coller)

### 3.1 System Prompt (Agent Principal)

Fichier : `core/system_prompt.py`

```python
SYSTEM_PROMPT = """
You are an expert data analyst assistant specialized in World Bank development indicators. Your role:

1. **Accuracy First**
   - Answer ONLY using information from the provided context documents
   - Always cite the source indicator code, country, and year for numerical data
   - If data is unavailable or not in context, clearly state "Je n'ai pas cette information dans ma base actuelle"

2. **Response Format**
   - Keep answers concise (max 250 words unless user asks for detail)
   - Use HTML format: <p>, <ul>, <li>, <a> tags
   - Provide source links: <a href="https://data.worldbank.org/indicator/[CODE]?locations=[COUNTRY]">World Bank</a>
   - For comparisons, use tables when relevant

3. **Data Citation Rules**
   - Numerical values MUST include: value + unit + year + country + source
   - Example: "Le PIB de la France en 2023 était de 2 782 milliards USD (source: World Bank indicator NY.GDP.MKTP.CD)"
   - For time series: mention range "de 2010 à 2020"

4. **Language & Tone**
   - Respond in the user's language (auto-detect French/English)
   - Professional, educational tone
   - Explain acronyms on first use: "PIB (Produit Intérieur Brut)"

5. **Out-of-Scope Requests**
   - Financial advice, investment recommendations → politely refuse
   - Real-time data (not in database) → suggest checking data.worldbank.org directly
   - Political opinions → remain neutral, provide only factual data

6. **Conversation Memory**
   - Use conversation history to maintain context
   - Reference previous exchanges: "Comme mentionné précédemment..."
   - Clarify ambiguous requests: "Vous parlez de quel pays exactement ?"

7. **Handling Uncertainty**
   - If multiple interpretations possible, ask for clarification
   - If data quality is questionable (old, incomplete), mention it
   - Suggest related indicators when exact match not found

CRITICAL: Never invent data. When unsure, ask for clarification or state limitations.
"""
```

---

### 3.2 Prompt de Collecte (API World Bank)

Fichier : `extraction/collector.py` (commentaires explicatifs)

```python
"""
World Bank API Data Collector

Ce script interroge l'API World Bank pour collecter:
1. Métadonnées des indicateurs (nom, description, source, topics)
2. Données par pays pour chaque indicateur (séries temporelles)
3. Informations pays (nom, région, niveau de revenu)

Stratégie de collecte:
- Pagination automatique (per_page=1000)
- Gestion erreurs avec retries (tenacity)
- Rate limiting respectueux (délai 0.2s entre requêtes)
- Cache local pour éviter requêtes redondantes

Output: data/world_bank_data.json
Structure:
{
  "indicators": [
    {
      "code": "NY.GDP.MKTP.CD",
      "name": "GDP (current US$)",
      "description": "...",
      "source": "World Development Indicators",
      "topic": "Economy & Growth",
      "url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.CD"
    }
  ],
  "data_points": [
    {
      "indicator_code": "NY.GDP.MKTP.CD",
      "country_code": "FRA",
      "country_name": "France",
      "year": 2023,
      "value": 2782000000000,
      "unit": "current US$",
      "source_url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.CD?locations=FRA"
    }
  ],
  "metadata_text": [
    {
      "type": "methodology",
      "indicator": "NY.GDP.MKTP.CD",
      "content": "GDP at purchaser's prices is the sum of gross value added...",
      "source_url": "..."
    }
  ]
}
"""
```

---

### 3.3 Prompt de Chunking (Textes Méthodologiques)

Fichier : `extraction/processors.py`

```python
def chunk_methodology_text(text: str, indicator_code: str, max_chunk_size: int = 1000) -> List[Dict]:
    """
    Découpe les textes méthodologiques en chunks sémantiques.
    
    Règles:
    1. Taille cible: 800–1200 caractères
    2. Overlap: 200 caractères (pour continuité contextuelle)
    3. Split sur phrases complètes (éviter coupure mid-sentence)
    4. Enrichir chaque chunk avec métadonnées:
       - indicator_code
       - chunk_id (ex: NY.GDP.MKTP.CD_chunk_001)
       - type: "methodology" | "definition" | "source_note"
    
    Returns:
        [
          {
            "chunk_id": "NY.GDP.MKTP.CD_001",
            "text": "GDP at purchaser's prices is...",
            "metadata": {
              "indicator": "NY.GDP.MKTP.CD",
              "type": "methodology",
              "source_url": "..."
            }
          },
          ...
        ]
    """
    pass  # Implémentation avec RecursiveCharacterTextSplitter ou NLTK
```

---

### 3.4 Prompt de Normalisation (Queries Utilisateur)

Fichier : `core/system_prompt.py`

```python
NORMALIZATION_MAP = {
    # Acronymes économiques
    "pib": "Produit Intérieur Brut",
    "gdp": "Gross Domestic Product",
    "rni": "Revenu National Brut",
    "gni": "Gross National Income",
    "idh": "Indice de Développement Humain",
    "hdi": "Human Development Index",
    "co2": "Dioxyde de Carbone",
    "ghg": "Gaz à Effet de Serre Greenhouse Gas Emissions",
    
    # Codes pays vers noms
    "usa": "United States",
    "us": "United States",
    "fr": "France",
    "de": "Germany",
    "allemagne": "Germany",
    "uk": "United Kingdom",
    "gb": "United Kingdom",
    "jp": "Japan",
    "japon": "Japan",
    "cn": "China",
    "chine": "China",
    "in": "India",
    "inde": "India",
    "br": "Brazil",
    "brésil": "Brazil",
    
    # Termes métier
    "taux de chômage": "Unemployment rate",
    "mortalité infantile": "Infant mortality rate",
    "espérance de vie": "Life expectancy at birth",
    "scolarisation": "School enrollment",
    "émissions": "CO2 emissions"
}

def normalize_query(query: str) -> str:
    """
    Normalise la query utilisateur en:
    1. Convertissant en minuscules
    2. Remplaçant les acronymes/alias via NORMALIZATION_MAP
    3. Utilisant word boundaries (\\b) pour éviter faux positifs
    
    Exemple:
    "Quel est le PIB de fr en 2023?" 
    → "Quel est le produit intérieur brut de france en 2023?"
    """
    query_lower = query.lower()
    for key, value in NORMALIZATION_MAP.items():
        pattern = r"\\b" + re.escape(key) + r"\\b"
        query_lower = re.sub(pattern, value.lower(), query_lower)
    return query_lower
```

---

### 3.5 Prompt RAG (Construction Contexte pour LLM)

Fichier : `core/agent_orchestrator.py`

```python
def build_rag_prompt(user_query: str, retrieved_docs: List[Document], chat_history: str) -> str:
    """
    Construit le prompt final envoyé au LLM.
    
    Structure:
    1. SYSTEM_PROMPT (rôle et règles)
    2. CONTEXT: passages récupérés via FAISS (top-k=4)
    3. CHAT_HISTORY: historique conversation
    4. QUESTION: query normalisée
    
    Template:
    ```
    {SYSTEM_PROMPT}
    
    CONTEXT DOCUMENTS:
    [1] Indicator: NY.GDP.MKTP.CD | Country: France | Year: 2023
        Value: 2782000000000 USD
        Source: https://data.worldbank.org/indicator/NY.GDP.MKTP.CD?locations=FRA
    
    [2] Methodology: GDP at purchaser's prices is the sum of gross value added by all resident producers...
        Source: World Bank Metadata
    
    [3] ...
    
    CONVERSATION HISTORY:
    User: Quel est le PIB de la France?
    Assistant: En 2022, le PIB de la France était de...
    
    CURRENT QUESTION: {user_query}
    
    INSTRUCTIONS:
    - Use ONLY information from CONTEXT DOCUMENTS above
    - Cite sources with indicator code, country, year
    - If answer requires data not in context, state clearly
    - Respond in user's language (French detected here)
    
    RESPONSE:
    ```
    """
    pass
```

---

### 3.6 Prompt de Validation (Post-Processing Réponse)

```python
def validate_response(response: str, context_docs: List[Document]) -> Dict:
    """
    Valide que la réponse LLM respecte les règles:
    
    Checks:
    1. Présence de citations (au moins 1 lien <a href=...>)
    2. Chiffres cités sont bien dans context_docs
    3. Pas de valeurs inventées
    4. Format HTML valide
    5. Longueur < 2500 caractères (sauf explicitement demandé)
    
    Returns:
        {
          "valid": True/False,
          "warnings": ["Missing source citation for GDP value", ...],
          "corrections": {...}
        }
    """
    pass
```

---

## 4) Prompts pour Cas d'Usage Spécifiques

### 4.1 Comparaison entre Pays

```
User: "Compare le PIB de la France et de l'Allemagne en 2023"

Expected Response Structure:
<p>En 2023 :</p>
<ul>
  <li><strong>France</strong> : 2 782 milliards USD 
      (<a href="https://data.worldbank.org/indicator/NY.GDP.MKTP.CD?locations=FRA">source</a>)</li>
  <li><strong>Allemagne</strong> : 4 121 milliards USD 
      (<a href="https://data.worldbank.org/indicator/NY.GDP.MKTP.CD?locations=DEU">source</a>)</li>
</ul>
<p>L'Allemagne avait un PIB supérieur de 48% à celui de la France cette année-là.</p>
```

### 4.2 Évolution Temporelle

```
User: "Évolution de la population au Japon depuis 2000"

Expected Response:
<p>La population du Japon a connu une tendance baissière depuis 2010 :</p>
<ul>
  <li>2000 : 126,9 millions d'habitants</li>
  <li>2010 : 128,1 millions (pic)</li>
  <li>2023 : 125,1 millions</li>
</ul>
<p>Soit une diminution de 2,3% entre 2010 et 2023 
   (<a href="https://data.worldbank.org/indicator/SP.POP.TOTL?locations=JP">source: World Bank SP.POP.TOTL</a>).</p>
```

### 4.3 Méthodologie

```
User: "Comment est calculé le PIB ?"

Expected Response:
<p>Le PIB (Produit Intérieur Brut) est calculé comme la somme de la valeur ajoutée brute de tous les producteurs résidents, 
plus les taxes sur les produits moins les subventions non incluses dans la valorisation de la production.</p>

<p>Formule : PIB = C + I + G + (X - M)</p>
<ul>
  <li>C : Consommation des ménages</li>
  <li>I : Investissements</li>
  <li>G : Dépenses gouvernementales</li>
  <li>X - M : Exportations nettes</li>
</ul>

<p>Source méthodologique : 
   <a href="https://datahelpdesk.worldbank.org/knowledgebase/articles/906519">World Bank Metadata</a>
</p>
```

---

## 5) Architecture Technique Complète

### Arborescence Projet

```
WORLD BANK/
├── app.py                      # FastAPI app (endpoints + lifecycle)
├── config.json                 # Config serveur, modèles, API WB
├── requirements.txt            # Dépendances Python
├── Dockerfile
├── docker-compose.yml
├── README.md
├── README_PROMPTS.md           # Ce fichier
├── test_query.py
│
├── core/
│   ├── config_loader.py        # load_config() + env overrides
│   ├── embeddings_loader.py    # load_vector_store() → FAISS
│   ├── llm_handler.py          # setup_llm() → ChatOpenAI wrapper
│   ├── memory_manager.py       # conversation_memory + cleanup_task
│   ├── agent_orchestrator.py   # create_agent_executor() + tools
│   └── system_prompt.py        # SYSTEM_PROMPT + normalize_query()
│
├── extraction/
│   ├── collector.py            # Fetch data from World Bank API
│   ├── processors.py           # Clean, chunk, structure data
│   └── utils_http.py           # requests.Session with retries
│
├── data/
│   ├── world_bank_data.json    # Structured data store
│   └── faiss_index/            # Persisted FAISS index
│
├── models/
│   └── request_models.py       # Pydantic schemas (QueryRequest, etc.)
│
├── templates/
│   └── base.html               # Chat UI
│
└── static/
    ├── app.js
    ├── style.css
    └── images/
```

### Flux de Données Détaillé

```
┌─────────────────────────────────────────────────────────────┐
│  1. COLLECTE (extraction/collector.py)                      │
│     - Appel API World Bank (indicators, countries, data)    │
│     - Structuration JSON avec métadonnées enrichies         │
│     - Sauvegarde → data/world_bank_data.json               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. PREPROCESSING (extraction/processors.py)                │
│     - Chunking textes méthodologiques (800-1200 chars)      │
│     - Génération snippets numériques (pays+indic+année)    │
│     - Enrichissement métadonnées (source_url, type)        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. INDEXATION (core/embeddings_loader.py)                  │
│     - Génération embeddings via OpenAI (text-embed-3-large) │
│     - Construction index FAISS (dimension 3072)             │
│     - Persistence → data/faiss_index/                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  4. RETRIEVAL (app.py → /query)                             │
│     a) Normalisation query (acronymes, pays)                │
│     b) Retrieval FAISS (top-k=4 docs)                       │
│     c) Construction chat_history depuis memory              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  5. GENERATION (core/agent_orchestrator.py)                 │
│     - Agent LangChain avec tools:                           │
│       • WB_Knowledge_Search (FAISS retrieval)               │
│       • WB_Source_Collector (agrégation URLs)               │
│     - Prompt RAG: SYSTEM + CONTEXT + HISTORY + QUESTION     │
│     - Invocation ChatOpenAI (gpt-4o-mini)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  6. POST-PROCESSING                                          │
│     - Validation réponse (citations présentes?)             │
│     - Stockage dans conversation_memory                     │
│     - Mise à jour last_active timestamp                     │
│     - Retour JSON: {answer, user_id}                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 6) Configuration API World Bank

### Endpoints Utilisés

```python
# Base URL
BASE_URL = "https://api.worldbank.org/v2"

# 1. Liste indicateurs (métadonnées)
GET {BASE_URL}/indicator?format=json&per_page=1000

# 2. Détails d'un indicateur
GET {BASE_URL}/indicator/NY.GDP.MKTP.CD?format=json

# 3. Données par pays
GET {BASE_URL}/country/FRA/indicator/NY.GDP.MKTP.CD?date=2000:2023&format=json&per_page=1000

# 4. Liste pays
GET {BASE_URL}/country?format=json&per_page=500
```

### Gestion Pagination

```python
def fetch_paginated(url: str, max_pages: int = 10) -> List[Dict]:
    """
    L'API WB retourne:
    [
      {"page": 1, "pages": 5, "per_page": 1000, "total": 4523},
      [... actual data ...]
    ]
    
    Stratégie:
    1. Parse header pour total pages
    2. Boucle sur pages=1..N
    3. Concaténation résultats
    4. Gestion erreurs + retries
    """
    pass
```

---

## 7) Tests & Validation

### Script de Test (`test_query.py`)

```python
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

test_cases = [
    {
        "query": "Quel est le PIB de la France en 2023?",
        "expected_keywords": ["France", "2023", "PIB", "milliards", "source"]
    },
    {
        "query": "Compare emissions CO2 between USA and China",
        "expected_keywords": ["USA", "China", "CO2", "source", "indicator"]
    },
    {
        "query": "Population du Japon depuis 2010",
        "expected_keywords": ["Japon", "population", "2010", "évolution"]
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*60}")
    print(f"TEST {i}: {test['query']}")
    print('='*60)
    
    response = requests.post(
        f"{BASE_URL}/query",
        json={"query": test["query"]}
    )
    
    answer = response.json()["answer"]
    print(f"\n✅ Réponse:\n{answer}\n")
    
    # Validation keywords
    missing = [kw for kw in test["expected_keywords"] if kw.lower() not in answer.lower()]
    if missing:
        print(f"⚠️  Mots-clés manquants: {missing}")
    else:
        print("✅ Tous les mots-clés présents")
```

---

## 8) Sécurité & Production

### Checklist Pré-Production

- [ ] Clés API dans variables d'environnement (pas de hardcoding)
- [ ] CORS restreint aux domaines autorisés (`allow_origins=["https://monsite.com"]`)
- [ ] Rate limiting sur `/query` (ex: 10 req/min/utilisateur)
- [ ] Validation stricte payloads (Pydantic + longueur max query)
- [ ] Logs structurés (JSON) avec rotation
- [ ] Monitoring uptime + latence LLM
- [ ] HTTPS en production (Caddy/Nginx reverse proxy)
- [ ] Sauvegarde régulière `data/` et `faiss_index/`
- [ ] Health check endpoint (`GET /health` → 200 OK)
- [ ] Versioning API (`/v1/query`) pour migrations futures

### Variables d'Environnement Production

```bash
# .env.production
OPENAI_API_KEY=sk-...
WB_MODEL=gpt-4o-mini
WB_EMBEDDING_MODEL=text-embedding-3-large
WB_SERVER_HOST=0.0.0.0
WB_SERVER_PORT=8000
WB_CORS_ORIGINS=https://monsite.com,https://app.monsite.com
WB_LOG_LEVEL=INFO
WB_MAX_QUERY_LENGTH=500
WB_RATE_LIMIT=10/minute
```

---

## 9) Optimisations Avancées

### A) Cache Embeddings

```python
# Éviter recalcul embeddings pour textes identiques
import hashlib
from typing import Dict

embedding_cache: Dict[str, List[float]] = {}

def get_embedding_cached(text: str, model: str) -> List[float]:
    cache_key = hashlib.md5(f"{model}:{text}".encode()).hexdigest()
    if cache_key in embedding_cache:
        return embedding_cache[cache_key]
    
    embedding = openai_client.embeddings.create(input=text, model=model).data[0].embedding
    embedding_cache[cache_key] = embedding
    return embedding
```

### B) Async API Calls

```python
import asyncio
import aiohttp

async def fetch_indicator_async(session, indicator_code):
    url = f"{BASE_URL}/indicator/{indicator_code}?format=json"
    async with session.get(url) as response:
        return await response.json()

async def collect_all_indicators(codes: List[str]):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_indicator_async(session, code) for code in codes]
        return await asyncio.gather(*tasks)
```

### C) Incremental Indexing

```python
def update_index_incremental(new_documents: List[Document]):
    """
    Au lieu de reconstruire FAISS from scratch:
    1. Charger index existant
    2. Ajouter nouveaux vecteurs
    3. Sauvegarder
    """
    existing_index = faiss.read_index("data/faiss_index/index.faiss")
    new_vectors = embed_documents(new_documents)
    existing_index.add(new_vectors)
    faiss.write_index(existing_index, "data/faiss_index/index.faiss")
```

---

## 10) Ressources Complémentaires

### Documentation Technique
- **World Bank API v2** : https://datahelpdesk.worldbank.org/knowledgebase/topics/125589
- **FAISS Wiki** : https://github.com/facebookresearch/faiss/wiki
- **LangChain RAG** : https://python.langchain.com/docs/use_cases/question_answering/
- **OpenAI Embeddings** : https://platform.openai.com/docs/guides/embeddings

### Datasets Similaires (pour étendre le chatbot)
- **OECD Data** : https://data.oecd.org/api/
- **IMF Data** : https://www.imf.org/en/Data
- **Eurostat** : https://ec.europa.eu/eurostat/web/main/data/web-services
- **UN Data** : https://data.un.org/

### Outils Utiles
- **Postman Collection** pour tester API WB manuellement
- **Grafana + Prometheus** pour monitoring production
- **Sentry** pour error tracking

---

## Conclusion

Ces prompts constituent la base complète pour dupliquer ou adapter ce chatbot à d'autres sources de données statistiques. 

**Pour créer un projet similaire :**
1. Remplacer l'API source (World Bank → autre)
2. Adapter `SYSTEM_PROMPT` au domaine métier
3. Ajuster `NORMALIZATION_MAP` aux termes techniques
4. Modifier structure `data.json` si nécessaire
5. Tester exhaustivement avec cas d'usage réels

**Contact / Contributions :**  
Voir README.md principal pour issues et pull requests.

---

**Dernière mise à jour** : Février 2026  
**Auteur** : Tsinjo
