from flask import Flask, render_template, request, jsonify, send_from_directory
import threading
from main_scraper import get_all_sitemap_urls, apply_filter, scrape_multiple_pages, save_scraped_content
from booking_scraper import scrape_booking_page, structure_content
import os
import re

app = Flask(__name__)

# Variable globale pour stocker l'état du scraping
scraping_status = {
    'is_running': False,
    'step': '',
    'progress': 0,
    'total_urls': 0,
    'current_url': '',
    'all_urls': [],
    'filtered_urls': [],
    'scraped_urls': [],
    'errors': [],
    'output_file': ''
}

# Configuration du répertoire de téléchargement
UPLOAD_DIRECTORY = os.path.join(app.root_path, 'uploads')
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    global scraping_status
    if scraping_status['is_running']:
        return jsonify({'status': 'error', 'message': 'Scraping is already running'})
    
    url = request.form['url']
    scraping_status = {
        'is_running': True,
        'step': 'finding_sitemap',
        'progress': 0,
        'total_urls': 0,
        'current_url': '',
        'all_urls': [],
        'filtered_urls': [],
        'scraped_urls': [],
        'errors': [],
        'output_file': ''
    }
    
    threading.Thread(target=find_sitemap, args=(url,)).start()
    return jsonify({'status': 'success', 'message': 'Sitemap search started'})

def find_sitemap(url):
    global scraping_status
    try:
        scraping_status['all_urls'] = get_all_sitemap_urls(url)
        scraping_status['filtered_urls'] = scraping_status['all_urls'].copy()  # Initialiser filtered_urls avec toutes les URLs
        scraping_status['total_urls'] = len(scraping_status['all_urls'])
        scraping_status['step'] = 'sitemap_found'
    except Exception as e:
        scraping_status['errors'].append(f"Error finding sitemap: {str(e)}")
        scraping_status['step'] = 'error'
    finally:
        scraping_status['is_running'] = False
    
@app.route('/apply_filter', methods=['POST'])
def apply_filter_route():
    global scraping_status
    filter_type = request.form['filter_type']
    keywords = request.form['keywords'].split(',')
    
    scraping_status['filtered_urls'] = apply_filter(scraping_status['all_urls'], filter_type, keywords)
    scraping_status['total_urls'] = len(scraping_status['filtered_urls'])
    scraping_status['step'] = 'urls_filtered'
    
    return jsonify({
        'status': 'success',
        'message': f'Filter applied. {len(scraping_status["filtered_urls"])} URLs remaining.',
        'filtered_urls': scraping_status['filtered_urls'],
        'filtered_count': len(scraping_status['filtered_urls'])
    })

@app.route('/start_scraping_filtered', methods=['POST'])
def start_scraping_filtered():
    global scraping_status
    if scraping_status['step'] != 'urls_filtered':
        return jsonify({'status': 'error', 'message': 'URLs must be filtered before scraping'})
    
    scraping_status['step'] = 'scraping'
    scraping_status['is_running'] = True
    threading.Thread(target=scrape_filtered_urls).start()
    return jsonify({'status': 'success', 'message': 'Scraping of filtered URLs started'})

def scrape_filtered_urls():
    global scraping_status
    try:
        total_urls = len(scraping_status['filtered_urls'])
        for i, url in enumerate(scraping_status['filtered_urls']):
            scraping_status['current_url'] = url
            scraping_status['progress'] = (i + 1) / total_urls * 100
            try:
                result = scrape_multiple_pages([url])  # Scrape une seule URL à la fois
                if result:
                    scraping_status['scraped_urls'].extend(result)
            except Exception as e:
                scraping_status['errors'].append(f"Error scraping {url}: {str(e)}")
        scraping_status['step'] = 'scraping_complete'
        output_file = 'scraped_content.txt'
        save_scraped_content(scraping_status['scraped_urls'], output_file)
        scraping_status['output_file'] = os.path.abspath(output_file)
    except Exception as e:
        scraping_status['errors'].append(f"General error during scraping: {str(e)}")
    finally:
        scraping_status['is_running'] = False

@app.route('/scraping_status')
def get_scraping_status():
    return jsonify(scraping_status)

# Nouvelle route pour le scraping de Booking.com
def is_valid_booking_url(url):
    regex = r'^https://www\.booking\.com/hotel/[a-z]{2}/[a-z0-9-]+\.(?:[a-z]{2}\.)?html$'
    return re.match(regex, url) is not None

@app.route('/scrape_booking', methods=['POST'])
def scrape_booking():
    url = request.form['url']
    if not is_valid_booking_url(url):
        return jsonify({
            'status': 'error',
            'message': "L'URL n'est pas au bon format. Veuillez entrer une URL valide de Booking.com."
        })
    
    try:
        text_content, html_content = scrape_booking_page(url)
        structured_content = structure_content(text_content, html_content)
        
        # Sauvegarde du contenu structuré
        output_file = 'booking_scraped_content.txt'
        full_path = os.path.join(UPLOAD_DIRECTORY, output_file)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(structured_content)
        
        download_link = f'/download/{output_file}'
        
        return jsonify({
            'status': 'success',
            'message': 'Scraping de Booking.com terminé avec succès',
            'content_preview': structured_content[:500] + '...',  # Aperçu du contenu
            'download_link': download_link
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Erreur lors du scraping de Booking.com: {str(e)}"
        })

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_DIRECTORY, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)