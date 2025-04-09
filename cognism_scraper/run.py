#!/usr/bin/env python
"""
Script principal pour démarrer l'outil d'extraction Cognism.
Vous pouvez exécuter ce script directement pour lancer l'interface web.
"""
import os
import sys
import logging
from app import app
from database import init_db

if __name__ == "__main__":
    # Configurer le logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("cognism_app.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Créer les répertoires nécessaires
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('exports', exist_ok=True)
    
    # Initialiser la base de données
    logger.info("Initialisation de la base de données...")
    init_db()
    
    # Démarrer l'application
    logger.info("Démarrage de l'application...")
    print("\n==================================================")
    print("Démarrage du serveur sur: http://127.0.0.1:9000")
    print("==================================================\n")
    # Utiliser 127.0.0.1 et port 9000 - port qui fonctionne sur cette machine
    app.run(debug=True, host='127.0.0.1', port=9000, threaded=True)