## Démarrer le backend - World Bank Chatbot

Petit guide rapide pour préparer, lancer et dépanner le backend localement (WSL / Linux).

**Préparation (une seule fois)**

- Créer et installer l'environnement virtuel:
```bash
cd /mnt/c/Users/Tsinjo/Documents/H4H_Career/WORLD\ BANK/AGENT_CONVERSATIONEL
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Nettoyer `.env` (supprime CRLF et guillemets autour de la clé):
```bash
cp .env .env.bak
python - <<'PY'
import re
s = open('.env','rb').read().decode('utf-8',errors='ignore')
s = s.replace('\r','')
s = re.sub(r'(?m)^OPENAI_API_KEY\s*=\s*["\']?(.*?)["\']?\s*$', lambda m: f'OPENAI_API_KEY={m.group(1).strip()}', s)
open('.env','w', encoding='utf-8').write(s)
print('cleaned .env')
PY
```

**À chaque démarrage**

1. Activer l'environnement et charger `.env`:
```bash
cd /mnt/c/Users/Tsinjo/Documents/H4H_Career/WORLD\ BANK/AGENT_CONVERSATIONEL
source .venv/bin/activate
set -a && source .env && set +a
```

2. Définir le chemin absolu du fichier de données (évite erreurs liées au CWD):
```bash
export WB_DATA_FILE="$(pwd)/data/world_bank_data.json"
export OPENAI_API_KEY="$(echo \"$OPENAI_API_KEY\" | tr -d '\r')"
```

3. Libérer le port 8000 (si occupé) ou lancer sur un port alternatif:
```bash
# Vérifier si 8000 est occupé
ss -ltnp | grep ':8000' || true

# Tuer uvicorn sans sudo si possible
pkill -f uvicorn || true

# Ou lancer sur 8001 si vous ne voulez pas tuer de processus
python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

4. Lancer le serveur (dev / prod):
```bash
# mode dev (reload)
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload --app-dir .

# sans reload (plus stable)
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

5. Vérifications
```bash
curl http://localhost:8000/health

# Exemple de requête
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","query":"bonjour","lang":"fr"}' | jq
```

**Docker (optionnel)**
```bash
cd AGENT_CONVERSATIONEL
# Copier .env ici ou utiliser env_file dans docker-compose.yml
docker-compose up --build
```

**Dépannage rapide**
- Erreur CRLF / header invalide: nettoyez `.env` comme ci-dessus et vérifiez la variable:
```bash
python -c "import os; print(repr(os.environ.get('OPENAI_API_KEY')))"
```
- Port occupé: utiliser `pkill -f uvicorn` ou lancer sur un port différent.
- Si `--reload` provoque des arrêts/reloads constants, lancez sans `--reload` (subprocess plus stable).
- Sécurité: si votre clé OpenAI a été exposée, révoquez/rotatez-la immédiatement.

Si vous voulez, je peux ajouter un script `run.sh` pour automatiser ces étapes.
