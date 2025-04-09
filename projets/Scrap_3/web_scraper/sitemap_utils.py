import os
import requests
import xml.etree.ElementTree as ET
import re
from urllib.parse import urlparse

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def clean_filename(url):
    parsed_url = urlparse(url)
    filename = f"{parsed_url.netloc}{parsed_url.path}".replace('/', '_').replace('.', '_')
    return f"resultats_{filename[:200]}.txt"

def get_sitemap(url):
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

def select_urls_from_sitemap(sitemap_urls):
    print("\nVoici les URLs trouvées dans le sitemap:")
    for i, url in enumerate(sitemap_urls, 1):
        print(f"{i}. {url}")
    
    selected_indices = input("\nEntrez les numéros des URLs que vous voulez scraper (séparés par des virgules) ou 'all' pour toutes : ").strip()
    
    if selected_indices.lower() == 'all':
        return sitemap_urls
    else:
        indices = [int(idx.strip()) - 1 for idx in selected_indices.split(',')]
        return [sitemap_urls[i] for i in indices if 0 <= i < len(sitemap_urls)]
