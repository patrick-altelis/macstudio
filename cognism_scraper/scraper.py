"""Cognism web scraper for extracting professional profiles."""
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
import pandas as pd

import config
from database import init_db, get_db, get_or_create_company, save_profile

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cognism_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CognismScraper:
    """Scraper for extracting professional profiles from Cognism."""
    
    def __init__(self):
        """Initialize the scraper."""
        self.driver = None
        self.wait = None
        self.is_logged_in = False
        self.setup_driver()
        
    def setup_driver(self):
        """Set up the Chrome WebDriver."""
        import os
        import platform
        
        chrome_options = Options()
        # Forcer le mode non-headless pour voir ce qui se passe
        # if config.BROWSER_HEADLESS:
        #     chrome_options.add_argument("--headless=new")  # nouveau format pour headless
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            # Vérifier si nous sommes sur Mac ARM
            is_mac_arm = platform.system() == 'Darwin' and platform.machine() == 'arm64'
            
            # Vérifier les chemins possibles pour Chrome sur Mac
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chrome.app/Contents/MacOS/Chrome",
                # Ajouter d'autres chemins possibles ici
            ]
            
            if is_mac_arm:
                # Trouver le premier chemin de Chrome qui existe
                chrome_binary = None
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_binary = path
                        break
                
                if chrome_binary:
                    logger.info(f"Utilisation du binaire Chrome: {chrome_binary}")
                    chrome_options.binary_location = chrome_binary
            
            # Utiliser Chrome directement sans ChromeDriverManager
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, config.BROWSER_TIMEOUT)
            logger.info("WebDriver initialized successfully")
        
        except WebDriverException as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def login(self):
        """Log in to Cognism."""
        if self.is_logged_in:
            logger.info("Already logged in")
            return True
        
        if not config.COGNISM_EMAIL or not config.COGNISM_PASSWORD:
            logger.error("Cognism credentials not found in .env file")
            raise ValueError("Cognism credentials not found. Please set COGNISM_EMAIL and COGNISM_PASSWORD in .env file")
        
        try:
            logger.info("Logging in to Cognism...")
            self.driver.get(config.COGNISM_LOGIN_URL)
            
            # Ajouter un délai pour s'assurer que la page est complètement chargée
            time.sleep(5)  # Augmenté à 5 secondes
            
            # Prendre une capture d'écran de la page de connexion
            self.save_screenshot("login_page_before.png")
            
            # Essayer de faire un dump de la source HTML
            try:
                html_source = self.driver.page_source
                with open("login_page_source.html", "w") as f:
                    f.write(html_source)
                logger.info("Page source saved to login_page_source.html")
            except Exception as e:
                logger.error(f"Failed to save page source: {e}")
            
            logger.info("Recherche du champ email...")
            # Essayer plusieurs sélecteurs pour le champ email
            email_selectors = [
                "//input[@placeholder='e.g. john@example.com']",
                "//input[@type='email']", 
                "//input[@name='email']", 
                "//input[@id='email']",
                "//input[contains(@placeholder, 'mail')]"
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    logger.info(f"Essai du sélecteur pour email: {selector}")
                    email_field = self.driver.find_element(By.XPATH, selector)
                    if email_field and email_field.is_displayed():
                        logger.info(f"Champ email trouvé avec sélecteur: {selector}")
                        break
                except NoSuchElementException:
                    logger.warning(f"Sélecteur non trouvé: {selector}")
                    continue
            
            if not email_field:
                logger.error("Champ email non trouvé!")
                self.save_screenshot("login_error_email_field.png")
                raise NoSuchElementException("Email field not found")
            
            logger.info("Recherche du champ mot de passe...")
            # Essayer plusieurs sélecteurs pour le champ mot de passe
            password_selectors = [
                "//input[@type='password']",
                "//input[@name='password']",
                "//input[@id='password']",
                "//input[contains(@placeholder, 'password')]",
                "//input[@aria-label='Password']"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    logger.info(f"Essai du sélecteur pour mot de passe: {selector}")
                    password_field = self.driver.find_element(By.XPATH, selector)
                    if password_field and password_field.is_displayed():
                        logger.info(f"Champ mot de passe trouvé avec sélecteur: {selector}")
                        break
                except NoSuchElementException:
                    logger.warning(f"Sélecteur non trouvé: {selector}")
                    continue
            
            if not password_field:
                logger.error("Champ mot de passe non trouvé!")
                self.save_screenshot("login_error_password_field.png")
                raise NoSuchElementException("Password field not found")
            
            # Enter credentials
            logger.info(f"Saisie des identifiants: {config.COGNISM_EMAIL}")
            email_field.clear()
            email_field.send_keys(config.COGNISM_EMAIL)
            password_field.clear()
            password_field.send_keys(config.COGNISM_PASSWORD)
            
            # Prendre une capture d'écran après la saisie
            self.save_screenshot("login_page_after_input.png")
            
            logger.info("Recherche du bouton de connexion...")
            # Essayer plusieurs sélecteurs pour le bouton de connexion
            login_button_selectors = [
                "//button[text()='Log in']",
                "//button[contains(text(), 'Log in')]",
                "//button[@type='submit']",
                "//button[contains(@class, 'login')]",
                "//input[@type='submit']",
                "//button"
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    logger.info(f"Essai du sélecteur pour bouton de connexion: {selector}")
                    login_button = self.driver.find_element(By.XPATH, selector)
                    if login_button and login_button.is_displayed():
                        logger.info(f"Bouton de connexion trouvé avec sélecteur: {selector}")
                        break
                except NoSuchElementException:
                    logger.warning(f"Sélecteur non trouvé: {selector}")
                    continue
            
            if not login_button:
                logger.error("Bouton de connexion non trouvé!")
                self.save_screenshot("login_error_button.png")
                raise NoSuchElementException("Login button not found")
            
            logger.info("Clic sur le bouton de connexion...")
            login_button.click()
            
            # Attendre un peu pour voir ce qui se passe après le clic
            time.sleep(10)
            
            # Prendre une capture d'écran après le clic sur le bouton
            self.save_screenshot("after_login_click.png")
            
            # Vérifier si on est toujours sur la page de connexion (échec)
            if "login" in self.driver.current_url.lower():
                logger.error("Toujours sur la page de connexion après clic!")
                
                # Essayons de voir s'il y a un message d'erreur
                try:
                    error_messages = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'alert')]")
                    if error_messages:
                        for msg in error_messages:
                            if msg.is_displayed():
                                logger.error(f"Message d'erreur trouvé: {msg.text}")
                except:
                    pass
                
                # Essayons de vérifier si captcha présent
                try:
                    captcha = self.driver.find_elements(By.XPATH, "//iframe[contains(@src, 'recaptcha') or contains(@src, 'captcha')]")
                    if captcha:
                        logger.error("CAPTCHA détecté! Impossible de se connecter automatiquement.")
                except:
                    pass
            
            # Essayons de trouver des éléments de la page d'accueil
            dashboard_elements = [
                "//nav",
                "//*[contains(@class, 'dashboard')]",
                "//*[contains(@class, 'sidebar')]",
                "//*[contains(@class, 'header')]"
            ]
            
            dashboard_loaded = False
            for selector in dashboard_elements:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element and element.is_displayed():
                        logger.info(f"Élément de la page d'accueil trouvé: {selector}")
                        dashboard_loaded = True
                        break
                except:
                    continue
            
            if not dashboard_loaded:
                logger.error("Impossible de confirmer l'accès à la page d'accueil après connexion")
                self.save_screenshot("login_failure_no_dashboard.png")
                raise Exception("Login failed - dashboard not loaded")
                
            # Ajoutons un délai supplémentaire pour s'assurer que tout est chargé
            time.sleep(3)
            
            self.is_logged_in = True
            logger.info("Successfully logged in to Cognism")
            return True
        
        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"Failed to log in to Cognism: {e}")
            self.save_screenshot("login_error.png")
            return False
    
    def search_company(self, company_name):
        """Search for a company and navigate to the search results."""
        try:
            logger.info(f"Searching for company: {company_name}")
            
            # Navigate to search page
            self.driver.get(config.COGNISM_SEARCH_URL)
            
            # Ajouter un délai pour s'assurer que la page est complètement chargée
            time.sleep(5)
            
            # Prendre une capture d'écran pour voir l'interface de recherche
            self.save_screenshot("search_page.png")
            
            # Dans l'interface vue sur la capture d'écran, le champ de recherche est la barre centrée en haut
            # avec un placeholder qui pourrait mentionner "Search" ou être une barre de recherche générique
            
            # Approche simple et directe - trouver le champ de texte principal
            try:
                # Regarder d'abord les champs de recherche évidents
                search_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='search'], input[type='text']")
                
                # Vérifier que c'est bien visible
                if not search_input.is_displayed():
                    logger.warning("Search input found but not visible, trying alternative methods")
                    # Vérifier d'autres options
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    for inp in inputs:
                        if inp.is_displayed():
                            search_input = inp
                            break
            except:
                # Si la méthode directe échoue, essayer des options plus souples
                try:
                    # Trouver tous les champs de saisie visibles
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    for inp in inputs:
                        if inp.is_displayed():
                            search_input = inp
                            break
                except:
                    logger.error("Failed to find any visible input field")
                    self.save_screenshot(f"search_error_no_input_{company_name.replace(' ', '_')}.png")
                    return False
            
            # Effacer le contenu du champ
            search_input.clear()
            
            # Taper le nom de l'entreprise
            search_input.send_keys(company_name)
            
            # Capture d'écran après avoir saisi le texte
            self.save_screenshot(f"search_input_{company_name.replace(' ', '_')}.png")
            
            # Appuyer sur ENTRÉE pour lancer la recherche
            from selenium.webdriver.common.keys import Keys
            search_input.send_keys(Keys.RETURN)
            
            # Attendre que les résultats se chargent
            time.sleep(5)
            
            # Capturer l'écran des résultats initiaux
            self.save_screenshot(f"search_results_initial_{company_name.replace(' ', '_')}.png")
            
            # Vérifier si des résultats sont présents
            try:
                results_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Contacts Found')]")
                if results_text:
                    logger.info(f"Found initial results for {company_name}")
            except:
                try:
                    # Chercher des lignes de tableau
                    rows = self.driver.find_elements(By.TAG_NAME, "tr")
                    if len(rows) <= 1:  # Pas de résultats significatifs
                        logger.warning(f"No significant results found for {company_name}")
                        return False
                except:
                    logger.warning(f"Could not verify results for {company_name}")
            
            # Appliquer des filtres pour cibler les profils souhaités
            logger.info("Applying filters to target specific profiles")
            
            # Rechercher le menu des filtres
            try:
                # Essayons d'abord de cliquer sur le bouton Filtres s'il existe
                filter_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Filter') or contains(text(), 'Filtre')]")
                filters_found = False
                
                for button in filter_buttons:
                    if button.is_displayed():
                        logger.info("Clicking on Filter button")
                        button.click()
                        time.sleep(2)
                        filters_found = True
                        break
                
                # Si aucun bouton Filtres trouvé, cherchons d'autres possibilités
                if not filters_found:
                    filter_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Job Title') or contains(text(), 'Seniority') or contains(text(), 'Department')]")
                    if filter_elements:
                        for element in filter_elements:
                            if element.is_displayed():
                                logger.info(f"Found filter section: {element.text}")
                                element.click()
                                time.sleep(1)
                                filters_found = True
                                break
                
                # Capture d'écran des filtres
                self.save_screenshot(f"filters_{company_name.replace(' ', '_')}.png")
                
                # Si on a trouvé la section des filtres, essayons d'appliquer nos filtres
                if filters_found:
                    # Filtre par titre de poste
                    self._apply_filter_by_text("Job Title", config.TARGET_JOB_TITLES)
                    
                    # Filtre par niveau de séniorité
                    self._apply_filter_by_text("Seniority", config.TARGET_SENIORITY)
                    
                    # Filtre par département
                    self._apply_filter_by_text("Department", config.TARGET_DEPARTMENTS)
                    
                    # Chercher et cliquer sur le bouton d'application des filtres
                    apply_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Apply') or contains(text(), 'Appliquer')]")
                    for button in apply_buttons:
                        if button.is_displayed():
                            logger.info("Applying filters")
                            button.click()
                            time.sleep(3)
                            break
                else:
                    logger.warning("Could not find filter section, continuing without filters")
            
            except Exception as e:
                logger.warning(f"Error applying filters: {e}, continuing without filters")
            
            # Attendre que les résultats filtrés se chargent
            time.sleep(5)
            
            # Capturer l'écran des résultats filtrés
            self.save_screenshot(f"search_results_filtered_{company_name.replace(' ', '_')}.png")
            
            # Vérifier les résultats filtrés
            try:
                # Chercher le nombre total de contacts
                total_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Contacts Found')]")
                if total_elements:
                    total_text = total_elements[0].text
                    logger.info(f"Filtered results: {total_text}")
                
                # Vérifier s'il y a des lignes de résultat
                rows = self.driver.find_elements(By.TAG_NAME, "tr")
                if len(rows) > 1:
                    logger.info(f"Found {len(rows)-1} filtered result rows for {company_name}")
                    return True
                else:
                    logger.warning(f"No filtered results for {company_name}")
                    return False
            except Exception as e:
                logger.warning(f"Error checking filtered results: {e}")
            
            # Si nous sommes ici, nous avons probablement des résultats mais n'avons pas pu les vérifier spécifiquement
            logger.info(f"Proceeding with extraction for {company_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error searching for company {company_name}: {e}")
            self.save_screenshot(f"search_error_{company_name.replace(' ', '_')}.png")
            return False
    
    def _apply_filter_by_text(self, filter_name, values):
        """Helper method to apply a filter by text values."""
        try:
            # Trouver la section du filtre
            filter_sections = self.driver.find_elements(By.XPATH, 
                f"//*[contains(text(), '{filter_name}') or contains(@placeholder, '{filter_name}') or contains(@aria-label, '{filter_name}')]"
            )
            
            filter_section_found = False
            for section in filter_sections:
                if not section.is_displayed():
                    continue
                
                logger.info(f"Found filter section: {filter_name}")
                filter_section_found = True
                
                try:
                    # Vérifier si c'est un menu déroulant ou une section à cliquer
                    tag_name = section.tag_name.lower()
                    
                    # Si c'est une section à cliquer
                    if tag_name in ['span', 'div', 'button', 'h3', 'h4', 'p']:
                        # Cliquer pour ouvrir les options
                        section.click()
                        time.sleep(2)
                        
                        # Prenons une capture d'écran pour voir les options disponibles
                        self.save_screenshot(f"filter_options_{filter_name}.png")
                        
                        # Si c'est un champ de recherche déroulant, essayons d'abord le champ de recherche
                        search_fields = self.driver.find_elements(By.XPATH, "//input[@type='text' and (@placeholder or @aria-label)]")
                        search_field_found = False
                        
                        for field in search_fields:
                            if field.is_displayed():
                                logger.info(f"Found filter search field for {filter_name}")
                                search_field_found = True
                                
                                # Pour chaque valeur, chercher et sélectionner
                                checked_values = 0
                                for value in values:
                                    try:
                                        # Effacer le champ
                                        field.clear()
                                        
                                        # Taper la valeur
                                        field.send_keys(value)
                                        time.sleep(1)
                                        
                                        # Chercher des résultats correspondants
                                        matching_elements = self.driver.find_elements(By.XPATH, 
                                            f"//*[contains(text(), '{value}') and not(ancestor::input)]"
                                        )
                                        
                                        clicked = False
                                        for element in matching_elements:
                                            if element.is_displayed():
                                                try:
                                                    logger.info(f"Clicking filter value: {value}")
                                                    element.click()
                                                    time.sleep(0.5)
                                                    checked_values += 1
                                                    clicked = True
                                                    
                                                    # Si nous avons cliqué sur 5 valeurs, c'est suffisant
                                                    if checked_values >= 5:
                                                        logger.info(f"Selected {checked_values} values for {filter_name}, proceeding")
                                                        break
                                                    
                                                except Exception as click_err:
                                                    logger.debug(f"Could not click element for {value}: {click_err}")
                                        
                                        if not clicked:
                                            logger.debug(f"No matching elements found for {value}")
                                        
                                        # Limiter le nombre de valeurs pour ne pas surcharger
                                        if checked_values >= 5:
                                            break
                                            
                                    except Exception as e:
                                        logger.debug(f"Error searching for {value}: {e}")
                                
                                break
                        
                        # Si pas de champ de recherche, chercher directement les options
                        if not search_field_found:
                            # Pour chaque valeur, essayer de trouver des cases à cocher ou des éléments cliquables
                            for value in values:
                                try:
                                    # Chercher des éléments contenant la valeur
                                    text_elements = self.driver.find_elements(By.XPATH, 
                                        f"//*[contains(text(), '{value}')]"
                                    )
                                    
                                    clicked = False
                                    for element in text_elements:
                                        if element.is_displayed():
                                            try:
                                                # Essayer de cliquer sur l'élément ou sa case à cocher
                                                try:
                                                    # Trouver la case à cocher associée
                                                    checkbox = element.find_element(By.XPATH, 
                                                        "./preceding::input[@type='checkbox'][1] | " +
                                                        "./following::input[@type='checkbox'][1] | " +
                                                        "./input[@type='checkbox']"
                                                    )
                                                    
                                                    if checkbox.is_displayed():
                                                        logger.info(f"Clicking checkbox for: {value}")
                                                        checkbox.click()
                                                        clicked = True
                                                        time.sleep(0.5)
                                                        break
                                                except:
                                                    # Si pas de case à cocher, cliquer sur l'élément lui-même
                                                    logger.info(f"Clicking element for: {value}")
                                                    element.click()
                                                    clicked = True
                                                    time.sleep(0.5)
                                                    break
                                            except Exception as click_err:
                                                logger.debug(f"Could not click element for {value}: {click_err}")
                                    
                                    if not clicked:
                                        logger.debug(f"No clickable elements found for {value}")
                                
                                except Exception as e:
                                    logger.debug(f"Error processing value {value}: {e}")
                        
                        # Chercher et cliquer sur le bouton d'application ou de fermeture
                        buttons = self.driver.find_elements(By.XPATH, 
                            "//button[contains(text(), 'Apply') or contains(text(), 'Appliquer') or " +
                            "contains(text(), 'OK') or contains(text(), 'Done') or contains(text(), 'Close')]"
                        )
                        
                        for button in buttons:
                            if button.is_displayed():
                                logger.info(f"Clicking button to apply {filter_name} filters")
                                button.click()
                                time.sleep(1)
                                break
                    
                    # Si c'est un menu déroulant ou un champ de saisie
                    elif tag_name in ['select', 'input']:
                        logger.info(f"Found input/select element for {filter_name}")
                        
                        # Si c'est un champ de saisie, essayer de saisir les valeurs
                        if tag_name == 'input':
                            # Effacer le champ
                            section.clear()
                            
                            # Saisir les premières valeurs séparées par virgule
                            values_str = ", ".join(values[:3])  # Limiter à 3 valeurs
                            section.send_keys(values_str)
                            
                            # Appuyer sur Entrée
                            from selenium.webdriver.common.keys import Keys
                            section.send_keys(Keys.RETURN)
                            time.sleep(1)
                        
                        # Si c'est un menu déroulant, essayer de sélectionner des options
                        elif tag_name == 'select':
                            from selenium.webdriver.support.ui import Select
                            select = Select(section)
                            
                            # Essayer de sélectionner chaque valeur
                            for value in values:
                                try:
                                    select.select_by_visible_text(value)
                                    logger.info(f"Selected {value} from dropdown")
                                    time.sleep(0.5)
                                except:
                                    try:
                                        # Essayer par texte partiel
                                        options = select.options
                                        for option in options:
                                            if value.lower() in option.text.lower():
                                                option.click()
                                                logger.info(f"Selected option containing {value}")
                                                time.sleep(0.5)
                                                break
                                    except Exception as e:
                                        logger.debug(f"Could not select {value} from dropdown: {e}")
                    
                    # Prendre une capture d'écran après l'application des filtres
                    self.save_screenshot(f"after_filter_{filter_name}.png")
                
                except Exception as e:
                    logger.warning(f"Error interacting with filter section {filter_name}: {e}")
                
                break
            
            # Si nous n'avons pas trouvé la section principale, essayer avec des noms alternatifs
            if not filter_section_found:
                alternative_names = {
                    "Job Title": ["Title", "Position", "Role", "Fonction", "Poste"],
                    "Seniority": ["Level", "Niveau", "Rank", "Grade"],
                    "Department": ["Service", "Division", "Team", "Équipe"]
                }
                
                if filter_name in alternative_names:
                    for alt_name in alternative_names[filter_name]:
                        logger.info(f"Trying alternative name for {filter_name}: {alt_name}")
                        self._apply_filter_by_text(alt_name, values)
        
        except Exception as e:
            logger.warning(f"Error applying filter {filter_name}: {e}")
    
    def extract_profiles(self, company_name, max_profiles=None):
        """Extract profiles from the search results."""
        if max_profiles is None:
            max_profiles = config.MAX_PROFILES_PER_COMPANY
        
        profiles = []
        try:
            logger.info(f"Extracting up to {max_profiles} profiles for {company_name}")
            
            # Prendre une capture d'écran des résultats
            self.save_screenshot(f"extract_start_{company_name.replace(' ', '_')}.png")
            
            # L'image montre une liste de profils sous forme de tableau
            # Approche directe et simple pour trouver les profils
            
            # 1. Essayons d'abord de trouver les lignes du tableau
            table_rows = []
            try:
                # Chercher les lignes de tableau standards
                rows = self.driver.find_elements(By.TAG_NAME, "tr")
                if len(rows) > 1:  # Ignorer la ligne d'en-tête si présente
                    table_rows = rows[1:] 
                    logger.info(f"Found {len(table_rows)} table rows")
            except Exception as e:
                logger.warning(f"Failed to find table rows: {e}")
            
            # Si nous n'avons pas trouvé de lignes de tableau, essayons de chercher des noms de personnes
            if not table_rows:
                try:
                    # Chercher tous les liens qui contiennent probablement des noms (avec un espace)
                    name_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), ' ')]")
                    
                    if name_links:
                        logger.info(f"Found {len(name_links)} name links")
                        
                        # Pour chaque lien avec un nom, créer un profil
                        for i, link in enumerate(name_links[:max_profiles]):
                            try:
                                name_text = link.text.strip()
                                
                                # Diviser le nom en prénom et nom de famille
                                name_parts = name_text.split(maxsplit=1)
                                
                                profile_data = {
                                    'company': company_name,
                                    'first_name': name_parts[0] if len(name_parts) > 0 else "",
                                    'last_name': name_parts[1] if len(name_parts) > 1 else ""
                                }
                                
                                # Essayer de trouver le titre du poste (généralement à côté du nom)
                                try:
                                    # Essayer de trouver l'élément parent de la ligne
                                    parent_row = link.find_element(By.XPATH, "./ancestor::tr")
                                    
                                    # Chercher le titre dans les cellules suivantes
                                    job_cells = parent_row.find_elements(By.TAG_NAME, "td")
                                    if len(job_cells) > 1:
                                        profile_data['job_title'] = job_cells[1].text.strip()
                                except:
                                    # Si on ne trouve pas le parent, on continue sans le titre
                                    pass
                                
                                profiles.append(profile_data)
                                logger.info(f"Extracted profile from name link: {name_text}")
                            except Exception as e:
                                logger.error(f"Error extracting profile from name link: {e}")
                        
                        # Retourner les profils extraits
                        return profiles
                except Exception as e:
                    logger.warning(f"Failed to find name links: {e}")
            
            # Si nous sommes ici, nous avons trouvé des lignes de tableau
            # Limiter le nombre de profils
            profile_rows = table_rows[:max_profiles]
            
            # Pour chaque ligne, extraire les informations
            for i, row in enumerate(profile_rows):
                try:
                    # Créer un dictionnaire pour stocker les données du profil
                    profile_data = {
                        'company': company_name
                    }
                    
                    # Capturer une image de la ligne
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", row)
                    time.sleep(1)
                    self.save_screenshot(f"profile_row_{company_name}_{i}.png")
                    
                    # Extraire le nom (prénom et nom)
                    try:
                        # Chercher un lien dans la ligne qui contient probablement un nom
                        name_elements = row.find_elements(By.XPATH, ".//a[contains(text(), ' ')]")
                        if name_elements:
                            name_text = name_elements[0].text.strip()
                            name_parts = name_text.split(maxsplit=1)
                            
                            if len(name_parts) > 0:
                                profile_data['first_name'] = name_parts[0]
                                if len(name_parts) > 1:
                                    profile_data['last_name'] = name_parts[1]
                            
                            logger.info(f"Extracted name: {name_text}")
                    except Exception as e:
                        logger.warning(f"Failed to extract name from row {i}: {e}")
                    
                    # Extraire le titre du poste
                    try:
                        # Le titre est généralement dans la deuxième cellule
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) > 1:
                            job_title = cells[1].text.strip()
                            profile_data['job_title'] = job_title
                            logger.info(f"Extracted job title: {job_title}")
                    except Exception as e:
                        logger.warning(f"Failed to extract job title from row {i}: {e}")
                    
                    # Extraire l'URL LinkedIn si disponible
                    try:
                        linkedin_elements = row.find_elements(By.XPATH, ".//a[contains(@href, 'linkedin.com')]")
                        if linkedin_elements:
                            linkedin_url = linkedin_elements[0].get_attribute("href")
                            profile_data['linkedin_url'] = linkedin_url
                            logger.info(f"Extracted LinkedIn URL: {linkedin_url}")
                    except Exception as e:
                        logger.debug(f"No LinkedIn URL found in row {i}: {e}")
                    
                    # Si nous avons au moins un nom ou un titre, ajouter le profil
                    if profile_data.get('first_name') or profile_data.get('last_name') or profile_data.get('job_title'):
                        profiles.append(profile_data)
                        logger.info(f"Added profile {i+1}: {profile_data.get('first_name', '')} {profile_data.get('last_name', '')}")
                    else:
                        logger.warning(f"Skipping row {i} due to insufficient data")
                
                except Exception as e:
                    logger.error(f"Error extracting profile from row {i}: {e}")
            
            # Si nous n'avons extrait aucun profil, journaliser un avertissement
            if not profiles:
                logger.warning(f"No profiles extracted for {company_name}")
                self.save_screenshot(f"no_profiles_{company_name.replace(' ', '_')}.png")
            else:
                logger.info(f"Successfully extracted {len(profiles)} profiles for {company_name}")
            
            return profiles
        
        except Exception as e:
            logger.error(f"Error extracting profiles for {company_name}: {e}")
            self.save_screenshot(f"extraction_error_{company_name.replace(' ', '_')}.png")
            return profiles
    
    def save_screenshot(self, filename):
        """Save a screenshot for debugging."""
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")


