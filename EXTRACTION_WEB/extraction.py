"""
World Bank Data Extraction — Script principal

Collecte les données depuis l'API World Bank, structure en catégories,
et génère le data.json au format compatible avec le chatbot (format AAA).

Usage:
    cd EXTRACTION_WEB
    python extraction.py                          # collecte complète
    python extraction.py --quick                  # collecte rapide (5 indicateurs, 5 pays)
    python extraction.py --countries FRA USA DEU  # pays spécifiques
    python extraction.py --date-range 2018:2023   # plage réduite

Sorties:
    data/world_bank_data.json  — données brutes (format WB avec metadata)
    data/data.json             — données chatbot (format AAA: [{category, pages}])
    data/world_bank_pages.csv  — résumé CSV des pages collectées
"""

import os
import sys
import json
import csv
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Ajouter EXTRACTION_WB au path
sys.path.insert(0, str(Path(__file__).parent / "EXTRACTION_WB"))

from EXTRACTION_WB.collector import WorldBankCollector
from EXTRACTION_WB.processors import validate_data_structure

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ── Paths ──
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
WB_DATA_FILE = DATA_DIR / "world_bank_data.json"
CHATBOT_DATA_FILE = DATA_DIR / "data.json"
CSV_FILE = DATA_DIR / "world_bank_pages.csv"

# Copie vers le chatbot
CHATBOT_DATA_DIR = Path(__file__).parent.parent / "AGENT_CONVERSATIONEL" / "data"

# ── Indicateurs complets ──
# https://data.worldbank.org/indicator

INDICATORS_FULL = [
    # Économie
    "NY.GDP.MKTP.CD",       # PIB (USD courant)
    "NY.GDP.MKTP.KD.ZG",    # Croissance PIB (%)
    "NY.GDP.PCAP.CD",       # PIB par habitant (USD)
    "NY.GNP.MKTP.CD",       # RNB (USD courant)
    "FP.CPI.TOTL.ZG",       # Inflation, prix à la consommation (%)
    "GC.DOD.TOTL.GD.ZS",    # Dette publique (% PIB)
    "NE.EXP.GNFS.ZS",       # Exportations (% PIB)
    "NE.IMP.GNFS.ZS",       # Importations (% PIB)
    "BX.KLT.DINV.WD.GD.ZS", # IDE entrants (% PIB)

    # Population & démographie
    "SP.POP.TOTL",           # Population totale
    "SP.POP.GROW",           # Croissance population (%)
    "SP.DYN.LE00.IN",        # Espérance de vie à la naissance
    "SP.DYN.TFRT.IN",        # Taux de fécondité
    "SP.URB.TOTL.IN.ZS",     # Population urbaine (%)

    # Emploi
    "SL.UEM.TOTL.ZS",        # Chômage (% population active)
    "SL.UEM.25-64.MA.ZS",    # Chômage hommes 25-64
    "SL.UEM.25-64.FE.ZS",    # Chômage femmes 25-64
    "SL.TLF.CACT.ZS",        # Participation force de travail (%)

    # Éducation
    "SE.ADT.LITR.ZS",        # Taux alphabétisation adultes
    "SE.XPD.TOTL.GD.ZS",     # Dépenses éducation (% PIB)
    "SE.PRM.ENRR",            # Taux scolarisation primaire brut
    "SE.SEC.ENRR",            # Taux scolarisation secondaire brut

    # Santé
    "SH.XPD.CHEX.GD.ZS",     # Dépenses santé (% PIB)
    "SH.DYN.MORT",            # Mortalité infantile (pour 1000)
    "SH.STA.MMRT",            # Mortalité maternelle (pour 100k)

    # Environnement
    "EN.ATM.CO2E.PC",         # Émissions CO2 par habitant (tonnes métriques)
    "EN.ATM.CO2E.KT",         # Émissions CO2 total (kilotonnes)
    "EG.USE.PCAP.KG.OE",      # Consommation énergie par habitant (kg pétrole éq.)
    "EG.FEC.RNEW.ZS",         # Énergie renouvelable (% consommation)
    "AG.LND.FRST.ZS",         # Surface forestière (% territoire)

    # Technologie
    "IT.NET.USER.ZS",         # Utilisateurs internet (% population)
    "IT.CEL.SETS.P2",         # Abonnements téléphone mobile (pour 100)
]

