import time
from config import setup_logging, SCRIPT_DIR
from utils.file_operations import read_input_file, save_output_file
from utils.api_clients import choose_model, initialize_client, test_api_connection
from processors.french_content_processor import remove_non_french_content

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
    print(f"Fichier lu avec succès. Taille : {original_char_count} caractères.")

    start_time = time.time()
    french_only_text = remove_non_french_content(model_choice, text_content)
    end_time = time.time()

    processing_time = end_time - start_time
    processed_char_count = len(french_only_text)

    print(f"\nTraitement terminé en {processing_time:.2f} secondes.")
    print(f"Texte original : {original_char_count} caractères")
    print(f"Texte traité : {processed_char_count} caractères")
    print(f"Différence : {processed_char_count - original_char_count} caractères")

    save_output_file(SCRIPT_DIR / 'texte_traite.md', french_only_text)

if __name__ == "__main__":
    main()
