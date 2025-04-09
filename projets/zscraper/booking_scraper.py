import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def scrape_booking_page(url):
    print(f"Début du scraping de l'URL : {url}")
    
    driver = setup_driver()
    driver.get(url)
    
    print("Page chargée, attente de 20 secondes...")
    time.sleep(20)  # Attendre 20 secondes pour laisser la page se charger complètement

    # Récupérer tout le texte et le HTML de la page
    page_text = driver.find_element(By.TAG_NAME, 'body').text
    page_html = driver.page_source
    
    driver.quit()
    
    return page_text, page_html

def structure_content(text_content, html_content):
    def create_section(title, pattern, content, all_matches=False):
        if all_matches:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                if isinstance(matches[0], tuple):
                    return f"\n\n{title}\n{'-' * len(title)}\n" + "\n".join([f"• {' - '.join(match).strip()}" for match in matches])
                else:
                    return f"\n\n{title}\n{'-' * len(title)}\n" + "\n".join([f"• {match.strip()}" for match in matches])
            return ""
        else:
            match = re.search(pattern, content, re.DOTALL)
            return f"\n\n{title}\n{'-' * len(title)}\n{match.group(1).strip()}" if match else ""

    structured_content = "DÉTAILS DE L'HÔTEL SUR BOOKING.COM\n"
    structured_content += "=" * 40 + "\n"

    # Nom de l'hôtel (approche plus générique)
    hotel_name_patterns = [
        r"<title>(.*?)(?: - |,).*?</title>",
        r"<h1.*?>(.*?)</h1>",
        r"<h2.*?>(.*?)</h2>",
        r"data-testid=\"property-header\".*?>(.*?)<",
    ]

    hotel_name = None
    for pattern in hotel_name_patterns:
        match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
        if match:
            hotel_name = match.group(1).strip()
            break

    if hotel_name:
        structured_content += f"\nNom de l'hôtel\n{'-' * 14}\n{hotel_name}\n"
    else:
        structured_content += "\nNom de l'hôtel\n{'-' * 14}\nNon trouvé\n"

    # Adresse (recherche plus flexible)
    address_pattern = r"(\d+[^,\n]+,\s*\d{5}\s+[\w\s-]+,\s*France)"
    address_match = re.search(address_pattern, text_content)
    if address_match:
        structured_content += f"\nAdresse\n{'-' * 7}\n{address_match.group(1)}\n"
    else:
        structured_content += "\nAdresse\n{'-' * 7}\nNon trouvée\n"

    structured_content += create_section("Note globale", r"Avec une note de ([\d.]+)", text_content)
    structured_content += create_section("Description de l'hôtel", r"((?:Le |L').*? est situé à.*?(?:Un |Une )parking .+? est disponible .+?\.)", text_content)
    structured_content += create_section("Équipements et services", r"Ses points forts(.*?)(?:Brit Hotel|Chaîne hôtelière)", text_content)

    # Avis des clients (formatage amélioré)
    reviews = re.findall(r"« (.+?) »\s*(.*?)\s*(?:France|Belgique|Maroc|Suisse|Royaume-Uni|Allemagne)", text_content, re.DOTALL)
    if reviews:
        structured_content += "\n\nAvis des clients\n" + "-" * 16 + "\n"
        for review, author in reviews[:10]:  # Limiter à 10 avis pour la lisibilité
            structured_content += f"• \"{review.strip()}\" - {author.strip()}\n\n"

    structured_content += create_section("Types de chambres", r"Type de logement(.*?)Pratiques de l'établissement", text_content)
    structured_content += create_section("Informations pratiques", r"Pratiques de l'établissement(.*?)Commentaires clients", text_content)

    # Sections supplémentaires
    additional_sections = [
        ("Disponibilité", r"Disponibilité(.*?)Type de logement"),
        ("Équipements de l'établissement", r"Équipements de l'établissement.*?(.*?)Règles de la maison"),
        ("Règles de la maison", r"Règles de la maison(.*?)Commentaires clients"),
        ("Environs de l'hôtel", r"Environs de l'hôtel(.*?)Équipements de l'établissement"),
        ("Questions fréquentes", r"Questions des voyageurs(.*?)Environs de l'hôtel"),
        ("Informations légales", r"Informations juridiques(.*?)Les incontournables de :"),
    ]

    for title, pattern in additional_sections:
        structured_content += create_section(title, pattern, text_content)

    return structured_content

def save_results(text, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Résultats sauvegardés dans {filename}")

if __name__ == "__main__":
    url = input("Entrez l'URL de la page Booking à scraper : ")
    text_content, html_content = scrape_booking_page(url)
    
    structured_content = structure_content(text_content, html_content)
    
    timestamp = time.strftime('%Y%m%d-%H%M%S')
    filename = f"booking_structured_{timestamp}.txt"
    save_results(structured_content, filename)
    
    print("\nScraping et structuration terminés.")
    print(f"Contenu structuré sauvegardé dans '{filename}'")