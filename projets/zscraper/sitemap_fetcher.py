import re
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import gzip
import io
import time
from bs4 import BeautifulSoup
import os
import concurrent.futures

# Configuration des headers pour les requêtes
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# Fonction pour récupérer les sitemaps à partir de robots.txt
def get_robots_sitemaps(url):
    robots_url = f"{url.rstrip('/')}/robots.txt"
    sitemaps = []
    try:
        response = requests.get(robots_url, timeout=10, headers=HEADERS)
        response.raise_for_status()
        sitemap_matches = re.findall(r'Sitemap:\s*(\S+)', response.text, re.IGNORECASE)
        for match in sitemap_matches:
            sitemaps.append(match.strip())
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération de robots.txt : {e}")
    return sitemaps

# Fonction pour essayer des emplacements communs pour les sitemaps
def try_common_sitemap_locations(url):
    common_paths = [
        '/sitemap.xml',
        '/sitemap_index.xml',
        '/sitemap1.xml',
        '/sitemap_fr.xml',
        '/fr/sitemap.xml',
        '/sitemap.xml.gz'
    ]
    sitemaps = []
    for path in common_paths:
        sitemap_url = urljoin(url, path)
        try:
            response = requests.get(sitemap_url, timeout=10, headers=HEADERS)
            if response.status_code == 200:
                sitemaps.append(sitemap_url)
        except requests.RequestException:
            continue
    return sitemaps

# Fonction pour récupérer et traiter les URLs dans un sitemap
def fetch_sitemap(sitemap_url):
    urls = []
    try:
        response = requests.get(sitemap_url, timeout=10, headers=HEADERS)
        response.raise_for_status()

        # Gestion des fichiers gzip
        if sitemap_url.endswith('.gz'):
            with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
                content = gz.read()
        else:
            content = response.content

        try:
            root = ET.fromstring(content)
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        except ET.ParseError:
            print(f"Erreur lors du parsing XML du sitemap {sitemap_url}. Tentative sans namespace.")
            try:
                root = ET.fromstring(content.decode('utf-8'))
                namespace = {}  # Pas de namespace
            except Exception as e:
                print(f"Échec de la récupération du sitemap : {e}")
                return []

        sitemap_index = root.findall('ns:sitemap', namespaces=namespace)
        if sitemap_index:
            for sitemap in sitemap_index:
                loc = sitemap.find('ns:loc', namespaces=namespace)
                if loc is not None and loc.text:
                    urls.extend(fetch_sitemap(loc.text))
        else:
            for elem in root.findall('ns:url/ns:loc', namespaces=namespace):
                if elem.text:
                    urls.append(elem.text.strip())
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération du sitemap {sitemap_url} : {e}")
    except ET.ParseError as e:
        print(f"Erreur lors du parsing du sitemap {sitemap_url} : {e}")
    return urls

# Fonction pour crawler un site manuellement (crawling avec multithreading)
def crawl_site(base_url, max_pages=1000):
    print("Aucun sitemap trouvé. Démarrage du crawling manuel du site...")
    visited = set()
    urls = set()
    to_visit = [base_url]
    count = 0

    def crawl_page(url):
        nonlocal count
        if url in visited or count >= max_pages:
            return []
        visited.add(url)
        count += 1
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                return []
            soup = BeautifulSoup(response.text, 'html.parser')
            new_urls = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                href = urljoin(base_url, href)
                parsed_href = urlparse(href)
                href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
                if href not in visited and href.startswith(base_url):
                    new_urls.append(href)
                    urls.add(href)
            return new_urls
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération de {url} : {e}")
            return []
        except Exception as e:
            print(f"Erreur inattendue lors de la récupération de {url} : {e}")
            return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        while to_visit and count < max_pages:
            futures = {executor.submit(crawl_page, url) for url in to_visit}
            to_visit = []
            for future in concurrent.futures.as_completed(futures):
                to_visit.extend(future.result())
            time.sleep(0.2)

    print(f"Crawling terminé. {len(urls)} URLs trouvées.")
    return list(urls)

