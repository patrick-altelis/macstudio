from bs4 import BeautifulSoup

def clean_html(html_content):
    """
    Nettoie le contenu HTML en extrayant le texte et en conservant les sauts de ligne.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remplacer les balises <br> et <p> par des sauts de ligne
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.replace_with(p.get_text() + "\n")
    
    # Obtenir le texte et supprimer les espaces superflus
    cleaned_text = soup.get_text()
    cleaned_text = "\n".join([line.strip() for line in cleaned_text.split("\n") if line.strip()])
    
    return cleaned_text