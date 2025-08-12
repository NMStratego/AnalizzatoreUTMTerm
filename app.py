from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify, session
import pandas as pd
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
        df = pd.read_csv(file_path)
        
        # Filtra solo le righe che hanno una SORGENTE (URL) con utm_term
        df_with_url = df[df['SORGENTE'].notna() & df['SORGENTE'].str.contains('utm_term', na=False)]
        
        # Estrai i parametri UTM
        df_with_url = df_with_url.copy()
        df_with_url['utm_term_extracted'] = df_with_url['SORGENTE'].apply(extract_utm_term_from_url)
        df_with_url['utm_campaign_extracted'] = df_with_url['SORGENTE'].apply(extract_campaign_name_from_url)
        df_with_url['utm_content_extracted'] = df_with_url['SORGENTE'].apply(extract_content_name_from_url)
        
        # Rimuovi righe senza utm_term
        df_with_utm_term = df_with_url[df_with_url['utm_term_extracted'].notna()]
        
        # Analizza i valori utm_term più frequenti
        utm_term_counts = Counter(df_with_utm_term['utm_term_extracted'])
        
        # Crea un mapping utm_term -> nome inserzione basato su utm_content
        utm_term_to_content = {}
        
        for utm_term in utm_term_counts.keys():
            if utm_term:
                subset = df_with_utm_term[df_with_utm_term['utm_term_extracted'] == utm_term]
                content_counts = Counter(subset['utm_content_extracted'].dropna())
                if content_counts:
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
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('numero_lead', ascending=False)
        
        # Prepara i dati dettagliati
        detailed_results = df_with_utm_term[['Data', 'Ora', 'Email', 'utm_term_extracted', 'utm_campaign_extracted', 'utm_content_extracted']].copy()
        detailed_results.columns = ['Data', 'Ora', 'Email', 'UTM_Term', 'Campagna', 'Nome_Inserzione']
        
        return {
            'success': True,
            'total_rows': len(df),
            'rows_with_utm_term': len(df_with_utm_term),
            'unique_ads': len(results_df),
            'results_df': results_df,
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
        df = pd.read_csv(file_path)
        
        # Verifica che esista la colonna SORGENTE
        if 'SORGENTE' not in df.columns:
            return {'error': 'Il file deve contenere una colonna "SORGENTE"'}
        
        # Estrai utm_term, utm_campaign e utm_content dagli URL
        utm_data = []
        for idx, row in df.iterrows():
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
        
        # Crea DataFrame con i dati UTM
        df_utm = pd.DataFrame(utm_data)
        
        # Conta le occorrenze di ogni utm_term
        utm_term_counts = df_utm['utm_term'].value_counts()
        
        # Mappa utm_term a nome inserzione usando utm_content
        utm_mapping = {}
        for utm_term in utm_term_counts.index:
            # Trova il utm_content più frequente per questo utm_term
            content_for_term = df_utm[df_utm['utm_term'] == utm_term]['utm_content']
            most_common_content = content_for_term.mode().iloc[0] if not content_for_term.empty else utm_term
            
            # Se utm_content è vuoto, usa utm_term
            nome_inserzione = most_common_content if most_common_content else utm_term
            utm_mapping[utm_term] = nome_inserzione
        
        # Crea il DataFrame dei risultati
        results_data = []
        for utm_term, count in utm_term_counts.items():
            results_data.append({
                'utm_term': utm_term,
                'nome_inserzione': utm_mapping[utm_term],
                'numero_lead': count
            })
        
        results_df = pd.DataFrame(results_data)
        
        # Aggiungi nome inserzione al DataFrame dettagliato
        df_utm['nome_inserzione'] = df_utm['utm_term'].map(utm_mapping)
        
        # Salva i file CSV
        results_df.to_csv('utm_term_inserzioni.csv', index=False)
        df_utm.to_csv('lead_dettagliati_con_inserzioni.csv', index=False)
        
        return {
            'results_df': results_df,
            'detailed_df': df_utm,
            'total_rows': len(df),
            'rows_with_utm_term': len(df_utm),
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
            top_insertions_list = results['results_df'].to_dict('records')
            
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
            df = results['results_df']
            
            # Crea un file temporaneo
            temp_file = os.path.join(upload_folder, 'temp_utm_term_inserzioni.csv')
            df.to_csv(temp_file, index=False, encoding='utf-8-sig')
            
            return send_file(temp_file, 
                           as_attachment=True, 
                           download_name='utm_term_inserzioni.csv',
                           mimetype='text/csv')
        
        elif file_type == 'lead_dettagliati_con_inserzioni.csv':
            # File dettagliato con tutti i lead
            df = results['detailed_df']
            
            # Crea un file temporaneo
            temp_file = os.path.join(upload_folder, 'temp_lead_dettagliati.csv')
            df.to_csv(temp_file, index=False, encoding='utf-8-sig')
            
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