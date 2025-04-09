import os
import requests
import json

def read_file(file_path):
    """Lit le contenu d'un fichier."""
    print(f"Tentative de lecture du fichier : {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        print(f"Fichier lu avec succès. {len(content)} caractères lus.")
        return content
    except IOError as e:
        print(f"Erreur lors de la lecture du fichier : {e}")
        return None

def query_assistant(prompt, content):
    """Envoie une requête à l'API de Claude 3.5 Sonnet et retourne la réponse."""
    print("Préparation de la requête à l'API Claude 3.5 Sonnet...")
    API_URL = "https://api.anthropic.com/v1/messages"
    API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    if not API_KEY:
        print("Erreur : La clé API n'est pas définie.")
        raise ValueError("La clé API n'est pas définie. Veuillez définir la variable d'environnement ANTHROPIC_API_KEY.")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "model": "claude-3-sonnet-20240229",
        "messages": [
            {"role": "user", "content": f"Prompt: {prompt}\n\nContenu à traiter: {content}"}
        ],
        "max_tokens": 5000
    }
    
    print("Envoi de la requête à l'API...")
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()['content'][0]['text']
        print(f"Réponse reçue de l'API. Longueur de la réponse : {len(result)} caractères.")
        return result
    except requests.RequestException as e:
        print(f"Erreur lors de la requête à l'API : {e}")
        return None

def write_file(file_path, content):
    """Écrit le contenu dans un fichier."""
    print(f"Tentative d'écriture dans le fichier : {file_path}")
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Contenu écrit avec succès dans {file_path}. {len(content)} caractères écrits.")
    except IOError as e:
        print(f"Erreur lors de l'écriture dans le fichier : {e}")

def main():
    print("Démarrage du traitement du contenu de l'hôtel...")
    
    # Obtenir le chemin du répertoire courant du script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Répertoire de travail : {current_dir}")
    
    # Construire les chemins complets vers les fichiers d'entrée et de sortie
    input_file = os.path.join(current_dir, "contenu_scrappe.txt")
    output_file = os.path.join(current_dir, "resultat_traite.txt")
    print(f"Fichier d'entrée : {input_file}")
    print(f"Fichier de sortie : {output_file}")

    # Vérifier si le fichier d'entrée existe
    if not os.path.exists(input_file):
        print(f"Erreur : Le fichier '{input_file}' n'existe pas. Veuillez vérifier le chemin et réessayer.")
        return

    # Lire le contenu du fichier d'entrée
    content = read_file(input_file)
    if content is None:
        print("Impossible de continuer sans le contenu du fichier d'entrée.")
        return

    # Définir le prompt
    prompt = """Filtrer et optimiser le contenu suivant pour un chatbot d'hôtel :
    1. Ne conserver que le contenu en français.
    2. Supprimer toutes les informations répétées.
    3. Organiser le contenu de manière claire et structurée, similaire à ceci :
       - Présentation de l'hôtel
       - Localisation
       - Types de chambres
       - Services principaux
       - Équipements
    4. Garder uniquement les informations essentielles sur l'hôtel et ses services.
    5. Présenter les informations de manière concise mais complète."""
    
    print("Prompt défini pour le traitement du contenu.")

    # Envoyer la requête à Claude 3.5 Sonnet
    print("Envoi de la requête à l'API Claude 3.5 Sonnet...")
    result = query_assistant(prompt, content)
    if result is None:
        print("Impossible de continuer sans la réponse de l'API.")
        return

    # Écrire le résultat dans un fichier
    write_file(output_file, result)

    print("Traitement terminé. Vérifiez le fichier de sortie pour les résultats.")

if __name__ == "__main__":
    main()