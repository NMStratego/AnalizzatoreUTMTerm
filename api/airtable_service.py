import requests
import json
from datetime import datetime
from config import Config

class AirtableService:
    def __init__(self):
        self.api_key = Config.AIRTABLE_API_KEY
        self.base_id = Config.AIRTABLE_BASE_ID
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def authenticate_user(self, username, password):
        """Autentica un utente verificando username e password su Airtable"""
        try:
            # Cerca l'utente nella tabella Utenti
            url = f"{self.base_url}/Utenti"
            params = {
                'filterByFormula': f"AND({{username}}='{username}', {{password}}='{password}')"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data['records']:
                    user_record = data['records'][0]
                    return {
                        'success': True,
                        'user_id': user_record['id'],
                        'username': user_record['fields'].get('username'),
                        'user_data': user_record['fields']
                    }
                else:
                    return {'success': False, 'message': 'Credenziali non valide'}
            else:
                return {'success': False, 'message': 'Errore di connessione al database'}
                
        except Exception as e:
            return {'success': False, 'message': f'Errore durante l\'autenticazione: {str(e)}'}
    
    def verify_license(self, user_id, app_name):
        """Verifica se l'utente ha una licenza attiva per l'applicazione specificata"""
        try:
            # Cerca la licenza nella tabella Licenze
            url = f"{self.base_url}/Licenze"
            params = {
                'filterByFormula': f"AND({{Utente_Link}}='{user_id}', {{Applicazione}}='{app_name}', {{Stato}}='Attivo')"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data['records']:
                    license_record = data['records'][0]
                    return {
                        'success': True,
                        'license_active': True,
                        'license_data': license_record['fields']
                    }
                else:
                    return {
                        'success': True,
                        'license_active': False,
                        'message': 'Licenza non attiva per questa applicazione'
                    }
            else:
                return {'success': False, 'message': 'Errore durante la verifica della licenza'}
                
        except Exception as e:
            return {'success': False, 'message': f'Errore durante la verifica della licenza: {str(e)}'}
    
    # Funzione di logging rimossa - non necessaria per il funzionamento base
    
    def get_user_profile(self, user_id):
        """Ottiene il profilo completo dell'utente"""
        try:
            url = f"{self.base_url}/Utenti/{user_id}"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'success': True,
                    'user_data': user_data['fields']
                }
            else:
                return {'success': False, 'message': 'Utente non trovato'}
                
        except Exception as e:
            return {'success': False, 'message': f'Errore durante il recupero del profilo: {str(e)}'}
    
    def get_user_preferences(self, user_id):
        """Ottiene le preferenze dell'utente"""
        try:
            url = f"{self.base_url}/Preferenze utente"
            params = {
                'filterByFormula': f"{{user_id}}='{user_id}'"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data['records']:
                    prefs = data['records'][0]['fields']
                    return {
                        'success': True,
                        'preferences': {
                            'theme': prefs.get('Tema interfaccia', 'Chiaro'),
                            'json_prefs': prefs.get('json pref', '{}')
                        }
                    }
                else:
                    # Crea preferenze di default se non esistono
                    return {
                        'success': True,
                        'preferences': {
                            'theme': 'Chiaro',
                            'json_prefs': '{}'
                        }
                    }
            else:
                return {'success': False, 'message': 'Errore durante il recupero delle preferenze'}
                
        except Exception as e:
            return {'success': False, 'message': f'Errore durante il recupero delle preferenze: {str(e)}'}