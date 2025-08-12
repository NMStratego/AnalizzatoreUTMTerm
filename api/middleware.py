from functools import wraps
from flask import session, request, jsonify, redirect, url_for
from services.airtable_service import AirtableService
from config import Config

def login_required(f):
    """Decorator che richiede l'autenticazione dell'utente"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Accesso richiesto',
                    'redirect': '/login'
                }), 401
            else:
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def license_required(app_name=None):
    """Decorator che richiede una licenza attiva per l'applicazione"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'message': 'Accesso richiesto',
                        'redirect': '/login'
                    }), 401
                else:
                    return redirect(url_for('login'))
            
            # Verifica la licenza
            airtable_service = AirtableService()
            app_to_check = app_name or Config.APP_NAME
            
            license_result = airtable_service.verify_license(
                session['user_id'], 
                app_to_check
            )
            
            if not license_result['success']:
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'message': 'Errore durante la verifica della licenza',
                        'error': license_result['message']
                    }), 500
                else:
                    return redirect(url_for('license_error'))
            
            if not license_result['license_active']:
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'message': 'Licenza non attiva per questa applicazione',
                        'license_required': True
                    }), 403
                else:
                    return redirect(url_for('license_error'))
            
            # Accesso autorizzato - logging rimosso
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_session_timeout():
    """Controlla se la sessione è scaduta"""
    if 'user_id' in session:
        from datetime import datetime, timedelta
        
        last_activity = session.get('last_activity')
        if last_activity:
            last_activity = datetime.fromisoformat(last_activity)
            if datetime.now() - last_activity > timedelta(seconds=Config.SESSION_TIMEOUT):
                session.clear()
                return False
        
        # Aggiorna l'ultimo accesso
        session['last_activity'] = datetime.now().isoformat()
        return True
    
    return False

def admin_required(f):
    """Decorator che richiede privilegi di amministratore"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Accesso richiesto',
                    'redirect': '/login'
                }), 401
            else:
                return redirect(url_for('login'))
        
        # Controlla se l'utente è admin
        user_role = session.get('user_role', 'user')
        if user_role != 'admin':
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Privilegi di amministratore richiesti'
                }), 403
            else:
                return redirect(url_for('access_denied'))
        
        return f(*args, **kwargs)
    return decorated_function