def read_company_list(file_path=None):
    """Read the list of companies from a CSV file."""
    if file_path is None:
        file_path = config.INPUT_FILE
    
    try:
        df = pd.read_csv(file_path)
        # Assume the column name is 'company' or the first column
        company_col = 'company' if 'company' in df.columns else df.columns[0]
        return df[company_col].tolist()
    except Exception as e:
        logger.error(f"Error reading company list from {file_path}: {e}")
        return []


def export_to_csv(db_session, file_path=None):
    """Export all profiles to a CSV file."""
    if file_path is None:
        file_path = config.OUTPUT_FILE
    
    try:
        from database import Company, Profile
        
        # Query all profiles with company information
        results = db_session.query(
            Company.name.label('company_name'),
            Profile.first_name,
            Profile.last_name,
            Profile.job_title,
            Profile.email,
            Profile.phone,
            Profile.direct_phone,
            Profile.linkedin_url,
            Profile.location,
            Profile.department,
            Profile.seniority
        ).join(Profile).all()
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(results)
        
        # Export to CSV
        df.to_csv(file_path, index=False)
        logger.info(f"Exported {len(df)} profiles to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error exporting profiles to CSV: {e}")
        return False


def main():
    """Main function to run the scraper."""
    logger.info("Starting Cognism scraper")
    
    # Initialize database
    init_db()
    db = get_db()
    
    # Read company list
    companies = read_company_list()
    if not companies:
        logger.error("No companies found in input file")
        return
    
    logger.info(f"Found {len(companies)} companies to scrape")
    
    # Initialize scraper
    scraper = CognismScraper()
    
    try:
        # Log in to Cognism
        if not scraper.login():
            logger.error("Failed to log in to Cognism")
            return
        
        # Process each company
        for company_name in tqdm(companies, desc="Processing companies"):
            # Get or create company in database
            company = get_or_create_company(db, company_name)
            
            # Search for company
            if not scraper.search_company(company_name):
                logger.warning(f"Skipping company: {company_name}")
                continue
            
            # Extract profiles
            profiles = scraper.extract_profiles(company_name)
            
            # Save profiles to database
            for profile_data in profiles:
                save_profile(db, company.id, profile_data)
            
            # Wait between companies
            time.sleep(config.WAIT_BETWEEN_SEARCHES + random.uniform(1.0, 3.0))
        
        # Export results to CSV
        export_to_csv(db)
        
        logger.info("Cognism scraper completed successfully")
    
    except Exception as e:
        logger.error(f"Error running Cognism scraper: {e}")
    
    finally:
        # Close the scraper
        scraper.close()


if __name__ == "__main__":
    main()