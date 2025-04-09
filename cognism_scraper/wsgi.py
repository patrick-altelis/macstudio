#!/usr/bin/env python3
"""
Script WSGI pour démarrer l'application Cognism Scraper.
Utilisez avec gunicorn: gunicorn -w 4 -b 127.0.0.1:3000 wsgi:application
"""
from app import app as application

if __name__ == "__main__":
    # Exécution directe pour les tests
    application.run(host='127.0.0.1', port=3000, debug=True)