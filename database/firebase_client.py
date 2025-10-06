"""
Firebase connection and initialization
Central place for Firebase configuration and client setup
"""

import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Global Firebase client - will be initialized once
_db_client = None
_firebase_app = None

def initialize_firebase():
    """Initialize Firebase connection"""
    global _db_client, _firebase_app
    
    if _firebase_app is not None:
        logger.info("Firebase already initialized")
        return _db_client
    
    try:
        # Get the path to the service account key
        dir_path = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(dir_path, '..', 'p-ai-private-key.json')
        
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"Firebase service account key not found at: {key_path}")
        
        # Initialize Firebase
        cred = credentials.Certificate(key_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        _db_client = firestore.client()
        
        logger.info("Firebase initialized successfully")
        return _db_client
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {str(e)}")
        raise

def get_firestore_client():
    """Get the Firestore client, initializing if necessary"""
    global _db_client
    
    if _db_client is None:
        return initialize_firebase()
    
    return _db_client

def get_auth():
    """Get Firebase Auth instance"""
    if _firebase_app is None:
        initialize_firebase()
    return auth

# Initialize Firebase when the module is imported
try:
    initialize_firebase()
except Exception as e:
    logger.error(f"Failed to auto-initialize Firebase: {str(e)}")
    # Don't raise here - let individual functions handle initialization