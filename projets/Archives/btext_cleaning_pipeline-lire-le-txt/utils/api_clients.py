import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic

def load_environment():
    load_dotenv()
    return os.getenv("OPENAI_API_KEY"), os.getenv("ANTHROPIC_API_KEY")

def choose_model():
    while True:
        model_choice = input("Choisissez le modèle (1 pour gpt-4o-mini, 2 pour Claude 3.5 Sonnet): ")
        if model_choice in ['1', '2']:
            return model_choice
        print("Choix invalide. Veuillez entrer 1 ou 2.")

def initialize_client(model_choice):
    openai_key, anthropic_key = load_environment()
    if model_choice == "1":
        return OpenAI(api_key=openai_key), "gpt-4o-mini"
    return Anthropic(api_key=anthropic_key), "claude-3-sonnet-20240229"

def test_api_connection(client, model):
    try:
        if "gpt" in model:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Dis 'Hello, World!'"}]
            )
            print("Réponse:", response.choices[0].message.content)
        else:
            response = client.messages.create(
                model=model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Dis 'Hello, World!'"}]
            )
            print("Réponse:", response.content[0].text)
        print("Connexion API réussie!")
        return True
    except Exception as e:
        logging.error(f"Erreur lors de la connexion à l'API {model}: {str(e)}")
        print(f"Erreur lors de la connexion à l'API {model}:", str(e))
        return False
