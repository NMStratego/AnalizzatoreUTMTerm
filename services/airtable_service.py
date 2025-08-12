import requests
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class AirtableService:
    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.base_url = f'https://api.airtable.com/v0/{self.base_id}'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Autentica un utente verificando username e password"""
        try:

            
            # Cerca l'utente per username
            url = f"{self.base_url}/Utenti"
            params = {
                'filterByFormula': f"TRIM({{username}}) = '{username}'",
                'maxRecords': 1
            }
            

            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()

            
            if not data.get('records'):

                return None
            
            user_record = data['records'][0]
            user_fields = user_record['fields']
            
            # Verifica la password
            stored_password = user_fields.get('password')

            
            if stored_password == password:

                return {
                    'id': user_record['id'],
                    'user_id': user_fields.get('user_id'),
                    'username': user_fields.get('username'),
                    'name': user_fields.get('Name')
                }
            

            return None
            
        except Exception as e:
            print(f"Errore durante l'autenticazione: {e}")
            return None
    
    def get_user_licenses(self, user_id: str, app_name: str):
        """Recupera le licenze di un utente per una specifica applicazione"""
        try:
    
            
            # Prima stampa tutte le licenze disponibili
            all_licenses_url = f"{self.base_url}/Licenze"
            all_licenses_response = requests.get(all_licenses_url, headers=self.headers)
            all_licenses_response.raise_for_status()
            all_licenses_data = all_licenses_response.json()

            
            # Cerca le licenze nella tabella Licenze
            # Dato che i filtri non funzionano con gli array, prendiamo tutti i record e filtriamo manualmente
            filter_formula = f"{{Applicazione}} = '{app_name}'"

            
            url = f"{self.base_url}/Licenze"
            params = {
                'filterByFormula': filter_formula
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()

            
            licenses = []
            
            for record in data.get('records', []):
                fields = record['fields']
                # Controlla se l'user_id è nell'array Utente_Collegato
                utenti_collegati = fields.get('Utente_Collegato', [])

                
                if user_id in utenti_collegati:
                    license_data = {
                        'id': record['id'],
                        'stato': fields.get('Stato'),
                        'applicazione': fields.get('Applicazione'),
                        'username': fields.get('Username'),
                        'data_creazione': fields.get('Data_Creazione')
                    }
                    licenses.append(license_data)

            

            return licenses
            
        except Exception as e:
            print(f"Errore durante il recupero delle licenze: {e}")
            return []
    
    def check_user_license(self, user_id: str, app_name: str) -> bool:
        """Verifica se un utente ha una licenza attiva per una specifica applicazione"""
        licenses = self.get_user_licenses(user_id, app_name)
        
        for license in licenses:
            if license.get('stato') == 'Attivo':
                return True
        
        return False
    
    def verify_license(self, user_id: str, app_name: str) -> Dict[str, Any]:
        """Verifica se l'utente ha una licenza attiva per l'applicazione specificata"""
        try:
            licenses = self.get_user_licenses(user_id, app_name)
            
            for license in licenses:
                if license.get('stato') == 'Attivo':
                    return {
                        'success': True,
                        'license_active': True,
                        'license_data': license
                    }
            
            return {
                'success': True,
                'license_active': False,
                'message': 'Licenza non attiva per questa applicazione'
            }
            
        except Exception as e:
            print(f"Errore durante la verifica della licenza: {e}")
            return {
                'success': False,
                'message': f'Errore durante la verifica della licenza: {str(e)}'
            }
    
    # Funzione di logging rimossa - non necessaria per il funzionamento base
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Recupera il profilo completo di un utente"""
        try:
            url = f"{self.base_url}/Utenti/{user_id}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            fields = data['fields']
            
            return {
                'id': data['id'],
                'user_id': fields.get('user_id'),
                'username': fields.get('username'),
                'name': fields.get('Name'),
                'incrementale': fields.get('Incrementale')
            }
            
        except Exception as e:
            print(f"Errore durante il recupero del profilo: {e}")
            return None
    
    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Recupera le preferenze di un utente"""
        try:
            url = f"{self.base_url}/Preferenze utente"
            params = {
                'filterByFormula': f"{{user_id}} = '{user_id}'",
                'maxRecords': 1
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('records'):
                return None
            
            record = data['records'][0]
            fields = record['fields']
            
            return {
                'id': record['id'],
                'tema_interfaccia': fields.get('Tema interfaccia'),
                'json_pref': fields.get('json pref')
            }
            
        except Exception as e:
            print(f"Errore durante il recupero delle preferenze: {e}")
            return None
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Aggiorna le preferenze di un utente"""
        try:
            # Prima trova il record delle preferenze
            url = f"{self.base_url}/Preferenze utente"
            params = {
                'filterByFormula': f"{{user_id}} = '{user_id}'",
                'maxRecords': 1
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('records'):
                # Aggiorna il record esistente
                record_id = data['records'][0]['id']
                update_url = f"{self.base_url}/Preferenze utente/{record_id}"
                
                update_data = {
                    'fields': {
                        'Tema interfaccia': preferences.get('tema_interfaccia'),
                        'json pref': preferences.get('json_pref', '')
                    }
                }
                
                response = requests.patch(update_url, headers=self.headers, json=update_data)
                response.raise_for_status()
            else:
                # Crea un nuovo record
                create_data = {
                    'fields': {
                        'Tema interfaccia': preferences.get('tema_interfaccia'),
                        'json pref': preferences.get('json_pref', ''),
                        'Utente': [user_id]
                    }
                }
                
                response = requests.post(url, headers=self.headers, json=create_data)
                response.raise_for_status()
            
            return True
            
        except Exception as e:
            print(f"Errore durante l'aggiornamento delle preferenze: {e}")
            return False
    
    # Funzione di recupero log rimossa - non necessaria per il funzionamento base