# Cognism Profile Scraper

Un outil d'automatisation pour extraire des profils professionnels depuis Cognism.

## Fonctionnalités

- Accepte une liste d'entreprises en entrée (CSV, TXT ou saisie manuelle)
- Se connecte à Cognism et effectue des recherches automatisées
- Extrait jusqu'à 5 profils par entreprise (configurable)
- Collecte les informations de contact et professionnelles
- Stocke les données dans une base de données SQLite
- Interface web conviviale pour gérer les extractions
- Export des résultats en CSV

## Installation

1. Cloner ce dépôt :
```bash
git clone <URL_DU_REPO>
cd cognism_scraper
```

2. Créer un environnement virtuel Python et l'activer :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurer les identifiants Cognism :
```bash
cp .env.example .env
```
Puis modifiez le fichier `.env` avec vos identifiants Cognism.

## Utilisation

### Interface Web

1. Démarrer l'application web :
```bash
python run.py
```

2. Ouvrir votre navigateur à l'adresse `http://127.0.0.1:9000`

3. Télécharger un fichier CSV contenant une liste d'entreprises ou saisir manuellement les noms d'entreprises

4. Lancer l'extraction

### Ligne de commande

Vous pouvez également exécuter le scraper directement en ligne de commande :

```bash
python scraper.py
```

Par défaut, le script lira la liste d'entreprises depuis le fichier `companies.csv` défini dans votre `.env`.

## Configuration

Toutes les configurations sont disponibles dans le fichier `.env` :

- `COGNISM_EMAIL` et `COGNISM_PASSWORD` : Vos identifiants Cognism
- `BROWSER_HEADLESS` : Exécuter le navigateur en mode headless (sans interface graphique)
- `MAX_PROFILES_PER_COMPANY` : Nombre maximum de profils à extraire par entreprise
- `WAIT_BETWEEN_SEARCHES` et `WAIT_BETWEEN_PROFILES` : Temps d'attente entre les recherches
- `INPUT_FILE` : Chemin vers le fichier d'entrée contenant la liste des entreprises
- `OUTPUT_FILE` : Chemin vers le fichier de sortie pour l'export CSV

## Format des fichiers d'entrée

### CSV
Un fichier CSV avec une colonne `company` ou la première colonne contenant les noms d'entreprises :

```
company
Entreprise1
Entreprise2
Entreprise3
```

### TXT
Un fichier texte avec un nom d'entreprise par ligne :

```
Entreprise1
Entreprise2
Entreprise3
```

## Structure du projet

- `app.py` : Application Flask pour l'interface web
- `scraper.py` : Script principal d'extraction de données
- `database.py` : Modèles et fonctions de base de données
- `config.py` : Configuration du projet
- `templates/` : Templates HTML pour l'interface web
- `requirements.txt` : Dépendances Python

## Notes importantes

- Cet outil est conçu pour un usage professionnel et éthique
- Respectez les conditions d'utilisation de Cognism
- L'utilisation de proxies et la rotation d'adresses IP peuvent être nécessaires pour des volumes importants
- Prévoyez des délais suffisants entre les requêtes pour ne pas surcharger le service

## Dépannage

Si vous rencontrez des problèmes :

1. Vérifiez vos identifiants Cognism
2. Assurez-vous que Chrome ou Chromium est installé sur votre système
3. Consultez les fichiers de logs (`cognism_scraper.log` et `cognism_app.log`)
4. Désactivez le mode headless (`BROWSER_HEADLESS=False`) pour voir ce qui se passe

Si vous rencontrez des problèmes de connexion à l'interface web :

1. Assurez-vous d'utiliser `http://127.0.0.1:9000` et non localhost
2. Vérifiez que le port 9000 n'est pas utilisé par une autre application
3. Essayez d'utiliser le script `launch_local.py` pour le diagnostic
4. Si nécessaire, modifiez le port dans `run.py` vers un autre port (comme 8080, 8888, etc.)