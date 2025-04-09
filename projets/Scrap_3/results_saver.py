def save_results(scraped_data):
    """
    Sauvegarde les résultats du scraping dans un fichier texte.
    """
    filename = "scraped_results.fr"
    with open(filename, 'w', encoding='utf-8') as f:
        for url, title, content in scraped_data:
            f.write(f"URL : {url}\n")
            f.write(f"Titre : {title}\n")
            f.write(f"Contenu :\n{content}\n\n")
    print(f"Les résultats ont été sauvegardés dans {filename}")
