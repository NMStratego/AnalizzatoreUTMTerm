import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

class Config:
    # Configurazione Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configurazione Airtable
    AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY') or 'patD0oILpVSAgGlXH.340137025a6213e618f73e85886219cadc77c33e93168022f89fad7224d25bd8'
    AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID') or 'app7QNXXGNwobUi0N'
    
    # Configurazione applicazione
    APP_NAME = os.environ.get('APP_NAME') or 'Estrattore UTM Term'
    APP_VERSION = os.environ.get('APP_VERSION') or '1.0.0'
    
    # Configurazione sessioni
    SESSION_TIMEOUT = 3600  # 1 ora in secondi
    
    # Configurazione upload
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size