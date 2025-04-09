from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def wait_and_find_element(driver, by, value, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        logging.error(f"Élément non trouvé : {by}, {value}")
        return None

def wait_for_modal(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.hp_rt_lightbox_content"))
        )
        logging.info("Modale chargée avec succès")
        return True
    except TimeoutException:
        logging.error("Timeout en attendant le chargement de la modale")
        return False

def scrape_modal_details(driver):
    modal_details = {}
    if not wait_for_modal(driver):
        return modal_details

    try:
        modal_element = driver.find_element(By.CSS_SELECTOR, "div.hp_rt_lightbox_content")
        details_text = modal_element.text
        modal_details['details_complets'] = details_text
        logging.info(f"Détails extraits : {details_text[:100]}...")  # Affiche les 100 premiers caractères
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des détails de la modale : {e}")

    return modal_details

def scrape_room_details(driver, room_element):
    room = {}
    try:
        name_element = room_element.find_element(By.CSS_SELECTOR, 'a.js-legacy-room-name span')
        room['name'] = name_element.text
        logging.info(f"\nExtraction des détails pour : {room['name']}")

        driver.execute_script("arguments[0].click();", name_element)
        time.sleep(2)  # Attendre que la modale s'ouvre

        modal_details = scrape_modal_details(driver)
        room.update(modal_details)

        close_button = wait_and_find_element(driver, By.CSS_SELECTOR, "a.lightbox_close_button[aria-label='Fermer']")
        if close_button:
            close_button.click()
            logging.info("Modale fermée")
        else:
            logging.warning("Bouton de fermeture non trouvé, continuons...")
        time.sleep(1)  # Attendre que la modale se ferme
    except NoSuchElementException as e:
        logging.error(f"Erreur lors de l'extraction des détails de la chambre : {e}")
    except Exception as e:
        logging.error(f"Erreur inattendue : {e}")

    return room

def scrape_rooms(url):
    driver = setup_driver()
    logging.info(f"Accès à l'URL : {url}")
    driver.get(url)
    time.sleep(5)

    cookie_button = wait_and_find_element(driver, By.ID, "onetrust-accept-btn-handler")
    if cookie_button:
        cookie_button.click()
        logging.info("Cookies acceptés")
    else:
        logging.warning("Bouton d'acceptation des cookies non trouvé")

    rooms = []
    try:
        room_section = wait_and_find_element(driver, By.ID, "maxotelRoomArea")
        if room_section:
            room_elements = room_section.find_elements(By.CSS_SELECTOR, 'div.adc8292e09.ea1e323a59.a3c80e4a68.cab35cf0da.fbe4119cc7.f795ed9755.b41b79ca78.e3471aba6c')
            logging.info(f"Nombre d'éléments de chambre trouvés : {len(room_elements)}")

            for room_element in room_elements:
                room = scrape_room_details(driver, room_element)
                if room:
                    rooms.append(room)
                    logging.info(f"Chambre ajoutée : {room['name']}")
        else:
            logging.error("Section des chambres non trouvée")
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des chambres : {e}")

    driver.quit()
    return rooms

def save_rooms_to_txt(rooms):
    with open('chambres_details.txt', 'w', encoding='utf-8') as f:
        for room in rooms:
            f.write(f"# {room['name']}\n\n")
            details = room.get('details_complets', 'Aucun détail trouvé')
            for line in details.split('\n'):
                f.write(f"{line}\n")
            f.write("\n\n")  # Ajout d'espace entre les chambres
    logging.info("Détails de toutes les chambres sauvegardés dans chambres_details.txt")

if __name__ == "__main__":
    url = input("Entrez l'URL de la page Booking à scraper pour les détails des chambres : ")
    rooms = scrape_rooms(url)

    logging.info(f"\nNombre total de chambres trouvées : {len(rooms)}")
    for room in rooms:
        print(f"- Nom: {room['name']}")
        print("  Détails:")
        print(f"    {room.get('details_complets', 'Aucun détail trouvé')[:200]}...")
        print()

    # Sauvegarde des résultats dans un fichier JSON
    with open('room_details.json', 'w', encoding='utf-8') as f:
        json.dump(rooms, f, ensure_ascii=False, indent=2)
    logging.info("Résultats sauvegardés dans room_details.json")

    # Sauvegarde des résultats dans un seul fichier TXT
    save_rooms_to_txt(rooms)