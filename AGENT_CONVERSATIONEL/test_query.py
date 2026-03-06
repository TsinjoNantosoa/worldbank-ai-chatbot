#!/usr/bin/env python3
"""Simple test script to query the FastAPI chatbot."""
import requests
import json
import sys

def test_query():
    url = "http://127.0.0.1:8000/query"
    
    # Test query about France GDP in 2023
    payload = {
        "query": "Quel est le PIB de la France en 2023 ?",
        "user_id": "test",
        "lang": "fr"
    }
    
    print("=" * 80)
    print("Testing World Bank Chatbot")
    print("=" * 80)
    print(f"\nQuery: {payload['query']}")
    print("\nSending POST request...")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"\n✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n" + "=" * 80)
            print("Response:")
            print("=" * 80)
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("\n" + "=" * 80)
            return 0
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
            return 1
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out after 60 seconds")
        return 1
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection error - is the server running?")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(test_query())
