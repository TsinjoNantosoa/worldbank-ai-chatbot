"""
Data Processors - Nettoyage, chunking et structuration

Fonctions utilitaires pour traiter les données brutes de l'API World Bank
"""

import re
import json
import hashlib
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime


def clean_text(text: str) -> str:
    """
    Nettoie un texte (méthodologie, description)
    
    Args:
        text: Texte brut
        
    Returns:
        Texte nettoyé
    """
    if not text:
        return ""
    
    # Supprimer HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&amp;", "&")
    
    # Normaliser whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def chunk_methodology_text(
    text: str,
    indicator_code: str,
    max_chunk_size: int = 1000,
    overlap: int = 200
) -> List[Dict[str, Any]]:
    """
    Découpe un texte méthodologique en chunks sémantiques
    
    Args:
        text: Texte à découper
        indicator_code: Code indicateur associé
        max_chunk_size: Taille max caractères par chunk
        overlap: Overlap entre chunks
        
    Returns:
        Liste de dicts {chunk_id, text, metadata}
    """
    if not text or len(text) < 100:
        return []
    
    chunks = []
    
    # Split sur phrases (approximatif)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    current_chunk = ""
    chunk_num = 1
    
    for sentence in sentences:
        # Si ajout de cette phrase dépasse max_chunk_size
        if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
            # Sauvegarder chunk actuel
            chunk_id = f"{indicator_code}_methodology_{chunk_num:03d}"
            chunks.append({
                "chunk_id": chunk_id,
                "text": current_chunk.strip(),
                "metadata": {
                    "indicator_code": indicator_code,
                    "type": "methodology",
                    "chunk_number": chunk_num
                }
            })
            
            # Commencer nouveau chunk avec overlap
            # Prendre derniers mots de current_chunk
            words = current_chunk.split()
            overlap_text = " ".join(words[-20:]) if len(words) > 20 else ""
            current_chunk = overlap_text + " " + sentence
            chunk_num += 1
        else:
            current_chunk += " " + sentence
    
    # Dernier chunk
    if current_chunk.strip():
        chunk_id = f"{indicator_code}_methodology_{chunk_num:03d}"
        chunks.append({
            "chunk_id": chunk_id,
            "text": current_chunk.strip(),
            "metadata": {
                "indicator_code": indicator_code,
                "type": "methodology",
                "chunk_number": chunk_num
            }
        })
    
    return chunks


def create_data_point_snippet(
    indicator_name: str,
    country_name: str,
    data_points: List[Dict],
    indicator_code: str,
    country_code: str,
    max_points: int = 10
) -> str:
    """
    Crée un snippet textuel à partir de data points numériques
    
    Args:
        indicator_name: Nom indicateur
        country_name: Nom pays
        data_points: Liste data points de l'API WB
        indicator_code: Code indicateur
        country_code: Code pays
        max_points: Nombre max de points à inclure
        
    Returns:
        Snippet textuel formaté
    """
    # Trier par date décroissante
    sorted_points = sorted(
        data_points,
        key=lambda x: x.get("date", ""),
        reverse=True
    )[:max_points]
    
    # Construction snippet
    lines = [
        f"Indicator: {indicator_name} ({indicator_code})",
        f"Country: {country_name} ({country_code})",
        "",
        "Data points:"
    ]
    
    for point in sorted_points:
        year = point.get("date", "N/A")
        value = point.get("value")
        unit = point.get("unit", "")
        
        if value is not None:
            # Formater valeur selon magnitude
            if value > 1e9:
                formatted_value = f"{value / 1e9:.2f} billion"
            elif value > 1e6:
                formatted_value = f"{value / 1e6:.2f} million"
            elif value > 1000:
                formatted_value = f"{value:,.0f}"
            else:
                formatted_value = f"{value:.2f}"
            
            lines.append(f"  - {year}: {formatted_value} {unit}")
    
    # Ajouter tendance si assez de points
    if len(sorted_points) >= 2:
        latest = sorted_points[0].get("value")
        oldest = sorted_points[-1].get("value")
        
        if latest and oldest and oldest != 0:
            change_pct = ((latest - oldest) / oldest) * 100
            trend = "increase" if change_pct > 0 else "decrease"
            lines.append("")
            lines.append(
                f"Trend ({sorted_points[-1]['date']} to {sorted_points[0]['date']}): "
                f"{abs(change_pct):.1f}% {trend}"
            )
    
    lines.append("")
    lines.append(f"Source: World Bank Open Data")
    
    return "\n".join(lines)


def merge_data_incrementally(existing_file: Path, new_data: Dict) -> Dict:
    """
    Fusionne nouvelles données avec fichier existant
    
    Args:
        existing_file: Chemin fichier JSON existant
        new_data: Nouvelles données à fusionner
        
    Returns:
        Données fusionnées
    """
    if not existing_file.exists():
        return new_data
    
    try:
        with open(existing_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return new_data
    
    # Fusionner métadonnées
    merged = {
        "metadata": {
            **existing_data.get("metadata", {}),
            "last_update": datetime.utcnow().isoformat(),
            "merge_count": existing_data.get("metadata", {}).get("merge_count", 0) + 1
        },
        "categories": []
    }
    
    # Index catégories existantes par nom
    existing_categories = {
        cat.get("category"): cat
        for cat in existing_data.get("categories", [])
    }
    
    # Fusionner nouvelles catégories
    for new_cat in new_data.get("categories", []):
        cat_name = new_cat.get("category")
        
        if cat_name in existing_categories:
            # Fusionner pages (dédupliquer par URL)
            existing_cat = existing_categories[cat_name]
            existing_urls = {
                page.get("url"): page
                for page in existing_cat.get("pages", [])
            }
            
            # Update/ajouter nouvelles pages
            for new_page in new_cat.get("pages", []):
                url = new_page.get("url")
                existing_urls[url] = new_page  # Remplace si existe
            
            # Reconstruire catégorie
            merged_cat = {
                **existing_cat,
                "pages": list(existing_urls.values()),
                "last_update": datetime.utcnow().isoformat()
            }
            merged["categories"].append(merged_cat)
        else:
            # Nouvelle catégorie
            merged["categories"].append(new_cat)
    
    # Ajouter catégories existantes non présentes dans new_data
    new_cat_names = {cat.get("category") for cat in new_data.get("categories", [])}
    for cat_name, cat_data in existing_categories.items():
        if cat_name not in new_cat_names:
            merged["categories"].append(cat_data)
    
    return merged


def validate_data_structure(data: Dict) -> bool:
    """
    Valide la structure des données
    
    Args:
        data: Données à valider
        
    Returns:
        True si valide, False sinon
    """
    required_keys = ["metadata", "categories"]
    
    if not all(key in data for key in required_keys):
        return False
    
    if not isinstance(data["categories"], list):
        return False
    
    for category in data["categories"]:
        if not isinstance(category.get("pages"), list):
            return False
        
        for page in category["pages"]:
            if "url" not in page or "content" not in page:
                return False
    
    return True
