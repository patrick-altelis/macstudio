import sys
import time
from sitemap_utils import get_sitemap, clean_filename, select_urls_from_sitemap, DATA_DIR
from scraping_utils import scrape_multiple_pages, find_repetitive_content, save_results

def filter_urls(urls, include_keywords=None, exclude_keywords=None):
    print(f"Filtrage des URLs. Nombre initial : {len(urls)}")
    print(f"Mots-clés à inclure : {include_keywords}")
    print(f"Mots-clés à exclure : {exclude_keywords}")
    
    if include_keywords:
        urls = [url for url in urls if any(keyword.lower() in url.lower() for keyword in include_keywords)]
        print(f"Après inclusion : {len(urls)} URLs")
    if exclude_keywords:
        urls = [url for url in urls if not any(keyword.lower() in url.lower() for keyword in exclude_keywords)]
        print(f"Après exclusion : {len(urls)} URLs")
    
    print("URLs après filtrage:")
    for url in urls:
        print(url)
    
    return urls

def filter_urls_interactively(urls):
    while True:
        print(f"\nNombre d'URLs actuellement : {len(urls)}")
        filter_choice = input("Voulez-vous filtrer les URLs ? (o/n) : ").strip().lower()
        if filter_choice != 'o':
            break

        include_keywords = input("Entrez les mots-clés à inclure (séparés par des virgules) ou appuyez sur Entrée pour passer : ").strip()
        exclude_keywords = input("Entrez les mots-clés à exclure (séparés par des virgules) ou appuyez sur Entrée pour passer : ").strip()

        include_list = [k.strip() for k in include_keywords.split(',')] if include_keywords else None
        exclude_list = [k.strip() for k in exclude_keywords.split(',')] if exclude_keywords else None

        urls = filter_urls(urls, include_list, exclude_list)
        
        print(f"\nNombre d'URLs après filtrage : {len(urls)}")
        input("Appuyez sur Entrée pour continuer...")

    return urls

def main():
    try:
        print("Début du script de web scraping")
        
        main_url = input("Veuillez entrer l'URL principale du site pour récupérer le sitemap : ").strip()
        urls = get_sitemap(main_url)
        
        if not urls:
            print("Aucun sitemap trouvé. Le script va se terminer.")
            sys.exit(1)
        
        filename = clean_filename(main_url)
        
        urls = filter_urls_interactively(urls)
        urls = select_urls_from_sitemap(urls)

        # Reste du code...

    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
    finally:
        print("Fin du script")
        print(f"Vérifiez le fichier 'data/{filename}' pour les résultats complets.")
        input("Appuyez sur Enter pour terminer...")

if __name__ == "__main__":
    main()