import requests
from bs4 import BeautifulSoup
import concurrent.futures
from difflib import SequenceMatcher
import os
from sitemap_utils import DATA_DIR

def scrape_page(url):
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
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(scrape_page, urls))
    return results

def find_repetitive_content(texts):
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
    if repetitive_content:
        return text.replace(repetitive_content, '')
    return text

def save_results(results, filename, repetitive_content):
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
