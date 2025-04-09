import os
from dotenv import load_dotenv
from openai import OpenAI
from src.pipeline import TextCleaningPipeline
import json

def test_api_connection(client):
    """Teste la connexion à l'API OpenAI."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Dis 'Hello, World!'"}
            ]
        )
        print("Connexion API réussie!")
        print("Réponse:", response.choices[0].message.content)
        return True
    except Exception as e:
        print("Erreur lors de la connexion à l'API:", str(e))
        return False

def process_text_with_openai(client, text):
    """Traite le texte avec l'API OpenAI."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un assistant spécialisé dans le traitement et la structuration de textes."},
                {"role": "user", "content": f"""Traite le texte suivant selon ces instructions :
                1. Supprime ce qui n'est pas en français
                2. Supprime le code HTML
                3. Élimine les répétitions en ne gardant qu'une occurrence
                4. Corrige le texte
                5. Structure le contenu en markdown cohérent

                Texte à traiter : {text}
                """}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Erreur lors du traitement du texte avec OpenAI : {str(e)}"

def main():
    # Charger les variables d'environnement
    load_dotenv()
    
    # Initialiser le client OpenAI
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception as e:
        print(f"Erreur lors de l'initialisation du client OpenAI: {str(e)}")
        return

    # Tester la connexion API
    if not test_api_connection(client):
        print("Impossible de se connecter à l'API. Vérifiez votre clé API et votre connexion internet.")
        return

    # Lire le contenu du fichier texte
    try:
        with open('texte_a_traiter.txt', 'r', encoding='utf-8') as file:
            text_content = file.read()
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier : {str(e)}")
        return

    # Traiter le texte avec OpenAI
    processed_text = process_text_with_openai(client, text_content)

    # Afficher le résultat
    print("\nTexte traité :")
    print(processed_text)

    # Optionnel : Sauvegarder le résultat dans un fichier
    with open('texte_traite.md', 'w', encoding='utf-8') as file:
        file.write(processed_text)

if __name__ == "__main__":
    main()