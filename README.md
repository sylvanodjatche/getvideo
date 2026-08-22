# 🎬 Universal Media Downloader (Zero-Cost & Zero-Storage)

Application web moderne et performante permettant d'extraire, prévisualiser et télécharger des vidéos et audios depuis de multiples plateformes (**YouTube, TikTok sans filigrane, Instagram, Twitter/X, SoundCloud, Reddit, Facebook**) avec une architecture **Zero-Storage** (aucun fichier stocké sur le serveur).

---

## 🚀 Fonctionnalités Clés

- **Multi-plateformes Universel** : Détection automatique des liens YouTube, TikTok, Instagram, Twitter, etc.
- **TikTok Sans Filigrane** : Téléchargement automatique de la version propre sans watermark.
- **Passerelle Streaming Proxy** : Téléchargement direct sans restriction 403 et sans saturation mémoire serveur (chunks de 64 Ko).
- **Interface Moderne** : UI sombre glassmorphism responsive (TailwindCSS, Lucide Icons).
- **Architecture Zero-Cost** : Prêt pour le déploiement gratuit à vie (Oracle Cloud OCI / Hugging Face Spaces / Render).

---

## 📁 Structure du Projet

```text
media/
├── backend/
│   ├── app/
│   │   ├── config.py           # Configuration (CORS, taille de chunk)
│   │   ├── main.py             # Point d'entrée FastAPI & routes
│   │   └── services/
│   │       ├── extractor.py    # Service d'analyse yt-dlp
│   │       └── streamer.py     # Service de proxy streaming chunked
│   └── requirements.txt        # Dépendances Python
│
├── frontend/
│   ├── index.html              # Interface utilisateur
│   ├── app.js                  # Logique JavaScript
│   └── style.css               # Styles personnalisés
│
├── Dockerfile                  # Conteneurisation Docker
├── run.sh                      # Script de démarrage rapide local
└── Documentation_Technique_MediaDownloader.docx # Spécification complète Word
```

---

## 💻 Démarrage Rapide en Local

### Option 1 : Avec le script automatique
```bash
chmod +x run.sh
./run.sh
```

### Option 2 : Manuellement avec Python
```bash
# 1. Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 2. Installer les dépendances
pip install -r backend/requirements.txt

# 3. Lancer l'API
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Accédez ensuite à votre navigateur sur **`http://localhost:8000`**.  
La documentation interactive Swagger est accessible sur **`http://localhost:8000/docs`**.

---

## 🐳 Déploiement avec Docker

```bash
# Construction de l'image
docker build -t universal-media-downloader .

# Exécution du conteneur
docker run -d -p 8000:8000 --name media-downloader universal-media-downloader
```

---

## 🌐 Déploiement Gratuit en Ligne

1. **Oracle Cloud Always Free (Recommandé - 4 vCPU, 24 Go RAM, 10 To bande passante/mois) :**
   - Créez une instance Compute Ubuntu ARM gratuite.
   - Clonez le projet, lancez `docker run` ou `run.sh` et configurez un nom de domaine avec Cloudflare.

2. **Hugging Face Spaces :**
   - Créez un nouvel Espace Docker (Type Dockerfile).
   - Déposez les fichiers du dépôt : l'application tourne gratuitement sans limite de mise en veille agressive.
