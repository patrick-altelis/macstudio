#!/usr/bin/env python3
"""
Démarrer l'application avec waitress - un serveur WSGI de production.
"""
from waitress import serve
from app import app

if __name__ == "__main__":
    print("==================================================")
    print("Démarrage du serveur sur http://127.0.0.1:8080")
    print("==================================================")
    # Utilisez waitress pour servir l'application
    serve(app, host="127.0.0.1", port=8080)