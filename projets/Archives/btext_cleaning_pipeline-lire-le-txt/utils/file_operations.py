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
