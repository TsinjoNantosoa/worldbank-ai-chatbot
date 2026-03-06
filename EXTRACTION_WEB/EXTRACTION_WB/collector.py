"""
World Bank Data Collector - Main Script

Ce script collecte les données depuis l'API World Bank et les structure
pour l'indexation FAISS du chatbot.

Usage:
    python collector.py
    python collector.py --indicators NY.GDP.MKTP.CD SP.POP.TOTL
    python collector.py --countries FRA DEU USA --date-range 2015:2023
"""

import os
import json
import time
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from .processors import (
        clean_text,
        chunk_methodology_text,
        create_data_point_snippet,
        merge_data_incrementally
    )
    from .utils_http import create_session_with_retries
except ImportError:
    from processors import (
        clean_text,
        chunk_methodology_text,
        create_data_point_snippet,
        merge_data_incrementally
    )
    from utils_http import create_session_with_retries

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration API World Bank
WB_API_BASE = "https://api.worldbank.org/v2"
WB_FORMAT = "json"
WB_PER_PAGE = 1000
RATE_LIMIT_DELAY = 0.2  # secondes entre requêtes

# Chemins fichiers
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_FILE = DATA_DIR / "world_bank_data.json"


class WorldBankCollector:
    """Collecteur de données World Bank API"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize collector
        
        Args:
            config: Configuration dict (optional, loads from ../config.json if None)
        """
        self.session = create_session_with_retries()
        
        # Charger config
        if config is None:
            config_path = BASE_DIR / "config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    full_config = json.load(f)
                    config = full_config.get("world_bank_api", {})
            else:
                config = {}
        
        self.config = config
        self.base_url = config.get("base_url", WB_API_BASE)
        self.per_page = config.get("per_page", WB_PER_PAGE)
        self.rate_delay = config.get("rate_limit_delay_seconds", RATE_LIMIT_DELAY)
        
        logger.info(f"Initialized WorldBankCollector with base_url: {self.base_url}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _fetch_paginated(self, url: str, max_pages: int = 50) -> List[Dict]:
        """
        Récupère données paginées de l'API WB
        
        Args:
            url: URL endpoint (sans format/per_page)
            max_pages: Nombre max de pages à récupérer
            
        Returns:
            Liste de tous les résultats
        """
        all_results = []
        page = 1
        
        while page <= max_pages:
            # Construire URL avec pagination
            separator = "&" if "?" in url else "?"
            paginated_url = f"{url}{separator}format={WB_FORMAT}&per_page={self.per_page}&page={page}"
            
            logger.debug(f"Fetching: {paginated_url}")
            
            try:
                response = self.session.get(paginated_url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Format réponse WB: [metadata, results]
                if not isinstance(data, list) or len(data) < 2:
                    logger.warning(f"Unexpected response format: {data}")
                    break
                
                metadata = data[0]
                results = data[1]
                
                if not results:
                    logger.debug(f"No more results at page {page}")
                    break
                
                all_results.extend(results)
                
                # Vérifier si dernière page
                total_pages = metadata.get("pages", 1)
                logger.info(f"Page {page}/{total_pages} - {len(results)} items")
                
                if page >= total_pages:
                    break
                
                page += 1
                time.sleep(self.rate_delay)  # Rate limiting
                
            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
                raise
        
        logger.info(f"Total items fetched: {len(all_results)}")
        return all_results
    
    def get_countries(self) -> List[Dict]:
        """Récupère la liste des pays"""
        logger.info("Fetching countries list...")
        url = f"{self.base_url}/country"
        countries = self._fetch_paginated(url)
        
        # Filtrer pays valides (exclure régions/agrégats)
        valid_countries = [
            c for c in countries
            if c.get("region", {}).get("id") not in ["", "NA"]
            and c.get("capitalCity", "")  # A une capitale = pays réel
        ]
        
        logger.info(f"Found {len(valid_countries)} valid countries")
        return valid_countries
    
    def get_indicators_metadata(self, indicator_codes: Optional[List[str]] = None) -> List[Dict]:
        """
        Récupère métadonnées des indicateurs
        
        Args:
            indicator_codes: Liste codes (ex: ['NY.GDP.MKTP.CD']). Si None, tous.
            
        Returns:
            Liste dicts avec métadonnées indicateurs
        """
        logger.info("Fetching indicators metadata...")
        
        if indicator_codes:
            # Requêtes individuelles pour codes spécifiques
            indicators = []
            for code in indicator_codes:
                try:
                    url = f"{self.base_url}/indicator/{code}"
                    result = self._fetch_paginated(url, max_pages=1)
                    if result:
                        indicators.extend(result)
                    time.sleep(self.rate_delay)
                except Exception as e:
                    logger.warning(f"Failed to fetch indicator {code}: {e}")
            return indicators
        else:
            # Tous les indicateurs (attention: très volumineux)
            url = f"{self.base_url}/indicator"
            return self._fetch_paginated(url, max_pages=20)
    
    def get_indicator_data(
        self,
        country_code: str,
        indicator_code: str,
        date_range: str = "2000:2023"
    ) -> List[Dict]:
        """
        Récupère données d'un indicateur pour un pays
        
        Args:
            country_code: Code pays ISO (ex: 'FRA')
            indicator_code: Code indicateur (ex: 'NY.GDP.MKTP.CD')
            date_range: Plage années (ex: '2015:2023')
            
        Returns:
            Liste data points
        """
        url = f"{self.base_url}/country/{country_code}/indicator/{indicator_code}"
        url += f"?date={date_range}"
        
        logger.debug(f"Fetching {indicator_code} for {country_code} ({date_range})")
        
        try:
            data = self._fetch_paginated(url, max_pages=5)
            # Filtrer valeurs nulles
            return [d for d in data if d.get("value") is not None]
        except Exception as e:
            logger.warning(f"Failed to get data for {country_code}/{indicator_code}: {e}")
            return []
    
    def collect_all(
        self,
        indicator_codes: List[str],
        country_codes: List[str],
        date_range: str = "2000:2023"
    ) -> Dict[str, Any]:
        """
        Collecte complète des données
        
        Args:
            indicator_codes: Liste codes indicateurs
            country_codes: Liste codes pays
            date_range: Plage années
            
        Returns:
            Dict structuré pour data.json
        """
        logger.info(f"Starting collection: {len(indicator_codes)} indicators x {len(country_codes)} countries")
        
        # Structure output
        output = {
            "metadata": {
                "collection_date": datetime.utcnow().isoformat(),
                "date_range": date_range,
                "indicators_count": len(indicator_codes),
                "countries_count": len(country_codes)
            },
            "categories": []
        }
        
        # 1. Récupérer métadonnées indicateurs
        logger.info("Step 1/3: Fetching indicators metadata...")
        indicators_meta = self.get_indicators_metadata(indicator_codes)
        
        indicators_dict = {
            ind.get("id"): ind for ind in indicators_meta
        }
        
        # 2. Récupérer infos pays
        logger.info("Step 2/3: Fetching countries info...")
        all_countries = self.get_countries()
        countries_dict = {
            c.get("id"): c for c in all_countries
            if c.get("id") in country_codes
        }
        
        # 3. Collecter données par indicateur
        logger.info("Step 3/3: Collecting indicator data...")
        
        for idx, indicator_code in enumerate(indicator_codes, 1):
            logger.info(f"[{idx}/{len(indicator_codes)}] Processing {indicator_code}")
            
            indicator_meta = indicators_dict.get(indicator_code, {})
            indicator_name = indicator_meta.get("name", indicator_code)
            
            # Catégorie pour cet indicateur
            category = {
                "category": f"indicator_{indicator_code}",
                "name": indicator_name,
                "description": indicator_meta.get("sourceNote", ""),
                "source": indicator_meta.get("source", {}).get("value", "World Bank"),
                "pages": []
            }
            
            # Collecter données pour chaque pays
            for country_code in country_codes:
                country_info = countries_dict.get(country_code, {})
                country_name = country_info.get("name", country_code)
                
                data_points = self.get_indicator_data(
                    country_code,
                    indicator_code,
                    date_range
                )
                
                if data_points:
                    # Créer page avec snippet textuel
                    snippet = create_data_point_snippet(
                        indicator_name,
                        country_name,
                        data_points,
                        indicator_code,
                        country_code
                    )
                    
                    category["pages"].append({
                        "url": f"https://data.worldbank.org/indicator/{indicator_code}?locations={country_code}",
                        "content": snippet,
                        "metadata": {
                            "country_code": country_code,
                            "country_name": country_name,
                            "indicator_code": indicator_code,
                            "indicator_name": indicator_name,
                            "data_points_count": len(data_points),
                            "latest_year": max(d.get("date") for d in data_points if d.get("date")),
                            "latest_value": next(
                                (d.get("value") for d in sorted(data_points, key=lambda x: x.get("date", ""), reverse=True)),
                                None
                            )
                        }
                    })
                
                time.sleep(self.rate_delay / 2)  # Rate limiting
            
            # Ajouter méthodologie comme page séparée
            methodology = indicator_meta.get("sourceNote", "")
            if methodology and len(methodology) > 50:
                chunks = chunk_methodology_text(
                    clean_text(methodology),
                    indicator_code,
                    max_chunk_size=1000
                )
                
                for chunk in chunks:
                    category["pages"].append({
                        "url": f"https://data.worldbank.org/indicator/{indicator_code}",
                        "content": chunk["text"],
                        "metadata": {
                            "type": "methodology",
                            "indicator_code": indicator_code,
                            "chunk_id": chunk["chunk_id"]
                        }
                    })
            
            output["categories"].append(category)
        
        logger.info("Collection complete!")
        return output


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="World Bank Data Collector")
    parser.add_argument(
        "--indicators",
        nargs="+",
        help="Indicator codes (ex: NY.GDP.MKTP.CD SP.POP.TOTL)"
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        help="Country codes (ex: FRA DEU USA)"
    )
    parser.add_argument(
        "--date-range",
        default="2000:2023",
        help="Date range (ex: 2015:2023)"
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_FILE),
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    # Charger config
    config_path = BASE_DIR / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            wb_config = config.get("world_bank_api", {})
    else:
        wb_config = {}
    
    # Override avec args CLI si fournis
    indicators = args.indicators or wb_config.get("indicators", [
        "NY.GDP.MKTP.CD",
        "SP.POP.TOTL",
        "SL.UEM.TOTL.ZS"
    ])
    
    countries = args.countries or wb_config.get("countries", [
        "USA", "FRA", "DEU", "GBR", "JPN"
    ])
    
    date_range = args.date_range or wb_config.get("date_range", "2000:2023")
    
    logger.info(f"Configuration:")
    logger.info(f"  Indicators: {indicators}")
    logger.info(f"  Countries: {countries}")
    logger.info(f"  Date range: {date_range}")
    logger.info(f"  Output: {args.output}")
    
    # Créer dossier data si nécessaire
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Collecte
    collector = WorldBankCollector(wb_config)
    data = collector.collect_all(indicators, countries, date_range)
    
    # Fusion avec données existantes
    output_path = Path(args.output)
    if output_path.exists():
        logger.info("Merging with existing data...")
        data = merge_data_incrementally(output_path, data)
    
    # Sauvegarde
    logger.info(f"Saving to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Done! Collected {len(data['categories'])} categories")
    logger.info(f"   Total pages: {sum(len(cat['pages']) for cat in data['categories'])}")


if __name__ == "__main__":
    main()
