"""
Quick Start Script - World Bank Chatbot (Local Mode)
Démarre le chatbot en mode local sans Docker
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    print("\n" + "="*50)
    print(f"  {text}")
    print("="*50)

def check_python():
    """Vérifier Python 3.11+"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ requis")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_api_key():
    """Vérifier clé API OpenAI"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-your-api-key-here":
        print("❌ OPENAI_API_KEY non configurée!")
        print("\nDeux options:")
        print("  1. Éditer .env et remplacer sk-your-api-key_here")
        print("  2. Ou définir: set OPENAI_API_KEY=sk-votre-vraie-cle")
        return False
    print(f"✅ OPENAI_API_KEY configurée ({api_key[:10]}...)")
    return True

def install_packages():
    """Installer les packages essentiels"""
    print("\n📦 Installation des packages...")
    
    packages = [
        "fastapi",
        "uvicorn[standard]",
        "langchain",
        "langchain-openai",
        "langchain-community",
        "faiss-cpu",
        "openai",
        "python-dotenv",
        "requests",
        "tenacity"
    ]
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet"] + packages,
            check=True
        )
        print("✅ Packages installés")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erreur lors de l'installation")
        return False

def create_sample_data():
    """Créer des données de test minimales"""
    print("\n📄 Création de données de test...")
    
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    sample_data = {
        "indicators": [
            {
                "code": "NY.GDP.MKTP.CD",
                "name": "GDP (current US$)",
                "source": "World Development Indicators",
                "source_url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.CD",
                "description": "Gross domestic product at current dollars.",
                "methodology": "GDP data are compiled using the production approach.",
                "chunks": [
                    {
                        "text": "GDP (Gross Domestic Product) represents the total monetary value of all finished goods and services produced within a country's borders in a specific time period.",
                        "chunk_index": 0
                    }
                ]
            }
        ],
        "country_data": [
            {
                "indicator_code": "NY.GDP.MKTP.CD",
                "country_code": "USA",
                "country_name": "United States",
                "year": 2023,
                "value": 25462700000000,
                "source_url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.CD?locations=US",
                "snippet": "United States GDP in 2023: $25.46 trillion USD (World Bank)"
            }
        ]
    }
    
    import json
    data_file = data_dir / "world_bank_data.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Données de test créées: {data_file}")
    return True

def start_server():
    """Démarrer le serveur FastAPI"""
    print("\n🚀 Démarrage du serveur...")
    print("\nLe chatbot sera accessible à:")
    print("  👉 http://localhost:8000")
    print("\nAppuyez sur Ctrl+C pour arrêter")
    print("="*50 + "\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n✅ Serveur arrêté")

def main():
    print_header("World Bank Chatbot - Quick Start")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    if not check_python():
        return
    
    if not check_api_key():
        print("\n⚠️  Configurez d'abord votre clé API, puis relancez ce script")
        return
    
    if not install_packages():
        return
    
    if not Path("data/world_bank_data.json").exists():
        if not create_sample_data():
            return
    else:
        print("\n✅ Données existantes détectées")
    
    start_server()

if __name__ == "__main__":
    main()
