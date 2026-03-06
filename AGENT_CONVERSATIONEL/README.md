# 🌍 Agent Conversationnel — World Bank Data

> Chatbot RAG (Retrieval-Augmented Generation) connecté aux données ouvertes de la Banque Mondiale. Pose une question sur un indicateur économique, social ou environnemental et obtiens une réponse sourcée.

---

## 📋 Sommaire

1. [Vue d'ensemble](#vue-densemble)
2. [Fonctionnalités](#fonctionnalités)
3. [Stack technique](#stack-technique)
4. [Architecture & flux](#architecture--flux)
5. [Interactions entre fonctions](#interactions-entre-fonctions)
6. [Configuration](#configuration)
7. [Données & Vectorisation](#données--vectorisation)
8. [Exécution locale](#exécution-locale)
9. [Déploiement Docker](#déploiement-docker)
10. [Endpoint API](#endpoint-api)
11. [Widget injectable](#widget-injectable)
12. [Tests d'audit](#tests-daudit)
13. [Monitoring & Observabilité](#monitoring--observabilité)
14. [Roadmap](#roadmap)

---

## Vue d'ensemble

L'Agent Conversationnel World Bank est un assistant IA qui répond aux questions sur les indicateurs de développement de la Banque Mondiale (PIB, population, CO₂, santé, éducation, etc.) en s'appuyant sur un index vectoriel FAISS construit à partir des données ouvertes (CC BY 4.0).

**Principes clés :**
- **Pas d'hallucination** — L'agent ne répond qu'à partir du contexte fourni par la base vectorielle
- **Bilingue** — Détection automatique FR / EN
- **Sourcé** — Chaque donnée est accompagnée du code indicateur et d'un lien `data.worldbank.org`
- **Production-ready** — Rate limiting, mémoire, FAQ déterministe, hot-reload, Docker

---

## Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| **RAG vectoriel** | Recherche sémantique FAISS sur les données World Bank |
| **Agent LangChain** | `AgentExecutor` avec 2 outils (Knowledge_Search + Source_Collector) |
| **FAQ déterministe** | Réponses instantanées pour salutations, RGPD, indicateurs disponibles |
| **Normalisation** | Expansion automatique des acronymes (PIB → Produit Intérieur Brut) |
| **Mémoire** | Historique par `user_id`, paires {A,B}, nettoyage auto 30 min |
| **Rate limiting** | slowapi — 20 req/min par IP |
| **Hot-reload** | Rechargement automatique si `data.json` change (via `getmtime`) |
| **Bilingue** | Détection FR/EN, réponse dans la langue de l'utilisateur |
| **Fallback HTML** | Page d'accueil si accès via navigateur (`GET /`) |

---

## Stack technique

| Composant | Technologie |
|---|---|
| Backend | **FastAPI** (Python 3.11+) |
| LLM | **OpenAI GPT-4o-mini** |
| Embeddings | **text-embedding-3-large** (OpenAI) |
| Vector Store | **FAISS** (in-memory) |
| Orchestration | **LangChain** (AgentExecutor + create_openai_tools_agent) |
| Rate Limiting | **slowapi** (20/min par IP) |
| Modèles | **Pydantic v2** |
| Container | **Docker** + docker-compose |
| Widget | **JavaScript** vanille, injectable via `<script>` |

---

## Architecture & flux

```
┌──────────────┐     POST /query       ┌──────────────────────┐
│   Client     │ ──────────────────→   │      app.py          │
│ (Widget JS   │                       │  ┌── FAQ handler     │
│  ou HTML)    │                       │  │   ↓ (si match)    │
│              │ ←──────────────────   │  └── réponse directe │
│              │      JSON             │                      │
│              │ ←──────────────────   │  normalize_query()   │
│              │                       │  ↓                   │
└──────────────┘                       │  AgentExecutor       │
                                       │  ├─ Tool 1: Search   │
                                       │  │  └─ FAISS.as_retriever()
                                       │  ├─ Tool 2: Sources  │
                                       │  │  └─ metadata links│
                                       │  └─ GPT-4o-mini      │
                                       └──────────────────────┘
```

**Flux détaillé :**
1. Le client envoie `{query, user_id, lang}` via `POST /query`
2. `app.py` vérifie le rate limit (slowapi, 20/min)
3. **FAQ handler** — Si la question matche un pattern FAQ → réponse immédiate
4. **normalize_query** — Expansion des acronymes via `config.json`
5. **Mémoire** — Récupération de l'historique `{A,B}` pour le `user_id`
6. **Agent** — `invoke_agent_with_retry()` → LangChain AgentExecutor
7. L'agent utilise ses outils (FAISS retriever) pour chercher le contexte
8. GPT-4o-mini génère la réponse finale en HTML
9. Réponse `{answer, user_id, success}` renvoyée au client

---

## Interactions entre fonctions

```
app.py
 ├── FAQ_handler.get_response(query)       → core/faq_handler.py
 ├── normalize_query(query, config_map)    → inline (app.py)
 ├── build_chat_history(user_id)           → core/memory_manager.py
 ├── invoke_agent_with_retry(query, hist)  → core/agent_orchestrator.py
 │    ├── create_openai_tools_agent(llm, tools, prompt)
 │    │    ├── llm                         → core/llm_handler.py
 │    │    ├── tools[0] = retriever        → core/embeddings_loader.py
 │    │    └── system_prompt               → core/system_prompt.py
 │    └── AgentExecutor.invoke(...)
 ├── check_and_reload_vector_store()       → core/embeddings_loader.py
 └── update_memory(user_id, Q, A)          → core/memory_manager.py
```

---

## Configuration

Le fichier `config.json` centralise toute la configuration :

```json
{
  "DATA_PATH": "data/data.json",
  "LLM_MODEL": "gpt-4o-mini",
  "EMBEDDING_MODEL": "text-embedding-3-large",
  "RETRIEVER_K": 5,
  "MAX_HISTORY_PAIRS": 5,
  "RATE_LIMIT": "20/minute",
  "NORMALIZATION_MAP": { "pib": "Produit Intérieur Brut", ... }
}
```

**Variable d'environnement requise :**
```
OPENAI_API_KEY=sk-...
```

---

## Données & Vectorisation

Le fichier `data/data.json` contient les données extraites du site World Bank. Il peut être au format :

- **Liste de catégories** (format AAA) : `[{category, pages: [{title, url, content}]}]`
- **Dictionnaire** : `{indicators: [{...}], ...}`

Au démarrage, `embeddings_loader.py` :
1. Charge `data.json`
2. Split le contenu en `Document` LangChain
3. Génère les embeddings via `text-embedding-3-large`
4. Crée un index **FAISS** en mémoire
5. Retourne un `retriever` avec `k=5`

Le **hot-reload** surveille `getmtime(data.json)` et recharge automatiquement si le fichier est modifié.

---

## Exécution locale

### Prérequis
- Python 3.11+
- Clé API OpenAI

### Installation

```bash
cd AGENT_CONVERSATIONEL
pip install -r requirements.txt
```

### Lancement

```bash
export OPENAI_API_KEY=sk-...
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

L'API est disponible sur `http://localhost:8000`.
- Documentation Swagger : `http://localhost:8000/docs`
- Page d'accueil HTML : `http://localhost:8000/`

---

## Déploiement Docker

```bash
cd AGENT_CONVERSATIONEL

# Build
docker build -t chatbot_worldbank .

# Run
docker run -d -p 8000:8000 -e OPENAI_API_KEY=sk-... chatbot_worldbank
```

Ou via **docker-compose** :

```bash
docker-compose up -d
```

Le `docker-compose.yml` lit automatiquement le fichier `.env` pour `OPENAI_API_KEY`.

---

## Endpoint API

### `POST /query`

**Request :**
```json
{
  "query": "Quel est le PIB de la France ?",
  "user_id": "user-123",
  "lang": "fr"
}
```

**Response :**
```json
{
  "answer": "<p>Le PIB de la France en 2023 ...</p>",
  "user_id": "user-123",
  "success": true
}
```

**Codes HTTP :**
| Code | Description |
|---|---|
| 200 | Réponse OK |
| 429 | Rate limit dépassé (20/min) |
| 500 | Erreur serveur (réponse `success: false` avec fallback) |

### `GET /`

Page HTML de bienvenue avec liens vers `data.worldbank.org`.

---

## Widget injectable

Le fichier `interface_wp_chatbot.js` permet d'injecter un chatbot flottant sur n'importe quelle page web :

```html
<script src="https://YOUR_DOMAIN/interface_wp_chatbot.js"></script>
```

**Configuration :**
```html
<script>
  window.WB_CHATBOT_API = "https://your-api.com/query";
  window.WB_CHATBOT_LANG = "fr"; // ou "en"
</script>
<script src="interface_wp_chatbot.js"></script>
```

Le widget affiche :
- Un bouton flottant 🌍 en bas à droite
- Un panel de chat avec l'assistant World Bank
- Détection automatique de la langue

---

## Tests d'audit

Le fichier `test_chatbot.html` est une interface d'audit complète avec :

- **Panel gauche** — Suite de tests par catégorie :
  - 🔒 Sécurité (injection, XSS, divulgation)
  - 📊 Données Économiques (PIB, chômage, comparaisons)
  - 👥 Données Sociales (population, scolarisation, espérance de vie)
  - 🌍 Données Environnementales (CO₂, tendances)
  - 💬 UX (salutations, FAQ, politesse)
  - 🔐 RGPD (données personnelles)
  - 🚫 Hors périmètre (refus approprié)

- **Panel droit** — Interface chat avec résultats :
  - 🟢 **OK** — Résultat conforme
  - 🟠 **OK(!)** — Fonctionnel, qualité à améliorer
  - 🔴 **KO** — Bug ou résultat insuffisant

**Usage :** Ouvrir `test_chatbot.html` dans un navigateur avec le serveur lancé sur `localhost:8000`.

---

## Monitoring & Observabilité

- **Logs** — `logging` Python (INFO/WARNING/ERROR) sur stdout
- **Rate limit** — Réponse 429 avec message explicatif
- **Métriques** :
  - Nombre de tokens (visible dans logs via `token_usage` sur les retours OpenAI)
  - Temps de réponse (latence agent)
  - Taille mémoire par utilisateur

---

## Roadmap

- [ ] Ajout de métriques Prometheus
- [ ] Cache Redis pour les réponses fréquentes
- [ ] Streaming des réponses (SSE / WebSocket)
- [ ] Support multimodal (graphiques, tableaux interactifs)
- [ ] Intégration API World Bank en temps réel
- [ ] Authentification JWT pour usage en production
- [ ] Dashboard d'administration

---

## Structure des fichiers

```
AGENT_CONVERSATIONEL/
├── app.py                      # Point d'entrée FastAPI
├── config.json                 # Configuration centralisée
├── requirements.txt            # Dépendances Python
├── Dockerfile                  # Image Docker
├── docker-compose.yml          # Orchestration
├── test_chatbot.html           # Page de test audit
├── interface_wp_chatbot.js     # Widget injectable
├── README.md                   # Ce fichier
├── core/
│   ├── __init__.py             # Exports du module core
│   ├── agent_orchestrator.py   # AgentExecutor LangChain + outils
│   ├── config_loader.py        # Chargement config.json
│   ├── embeddings_loader.py    # FAISS vector store + retriever
│   ├── faq_handler.py          # FAQ déterministe (regex)
│   ├── llm_handler.py          # Instance ChatOpenAI
│   ├── memory_manager.py       # Mémoire conversationnelle
│   ├── system_prompt.py        # Prompt système
│   └── utils.py                # Utilitaires
├── models/
│   └── request_models.py       # QueryRequest / QueryResponse
└── data/
    └── data.json               # Données vectorisées
```

---

*Données fournies sous licence [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) par la Banque Mondiale.*
