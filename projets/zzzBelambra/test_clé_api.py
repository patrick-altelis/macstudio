from openai import OpenAI
import os
from dotenv import load_dotenv

# Charger la clé API depuis le fichier .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def test_openai_api():
    try:
        # Faire une requête simple à l'API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Dis-moi bonjour."}
            ]
        )
        
        # Vérifier la réponse
        if response.choices and response.choices[0].message:
            print("Succès ! Voici la réponse de l'API :")
            print(response.choices[0].message.content)
        else:
            print("La requête a réussi, mais la réponse est inattendue.")
        
        return True
    except Exception as e:
        print(f"Erreur lors du test de l'API : {str(e)}")
        return False

if __name__ == "__main__":
    if test_openai_api():
        print("Votre clé API fonctionne correctement !")
    else:
        print("Il y a un problème avec votre clé API ou la connexion à OpenAI.")