"""Flask web interface for the Cognism scraper."""
import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import threading
import logging

from database import init_db, get_db, Company, Profile
from scraper import CognismScraper, export_to_csv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cognism_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'dev_secret_key_for_testing'  # Using a fixed key for debugging
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
# Disable CSRF protection temporarily for debugging
app.config['WTF_CSRF_ENABLED'] = False

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
init_db()

# Global scraper thread
scraper_thread = None
is_scraping = False
scraping_progress = {
    'total': 0,
    'current': 0,
    'current_company': '',
    'status': 'idle'
}


def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'txt'}


def run_scraper(company_list):
    """Run the scraper in a separate thread."""
    global is_scraping, scraping_progress
    
    try:
        # Update progress
        is_scraping = True
        scraping_progress['total'] = len(company_list)
        scraping_progress['current'] = 0
        scraping_progress['status'] = 'running'
        
        # Initialize database session
        db = get_db()
        
        # Initialize scraper
        scraper = CognismScraper()
        
        # Login
        if not scraper.login():
            scraping_progress['status'] = 'error'
            scraping_progress['error'] = 'Failed to log in to Cognism'
            is_scraping = False
            return
        
        # Process each company
        for i, company_name in enumerate(company_list):
            # Update progress
            scraping_progress['current'] = i + 1
            scraping_progress['current_company'] = company_name
            
            # Get or create company in database
            from database import get_or_create_company
            company = get_or_create_company(db, company_name)
            
            # Search for company
            if not scraper.search_company(company_name):
                logger.warning(f"Skipping company: {company_name}")
                continue
            
            # Extract profiles
            profiles = scraper.extract_profiles(company_name)
            
            # Save profiles to database
            from database import save_profile
            for profile_data in profiles:
                save_profile(db, company.id, profile_data)
        
        # Export results to CSV
        export_to_csv(db)
        
        # Update progress
        scraping_progress['status'] = 'completed'
        
    except Exception as e:
        logger.error(f"Error running scraper: {e}")
        scraping_progress['status'] = 'error'
        scraping_progress['error'] = str(e)
    
    finally:
        # Close the scraper
        if 'scraper' in locals():
            scraper.close()
        
        is_scraping = False


@app.route('/', methods=['GET'])
def index():
    """Render the home page."""
    db = get_db()
    companies = db.query(Company).all()
    profile_count = db.query(Profile).count()
    
    # Add current year to template context
    from datetime import datetime
    now = datetime.now()
    
    return render_template(
        'index.html',
        companies=companies,
        profile_count=profile_count,
        is_scraping=is_scraping,
        progress=scraping_progress,
        now=now
    )


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload for company list."""
    global scraper_thread, is_scraping
    
    # Check if scraper is already running
    if is_scraping:
        flash('A scraping job is already running. Please wait for it to complete.', 'error')
        return redirect(url_for('index'))
    
    # Check if file was uploaded
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    # Check if file is empty
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))
    
    # Check file type
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Read company list from file
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
                # Assume the column name is 'company' or the first column
                company_col = 'company' if 'company' in df.columns else df.columns[0]
                company_list = df[company_col].tolist()
            else:  # .txt file
                with open(file_path, 'r') as f:
                    company_list = [line.strip() for line in f if line.strip()]
            
            # Start scraper in a separate thread
            scraper_thread = threading.Thread(target=run_scraper, args=(company_list,))
            scraper_thread.daemon = True
            scraper_thread.start()
            
            flash(f'Processing {len(company_list)} companies', 'success')
        
        except Exception as e:
            flash(f'Error reading company list: {str(e)}', 'error')
    
    else:
        flash('Invalid file type. Please upload a CSV or TXT file.', 'error')
    
    return redirect(url_for('index'))


@app.route('/manual', methods=['POST'])
def manual_input():
    """Handle manual input for company list."""
    global scraper_thread, is_scraping
    
    # Check if scraper is already running
    if is_scraping:
        flash('A scraping job is already running. Please wait for it to complete.', 'error')
        return redirect(url_for('index'))
    
    # Get company list from form
    company_text = request.form.get('companies', '')
    company_list = [line.strip() for line in company_text.split('\n') if line.strip()]
    
    if not company_list:
        flash('No companies provided', 'error')
        return redirect(url_for('index'))
    
    # Start scraper in a separate thread
    scraper_thread = threading.Thread(target=run_scraper, args=(company_list,))
    scraper_thread.daemon = True
    scraper_thread.start()
    
    flash(f'Processing {len(company_list)} companies', 'success')
    return redirect(url_for('index'))


@app.route('/status', methods=['GET'])
def status():
    """Return the current scraping status as JSON."""
    from flask import jsonify
    return jsonify({
        'is_scraping': is_scraping,
        'progress': scraping_progress
    })


@app.route('/download', methods=['GET'])
def download():
    """Download the results as a CSV file."""
    # Export the latest results
    db = get_db()
    export_to_csv(db, 'exports/cognism_results.csv')
    
    # Send the file
    return send_file(
        'exports/cognism_results.csv',
        as_attachment=True,
        download_name='cognism_results.csv',
        mimetype='text/csv'
    )


@app.route('/company/<int:company_id>', methods=['GET'])
def view_company(company_id):
    """View profiles for a specific company."""
    db = get_db()
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        flash('Company not found', 'error')
        return redirect(url_for('index'))
    
    profiles = db.query(Profile).filter(Profile.company_id == company_id).all()
    
    return render_template(
        'company.html',
        company=company,
        profiles=profiles
    )


@app.route('/profile/<int:profile_id>', methods=['GET'])
def view_profile(profile_id):
    """View a specific profile."""
    db = get_db()
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    
    if not profile:
        flash('Profile not found', 'error')
        return redirect(url_for('index'))
    
    return render_template(
        'profile.html',
        profile=profile
    )


if __name__ == '__main__':
    # Create required directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('exports', exist_ok=True)
    
    # Bind to all interfaces and use port 9000 instead
    print("Starting server on http://127.0.0.1:9000")
    app.run(debug=True, host='127.0.0.1', port=9000)