#!/usr/bin/env python3
"""
Serveur web minimal pour tester les problèmes de connexion.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        message = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test de connectivité</title>
        </head>
        <body>
            <h1>Le serveur fonctionne correctement!</h1>
            <p>Si vous voyez cette page, cela signifie que la connexion au serveur web fonctionne.</p>
        </body>
        </html>
        """
        
        self.wfile.write(message.encode())
        return

def run_server(port=8899):
    server_address = ('', port)  # Écoute sur toutes les interfaces
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Serveur démarré sur le port {port}")
    print(f"Ouvrez votre navigateur sur http://localhost:{port}")
    print(f"Ou essayez directement 127.0.0.1:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()