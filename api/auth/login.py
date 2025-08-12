from flask import Blueprint, request, jsonify, session
from services.airtable_service import AirtableService
from datetime import datetime
import hashlib

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Endpoint per l'autenticazione degli utenti"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dati non forniti'
            }), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username e password sono richiesti'
            }), 400
        
        # Inizializza il servizio Airtable
        airtable_service = AirtableService()
        
        # Autentica l'utente
        user_data = airtable_service.authenticate_user(username, password)
        
        if not user_data:
            return jsonify({
                'success': False,
                'message': 'Credenziali non valide'
            }), 401
        
        # L'utente è autenticato correttamente
        # Crea la sessione
        session['user_id'] = user_data['user_id']
        session['username'] = username
        session['user_role'] = 'user'
        session['last_activity'] = datetime.now().isoformat()
        session['login_time'] = datetime.now().isoformat()
        
        # Login riuscito - logging rimosso
        
        # Ottieni le preferenze utente
        preferences = airtable_service.get_user_preferences(user_data['user_id']) or {}
        
        return jsonify({
            'success': True,
            'message': 'Login effettuato con successo',
            'user': {
                'id': user_data['user_id'],
                'username': username,
                'role': 'user',
                'name': user_data.get('name', ''),
                'preferences': preferences
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore interno del server: {str(e)}'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Endpoint per il logout degli utenti"""
    try:
        # Pulisci la sessione
        session.clear()
        
        return jsonify({
            'success': True,
            'message': 'Logout effettuato con successo'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore durante il logout: {str(e)}'
        }), 500

@auth_bp.route('/check-session', methods=['GET'])
def check_session():
    """Endpoint per verificare lo stato della sessione"""
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'authenticated': False,
                'message': 'Sessione non attiva'
            }), 401
        
        # Controlla il timeout della sessione
        from api.middleware import check_session_timeout
        if not check_session_timeout():
            return jsonify({
                'success': False,
                'authenticated': False,
                'message': 'Sessione scaduta'
            }), 401
        
        return jsonify({
            'success': True,
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'username': session['username'],
                'role': session.get('user_role', 'user')
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore durante la verifica della sessione: {str(e)}'
        }), 500