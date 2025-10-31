
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import logging

# Setup logging
logger = logging.getLogger(__name__)

# --- Unified Firebase Client (All Collections: Users, Tasks, Sessions, Questions) ---
_db_client = None
_firebase_app = None
_KEY_FILE = 'educado-ai-private-key.json'  # Using the new unified database

def initialize_firebase():
    """Initialize Firebase connection for all collections"""
    global _db_client, _firebase_app
    
    if _firebase_app is not None:
        logger.info("Firebase app already initialized")
        return _db_client
    
    try:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(dir_path, '..', _KEY_FILE)
        
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"Firebase service account key not found at: {key_path}")
        
        # Initialize the default app
        cred = credentials.Certificate(key_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        _db_client = firestore.client()
        
        logger.info("Firebase app initialized successfully with unified database")
        return _db_client
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase app: {str(e)}")
        raise

def get_firestore_client():
    """Get the Firestore client"""
    global _db_client
    
    if _db_client is None:
        return initialize_firebase()
    
    return _db_client

def get_question_db_client():
    """
    Get the Firestore client for question database operations.
    Now points to the same unified database as get_firestore_client().
    Kept for backward compatibility.
    """
    return get_firestore_client()

def get_auth():
    """Get Firebase Auth instance"""
    if _firebase_app is None:
        initialize_firebase()
    return auth

# Initialize Firebase app when the module is imported
try:
    initialize_firebase()
except Exception as e:
    logger.error(f"Failed to auto-initialize Firebase: {str(e)}")
    # Don't raise here - let individual functions handle initialization