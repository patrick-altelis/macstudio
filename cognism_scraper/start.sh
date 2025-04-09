#!/bin/bash
# Script pour démarrer l'application Cognism Scraper

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null
then
    echo "Python 3 n'est pas installé. Veuillez l'installer."
    exit 1
fi

# Activer l'environnement virtuel si présent
if [ -d "venv" ]; then
    echo "Activation de l'environnement virtuel..."
    source venv/bin/activate
fi

# Installer les dépendances si nécessaire
if [ ! -f ".deps_installed" ]; then
    echo "Installation des dépendances..."
    pip install -r requirements.txt
    touch .deps_installed
fi

# Créer les répertoires nécessaires
mkdir -p uploads exports

# Démarrer le serveur sur le port 3333 (différent des ports précédents)
echo "Démarrage du serveur sur http://127.0.0.1:3333..."
export FLASK_APP=app.py
export FLASK_ENV=development
python3 -m flask run --host=127.0.0.1 --port=3333 --debugger