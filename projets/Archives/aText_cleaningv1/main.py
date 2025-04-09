import os
import json
import time
import logging
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
from tqdm import tqdm
import multiprocessing
from functools import partial

# Configuration
logging.basicConfig(filename='text_processing.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_CHUNK_SIZE = 4000

def load_environment():
    load_dotenv()
    return os.getenv("OPENAI_API_KEY"), os.getenv("ANTHROPIC_API_KEY")

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

def save_progress(chunks, processed_chunks):
    with open('progress.json', 'w', encoding='utf-8') as f:
        json.dump({'chunks': chunks, 'processed_chunks': processed_chunks}, f, ensure_ascii=False)

def load_progress():
    try:
        with open('progress.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def process_chunk(model_choice, chunk, chunk_number, total_chunks):
    client, model = initialize_client(model_choice)
    try:
        if "gpt" in model:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Tu es un assistant spécialisé dans le traitement et la structuration de textes."},
                    {"role": "user", "content": f"""Traite le texte suivant selon ces instructions :
                    1. Supprime ce qui n'est pas en français
                    2. Supprime le code HTML
                    3. Corrige le texte
                    4. Structure le contenu en markdown cohérent

                    Texte à traiter (partie {chunk_number}/{total_chunks}) : {chunk}
                    """}
                ]
            )
            return response.choices[0].message.content.strip()
        else:
            response = client.messages.create(
                model=model,
                max_tokens=1000,
                system="Tu es un assistant spécialisé dans le traitement et la structuration de textes.",
                messages=[
                    {"role": "user", "content": f"""Traite le texte suivant selon ces instructions :
                    1. Supprime ce qui n'est pas en français
                    2. Supprime le code HTML
                    3. Corrige le texte
                    4. Structure le contenu en markdown cohérent

                    Texte à traiter (partie {chunk_number}/{total_chunks}) : {chunk}
                    """}
                ]
            )
            return response.content[0].text.strip()
    except Exception as e:
        logging.error(f"Erreur lors du traitement de la partie {chunk_number}: {str(e)}")
        return None

def process_text_with_llm(model_choice, text):
    chunks = split_text(text)
    total_chunks = len(chunks)
    
    progress = load_progress()
    if progress:
        processed_chunks = progress['processed_chunks']
        start_index = len(processed_chunks)
        print(f"Reprise du traitement à partir de la partie {start_index + 1}")
    else:
        processed_chunks = []
        start_index = 0
    
    print(f"Traitement du texte en {total_chunks} parties...")
    logging.info(f"Début du traitement du texte en {total_chunks} parties.")

    with multiprocessing.Pool() as pool:
        process_func = partial(process_chunk, model_choice)
        results = list(tqdm(
            pool.starmap(process_func, [(chunk, i+1, total_chunks) for i, chunk in enumerate(chunks[start_index:], start=start_index)]),
            total=total_chunks - start_index,
            initial=start_index,
            desc="Progression",
            unit="partie"
        ))

    for result in results:
        if result is not None:
            processed_chunks.append(result)
        
        # Sauvegarde périodique
        if len(processed_chunks) % 5 == 0:
            save_progress(chunks, processed_chunks)
        
        time.sleep(1)  # Pour éviter de surcharger l'API

    processed_text = "\n\n".join(processed_chunks)
    return processed_text, len(processed_chunks)
def post_process_text(model_choice, text):
    client, model = initialize_client(model_choice)
    try:
        if "gpt" in model:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Tu es un assistant spécialisé dans le traitement et la structuration de textes."},
                    {"role": "user", "content": f"""Traite le texte suivant selon ces instructions :
                    1. Élimine les répétitions en ne gardant qu'une occurrence
                    2. Assure-toi que le contenu est cohérent et bien structuré en markdown
                    3. Vérifie que le texte est entièrement en français

                    Texte à traiter : {text}
                    """}
                ]
            )
            return response.choices[0].message.content.strip()
        else:
            response = client.messages.create(
                model=model,
                max_tokens=4000,
                system="Tu es un assistant spécialisé dans le traitement et la structuration de textes.",
                messages=[
                    {"role": "user", "content": f"""Traite le texte suivant selon ces instructions :
                    1. Élimine les répétitions en ne gardant qu'une occurrence
                    2. Assure-toi que le contenu est cohérent et bien structuré en markdown
                    3. Vérifie que le texte est entièrement en français

                    Texte à traiter : {text}
                    """}
                ]
            )
            return response.content[0].text.strip()
    except Exception as e:
        logging.error(f"Erreur lors du post-traitement : {str(e)}")
        return text

def read_input_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logging.error(f"Erreur lors de la lecture du fichier : {str(e)}")
        print(f"Erreur lors de la lecture du fichier : {str(e)}")
        print(f"Chemin du fichier tenté : {file_path}")
        return None

def save_output_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"Résultat sauvegardé dans : {file_path}")
    logging.info(f"Résultat sauvegardé dans : {file_path}")

def main():
    while True:
        model_choice = input("Choisissez le modèle (1 pour gpt-4o-mini, 2 pour Claude 3.5 Sonnet): ")
        if model_choice in ['1', '2']:
            break
        print("Choix invalide. Veuillez entrer 1 ou 2.")

    client, model = initialize_client(model_choice)
    if not test_api_connection(client, model):
        print(f"Impossible de se connecter à l'API {model}. Vérifiez votre clé API et votre connexion internet.")
        return

    input_file_path = os.path.join(SCRIPT_DIR, 'texte_a_traiter.txt')
    text_content = read_input_file(input_file_path)
    if text_content is None:
        return

    original_char_count = len(text_content)
    print(f"Fichier lu avec succès. Taille : {original_char_count} caractères.")
    logging.info(f"Fichier lu avec succès. Taille : {original_char_count} caractères.")

    print("Début du traitement du texte...")
    processed_text, last_processed = process_text_with_llm(model_choice, text_content)

    print("Post-traitement pour éliminer les répétitions globales...")
    final_text = post_process_text(model_choice, processed_text)

    processed_char_count = len(final_text)
    print(f"\nTraitement terminé. Nombre de caractères dans le texte traité : {processed_char_count}")
    logging.info(f"Traitement terminé. Nombre de caractères dans le texte traité : {processed_char_count}")
    
    char_diff = processed_char_count - original_char_count
    if char_diff > 0:
        print(f"Le texte traité est plus long de {char_diff} caractères.")
    elif char_diff < 0:
        print(f"Le texte traité est plus court de {abs(char_diff)} caractères.")
    else:
        print("Le texte traité a le même nombre de caractères que l'original.")

    print("Sauvegarde du résultat...")
    output_file_path = os.path.join(SCRIPT_DIR, 'texte_traite.md')
    save_output_file(output_file_path, final_text)

if __name__ == "__main__":
    main()