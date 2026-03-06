"""
Script de test pour l'API du chatbot World Bank Data

Usage:
    python test_query.py
"""

import requests
import json
from typing import List, Dict

# Configuration
BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = f"{BASE_URL}/query"

# Cas de test
TEST_CASES: List[Dict[str, any]] = [
    {
        "name": "Test 1: PIB France",
        "query": "Quel est le PIB de la France en 2023?",
        "expected_keywords": ["France", "2023", "PIB", "milliards", "source", "World Bank"]
    },
    {
        "name": "Test 2: Comparaison pays",
        "query": "Compare emissions CO2 between USA and China",
        "expected_keywords": ["USA", "China", "CO2", "source", "indicator"]
    }
]

def run_test(test_case: Dict) -> Dict:
    """Execute un test et retourne les résultats"""
    print(f"\n{'='*70}")
    print(f"🧪 {test_case['name']}")
    print(f"Query: {test_case['query']}")
    print('='*70)
    
    try:
        response = requests.post(
            ENDPOINT,
            json={"query": test_case["query"]},
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        answer = data.get("answer", "")
        user_id = data.get("user_id", "")
        
        print(f"\n✅ Réponse (user_id: {user_id}):")
        print(f"{answer}\n")
        
        missing_keywords = [
            kw for kw in test_case["expected_keywords"] 
            if kw.lower() not in answer.lower()
        ]
        
        if missing_keywords:
            print(f"⚠️  Mots-clés manquants: {', '.join(missing_keywords)}")
            status = "PARTIAL"
        else:
            print("✅ Tous les mots-clés attendus sont présents")
            status = "PASS"
        
        return {
            "status": status,
            "answer_length": len(answer),
            "missing_keywords": missing_keywords
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau: {e}")
        return {"status": "FAIL", "error": str(e)}
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return {"status": "ERROR", "error": str(e)}

def main():
    print("\n" + "="*70)
    print("🚀 TESTS CHATBOT WORLD BANK DATA")
    print("="*70)
    
    try:
        health_check = requests.get(BASE_URL, timeout=5)
        print(f"✅ Serveur accessible: {BASE_URL}")
    except:
        print(f"❌ Serveur inaccessible: {BASE_URL}")
        print("⚠️  Assurez-vous que le serveur est démarré:")
        print("    python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    results = []
    for test_case in TEST_CASES:
        result = run_test(test_case)
        results.append({
            "name": test_case["name"],
            **result
        })
    
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*70)
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    partial = sum(1 for r in results if r["status"] == "PARTIAL")
    failed = sum(1 for r in results if r["status"] in ["FAIL", "ERROR"]) 
    
    print(f"✅ Réussis: {passed}/{len(results)}")
    print(f"⚠️  Partiels: {partial}/{len(results)}")
    print(f"❌ Échoués: {failed}/{len(results)}")
    
    for result in results:
        status_icon = {
            "PASS": "✅",
            "PARTIAL": "⚠️",
            "FAIL": "❌",
            "ERROR": "❌"
        }.get(result["status"], "❓")
        print(f"{status_icon} {result['name']}: {result['status']}")

if __name__ == "__main__":
    main()
