import json
import asyncio
import aiohttp
from dotenv import load_dotenv
import os
import re
from aiohttp import ClientSession, TCPConnector
from asyncio import Queue, Semaphore

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_RETRIES = 5
CONCURRENT_REQUESTS = 10  # Réduit pour éviter de surcharger l'API
RETRY_DELAY = 10  # Délai en secondes entre les tentatives

async def process_page_with_llm(session, url, page_content, semaphore):
    prompt = f"""
    Extrait les informations suivantes du texte donné et renvoie-les au format JSON :
    - url: l'URL fournie
    - name: nom de l'établissement
    - brand: marque (toujours "Belambra")
    - location: adresse, ville, région, pays (toujours "France"), code postal
    - contact: téléphone, email, site web
    - description: courte et longue description
    - category: nombre d'étoiles, type d'établissement
    - accommodations: types de chambres/logements disponibles
    - amenities: équipements et services disponibles
    - activities: activités proposées sur place ou à proximité
    - dining: options de restauration
    - childrenServices: services pour les enfants
    
    URL : {url}
    
    Texte :
    {page_content[:4000]}
    """
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Tu es un assistant qui extrait des informations structurées à partir de texte."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            async with semaphore:
                async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data) as response:
                    response_json = await response.json()
                    if 'choices' in response_json and response_json['choices']:
                        content = response_json['choices'][0]['message']['content']
                        return extract_json_from_content(content)
                    else:
                        raise ValueError("Unexpected API response format")
        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
            print(f"Error processing URL {url} (attempt {attempt+1}/{MAX_RETRIES}): {e}")
            if attempt == MAX_RETRIES - 1:
                return {"error": str(e), "url": url, "raw_response": str(response_json)}
            await asyncio.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"Unexpected error processing URL {url}: {e}")
            return {"error": str(e), "url": url}

def extract_json_from_content(content):
    try:
        # Recherche du JSON entre les backticks
        match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        else:
            # Si pas de backticks, essayez de parser tout le contenu comme JSON
            return json.loads(content)
    except json.JSONDecodeError:
        # Si le parsing JSON échoue, retournez le contenu brut
        return {"error": "Failed to parse JSON", "raw_content": content}
    
async def worker(queue, results, session, semaphore):
    while True:
        url, page_content = await queue.get()
        result = await process_page_with_llm(session, url, page_content, semaphore)
        results.append(result)
        queue.task_done()
        print(f"Processed {len(results)} pages")

async def process_all_pages(page_pairs):
    queue = Queue()
    results = []
    semaphore = Semaphore(CONCURRENT_REQUESTS)

    for url, page_content in page_pairs:
        await queue.put((url, page_content))

    async with ClientSession(connector=TCPConnector(limit=CONCURRENT_REQUESTS)) as session:
        workers = [asyncio.create_task(worker(queue, results, session, semaphore)) 
                   for _ in range(CONCURRENT_REQUESTS)]
        
        await queue.join()

        for w in workers:
            w.cancel()

    return results

def split_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    pages = re.split(r'(URL: .+)\n={80,}', content)[1:]
    return [(pages[i], pages[i+1]) for i in range(0, len(pages), 2)]

async def main():
    file_path = input("Veuillez entrer le chemin du fichier d'entrée : ")
    page_pairs = split_file(file_path)
    results = await process_all_pages(page_pairs)
    
    with open("output.json", "w", encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Processed {len(results)} pages. Results saved to output.json")

if __name__ == "__main__":
    asyncio.run(main())