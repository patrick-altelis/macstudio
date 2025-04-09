#!/usr/bin/env python3
"""
Script d'urgence pour le lancement d'une application Flask simplifiée
pour dépanner les problèmes de connexion macOS.
"""
import os
import sys
import webbrowser
import subprocess
import time
from flask import Flask, render_template_string

# Créer une application minimale
app = Flask(__name__)

# Une page web simple pour tester
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test de connexion</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .success { color: green; background: #e8f5e9; padding: 20px; border-radius: 5px; }
        h1 { color: #333; }
        p { line-height: 1.6; }
    </style>
</head>
<body>
    <h1>Test de connexion réussi! 🎉</h1>
    <div class="success">
        <p><strong>Votre serveur web fonctionne correctement.</strong></p>
        <p>Si vous voyez cette page, cela signifie que:</p>
        <ul>
            <li>L'application Flask peut démarrer</li>
            <li>Le navigateur peut se connecter au serveur</li>
            <li>Aucun pare-feu ne bloque la connexion</li>
        </ul>
    </div>
    <p>Pour lancer l'application Cognism Scraper complète, exécutez:</p>
    <pre>python3 run.py</pre>
</body>
</html>
"""

@app.route('/')
def hello():
    return render_template_string(HTML)

def check_network():
    """Vérifie la configuration réseau et essaie de corriger les problèmes."""
    print("=== DIAGNOSTIC RÉSEAU ===")
    print("Vérification des interfaces...")
    
    # Vérifier le fichier hosts
    print("\nVérification du fichier hosts:")
    try:
        with open('/etc/hosts', 'r') as f:
            hosts = f.read()
            if '127.0.0.1 localhost' not in hosts:
                print("ALERTE: L'entrée '127.0.0.1 localhost' pourrait manquer dans votre fichier hosts!")
            else:
                print("OK: Entrée localhost trouvée dans le fichier hosts")
    except:
        print("Impossible de lire le fichier hosts")
    
    # Essayer d'ouvrir le navigateur
    for port in [8000, 5000, 3000]:
        print(f"\nTest du port {port}...")
        try:
            # Essayer d'ouvrir le port
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('127.0.0.1', port))
            s.listen(1)
            s.close()
            print(f"Port {port} disponible")
        except:
            print(f"Port {port} déjà utilisé ou non disponible")
    
    print("\n=== RECOMMANDATIONS ===")
    print("1. Vérifiez vos paramètres de proxy dans Safari ou Chrome")
    print("2. Vérifiez si Little Snitch ou un autre pare-feu est actif")
    print("3. Essayez de redémarrer votre ordinateur")
    print("4. Essayez un port plus élevé comme 8080 ou 9000")
    print("5. Désactivez temporairement le pare-feu macOS")
    
    # Retourner un port probablement disponible
    return 9000  # Port moins susceptible d'être utilisé

if __name__ == '__main__':
    # Exécuter le diagnostic réseau
    port = check_network()
    
    # Afficher des informations de démarrage
    print(f"\n=== DÉMARRAGE DU SERVEUR SUR PORT {port} ===")
    print(f"⚠️  ATTENTION: Si vous voyez une erreur dans le navigateur:")
    print(f"   - Essayez d'ouvrir manuellement: http://127.0.0.1:{port}")
    print(f"   - Ou essayez: http://localhost:{port}")
    print(f"   - Ou essayez l'adresse IP publique de votre machine\n")
    
    # Démarrer l'application
    try:
        # Essayer d'ouvrir le navigateur 
        url = f"http://127.0.0.1:{port}"
        webbrowser.open(url)
    except:
        pass
    
    # Exécuter l'application
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)