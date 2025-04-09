# Web Scraper Pro

Web Scraper Pro est un outil polyvalent conçu pour extraire efficacement des données à partir de sites web. Il offre des fonctionnalités de recherche de sitemap, de filtrage d'URL et de scraping de contenu.

## Fonctionnalités principales

1. **Recherche de sitemap** : Trouve automatiquement le sitemap d'un site web donné.
2. **Filtrage d'URL** : Permet de filtrer les URL obtenues selon des critères spécifiques.
3. **Scraping de contenu** : Extrait le contenu textuel des pages web sélectionnées.
4. **Sauvegarde des données** : Enregistre les URL et le contenu scrapé dans des fichiers texte.

## Prérequis

- Python 3.7+
- Bibliothèques requises : requests, beautifulsoup4, lxml

## Installation

1. Clonez ce dépôt :
   ```
   git clone https://github.com/votre-username/web-scraper-pro.git
   ```

2. Naviguez dans le dossier du projet :
   ```
   cd web-scraper-pro
   ```

3. Installez les dépendances :
   ```
   pip install -r requirements.txt
   ```

## Utilisation

1. Lancez le script principal :
   ```
   python main.py
   ```

2. Suivez les instructions à l'écran pour :
   - Entrer l'URL du site à scraper
   - Appliquer des filtres aux URL trouvées
   - Lancer le scraping du contenu

## Structure du projet

- `main.py` : Point d'entrée principal du script
- `sitemap_fetcher.py` : Fonctions pour la recherche et l'extraction des sitemaps
- `url_filter.py` : Fonctions pour le filtrage des URL
- `content_scraper.py` : Fonctions pour le scraping du contenu des pages
- `interface_flask.py` : Interface web Flask pour le scraper (si applicable)

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou à soumettre une pull request.

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.