INDICATORS_QUICK = [
    "NY.GDP.MKTP.CD",
    "SP.POP.TOTL",
    "SL.UEM.TOTL.ZS",
    "SP.DYN.LE00.IN",
    "EN.ATM.CO2E.PC",
]

# ── Pays ──
# Top 30 pays par PIB + pays francophones + BRICS
COUNTRIES_FULL = [
    # G7
    "USA", "GBR", "FRA", "DEU", "JPN", "CAN", "ITA",
    # BRICS
    "CHN", "IND", "BRA", "RUS", "ZAF",
    # Europe
    "ESP", "NLD", "BEL", "CHE", "SWE", "NOR", "POL", "AUT", "PRT",
    # Asie-Pacifique
    "KOR", "AUS", "IDN", "THA", "SGP", "MYS",
    # Afrique
    "NGA", "EGY", "KEN", "MAR", "SEN", "CIV", "TUN", "CMR",
    # Amérique latine
    "MEX", "ARG", "COL", "CHL",
    # Moyen-Orient
    "SAU", "ARE", "TUR",
]

COUNTRIES_QUICK = ["USA", "FRA", "DEU", "GBR", "JPN"]


def convert_to_chatbot_format(wb_data: dict) -> list:
    """
    Convertit le format WB ({metadata, categories}) vers le format AAA
    ([{category, pages: [{url, content}]}]) compatible avec le chatbot.
    """
    output = []

    for category in wb_data.get("categories", []):
        cat_entry = {
            "category": category.get("category", "unknown"),
            "pages": []
        }

        for page in category.get("pages", []):
            cat_entry["pages"].append({
                "url": page.get("url", ""),
                "content": page.get("content", "")
            })

        if cat_entry["pages"]:
            output.append(cat_entry)

    return output


def save_csv_summary(wb_data: dict, csv_path: Path):
    """Sauvegarde un CSV résumé (comme alan_allman_pages.csv)."""
    rows = []

    for category in wb_data.get("categories", []):
        cat_name = category.get("category", "")
        indicator_name = category.get("name", "")

        for page in category.get("pages", []):
            meta = page.get("metadata", {})
            rows.append({
                "url": page.get("url", ""),
                "category": cat_name,
                "indicator": indicator_name,
                "country": meta.get("country_name", meta.get("type", "")),
                "country_code": meta.get("country_code", ""),
                "data_points": meta.get("data_points_count", 0),
                "latest_year": meta.get("latest_year", ""),
                "collected_at": wb_data.get("metadata", {}).get("collection_date",
                               datetime.utcnow().isoformat())
            })

    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"📊 CSV summary saved to {csv_path} ({len(rows)} rows)")