# Récupération de toutes les URLs du sitemap ou via crawling
def get_all_sitemap_urls(url):
    all_sitemaps = set()

    # Tenter de récupérer les sitemaps via robots.txt
    robots_sitemaps = get_robots_sitemaps(url)
    all_sitemaps.update(robots_sitemaps)

    # Si aucun sitemap n'est trouvé dans robots.txt, essayer les emplacements communs
    if not all_sitemaps:
        common_sitemaps = try_common_sitemap_locations(url)
        all_sitemaps.update(common_sitemaps)

    # Si toujours aucun sitemap, démarrer le crawling manuel
    if not all_sitemaps:
        return crawl_site(url)

    # Récupérer les URLs depuis chaque sitemap trouvé
    all_urls = set()
    for sitemap in all_sitemaps:
        print(f"Récupération des URLs depuis : {sitemap}")
        urls = fetch_sitemap(sitemap)
        all_urls.update(urls)

    return list(all_urls)

# Fonction pour filtrer les URLs par mots-clés
def filter_urls_by_keywords(urls, keywords, exclude=False):
    if exclude:
        return [url for url in urls if not any(keyword.lower() in url.lower() for keyword in keywords)]
    else:
        return [url for url in urls if any(keyword.lower() in url.lower() for keyword in keywords)]

# Fonction pour sauvegarder et afficher les URLs
def save_and_display_urls(urls, filename="filtered_urls.txt", display_limit=None):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for i, url in enumerate(urls, 1):
                f.write(url + '\n')
                if display_limit is None or i <= display_limit:
                    print(f"{i}. {url}")
        
        if display_limit is not None and len(urls) > display_limit:
            print(f"... et {len(urls) - display_limit} URLs supplémentaires")
        
        print(f"\nLes URLs ont été sauvegardées dans {filename}")
        print(f"Chemin complet du fichier : {os.path.abspath(filename)}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des URLs : {e}")

# Fonction pour appliquer des filtres aux URLs
def apply_filter(urls):
    print("\nOptions de filtrage :")
    print("1. Exclure des URLs contenant certains mots")
    print("2. Garder uniquement les URLs contenant certains mots")
    print("3. Ne pas appliquer de filtre (garder toutes les URLs)")
    
    choice = input("Choisissez une option (1/2/3) : ").strip()
    
    if choice == '3':
        return urls
    
    keywords = input("Entrez les mots-clés séparés par des virgules : ").strip().split(',')
    keywords = [k.strip() for k in keywords if k.strip()]
    
    if choice == '1':
        return filter_urls_by_keywords(urls, keywords, exclude=True)
    elif choice == '2':
        return filter_urls_by_keywords(urls, keywords, exclude=False)
    else:
        print("Option non valide. Aucun filtre appliqué.")
        return urls

# Fonction principale pour lancer le script avec possibilité de filtrer plusieurs fois
if __name__ == "__main__":
    url = input("Entrez l'URL du site à scraper : ").strip()
    
    # Étape 1 : Récupérer toutes les URLs des sitemaps ou crawler
    all_urls = get_all_sitemap_urls(url)
    
    if all_urls:
        print(f"{len(all_urls)} URLs récupérées.")
        
        # Afficher toutes les URLs récupérées
        print("\nVoici les URLs récupérées :")
        for i, url in enumerate(all_urls, 1):
            print(f"{i}. {url}")
        
        filtered_urls = all_urls
        
        # Permettre de relancer plusieurs cycles de filtrage
        while True:
            # Demander si l'utilisateur veut continuer avec le filtrage
            continue_filter = input("\nVoulez-vous filtrer les URLs récupérées ? (o/n) : ").strip().lower()
            if continue_filter == 'o':
                # Appliquer un nouveau filtre sur les URLs filtrées précédemment
                filtered_urls = apply_filter(filtered_urls)
                print(f"{len(filtered_urls)} URLs après filtrage.")
            else:
                break

        # Étape 3 : Sauvegarder et afficher les résultats finaux
        save_and_display_urls(filtered_urls, "filtered_urls.txt", display_limit=10)
    else:
        print("Aucune URL récupérée.")
