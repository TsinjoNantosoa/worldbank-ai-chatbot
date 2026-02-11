# Architecture - World Bank Chatbot

## 🏗️ Vue d'ensemble

Ce document présente l'architecture complète du chatbot World Bank avec des diagrammes visuels.

## 📊 Architecture Système

### Diagramme de flux complet

```mermaid
graph TB
    User[👤 User Browser]
    
    subgraph "Frontend"
        HTML[base.html<br/>Chat Interface]
        JS[app.js<br/>Event Handlers]
        CSS[style.css<br/>Styling]
    end
    
    subgraph "FastAPI Backend"
        App[app.py<br/>Main API]
        Routes{Routes}
        Query[/query endpoint]
        Health[/health endpoint]
    end
    
    subgraph "Core Logic"
        Config[config_loader<br/>Settings]
        LLM[llm_handler<br/>GPT-4o-mini]
        Memory[memory_manager<br/>Conv History]
        Agent[agent_orchestrator<br/>RAG Agent]
        Prompt[system_prompt<br/>Instructions]
    end
    
    subgraph "Vector Store"
        Embeddings[embeddings_loader<br/>FAISS Manager]
        FAISS[(FAISS Index<br/>4096 dims)]
    end
    
    subgraph "Data Source"
        Collector[collector.py<br/>WB API Client]
        Processor[processors.py<br/>Chunking]
        WBAPI[World Bank API v2]
        Data[(world_bank_data.json)]
    end
    
    User -->|HTTP GET /| HTML
    HTML --> JS
    JS -->|POST /query| App
    App --> Routes
    Routes --> Query
    Routes --> Health
    
    Query --> Config
    Query --> Memory
    Query --> Agent
    
    Agent --> LLM
    Agent --> Embeddings
    Agent --> Prompt
    
    Embeddings --> FAISS
    FAISS -.->|Load from| Data
    
    Collector -->|Fetch| WBAPI
    Collector --> Processor
    Processor -->|Save| Data
    
    Agent -->|Response| Query
    Query -->|JSON| JS
    JS -->|Display| HTML
```

### Architecture en couches

```mermaid
graph LR
    subgraph "Layer 1: Presentation"
        UI[HTML/CSS/JS<br/>User Interface]
    end
    
    subgraph "Layer 2: API"
        API[FastAPI<br/>REST Endpoints]
    end
    
    subgraph "Layer 3: Business Logic"
        Agent[LangChain Agent]
        Memory[Conversation<br/>Memory]
    end
    
    subgraph "Layer 4: AI Services"
        LLM[OpenAI<br/>GPT-4o-mini]
        Embeddings[OpenAI<br/>text-embedding-3-large]
    end
    
    subgraph "Layer 5: Data"
        Vector[(FAISS<br/>Vector Store)]
        JSON[(JSON<br/>Raw Data)]
    end
    
    UI --> API
    API --> Agent
    API --> Memory
    Agent --> LLM
    Agent --> Vector
    Vector --> Embeddings
    Vector --> JSON
```

## 🔄 Flux de traitement d'une query

### Séquence complète

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend (JS)
    participant A as app.py
    participant M as memory_manager
    participant P as system_prompt
    participant AG as agent_orchestrator
    participant E as embeddings_loader
    participant L as llm_handler
    participant O as OpenAI API
    
    U->>F: Type question & click send
    F->>A: POST /query {query, user_id}
    
    A->>M: get conversation history(user_id)
    M-->>A: formatted history
    
    A->>P: normalize_query(query)
    P-->>A: normalized query
    
    A->>AG: invoke_agent(query, history)
    
    AG->>E: retriever.get_relevant_documents(query)
    E->>O: embed query
    O-->>E: embedding vector
    E->>E: FAISS similarity search (k=4)
    E-->>AG: top 4 documents
    
    AG->>AG: format docs + build prompt
    AG->>L: ChatOpenAI.invoke(prompt)
    L->>O: Chat Completion API
    O-->>L: Generated response
    L-->>AG: response text
    
    AG-->>A: final answer
    
    A->>M: save to history(user_id, query, answer)
    M-->>A: saved
    
    A-->>F: {answer, user_id, success}
    F->>F: append message to chat
    F-->>U: Display answer
