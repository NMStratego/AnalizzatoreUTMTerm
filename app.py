from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify, session
import csv
import os
from urllib.parse import urlparse, parse_qs
from collections import Counter
from werkzeug.utils import secure_filename
from datetime import datetime
import json
from dotenv import load_dotenv

# Carica le variabili d'ambiente (solo se il file .env esiste)
try:
    load_dotenv()
except Exception:
    # Su Vercel le variabili d'ambiente sono già disponibili
    pass

# Importa configurazione e servizi
from config import Config
from services.airtable_service import AirtableService
from api.middleware import login_required, license_required, check_session_timeout

# Importa le API routes
from api.auth.login import auth_bp
from api.licenses.verify import licenses_bp
from api.users.profile import users_bp

app = Flask(__name__)
app.config.from_object(Config)

# Registra i blueprint delle API
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(licenses_bp, url_prefix='/api/licenses')
app.register_blueprint(users_bp, url_prefix='/api/users')

# Crea la cartella uploads se non esiste (solo in ambiente locale)
try:
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
except (OSError, PermissionError):
    # Su Vercel usa /tmp per i file temporanei
    app.config['UPLOAD_FOLDER'] = '/tmp'

def extract_utm_term_from_url(url):
    """Estrae il valore utm_term da un URL"""
    if pd.isna(url) or not isinstance(url, str):
        return None
    
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        utm_term = query_params.get('utm_term', [None])[0]
        return utm_term
    except:
        return None

def extract_campaign_name_from_url(url):
    """Estrae il nome della campagna dall'URL"""
    if pd.isna(url) or not isinstance(url, str):
        return None
    
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        utm_campaign = query_params.get('utm_campaign', [None])[0]
        return utm_campaign
    except:
        return None

def extract_content_name_from_url(url):
    """Estrae il contenuto dell'inserzione dall'URL"""
    if pd.isna(url) or not isinstance(url, str):
        return None
    
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        utm_content = query_params.get('utm_content', [None])[0]
        return utm_content
    except:
        return None

