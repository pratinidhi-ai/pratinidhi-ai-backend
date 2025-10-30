
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import logging

# Setup logging
logger = logging.getLogger(__name__)

# --- Client for [DEFAULT] App (Users, Tasks, Sessions) ---
_db_client = None
_firebase_app = None
_DEFAULT_KEY_FILE = 'p-ai-private-key.json'
_DEFAULT_APP_NAME = '[DEFAULT]'

# --- Client for [QUESTION_DB] App (Question Bank) ---
_qdb_client = None
_qdb_firebase_app = None
_QDB_KEY_FILE = 'educado-ai-private-key.json' 
_QDB_APP_NAME = 'questionDB'                  

def initialize_firebase():
    """Initialize the [DEFAULT] Firebase connection (for Users, Tasks, etc.)"""
    global _db_client, _firebase_app
    
    if _firebase_app is not None:
        logger.info("Default Firebase app already initialized")
        return _db_client
    
    try:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(dir_path, '..', _DEFAULT_KEY_FILE)
        
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"Default Firebase service account key not found at: {key_path}")
        
        # Initialize the default app
        cred = credentials.Certificate(key_path)
        _firebase_app = firebase_admin.initialize_app(cred) # No name = [DEFAULT]
        _db_client = firestore.client()
        
        logger.info("Default Firebase app initialized successfully")
        return _db_client
        
    except Exception as e:
        logger.error(f"Failed to initialize default Firebase app: {str(e)}")
        raise

def initialize_question_db():
    """Initialize the [QUESTION_DB] Firebase connection (for Question Bank)"""
    global _qdb_client, _qdb_firebase_app
    
    if _qdb_firebase_app is not None:
        logger.info("Question DB Firebase app already initialized")
        return _qdb_client
    
    try:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(dir_path, '..', _QDB_KEY_FILE)
        
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"Question DB service account key not found at: {key_path}")
        
        # Initialize the named app
        cred = credentials.Certificate(key_path)
        _qdb_firebase_app = firebase_admin.initialize_app(cred, name=_QDB_APP_NAME)
        _qdb_client = firestore.client(app=_qdb_firebase_app) # Get client for the named app
        
        logger.info(f"Firebase app '{_QDB_APP_NAME}' initialized successfully")
        return _qdb_client
        
    except ValueError as e:
        # This can happen if the app is already initialized (e.g., in a race condition)
        if 'already exists' in str(e):
             logger.warning(f"Firebase app '{_QDB_APP_NAME}' already exists. Attempting to retrieve.")
             _qdb_firebase_app = firebase_admin.get_app(name=_QDB_APP_NAME)
             _qdb_client = firestore.client(app=_qdb_firebase_app)
             return _qdb_client
        else:
             logger.error(f"Failed to initialize Question DB Firebase app: {str(e)}")
             raise
    except Exception as e:
        logger.error(f"Failed to initialize Question DB Firebase app: {str(e)}")
        raise

def get_firestore_client():
    """Get the Firestore client for the [DEFAULT] app"""
    global _db_client
    
    if _db_client is None:
        return initialize_firebase()
    
    return _db_client

def get_question_db_client():
    """Get the Firestore client for the [QUESTION_DB] app"""
    global _qdb_client
    
    if _qdb_client is None:
        return initialize_question_db()
    
    return _qdb_client

def get_auth():
    """Get Firebase Auth instance (from the DEFAULT app)"""
    if _firebase_app is None:
        initialize_firebase()
    return auth # auth.client() will use the default app

# Initialize the DEFAULT Firebase app when the module is imported
try:
    initialize_firebase()
except Exception as e:
    logger.error(f"Failed to auto-initialize default Firebase: {str(e)}")
    # Don't raise here - let individual functions handle initialization