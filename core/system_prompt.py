"""
System Prompt - Prompt système et normalisation queries

Définit le comportement de l'assistant et la normalisation
"""

import re
from typing import Dict

# Prompt système principal
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
   - Example: "Le PIB de la France en 2023 était de 2 782 milliards USD (source: <a href='...'>World Bank indicator NY.GDP.MKTP.CD</a>)"
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


# Map de normalisation (acronymes, pays, termes métier)
# À fusionner avec config.json si présent
DEFAULT_NORMALIZATION_MAP = {
    # Acronymes économiques
    "pib": "Produit Intérieur Brut",
    "gdp": "Gross Domestic Product",
    "rni": "Revenu National Brut",
    "gni": "Gross National Income",
    "co2": "Dioxyde de Carbone",
    "population": "Population totale",
    
    # Codes pays
    "usa": "United States",
    "us": "United States",
    "fr": "France",
    "de": "Germany",
    "uk": "United Kingdom",
    "jp": "Japan",
    "cn": "China",
    "in": "India",
    "br": "Brazil"
}


def normalize_query(query: str, normalization_map: Dict[str, str] = None) -> str:
    """
    Normalise la query utilisateur (expansion acronymes, pays, etc.)
    
    Args:
        query: Query brute
        normalization_map: Map custom (ou DEFAULT si None)
        
    Returns:
        Query normalisée
    """
    if not query:
        return query
    
    norm_map = normalization_map or DEFAULT_NORMALIZATION_MAP
    
    query_lower = query.lower()
    
    # Remplacer termes (word boundaries pour éviter faux positifs)
    for key, value in norm_map.items():
        pattern = r"\b" + re.escape(key) + r"\b"
        query_lower = re.sub(pattern, value.lower(), query_lower)
    
    return query_lower
