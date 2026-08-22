#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "    Universal Media Downloader - Démarrage Local"
echo "=========================================================="

# Vérifier Python 3
if ! command -v python3 &> /dev/null; then
    echo "[!] Erreur : Python 3 n'est pas installé."
    exit 1
fi

# Créer un environnement virtuel si nécessaire
if [ ! -d "venv" ]; then
    echo "[*] Création de l'environnement virtuel Python..."
    python3 -m venv venv
fi

echo "[*] Activation de l'environnement virtuel..."
source venv/bin/activate

echo "[*] Installation des dépendances..."
pip install -q -r backend/requirements.txt

echo "[*] Lancement du serveur FastAPI..."
echo "[+] Application disponible sur : http://localhost:8000"
echo "[+] Documentation Swagger sur  : http://localhost:8000/docs"
echo "=========================================================="

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
