import re
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import gzip
import io
import time
from bs4 import BeautifulSoup
import os
import random

def get_robots_sitemaps(url):
    robots_url = f"{url.rstrip('/')}/robots.txt"
    sitemaps = []
    try:
        response = requests.get(robots_url, timeout=10)
        response.raise_for_status()
        sitemap_matches = re.findall(r'Sitemap:\s*(\S+)', response.text, re.IGNORECASE)
        for match in sitemap_matches:
            sitemaps.append(match.strip())
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération de robots.txt : {e}")
    return sitemaps

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
            response = requests.get(sitemap_url, timeout=10)
            if response.status_code == 200:
                sitemaps.append(sitemap_url)
        except requests.RequestException:
            continue
    return sitemaps

def fetch_sitemap(sitemap_url):
    urls = []
    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        
        if sitemap_url.endswith('.gz'):
            with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
                content = gz.read()
        else:
            content = response.content
        
        root = ET.fromstring(content)
        
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
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

def crawl_site(base_url, max_pages=1000):
    print("Aucun sitemap trouvé. Démarrage du crawling manuel du site...")
    visited = set()
    urls = set()
    to_visit = [base_url]
    count = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    while to_visit and count < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)
        count += 1
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link['href']
                href = urljoin(base_url, href)
                parsed_href = urlparse(href)
                href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
                if href not in visited and href.startswith(base_url):
                    to_visit.append(href)
                urls.add(href)
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération de {url} : {e}")
            continue
        except Exception as e:
            print(f"Erreur inattendue lors de la récupération de {url} : {e}")
            continue
        if count % 100 == 0:
            print(f"{count} pages crawled...")
        time.sleep(0.2)

    print(f"Crawling terminé. {len(urls)} URLs trouvées.")
    return list(urls)

def get_all_sitemap_urls(url):
    all_sitemaps = set()

    robots_sitemaps = get_robots_sitemaps(url)
    all_sitemaps.update(robots_sitemaps)

    if not all_sitemaps:
        common_sitemaps = try_common_sitemap_locations(url)
        all_sitemaps.update(common_sitemaps)

    if not all_sitemaps:
        return crawl_site(url)

    all_urls = set()
    for sitemap in all_sitemaps:
        print(f"Récupération des URLs depuis : {sitemap}")
        urls = fetch_sitemap(sitemap)
        all_urls.update(urls)

    return list(all_urls)

def filter_urls_by_keywords(urls, keywords, exclude=False):
    if exclude:
        return [url for url in urls if not any(keyword.lower() in url.lower() for keyword in keywords)]
    else:
        return [url for url in urls if any(keyword.lower() in url.lower() for keyword in keywords)]

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

if __name__ == "__main__":
    print("Ce script est conçu pour être importé et utilisé dans d'autres scripts.")
    print("Pour l'utiliser, importez les fonctions nécessaires dans votre script principal.")
__all__ = ['get_all_sitemap_urls', 'save_and_display_urls', 'apply_filter']