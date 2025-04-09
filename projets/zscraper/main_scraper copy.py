import sys
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import re
import os
import concurrent.futures
import time

# Configuration
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}
MAX_WORKERS = min(32, os.cpu_count() + 4)

def get_sitemap_urls(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        root = ET.fromstring(response.content)
        return [elem.text for elem in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    except Exception as e:
        print(f"Erreur lors de la récupération du sitemap {url}: {e}")
        return []

def get_all_sitemap_urls(main_url):
    sitemap_url = urljoin(main_url, '/sitemap.xml')
    urls = get_sitemap_urls(sitemap_url)
    if not urls:
        print("Sitemap principal non trouvé, recherche de sitemaps alternatifs...")
        robots_txt_url = urljoin(main_url, '/robots.txt')
        try:
            response = requests.get(robots_txt_url, headers=HEADERS, timeout=10)
            sitemap_urls = re.findall(r'Sitemap: (\S+)', response.text, re.IGNORECASE)
            for sitemap_url in sitemap_urls:
                urls.extend(get_sitemap_urls(sitemap_url))
        except Exception as e:
            print(f"Erreur lors de la recherche de sitemaps dans robots.txt: {e}")
    return list(set(urls))  # Supprime les doublons

def apply_filter(urls, filter_type, keywords):
    keywords = [k.strip().lower() for k in keywords if k.strip()]
    
    if filter_type == 'exclude':
        return [url for url in urls if not any(keyword in url.lower() for keyword in keywords)]
    elif filter_type == 'include':
        return [url for url in urls if any(keyword in url.lower() for keyword in keywords)]
    else:
        return urls

def save_scraped_content(scraped_urls, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in scraped_urls:
            f.write(f"URL: {item['url']}\n")
            f.write("=" * 80 + "\n")
            f.write(item['content'] + "\n")
            f.write("=" * 80 + "\n\n")

def clean_content(content):
    content = re.sub(r'\s+', ' ', content).strip()
    sentences = re.split(r'(?<=[.!?])\s+', content)
    unique_sentences = []
    for sentence in sentences:
        if sentence not in unique_sentences:
            unique_sentences.append(sentence)
    content = ' '.join(unique_sentences)
    content = re.sub(r'\b(\w+)( \1\b)+', r'\1', content)
    content = re.sub(r'Copyright © \d{4}.*', '', content)
    content = re.sub(r'Tous droits réservés\.?', '', content)
    content = re.sub(r'Politique de confidentialité|Mentions légales', '', content)
    return content.strip()

def scrape_page_content(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator='\n', strip=True)
        cleaned_text = clean_content(text)
        return url, cleaned_text
    except Exception as e:
        print(f"Erreur lors du scraping de {url}: {e}")
        return url, ""

def save_and_display_urls(urls, filename, display_limit=5):
    with open(filename, 'w', encoding='utf-8') as f:
        for i, url in enumerate(urls, 1):
            f.write(f"{url}\n")
            if i <= display_limit:
                print(f"{i}. {url}")
    
    if len(urls) > display_limit:
        print(f"... et {len(urls) - display_limit} URLs supplémentaires")
    
    print(f"\nLes URLs ont été sauvegardées dans {filename}")
    print(f"Chemin complet du fichier : {os.path.abspath(filename)}")

def main():
    main_url = input("Entrez l'URL principale du site de l'hôtel : ").strip()
    all_urls = get_all_sitemap_urls(main_url)
    print(f"\nNombre total d'URLs trouvées : {len(all_urls)}")
    save_and_display_urls(all_urls, "all_urls.txt")

    filtered_urls = all_urls
    filter_count = 0
    while True:
        print(f"\nNombre d'URLs actuelles : {len(filtered_urls)}")
        if input("Voulez-vous filtrer les URLs ? (o/n) : ").lower() != 'o':
            break
        filtered_urls = apply_filter(filtered_urls)
        filter_count += 1
        save_and_display_urls(filtered_urls, f"filtered_urls_{filter_count}.txt")

    print(f"\nNombre final d'URLs après {filter_count} filtrage(s) : {len(filtered_urls)}")

    if input("\nVoulez-vous scraper le contenu des pages filtrées ? (o/n) : ").lower() == 'o':
        output_file = "scraped_hotel_content.txt"
        print(f"Démarrage du scraping avec {MAX_WORKERS} workers...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_url = {executor.submit(scrape_page_content, url): url for url in filtered_urls}
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        url, content = future.result()
                        if content.strip():
                            f.write(f"URL: {url}\n")
                            f.write("=" * 80 + "\n")
                            f.write(content + "\n")
                            f.write("=" * 80 + "\n\n")
                            print(f"Scrapé et nettoyé: {url}")
                        else:
                            print(f"Contenu vide après nettoyage: {url}")
                    except Exception as exc:
                        print(f'{url} a généré une exception: {exc}')
        
        print(f"\nContenu scrapé et nettoyé sauvegardé dans le fichier '{output_file}'")
    
    print("\nProcessus de scraping terminé.")

def scrape_multiple_pages(urls):
    results = []
    for url in urls:
        url, content = scrape_page_content(url)
        if content:
            results.append({'url': url, 'content': content})
    return results

if __name__ == "__main__":
    main()


