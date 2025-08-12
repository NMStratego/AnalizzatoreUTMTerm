from flask import Blueprint, request, jsonify, session
from services.airtable_service import AirtableService
from api.middleware import login_required
from config import Config

licenses_bp = Blueprint('licenses', __name__)

@licenses_bp.route('/verify', methods=['GET', 'POST'])
@login_required
def verify_license():
    """Endpoint per verificare la licenza dell'utente per l'applicazione corrente"""
    try:
        # Ottieni il nome dell'applicazione dalla richiesta o usa quello di default
        if request.method == 'POST':
            data = request.get_json() or {}
            app_name = data.get('app_name', Config.APP_NAME)
        else:
            app_name = request.args.get('app_name', Config.APP_NAME)
        
        user_id = session['user_id']
        username = session['username']
        
        # Inizializza il servizio Airtable
        airtable_service = AirtableService()
        
        # Verifica la licenza
        has_license = airtable_service.check_user_license(user_id, app_name)
        
        if has_license:
            return jsonify({
                'success': True,
                'license_active': True,
                'message': 'Licenza attiva',
                'license_info': {
                    'app_name': app_name,
                    'license_type': 'Standard',
                    'status': 'Attivo'
                }
            }), 200
        else:
            return jsonify({
                'success': True,
                'license_active': False,
                'message': 'Licenza non attiva per questa applicazione',
                'app_name': app_name
            }), 403
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore interno del server: {str(e)}'
        }), 500

@licenses_bp.route('/list', methods=['GET'])
@login_required
def list_user_licenses():
    """Endpoint per ottenere tutte le licenze dell'utente"""
    try:
        user_id = session['user_id']
        username = session['username']
        
        # Inizializza il servizio Airtable
        airtable_service = AirtableService()
        
        # Ottieni tutte le licenze dell'utente
        try:
            import requests
            url = f"https://api.airtable.com/v0/{Config.AIRTABLE_BASE_ID}/Licenze"
            headers = {
                'Authorization': f'Bearer {Config.AIRTABLE_API_KEY}',
                'Content-Type': 'application/json'
            }
            params = {
                'filterByFormula': f"{{Utente_Link}}='{user_id}'"
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                licenses = []
                
                for record in data['records']:
                    fields = record['fields']
                    licenses.append({
                        'id': record['id'],
                        'app_name': fields.get('Applicazione', ''),
                        'status': fields.get('Stato', ''),
                        'license_type': fields.get('Tipo_Licenza', ''),
                        'expiry_date': fields.get('Data_Scadenza'),
                        'features': fields.get('Funzionalita_Abilitate', [])
                    })
                
                # Logging rimosso
                
                return jsonify({
                    'success': True,
                    'licenses': licenses,
                    'total_count': len(licenses)
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Errore durante il recupero delle licenze'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Errore durante il recupero delle licenze: {str(e)}'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore interno del server: {str(e)}'
        }), 500

@licenses_bp.route('/check-features', methods=['POST'])
@login_required
def check_feature_access():
    """Endpoint per verificare l'accesso a funzionalità specifiche"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dati non forniti'
            }), 400
        
        app_name = data.get('app_name', Config.APP_NAME)
        feature_name = data.get('feature_name')
        
        if not feature_name:
            return jsonify({
                'success': False,
                'message': 'Nome della funzionalità richiesto'
            }), 400
        
        user_id = session['user_id']
        username = session['username']
        
        # Inizializza il servizio Airtable
        airtable_service = AirtableService()
        
        # Verifica la licenza
        license_result = airtable_service.verify_license(user_id, app_name)
        
        if not license_result['success'] or not license_result['license_active']:
            return jsonify({
                'success': True,
                'feature_access': False,
                'message': 'Licenza non attiva'
            }), 200
        
        # Controlla se la funzionalità è abilitata
        license_data = license_result['license_data']
        enabled_features = license_data.get('Funzionalita_Abilitate', [])
        
        feature_access = feature_name in enabled_features
        
        # Logging rimosso
        
        return jsonify({
            'success': True,
            'feature_access': feature_access,
            'feature_name': feature_name,
            'app_name': app_name
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore interno del server: {str(e)}'
        }), 500