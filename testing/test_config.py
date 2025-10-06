"""
Test Configuration
Sets up environment for local task testing
"""

import os

# Set environment variables for testing
os.environ['FLASK_ENV'] = 'testing'
os.environ['FIREBASE_PROJECT_ID'] = 'test-project'
os.environ['FIREBASE_PRIVATE_KEY_ID'] = 'test-key-id'
os.environ['FIREBASE_PRIVATE_KEY'] = 'test-private-key'
os.environ['FIREBASE_CLIENT_EMAIL'] = 'test@test-project.iam.gserviceaccount.com'
os.environ['FIREBASE_CLIENT_ID'] = 'test-client-id'
os.environ['FIREBASE_AUTH_URI'] = 'https://accounts.google.com/o/oauth2/auth'
os.environ['FIREBASE_TOKEN_URI'] = 'https://oauth2.googleapis.com/token'

print("🔧 Test environment configured")