```

### Traitement agent (détail RAG)

```mermaid
graph TD
    Start([User Query]) --> Normalize[Normalize Query<br/>system_prompt.py]
    Normalize --> History[Load Chat History<br/>memory_manager.py]
    
    History --> AgentStart[Agent Executor Start]
    
    AgentStart --> Tool1{Tool Selection}
    
    Tool1 -->|Need data| KnowledgeSearch[WB_Knowledge_Search]
    Tool1 -->|Need sources| SourceCollect[WB_Source_Collector]
    
    KnowledgeSearch --> Embed[Embed Query<br/>OpenAI]
    Embed --> FAISSSearch[FAISS Similarity<br/>k=4 results]
    FAISSSearch --> FormatDocs[Format Documents]
    
    SourceCollect --> ExtractURLs[Extract Source URLs]
    
    FormatDocs --> BuildPrompt[Build Final Prompt]
    ExtractURLs --> BuildPrompt
    
    BuildPrompt --> LLM[ChatOpenAI<br/>GPT-4o-mini]
    LLM --> Response[Generated Answer]
    
    Response --> SaveMemory[Save to Memory]
    SaveMemory --> End([Return to User])
```

## 🗄️ Structure de données

### Format world_bank_data.json

```json
{
  "indicators": [
    {
      "code": "NY.GDP.MKTP.CD",
      "name": "GDP (current US$)",
      "source": "World Development Indicators",
      "source_url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.CD",
      "description": "Gross domestic product...",
      "methodology": "GDP at purchaser's prices...",
      "chunks": [
        {
          "text": "Chunk 1 of methodology (max 1000 chars)",
          "chunk_index": 0
        }
      ]
    }
  ],
  "country_data": [
    {
      "indicator_code": "NY.GDP.MKTP.CD",
      "country_code": "FRA",
      "country_name": "France",
      "year": 2023,
      "value": 2782000000000,
      "source_url": "https://data.worldbank.org/...",
      "snippet": "France GDP in 2023: $2.78 trillion USD"
    }
  ]
}
```

### Structure FAISS Index

```
data/faiss_index/
├── index.faiss          # Vector index (binary)
└── index.pkl            # Metadata (docstore, index_to_docstore_id)
```

**Documents dans FAISS**:
- **page_content**: Texte du chunk ou snippet
- **metadata**:
  - source: URL World Bank
  - category: "indicator" | "country_data" | "methodology"
  - type: "metadata" | "data_point" | "methodology_chunk"
  - indicator_code: ex. "NY.GDP.MKTP.CD"
  - country_code: ex. "FRA" (si data_point)
  - year: ex. 2023 (si data_point)

## 🔧 Configuration Flow

```mermaid
graph LR
    JSON[config.json<br/>Default settings]
    ENV[.env file<br/>Secrets]
    ENVVARS[Environment<br/>Variables]
    
    JSON --> Loader[config_loader.py]
    ENV --> ENVVARS
    ENVVARS --> Loader
    
    Loader --> Validate{Validate<br/>Required Keys}
    
    Validate -->|Valid| Config[Final Config Dict]
    Validate -->|Invalid| Error[Raise ValueError]
    
    Config --> App[app.py]
    Config --> Embeddings[embeddings_loader.py]
    Config --> LLM[llm_handler.py]
```

**Priority**: Environment Variables > .env > config.json

## 🐳 Architecture Docker

### Multi-service setup

```mermaid
graph TB
    subgraph "Docker Compose"
        subgraph "Service: wb-extraction"
            ExtContainer[Python Container<br/>collector.py]
            ExtVol[(Volume: ./data)]
        end
        
        subgraph "Service: worldbank-chatbot"
            ChatContainer[FastAPI + Uvicorn<br/>app.py]
            ChatVol[(Volume: ./data<br/>read-only)]
        end
    end
    
    ExtContainer -->|Writes| ExtVol
    ExtVol -->|Reads| ChatContainer
    
    ChatContainer -->|Port 8000| User[User Browser]
    
    Internet[World Bank API] -->|HTTPS| ExtContainer
```

### Container lifecycle

```mermaid
sequenceDiagram
    participant D as docker-compose
    participant E as wb-extraction
    participant C as worldbank-chatbot
    participant V as Volume (./data)
    
    D->>E: Start (run once)
    E->>E: pip install requirements
    E->>E: Run collector.py
    E->>V: Write world_bank_data.json
    E-->>D: Exit (success)
    
    D->>C: Start (persistent)
    C->>C: pip install requirements
    C->>V: Load world_bank_data.json
    C->>C: Build FAISS index
    C->>C: Start uvicorn server
    C-->>D: Running (port 8000)
    
    Note over C: Health check every 30s
    C->>D: /health OK
