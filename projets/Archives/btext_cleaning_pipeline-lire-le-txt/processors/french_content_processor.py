import os
import time
import logging
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
from langdetect import detect
import multiprocessing
from functools import partial

# Configuration du logging
logging.basicConfig(filename='text_processing.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_environment():
    """Charge les variables d'environnement."""
    load_dotenv()
    return os.getenv("OPENAI_API_KEY"), os.getenv("ANTHROPIC_API_KEY")

def initialize_client(model_choice):
    """Initialise et retourne le client API approprié."""
    openai_key, anthropic_key = load_environment()
    if model_choice == "1":
        return OpenAI(api_key=openai_key), "gpt-4o-mini"
    else:
        return Anthropic(api_key=anthropic_key), "claude-3-sonnet-20240229"

def is_french(text):
    """Vérifie si le texte est en français."""
    try:
        return detect(text) == 'fr'
    except:
        return False

def split_text(text, max_chunk_size=4000):
    """Divise le texte en morceaux gérables."""
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(' '.join(current_chunk)) > max_chunk_size:
            chunks.append(' '.join(current_chunk[:-1]))
            current_chunk = [word]
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def process_chunk(model_choice, chunk, chunk_number, total_chunks):
    """Traite un morceau de texte pour ne garder que le contenu français."""
    client, model = initialize_client(model_choice)
    try:
        if "gpt" in model:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Tu es un assistant spécialisé dans l'identification et la conservation du contenu en français."},
                    {"role": "user", "content": f"""Traite le texte suivant selon ces instructions :
                    1. Identifie et conserve uniquement le contenu en français
                    2. Supprime tout contenu qui n'est pas en français
                    3. Si aucun contenu français n'est trouvé, renvoie une chaîne vide

                    Texte à traiter (partie {chunk_number}/{total_chunks}) : {chunk}
                    """}
                ]
            )
            processed_chunk = response.choices[0].message.content.strip()
        else:
            response = client.messages.create(
                model=model,
                max_tokens=len(chunk),
                messages=[
                    {"role": "system", "content": "Tu es un assistant spécialisé dans l'identification et la conservation du contenu en français."},
                    {"role": "user", "content": f"""Traite le texte suivant selon ces instructions :
                    1. Identifie et conserve uniquement le contenu en français
                    2. Supprime tout contenu qui n'est pas en français
                    3. Si aucun contenu français n'est trouvé, renvoie une chaîne vide

                    Texte à traiter (partie {chunk_number}/{total_chunks}) : {chunk}
                    """}
                ]
            )
            processed_chunk = response.content[0].text.strip()
        
        # Vérification supplémentaire pour s'assurer que le contenu est en français
        if is_french(processed_chunk):
            return processed_chunk
        else:
            return ""
    except Exception as e:
        logging.error(f"Erreur lors du traitement de la partie {chunk_number}: {str(e)}")
        return ""

def remove_non_french_content(model_choice, text):
    """Fonction principale pour éliminer le contenu non français."""
    chunks = split_text(text)
    total_chunks = len(chunks)
    
    logging.info(f"Début de l'élimination du contenu non français en {total_chunks} parties.")
    print(f"Élimination du contenu non français en {total_chunks} parties...")

    # Utiliser un pool de processus
    with multiprocessing.Pool() as pool:
        process_func = partial(process_chunk, model_choice)
        results = list(tqdm(
            pool.starmap(process_func, [(chunk, i+1, total_chunks) for i, chunk in enumerate(chunks)]),
            total=total_chunks,
            desc="Progression",
            unit="partie"
        ))

    # Filtrer les résultats vides
    french_only_chunks = [chunk for chunk in results if chunk]

    french_only_text = "\n\n".join(french_only_chunks)
    logging.info(f"Traitement terminé. Longueur du texte final : {len(french_only_text)}")
    return french_only_text

# Cette fonction peut être appelée depuis votre script principal
def main(text_content):
    model_choice = input("Choisissez le modèle (1 pour gpt-4o-mini, 2 pour Claude 3.5 Sonnet): ")
    processed_text = remove_non_french_content(model_choice, text_content)
    return processed_text

if __name__ == "__main__":
    # Ce bloc ne sera exécuté que si le script est exécuté directement
    sample_text = "Ceci est un exemple de texte. This is an example of text. Esto es un ejemplo de texto."
    result = main(sample_text)
    print("Texte traité :", result)