def process_csv_file(file_path):
    """Processa il file CSV e restituisce i risultati"""
    try:
        # Leggi il file CSV
        rows = []
        with open(file_path, 'r', encoding='utf-8-sig', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rows.append(row)
        
        # Filtra solo le righe che hanno una SORGENTE (URL) con utm_term
        rows_with_url = []
        for row in rows:
            sorgente = row.get('SORGENTE', '')
            if sorgente and 'utm_term' in sorgente:
                rows_with_url.append(row)
        
        # Estrai i parametri UTM
        rows_with_utm_term = []
        for row in rows_with_url:
            utm_term = extract_utm_term_from_url(row.get('SORGENTE', ''))
            utm_campaign = extract_campaign_name_from_url(row.get('SORGENTE', ''))
            utm_content = extract_content_name_from_url(row.get('SORGENTE', ''))
            
            if utm_term:
                row['utm_term_extracted'] = utm_term
                row['utm_campaign_extracted'] = utm_campaign
                row['utm_content_extracted'] = utm_content
                rows_with_utm_term.append(row)
        
        # Analizza i valori utm_term più frequenti
        utm_term_counts = Counter([row['utm_term_extracted'] for row in rows_with_utm_term])
        
        # Crea un mapping utm_term -> nome inserzione basato su utm_content
        utm_term_to_content = {}
        
        for utm_term in utm_term_counts.keys():
            if utm_term:
                content_list = [row['utm_content_extracted'] for row in rows_with_utm_term 
                               if row['utm_term_extracted'] == utm_term and row.get('utm_content_extracted')]
                if content_list:
                    content_counts = Counter(content_list)
                    most_common_content = content_counts.most_common(1)[0][0]
                    utm_term_to_content[utm_term] = most_common_content
        
        # Prepara i risultati
        results = []
        for utm_term, content in utm_term_to_content.items():
            count = utm_term_counts[utm_term]
            results.append({
                'utm_term': utm_term,
                'nome_inserzione': content,
                'numero_lead': count
            })
        
        # Ordina per numero di lead
        results.sort(key=lambda x: x['numero_lead'], reverse=True)
        
        # Prepara i dati dettagliati
        detailed_results = []
        for row in rows_with_utm_term:
            detailed_results.append({
                'Data': row.get('Data', ''),
                'Ora': row.get('Ora', ''),
                'Email': row.get('Email', ''),
                'UTM_Term': row.get('utm_term_extracted', ''),
                'Campagna': row.get('utm_campaign_extracted', ''),
                'Nome_Inserzione': row.get('utm_content_extracted', '')
            })
        
        return {
            'success': True,
            'total_rows': len(rows),
            'rows_with_utm_term': len(rows_with_utm_term),
            'unique_ads': len(results),
            'results_df': results,
            'detailed_df': detailed_results,
            'top_utm_terms': utm_term_counts.most_common(10)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def process_csv(file_path):
    """Processa il file CSV e restituisce i risultati dell'analisi"""
    try:
        # Leggi il CSV
        rows = []
        with open(file_path, 'r', encoding='utf-8-sig', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            for row in reader:
                rows.append(row)
        
        # Verifica che esista la colonna SORGENTE
        if 'SORGENTE' not in fieldnames:
            return {'error': 'Il file deve contenere una colonna "SORGENTE"'}
        
        # Estrai utm_term, utm_campaign e utm_content dagli URL
        utm_data = []
        for row in rows:
            url = str(row.get('SORGENTE', ''))
            if 'utm_term=' in url:
                try:
                    parsed_url = urlparse(url)
                    query_params = parse_qs(parsed_url.query)
                    
                    utm_term = query_params.get('utm_term', [''])[0]
                    utm_campaign = query_params.get('utm_campaign', [''])[0]
                    utm_content = query_params.get('utm_content', [''])[0]
                    
                    if utm_term:
                        utm_data.append({
                            'utm_term': utm_term,
                            'utm_campaign': utm_campaign,
                            'utm_content': utm_content,
                            'data': row.get('Data', ''),
                            'ora': row.get('Ora', ''),
                            'email': row.get('Email', '')
                        })
                except Exception as e:
                    continue
        
        if not utm_data:
            return {'error': 'Nessun URL con utm_term trovato nel file'}
        
        # Conta le occorrenze di ogni utm_term
        utm_term_counts = Counter([item['utm_term'] for item in utm_data])
        
        # Mappa utm_term a nome inserzione usando utm_content
        utm_mapping = {}
        for utm_term in utm_term_counts.keys():
            # Trova il utm_content più frequente per questo utm_term
            content_for_term = [item['utm_content'] for item in utm_data if item['utm_term'] == utm_term and item['utm_content']]
            if content_for_term:
                content_counts = Counter(content_for_term)
                most_common_content = content_counts.most_common(1)[0][0]
                nome_inserzione = most_common_content if most_common_content else utm_term
            else:
                nome_inserzione = utm_term
            utm_mapping[utm_term] = nome_inserzione
        
        # Crea i risultati
        results_data = []
        for utm_term, count in utm_term_counts.items():
            results_data.append({
                'utm_term': utm_term,
                'nome_inserzione': utm_mapping[utm_term],
                'numero_lead': count
            })
        
        # Aggiungi nome inserzione ai dati dettagliati
        for item in utm_data:
            item['nome_inserzione'] = utm_mapping[item['utm_term']]
        
        return {
            'results_df': results_data,
            'detailed_df': utm_data,
            'total_rows': len(rows),
            'rows_with_utm_term': len(utm_data),
            'unique_ads': len(utm_term_counts)
        }
        
    except Exception as e:
        return {'error': f'Errore nel processare il file: {str(e)}'}

# Middleware per controllare la sessione su ogni richiesta
@app.before_request
def before_request():
    # Escludi le route che non richiedono autenticazione
    excluded_routes = ['/login', '/license-error', '/api/auth/login', '/api/auth/check-session', '/static']
    
    if request.endpoint and any(request.path.startswith(route) for route in excluded_routes):
        return
    
    # Controlla se l'utente è autenticato
    if 'user_id' not in session:
        if request.is_json:
            return jsonify({
                'success': False,
                'message': 'Accesso richiesto',
                'redirect': '/login'
            }), 401
        else:
            return redirect(url_for('login'))
    
    # Controlla il timeout della sessione
    if not check_session_timeout():
        if request.is_json:
            return jsonify({
                'success': False,
                'message': 'Sessione scaduta',
                'redirect': '/login'
            }), 401
        else:
            return redirect(url_for('login'))

@app.route('/login')
def login():
    """Pagina di login"""
    return render_template('login.html')

@app.route('/license-error')
def license_error():
    """Pagina di errore per licenze non attive"""
    return render_template('license_error.html')

@app.route('/')
@license_required()
def index():
    """Pagina principale - richiede licenza attiva"""
    # Logging rimosso
    
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
@license_required()
def upload_file():
    if 'file' not in request.files:
        flash('Nessun file selezionato')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('Nessun file selezionato')
        return redirect(request.url)
    
    if file and file.filename.lower().endswith('.csv'):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Processa il file
        results = process_csv(file_path)
        
        if 'error' not in results:
            # Logging rimosso
            
            # Prepara i dati per il template
            top_insertions_list = results['results_df']
            
            session_data = {
                'top_insertions': top_insertions_list,
                'stats': {
                    'total_leads': results['total_rows'],
                    'leads_with_utm': results['rows_with_utm_term'],
                    'unique_insertions': results['unique_ads']
                },
                'chart_data': {
                    'labels': json.dumps([ins['nome_inserzione'] for ins in top_insertions_list[:10]]),
                    'data': json.dumps([ins['numero_lead'] for ins in top_insertions_list[:10]])
                },
                'timestamp': datetime.now().strftime('%d/%m/%Y alle %H:%M')
            }
            
            return render_template('results.html', **session_data)
        else:
            flash(f'Errore nel processare il file: {results["error"]}')
            return redirect(url_for('index'))
    else:
        flash('Per favore carica un file CSV valido')
        return redirect(url_for('index'))

@app.route('/download/<file_type>')
@license_required()
def download_file(file_type):
    try:
        # Trova il file CSV più recente nella cartella uploads
        upload_folder = app.config['UPLOAD_FOLDER']
        csv_files = [f for f in os.listdir(upload_folder) if f.endswith('.csv')]
        
        if not csv_files:
            flash('Nessun file CSV trovato. Carica prima un file.')
            return redirect(url_for('index'))
        
        # Prendi il file più recente
        latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(upload_folder, x)))
        file_path = os.path.join(upload_folder, latest_file)
        
        # Processa il file per generare i risultati
        results = process_csv(file_path)
        
        if 'error' in results:
            flash(f'Errore nel processare il file: {results["error"]}')
            return redirect(url_for('index'))
        
        # Genera il file richiesto
        if file_type == 'utm_term_inserzioni.csv':
            # File riepilogo inserzioni
            data = results['results_df']
            
            # Crea un file temporaneo
            temp_file = os.path.join(upload_folder, 'temp_utm_term_inserzioni.csv')
            with open(temp_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
                if data:
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
            
            return send_file(temp_file, 
                           as_attachment=True, 
                           download_name='utm_term_inserzioni.csv',
                           mimetype='text/csv')
        
        elif file_type == 'lead_dettagliati_con_inserzioni.csv':
            # File dettagliato con tutti i lead
            data = results['detailed_df']
            
            # Crea un file temporaneo
            temp_file = os.path.join(upload_folder, 'temp_lead_dettagliati.csv')
            with open(temp_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
                if data:
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
            
            return send_file(temp_file, 
                           as_attachment=True, 
                           download_name='lead_dettagliati_con_inserzioni.csv',
                           mimetype='text/csv')
        
        else:
            flash('Tipo di file non riconosciuto')
            return redirect(url_for('index'))
            
    except Exception as e:
        flash(f'Errore durante il download: {str(e)}')
        return redirect(url_for('index'))

# For Vercel deployment - app is exported via index.py
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)