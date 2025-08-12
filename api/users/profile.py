from flask import Blueprint, request, jsonify, session
from services.airtable_service import AirtableService
from api.middleware import login_required
import json

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Endpoint per ottenere il profilo dell'utente"""
    try:
        user_id = session['user_id']
        username = session['username']
        
        # Inizializza il servizio Airtable
        airtable_service = AirtableService()
        
        # Ottieni il profilo utente
        profile_data = airtable_service.get_user_profile(user_id)
        
        if not profile_data:
            return jsonify({
                'success': False,
                'message': 'Profilo utente non trovato'
            }), 404
        
        # Ottieni le preferenze utente
        preferences = airtable_service.get_user_preferences(user_id) or {}
        
        # Logging rimosso
        
        return jsonify({
            'success': True,
            'profile': {
                'id': user_id,
                'username': profile_data.get('username', ''),
                'name': profile_data.get('name', ''),
                'user_id': profile_data.get('user_id', ''),
                'incrementale': profile_data.get('incrementale', ''),
                'preferences': preferences
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore interno del server: {str(e)}'
        }), 500

@users_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Endpoint per aggiornare il profilo dell'utente"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dati non forniti'
            }), 400
        
        user_id = session['user_id']
        username = session['username']
        
        # Campi aggiornabili dall'utente
        updatable_fields = ['Email', 'Nome', 'Cognome']
        update_data = {}
        
        for field in updatable_fields:
            if field.lower() in data:
                update_data[field] = data[field.lower()]
        
        if not update_data:
            return jsonify({
                'success': False,
                'message': 'Nessun campo valido da aggiornare'
            }), 400
        
        # Aggiorna il profilo su Airtable
        try:
            import requests
            from config import Config
            
            url = f"https://api.airtable.com/v0/{Config.AIRTABLE_BASE_ID}/Utenti/{user_id}"
            headers = {
                'Authorization': f'Bearer {Config.AIRTABLE_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'fields': update_data
            }
            
            response = requests.patch(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                # Logging rimosso
                airtable_service = AirtableService()
                
                return jsonify({
                    'success': True,
                    'message': 'Profilo aggiornato con successo',
                    'updated_fields': list(update_data.keys())
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Errore durante l\'aggiornamento del profilo'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Errore durante l\'aggiornamento: {str(e)}'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore interno del server: {str(e)}'
        }), 500

@users_bp.route('/preferences', methods=['GET'])
@login_required
def get_preferences():
    """Endpoint per ottenere le preferenze dell'utente"""
    try:
        user_id = session['user_id']
        username = session['username']
        
        # Inizializza il servizio Airtable
        airtable_service = AirtableService()
        
        # Ottieni le preferenze
        preferences = airtable_service.get_user_preferences(user_id)
        
        if preferences is None:
            return jsonify({
                'success': False,
                'message': 'Preferenze non trovate'
            }), 500
        
        # Logging rimosso
        
        return jsonify({
            'success': True,
            'preferences': preferences
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore interno del server: {str(e)}'
        }), 500

@users_bp.route('/preferences', methods=['PUT'])
@login_required
def update_preferences():
    """Endpoint per aggiornare le preferenze dell'utente"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dati non forniti'
            }), 400
        
        user_id = session['user_id']
        username = session['username']
        
        # Prepara i dati per l'aggiornamento
        update_data = {}
        
        if 'theme' in data:
            update_data['Tema interfaccia'] = data['theme']
        
        if 'json_prefs' in data:
            # Valida che sia un JSON valido
            try:
                json.loads(data['json_prefs'])
                update_data['json pref'] = data['json_prefs']
            except json.JSONDecodeError:
                return jsonify({
                    'success': False,
                    'message': 'Formato JSON non valido per le preferenze'
                }), 400
        
        if not update_data:
            return jsonify({
                'success': False,
                'message': 'Nessuna preferenza valida da aggiornare'
            }), 400
        
        # Aggiorna le preferenze usando il servizio Airtable
        airtable_service = AirtableService()
        
        # Converti i dati nel formato atteso dal servizio
        preferences_data = {}
        if 'theme' in data:
            preferences_data['theme'] = data['theme']
        if 'json_prefs' in data:
            preferences_data['json_prefs'] = data['json_prefs']
        
        success = airtable_service.update_user_preferences(user_id, preferences_data)
        
        if success:
            # Logging rimosso
            
            return jsonify({
                'success': True,
                'message': 'Preferenze aggiornate con successo'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Errore durante l\'aggiornamento delle preferenze'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore interno del server: {str(e)}'
        }), 500