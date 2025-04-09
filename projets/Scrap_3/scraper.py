import requests
from bs4 import BeautifulSoup
import time
import random

def scrape_page(url, include_elements=None, min_length=50):
    """
    Scrape une seule page web et extrait le contenu en fonction des balises et classes fournies.
    Par défaut, inclut toujours les balises <p>, <h1>, <h2>, <h3>, <h4>, <h5>, <h6>, <article>, <section>, <blockquote>, <li> 
    et les éléments avec les classes spécifiques. Exclut le footer et autres balises spécifiques comme <header>.
    
    Paramètres :
    - url : URL de la page à scraper.
    - include_elements : liste de sélecteurs CSS ou de balises des éléments à inclure.
    - min_length : longueur minimale du texte pour être conservé (par défaut à 50).
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Supprimer le footer et autres balises indésirables
        for tag in ['footer', 'header', 'nav', 'aside', 'svg', 'button']:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Utiliser un set pour stocker les contenus uniques
        unique_content = set()
        content = ''
        
        # Toujours inclure les éléments <p>, <h1> à <h6>, <article>, <section>, <blockquote>, <li>
        default_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article', 'section', 'blockquote', 'li']
        for tag in default_tags:
            for element in soup.find_all(tag):
                text = element.get_text(separator=' ', strip=True)
                if len(text) >= min_length and text not in unique_content:
                    unique_content.add(text)
                    content += text + '\n'
        
        # Inclure les éléments avec les classes spécifiques (comme .text, .content)
        default_classes = ['text', 'content', 'content-body', 'description', 'main-content', 'article-body', 'post-content', 'article-text']
        for class_name in default_classes:
            for element in soup.select(f"div.{class_name}, span.{class_name}"):
                text = element.get_text(separator=' ', strip=True)
                if len(text) >= min_length and text not in unique_content:
                    unique_content.add(text)
                    content += text + '\n'
        
        # Inclure les éléments spécifiés
        if include_elements:
            for element_name in include_elements:
                if element_name.startswith("tag:"):
                    tag = element_name.split(":")[1]
                    elements = soup.find_all(tag)
                elif element_name.startswith("class:"):
                    class_name = element_name.split(":")[1]
                    elements = soup.select(f".{class_name}")
                else:
                    elements = soup.select(element_name)

                for element in elements:
                    text = element.get_text(separator=' ', strip=True)
                    if len(text) >= min_length and text not in unique_content:
                        unique_content.add(text)
                        content += text + '\n'
        
        # Extraire le titre de la page
        title = soup.title.string.strip() if soup.title else "Pas de titre"
        return content, title
    
    except Exception as e:
        print(f"Erreur lors du scraping de {url}: {e}")
        return "", ""
    finally:
        time.sleep(random.uniform(1, 2))