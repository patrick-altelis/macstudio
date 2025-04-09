import os
import sys
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import time
import random
import xml.etree.ElementTree as ET
import re
from urllib.parse import urlparse
from difflib import SequenceMatcher

# Créer le répertoire 'data' s'il n'existe pas
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def clean_filename(url):
    """
    Génère un nom de fichier propre à partir d'une URL.
    """
    parsed_url = urlparse(url)
    filename = f"{parsed_url.netloc}{parsed_url.path}".replace('/', '_').replace('.', '_')
    return f"resultats_{filename[:200]}.txt"

def get_sitemap(url):
    """
    Récupère et parse le sitemap d'un site web.
    """
    print("Récupération du sitemap")

    robots_url = f"{url.rstrip('/')}/robots.txt"
    try:
        robots_response = requests.get(robots_url, timeout=10)
        robots_response.raise_for_status()
        sitemap_match = re.search(r'Sitemap:\s*(.*)', robots_response.text)
        if sitemap_match:
            sitemap_url = sitemap_match.group(1)
            print(f"Sitemap trouvé dans robots.txt: {sitemap_url}")
        else:
            sitemap_url = f"{url.rstrip('/')}/sitemap.xml"
            print(f"Aucun sitemap trouvé dans robots.txt, essai avec: {sitemap_url}")
    except requests.RequestException:
        sitemap_url = f"{url.rstrip('/')}/sitemap.xml"
        print(f"Pas de robots.txt trouvé, essai avec: {sitemap_url}")

    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        
        # Nettoyage du contenu XML
        content = response.text
        content = re.sub(r"<\?xml[^>]+\?>", "", content)
        content = content.strip()

        root = ET.fromstring(content)

        all_urls = []
        sitemaps = root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap")
        if sitemaps:
            print("Sitemap index trouvé")
            for sitemap in sitemaps:
                sitemap_loc = sitemap.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
                print(f"Traitement du sitemap: {sitemap_loc}")
                sitemap_response = requests.get(sitemap_loc, timeout=10)
                sitemap_response.raise_for_status()
                sitemap_content = sitemap_response.text
                sitemap_content = re.sub(r"<\?xml[^>]+\?>", "", sitemap_content)
                sitemap_content = sitemap_content.strip()
                sitemap_root = ET.fromstring(sitemap_content)
                all_urls.extend([elem.text for elem in sitemap_root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")])
        else:
            print("Sitemap simple trouvé")
            all_urls = [elem.text for elem in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]

        print(f"Nombre total d'URLs trouvées : {len(all_urls)}")
        
        urls_file_path = os.path.join(DATA_DIR, 'urls_trouvees.txt')
        print(f"Écriture des URLs dans le fichier '{urls_file_path}'")

        with open(urls_file_path, 'w') as f:
            for url in all_urls:
                f.write(f"{url}\n")

        print(f"Les URLs ont été écrites dans le fichier '{urls_file_path}'")

        return all_urls
    except ET.ParseError as e:
        print(f"Erreur lors du parsing XML : {e}")
        print("Contenu problématique :")
        print(content[:500])
        return None
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération du sitemap : {e}")
        return None

def find_repetitive_content(texts):
    """
    Trouve le contenu répétitif dans une liste de textes.
    """
    common_parts = []
    for i in range(len(texts)):
        for j in range(i+1, len(texts)):
            s = SequenceMatcher(None, texts[i], texts[j])
            for block in s.get_matching_blocks():
                if block.size > 100:
                    common_parts.append(texts[i][block.a:block.a+block.size])
    
    if common_parts:
        return max(common_parts, key=len)
    return ""

def remove_repetitive_content(text, repetitive_content):
    """
    Supprime le contenu répétitif d'un texte.
    """
    if repetitive_content:
        return text.replace(repetitive_content, '')
    return text

def scrape_page(url):
    """
    Scrape une page web individuelle.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else "Pas de titre"

        texts = soup.stripped_strings
        content = ' '.join(texts)

        return content, title
    except requests.RequestException as e:
        return f"Erreur lors du scraping de {url}: {e}", ""

def scrape_multiple_pages(urls):
    """
    Scrape plusieurs pages en parallèle.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(scrape_page, urls))
    return results

def save_results(results, filename, repetitive_content):
    """
    Sauvegarde les résultats du scraping dans un fichier.
    """
    file_path = os.path.join(DATA_DIR, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        if repetitive_content:
            f.write(f"Contenu répétitif détecté sur plusieurs pages:\n{repetitive_content}\n\n")
            f.write("====================================================================================================\n\n")
        for content, title in results:
            if isinstance(content, str) and not content.startswith("Erreur"):
                cleaned_content = remove_repetitive_content(content, repetitive_content)
                f.write(f"====================================================================================================\n")
                f.write(f"Titre: {title}\n\n")
                f.write(f"Contenu:\n{cleaned_content}\n\n")
            else:
                f.write(f"{content}\n\n")
    print(f"Les résultats ont été sauvegardés dans '{file_path}'")

def select_urls_from_sitemap(sitemap_urls):
    """
    Permet à l'utilisateur de sélectionner des URLs spécifiques du sitemap.
    """
    print("\nVoici les URLs trouvées dans le sitemap:")
    for i, url in enumerate(sitemap_urls, 1):
        print(f"{i}. {url}")
    
    selected_indices = input("\nEntrez les numéros des URLs que vous voulez scraper (séparés par des virgules) ou 'all' pour toutes : ").strip()
    
    if selected_indices.lower() == 'all':
        return sitemap_urls
    else:
        indices = [int(idx.strip()) - 1 for idx in selected_indices.split(',')]
        return [sitemap_urls[i] for i in indices if 0 <= i < len(sitemap_urls)]

if __name__ == "__main__":
    filename = "resultats_default.txt"
    try:
        print("Début du script de web scraping")
        
        choice = input("Voulez-vous scraper une URL spécifique (1) ou utiliser le sitemap (2) ? ").strip()
        
        if choice == '1':
            url_to_scrape = input("Entrez l'URL à scraper : ").strip()
            urls = [url_to_scrape]
            filename = clean_filename(url_to_scrape)
        elif choice == '2':
            main_url = input("Veuillez entrer l'URL principale du site pour récupérer le sitemap : ").strip()
            sitemap_urls = get_sitemap(main_url)
            
            if sitemap_urls:
                urls = select_urls_from_sitemap(sitemap_urls)
                filename = clean_filename(main_url)
            else:
                print("Aucun sitemap trouvé. Le script va se terminer.")
                sys.exit(1)
        else:
            print("Choix non valide. Le script va se terminer.")
            sys.exit(1)

        print(f"\nNombre total d'URLs à scraper : {len(urls)}")

        start_time = time.time()
        results = scrape_multiple_pages(urls)
        end_time = time.time()

        print(f"Scraping terminé en {end_time - start_time:.2f} secondes.")

        find_repetitive = input("Voulez-vous rechercher le contenu répétitif ? (o/n) : ").lower() == 'o'

        if find_repetitive:
            contents = [content for content, _ in results if isinstance(content, str) and not content.startswith("Erreur")]
            print("Recherche du contenu répétitif...")
            repetitive_content = find_repetitive_content(contents)
        else:
            repetitive_content = ""

        save_results(results, filename, repetitive_content)

    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
    finally:
        print("Fin du script")
        print(f"Vérifiez le fichier 'data/{filename}' pour les résultats complets.")
        input("Appuyez sur Enter pour terminer...")