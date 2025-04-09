#!/usr/bin/env python3
"""
Teste la création d'un socket TCP brut sur le port 8080 pour vérifier les problèmes de liaison.
"""
import socket
import sys

def test_server(port=8080):
    # Créer un socket TCP/IP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Permettre la réutilisation de l'adresse socket locale
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Essayer de lier le socket à l'adresse et port
    server_address = ('0.0.0.0', port)
    print(f'Essai de liaison sur {server_address}')
    
    try:
        sock.bind(server_address)
        print(f'Liaison réussie sur le port {port}')
        sock.listen(1)
        print(f'En attente de connexion sur le port {port}...')
        print(f'Essayez maintenant: http://127.0.0.1:{port}')
        
        # Attendre une connexion
        connection, client_address = sock.accept()
        try:
            print(f'Connexion depuis {client_address}')
            
            # Envoyer des données au client
            message = b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Ca fonctionne!</h1></body></html>\r\n'
            connection.sendall(message)
        finally:
            # Nettoyer la connexion
            connection.close()
    
    except socket.error as e:
        print(f'Erreur: {e}')
        sys.exit(1)
    finally:
        sock.close()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8080
    
    test_server(port)