import json
import re
from src.html_cleaner import clean_html

class TextCleaningPipeline:
    def __init__(self, client):
        self.client = client

    def process(self, text):
        cleaned_html = clean_html(text)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Vous êtes un assistant expert en analyse et traitement de texte français."},
                    {"role": "user", "content": f"""Analysez le texte suivant et effectuez les tâches demandées :

                    Texte : {cleaned_html}

                    Tâches :
                    1. Déterminez si le texte est en français. Répondez par 'true' ou 'false'.
                    2. Si le texte est en français, normalisez-le (corrigez l'orthographe, la grammaire et la ponctuation).
                    3. Fournissez un bref résumé du contenu en 2-3 phrases.

                    Répondez au format JSON avec les clés 'is_french', 'normalized_text', et 'summary'.
                    Si le texte n'est pas en français, utilisez 'null' pour 'normalized_text' et 'summary'.
                    N'incluez pas de balises de code ou de formatage Markdown dans votre réponse.
                    """}
                ]
            )
            
            result = response.choices[0].message.content.strip()
            return self.parse_llm_response(result)
        except Exception as e:
            return {"error": f"Erreur lors de l'appel à l'API : {str(e)}"}

    def parse_llm_response(self, response):
        try:
            # Nettoyer la réponse des balises Markdown ou de code
            cleaned_response = re.sub(r'```(?:json)?\n?', '', response).strip()
            cleaned_response = cleaned_response.rstrip('`')  # Supprimer les backticks restants à la fin
            
            parsed = json.loads(cleaned_response)
            # Convertir la chaîne 'true'/'false' en booléen si nécessaire
            if isinstance(parsed['is_french'], str):
                parsed['is_french'] = parsed['is_french'].lower() == 'true'
            return parsed
        except json.JSONDecodeError:
            return {"error": "Impossible de parser la réponse JSON", "raw_response": response}
        except Exception as e:
            return {"error": f"Erreur lors du traitement de la réponse : {str(e)}", "raw_response": response}