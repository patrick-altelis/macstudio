#!/usr/bin/env python3
"""
Ouvre automatiquement le navigateur pour tester la connexion.
"""
import http.server
import socketserver
import threading
import webbrowser
import os
import time
import socket

# Test si le port est utilisable
def is_port_available(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result != 0

# Trouve un port disponible
def find_available_port(start=8000, max_attempts=20):
    for port in range(start, start + max_attempts):
        if is_port_available(port):
            return port
    return None

# Configuration du serveur
PORT = find_available_port(8000)
if not PORT:
    print("ERREUR: Impossible de trouver un port disponible!")
    exit(1)

# Création d'un gestionnaire HTTP simple
class TestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Page HTML simple
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test de connexion</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .success {{ color: green; background: #e8f5e9; padding: 20px; border-radius: 5px; }}
                h1 {{ color: #333; }}
                p {{ line-height: 1.6; }}
            </style>
        </head>
        <body>
            <h1>Test de connexion réussi! 🎉</h1>
            <div class="success">
                <p><strong>Votre serveur web fonctionne correctement sur le port {PORT}.</strong></p>
                <p>Si vous voyez cette page, cela signifie que:</p>
                <ul>
                    <li>Le serveur web peut démarrer</li>
                    <li>Le navigateur peut se connecter</li>
                    <li>Aucun pare-feu ne bloque les connexions</li>
                </ul>
            </div>
            <p>Informations système:</p>
            <ul>
                <li>Port: {PORT}</li>
                <li>Adresse: 127.0.0.1</li>
                <li>Python version: {os.sys.version}</li>
            </ul>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())

# Fonction pour démarrer le serveur
def start_server():
    with socketserver.TCPServer(("", PORT), TestHandler) as httpd:
        print(f"Serveur démarré sur le port {PORT}")
        httpd.serve_forever()

# Démarrer le serveur dans un thread séparé
server_thread = threading.Thread(target=start_server)
server_thread.daemon = True
server_thread.start()

# Attendre un peu que le serveur démarre
time.sleep(1)

# Ouvrir le navigateur
print(f"Ouverture du navigateur à l'adresse: http://127.0.0.1:{PORT}")
url = f"http://127.0.0.1:{PORT}"

# Essayer différentes méthodes pour ouvrir le navigateur
try:
    # Méthode 1: utiliser webbrowser standard
    webbrowser.open(url)
    print("Navigateur ouvert avec webbrowser.open")
except:
    try:
        # Méthode 2: utiliser le module os
        import os
        os.system(f"open {url}")
        print("Navigateur ouvert avec os.system")
    except:
        print(f"Échec de l'ouverture automatique du navigateur. Veuillez ouvrir manuellement: {url}")

# Maintenir le serveur actif
print("Serveur en cours d'exécution. Appuyez sur Ctrl+C pour quitter.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Serveur arrêté.")