def main():
    parser = argparse.ArgumentParser(description="World Bank Data Extraction")
    parser.add_argument("--quick", action="store_true",
                        help="Mode rapide (5 indicateurs, 5 pays)")
    parser.add_argument("--indicators", nargs="+",
                        help="Codes indicateurs spécifiques")
    parser.add_argument("--countries", nargs="+",
                        help="Codes pays spécifiques")
    parser.add_argument("--date-range", default="2000:2023",
                        help="Plage dates (ex: 2015:2023)")
    parser.add_argument("--no-merge", action="store_true",
                        help="Écraser les données existantes")
    args = parser.parse_args()

    # Choix indicateurs / pays
    if args.quick:
        indicators = args.indicators or INDICATORS_QUICK
        countries = args.countries or COUNTRIES_QUICK
        logger.info("⚡ Mode QUICK — 5 indicateurs × 5 pays")
    else:
        indicators = args.indicators or INDICATORS_FULL
        countries = args.countries or COUNTRIES_FULL
        logger.info(f"🌍 Mode FULL — {len(indicators)} indicateurs × {len(countries)} pays")

    logger.info(f"📅 Date range: {args.date_range}")
    logger.info(f"📊 Indicateurs: {len(indicators)}")
    logger.info(f"🏳️  Pays: {len(countries)}")
    logger.info(f"📈 Requêtes estimées: ~{len(indicators) * len(countries) + len(indicators)}")
    logger.info("")

    # Créer dossier data
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Collecte via API ──
    logger.info("=" * 50)
    logger.info("ÉTAPE 1/3 — Collecte des données via API World Bank")
    logger.info("=" * 50)

    collector = WorldBankCollector()
    wb_data = collector.collect_all(indicators, countries, args.date_range)

    # Fusion avec données existantes
    if not args.no_merge and WB_DATA_FILE.exists():
        from EXTRACTION_WB.processors import merge_data_incrementally
        logger.info("🔄 Fusion avec données existantes...")
        wb_data = merge_data_incrementally(WB_DATA_FILE, wb_data)

    # Valider structure
    if not validate_data_structure(wb_data):
        logger.error("❌ Données invalides après collecte !")
        return

    # Sauvegarder données brutes WB
    with open(WB_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(wb_data, f, indent=2, ensure_ascii=False)
    logger.info(f"✅ Données brutes sauvées: {WB_DATA_FILE}")

    # ── Step 2: Conversion format chatbot ──
    logger.info("")
    logger.info("=" * 50)
    logger.info("ÉTAPE 2/3 — Conversion au format chatbot (AAA)")
    logger.info("=" * 50)

    chatbot_data = convert_to_chatbot_format(wb_data)

    # Sauvegarder dans EXTRACTION_WEB/data/
    with open(CHATBOT_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(chatbot_data, f, indent=2, ensure_ascii=False)
    logger.info(f"✅ Format chatbot sauvé: {CHATBOT_DATA_FILE}")

    # Copier aussi dans AGENT_CONVERSATIONEL/data/
    CHATBOT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    chatbot_dest = CHATBOT_DATA_DIR / "data.json"
    with open(chatbot_dest, "w", encoding="utf-8") as f:
        json.dump(chatbot_data, f, indent=2, ensure_ascii=False)
    logger.info(f"✅ Copié vers chatbot: {chatbot_dest}")

    # ── Step 3: CSV summary ──
    logger.info("")
    logger.info("=" * 50)
    logger.info("ÉTAPE 3/3 — Génération CSV résumé")
    logger.info("=" * 50)

    save_csv_summary(wb_data, CSV_FILE)

    # ── Résumé final ──
    total_categories = len(wb_data.get("categories", []))
    total_pages = sum(len(c.get("pages", [])) for c in wb_data.get("categories", []))

    logger.info("")
    logger.info("=" * 50)
    logger.info("🎉 EXTRACTION TERMINÉE")
    logger.info("=" * 50)
    logger.info(f"   Catégories (indicateurs): {total_categories}")
    logger.info(f"   Pages (pays × indicateurs): {total_pages}")
    logger.info(f"   Fichiers générés:")
    logger.info(f"     📁 {WB_DATA_FILE}")
    logger.info(f"     📁 {CHATBOT_DATA_FILE}")
    logger.info(f"     📁 {chatbot_dest}")
    logger.info(f"     📁 {CSV_FILE}")
    logger.info("")
    logger.info("   Prochaine étape: lancer le chatbot")
    logger.info("   cd ../AGENT_CONVERSATIONEL && uvicorn app:app --port 8000")


if __name__ == "__main__":
    main()
