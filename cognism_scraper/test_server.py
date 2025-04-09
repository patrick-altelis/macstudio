"""
Test server simple pour vérifier qu'un serveur HTTP fonctionne.
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

PORT = 8090

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Server</title>
        </head>
        <body>
            <h1>Test Server Fonctionne sur le port {PORT}!</h1>
            <p>Ce serveur de test fonctionne correctement.</p>
        </body>
        </html>
        """
        self.wfile.write(message.encode())
        return

print(f"Serveur démarré sur http://localhost:{PORT}")
httpd = HTTPServer(('localhost', PORT), Handler)
httpd.serve_forever()