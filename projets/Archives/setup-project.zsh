#!/bin/zsh

# Définir le nom du projet
PROJECT_NAME="text_cleaning_pipeline"

# Créer la structure du projet
mkdir -p $PROJECT_NAME/{utils,processors}

# Créer les fichiers principaux
touch $PROJECT_NAME/main.py
touch $PROJECT_NAME/config.py
touch $PROJECT_NAME/requirements.txt
touch $PROJECT_NAME/.env

# Créer les fichiers utils
touch $PROJECT_NAME/utils/__init__.py
touch $PROJECT_NAME/utils/file_operations.py
touch $PROJECT_NAME/utils/text_processing.py
touch $PROJECT_NAME/utils/api_clients.py

# Créer les fichiers processors
touch $PROJECT_NAME/processors/__init__.py
touch $PROJECT_NAME/processors/french_content_processor.py
touch $PROJECT_NAME/processors/html_cleaner.py
touch $PROJECT_NAME/processors/repetition_remover.py

# Fonction pour écrire le contenu dans un fichier
write_content() {
    echo "$2" > "$PROJECT_NAME/$1"
}

# Écrire le contenu dans main.py
write_content "main.py" "$(cat << EOF
import logging
from config import setup_logging, SCRIPT_DIR
from utils.file_operations import read_input_file, save_output_file
from utils.api_clients import choose_model, initialize_client, test_api_connection
from processors.french_content_processor import remove_non_french_content
# Import other processors as needed

def main():
    setup_logging()
    model_choice = choose_model()
    client, model = initialize_client(model_choice)
    if not test_api_connection(client, model):
        return

    text_content = read_input_file(SCRIPT_DIR / 'texte_a_traiter.txt')
    if text_content is None:
        return

    original_char_count = len(text_content)
    logging.info(f"Fichier lu avec succès. Taille : {original_char_count} caractères.")

    # Step 1: Remove non-French content
    french_only_text = remove_non_french_content(model_choice, text_content)
    
    # Add other processing steps here
    
    final_text = french_only_text  # For now, just use the French-only text

    processed_char_count = len(final_text)
    logging.info(f"Traitement terminé. Nombre de caractères dans le texte traité : {processed_char_count}")
    
    save_output_file(SCRIPT_DIR / 'texte_traite.md', final_text)

if __name__ == "__main__":
    main()
EOF
)"

# Écrire le contenu dans config.py
write_content "config.py" "$(cat << EOF
import logging
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
MAX_CHUNK_SIZE = 4000

def setup_logging():
    logging.basicConfig(filename='text_processing.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
EOF
)"

# Écrire le contenu dans requirements.txt
write_content "requirements.txt" "$(cat << EOF
python-dotenv==1.0.0
openai==1.3.0
anthropic==0.3.0
tqdm==4.66.1
EOF
)"

# Écrire le contenu dans .env (à remplir par l'utilisateur)
write_content ".env" "$(cat << EOF
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
EOF
)"

# Écrire le contenu dans utils/file_operations.py
write_content "utils/file_operations.py" "$(cat << EOF
import logging

def read_input_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logging.error(f"Erreur lors de la lecture du fichier : {str(e)}")
        print(f"Erreur lors de la lecture du fichier : {str(e)}")
        return None

def save_output_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    logging.info(f"Résultat sauvegardé dans : {file_path}")
    print(f"Résultat sauvegardé dans : {file_path}")
EOF
)"

# Écrire le contenu dans utils/text_processing.py
write_content "utils/text_processing.py" "$(cat << EOF
from config import MAX_CHUNK_SIZE

def split_text(text):
    words = text.split()
    chunks = []
    current_chunk = []
    for word in words:
        current_chunk.append(word)
        if len(' '.join(current_chunk)) > MAX_CHUNK_SIZE:
            chunks.append(' '.join(current_chunk[:-1]))
            current_chunk = [word]
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks
EOF
)"

# Écrire le contenu dans utils/api_clients.py
write_content "utils/api_clients.py" "$(cat << EOF
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
EOF
)"

# Écrire le contenu dans processors/french_content_processor.py
write_content "processors/french_content_processor.py" "$(cat << EOF
import time
import logging
from tqdm import tqdm
from utils.text_processing import split_text
from utils.api_clients import initialize_client

def remove_non_french_content(model_choice, text):
    client, model = initialize_client(model_choice)
    chunks = split_text(text)
    total_chunks = len(chunks)
    
    logging.info(f"Début de l'élimination du contenu non français en {total_chunks} parties.")
    print(f"Élimination du contenu non français en {total_chunks} parties...")

    french_only_chunks = []

    for i, chunk in enumerate(tqdm(chunks, desc="Progression", unit="partie")):
        try:
            if "gpt" in model:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "Tu es un assistant spécialisé dans l'identification et la conservation du contenu en français."},
                        {"role": "user", "content": f"""Traite le texte suivant selon ces instructions :
                        1. Identifie et conserve uniquement le contenu en français
                        2. Supprime tout contenu qui n'est pas en français
                        3. Conserve la structure du texte français (paragraphes, titres, etc.)

                        Texte à traiter (partie {i+1}/{total_chunks}) : {chunk}
                        """}
                    ]
                )
                french_only_chunks.append(response.choices[0].message.content.strip())
            else:
                response = client.messages.create(
                    model=model,
                    max_tokens=len(chunk),
                    system="Tu es un assistant spécialisé dans l'identification et la conservation du contenu en français.",
                    messages=[
                        {"role": "user", "content": f"""Traite le texte suivant selon ces instructions :
                        1. Identifie et conserve uniquement le contenu en français
                        2. Supprime tout contenu qui n'est pas en français
                        3. Conserve la structure du texte français (paragraphes, titres, etc.)

                        Texte à traiter (partie {i+1}/{total_chunks}) : {chunk}
                        """}
                    ]
                )
                french_only_chunks.append(response.content[0].text.strip())
            
            time.sleep(1)  # Pour éviter de surcharger l'API
        except Exception as e:
            logging.error(f"Erreur lors du traitement de la partie {i+1}: {str(e)}")
            french_only_chunks.append(chunk)  # En cas d'erreur, on garde le texte original

    french_only_text = "\n\n".join(french_only_chunks)
    return french_only_text
EOF
)"

echo "Structure du projet créée avec succès dans le dossier $PROJECT_NAME"
echo "N'oubliez pas de remplir le fichier .env avec vos clés API"
echo "Pour installer les dépendances, exécutez : cd $PROJECT_NAME && pip install -r requirements.txt"
