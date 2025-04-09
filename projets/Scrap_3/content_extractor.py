from scraper import scrape_page
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

def analyze_page(url):
    """
    Analyse une page web et retourne un dictionnaire des classes CSS et balises importantes avec la quantité de texte associée.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    element_text_length = defaultdict(int)

    important_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article', 'section', 'main', 'div', 'span']

    for element in soup.find_all(important_tags):
        text = element.get_text(strip=True)
        if element.name in important_tags:
            element_text_length[f"tag:{element.name}"] += len(text)
        if element.get('class'):
            class_names = ' '.join(element.get('class'))
            element_text_length[f"class:{class_names}"] += len(text)

    return element_text_length

def show_element_examples(url, detected_elements):
    """
    Montre deux exemples du contenu extrait pour chaque élément détecté.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    for element_name in detected_elements:
        if element_name.startswith("tag:"):
            tag = element_name.split(":")[1]
            elements = soup.find_all(tag)
        elif element_name.startswith("class:"):
            class_name = element_name.split(":")[1]
            elements = soup.find_all(class_=class_name)
        else:
            continue

        if elements:
            print(f"\nÉlément: {element_name}")
            print("Exemples de contenu extrait :")
            for i, element in enumerate(elements[:2], 1):
                print(f"Exemple {i} : {element.get_text(separator=' ', strip=True)[:100]}...")

def analyze_site(urls):
    """
    Analyse plusieurs pages d'un site pour identifier les éléments qui contiennent le plus de texte.
    """
    total_element_text_length = defaultdict(int)

    for url in urls:
        print(f"Analyse de {url}")
        element_text_length = analyze_page(url)

        for element_name, length in element_text_length.items():
            total_element_text_length[element_name] += length

    sorted_elements = sorted(total_element_text_length.items(), key=lambda x: x[1], reverse=True)
    
    print("\nÉléments les plus probables contenant du texte important :")
    for element_name, length in sorted_elements[:20]:
        print(f"{element_name}: {length} caractères de texte")
    
    return [element_name for element_name, _ in sorted_elements[:20]]

def filter_detected_elements(detected_elements, sample_url):
    """
    Montre des exemples de contenu pour chaque élément détecté, et demande à l'utilisateur
    quels éléments il souhaite garder.
    """
    show_element_examples(sample_url, detected_elements)

    selected_elements = input("\nEntrez les éléments que vous souhaitez conserver (séparés par des virgules) ou 'all' pour tous les conserver : ").strip()
    
    if selected_elements.lower() == 'all':
        return detected_elements
    elif not selected_elements:
        return []
    else:
        return [elem.strip() for elem in selected_elements.split(',') if elem.strip() in detected_elements]

def scrape_with_detected_classes(urls, detected_elements):
    """
    Scrape les pages du site en utilisant les éléments CSS et balises détectés.
    """
    scraped_data = []

    for url in urls:
        print(f"Scraping de {url}")
        content, title = scrape_page(url, include_elements=detected_elements)
        scraped_data.append((url, title, content))

    return scraped_data