```

## 📡 API Flow

### Endpoints

```mermaid
graph LR
    subgraph "FastAPI Routes"
        Root[GET /<br/>HTML Page]
        Query[POST /query<br/>Chat Logic]
        Health[GET /health<br/>Status Check]
        Static[/static/*<br/>CSS/JS]
    end
    
    Browser[User Browser] -->|Navigate| Root
    Browser -->|Fetch| Static
    Browser -->|POST JSON| Query
    Monitor[Docker/K8s] -->|Health probe| Health
    
    Root --> Templates[Jinja2<br/>base.html]
    Query --> CoreLogic[core/<br/>modules]
    Health --> ConfigCheck[Check config<br/>loaded]
```

### Request/Response Models

```mermaid
classDiagram
    class QueryRequest {
        +str query
        +Optional[str] user_id
    }
    
    class QueryResponse {
        +str answer
        +str user_id
        +bool success
    }
    
    QueryRequest ..> FastAPI : validates
    FastAPI ..> QueryResponse : returns
```

## 🧠 Agent Tools Architecture

```mermaid
graph TB
    Agent[LangChain Agent<br/>OpenAI Tools]
    
    subgraph "Available Tools"
        T1[WB_Knowledge_Search<br/>Search vector store]
        T2[WB_Source_Collector<br/>Get citation URLs]
    end
    
    Agent -->|Uses| T1
    Agent -->|Uses| T2
    
    T1 --> Retriever[FAISS Retriever<br/>k=4]
    T2 --> Retriever
    
    Retriever --> Docs[Documents]
    
    T1 --> Format1[_format_docs<br/>Text with sources]
    T2 --> Format2[_collect_sources<br/>URL list]
    
    Format1 --> AgentPrompt[Final Prompt]
    Format2 --> AgentPrompt
    
    AgentPrompt --> LLM[GPT-4o-mini]
    LLM --> Answer[Final Answer]
```

## 🔄 Memory Management

```mermaid
graph LR
    subgraph "conversation_memory dict"
        User1[user_id_1:<br/>{history, last_active}]
        User2[user_id_2:<br/>{history, last_active}]
        User3[user_id_n:<br/>{history, last_active}]
    end
    
    Query[New Query] -->|Get/Create| User1
    User1 -->|Build prompt| ChatHistory[Formatted History]
    
    Answer[Agent Answer] -->|Save| User1
    User1 -->|Update| LastActive[last_active = now()]
    
    Cleanup[Cleanup Task<br/>Every 60s] -->|Check timeout| User2
    User2 -.->|Inactive > 5min| Delete[Remove session]
```

## 🔐 Security Layers

```mermaid
graph TB
    User[User Input] --> Validation[Pydantic Validation<br/>Max 500 chars]
    Validation --> Sanitize[Query Normalization<br/>SQL injection safe]
    Sanitize --> Agent[Agent Execution]
    
    Agent --> LLM[OpenAI API<br/>HTTPS only]
    
    subgraph "Secret Management"
        ENV[.env file<br/>Not in git]
        Docker[Docker secrets]
    end
    
    ENV -->|OPENAI_API_KEY| Config[config_loader]
    Docker -->|Env vars| Config
    
    Config --> LLM
    
    subgraph "Network Security"
        CORS[CORS Middleware<br/>Restrict origins]
        HTTPS[HTTPS Termination<br/>Production]
    end
    
    CORS --> App[FastAPI App]
    HTTPS --> App
```

## 📊 Monitoring Points

```mermaid
graph LR
    subgraph "Application Metrics"
        M1[Query latency<br/>logger.info]
        M2[Agent success/fail<br/>try/except]
        M3[Memory size<br/>conversation_memory]
        M4[FAISS reload<br/>embeddings_loader]
    end
    
    subgraph "Infrastructure"
        I1[Container health<br/>/health endpoint]
        I2[CPU/Memory<br/>Docker stats]
        I3[Disk usage<br/>data/ volume]
    end
    
    M1 --> Logs[Application Logs]
    M2 --> Logs
    M3 --> Logs
    M4 --> Logs
    
    I1 --> Monitoring[External Monitoring<br/>Prometheus/Grafana]
    I2 --> Monitoring
    I3 --> Monitoring
```

---

## 🎯 Résumé Architecture

### Stack technique
- **Frontend**: HTML5 + Vanilla JS + CSS3
- **Backend**: FastAPI (Python 3.11+)
- **AI**: LangChain + OpenAI (GPT-4o-mini, text-embedding-3-large)
- **Vector DB**: FAISS (CPU)
- **Data Source**: World Bank API v2
- **Container**: Docker + Docker Compose
- **Deployment**: Uvicorn (dev), Gunicorn+Uvicorn (prod)

### Design patterns
- **RAG (Retrieval Augmented Generation)**: Combine retrieval + generation
- **Microservices**: Extraction service + Chatbot service separated
- **Repository Pattern**: config_loader, embeddings_loader encapsulent la logique
- **Dependency Injection**: Config passed to all modules
- **Circuit Breaker**: Retry mechanism avec tenacity

### Scalability considerations
- **Horizontal**: Deploy multiple FastAPI instances behind load balancer
- **Vertical**: Increase k in FAISS, larger context windows
- **Caching**: Add Redis for conversation memory (current: in-memory)
- **Database**: Migrate to PostgreSQL with pgvector for production vector search

---

📚 **Voir aussi**: [README.md](README.md) pour installation détaillée
