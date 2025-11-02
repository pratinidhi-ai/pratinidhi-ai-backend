"""
Script to generate a Firebase ID Token for testing APIs

This script signs in a test user and returns a valid Firebase ID token
that can be used as the Bearer token for API requests.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import json

# Firebase Web API Key - Get this from Firebase Console
# Go to: Project Settings > General > Web API Key
FIREBASE_WEB_API_KEY = "AIzaSyDD4eUr1EIvLQkJS_FZvtXpI0GXoHENQM4"

# Test user credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

def get_firebase_token(email, password, api_key):
    """
    Sign in with email and password to get Firebase ID token
    
    Args:
        email: User email
        password: User password
        api_key: Firebase Web API Key
    
    Returns:
        ID token string
    """
    
    # Firebase Auth REST API endpoint
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        id_token = data.get("idToken")
        refresh_token = data.get("refreshToken")
        expires_in = data.get("expiresIn")
        
        print("✅ Successfully obtained Firebase ID token!")
        print(f"\n{'='*80}")
        print("ID TOKEN (use this as Bearer token):")
        print(f"{'='*80}")
        print(id_token)
        print(f"{'='*80}\n")
        
        print(f"Token expires in: {expires_in} seconds (~{int(expires_in)//3600} hours)")
        print(f"\nRefresh token (for getting new tokens): {refresh_token[:50]}...")
        
        # Save to file for easy access
        token_file = os.path.join(os.path.dirname(__file__), 'test_token.txt')
        with open(token_file, 'w') as f:
            f.write(f"ID_TOKEN={id_token}\n")
            f.write(f"REFRESH_TOKEN={refresh_token}\n")
            f.write(f"EXPIRES_IN={expires_in}\n")
        
        print(f"\n✅ Token saved to: {token_file}")
        
        return id_token
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error getting token: {e}")
        print(f"Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def create_test_user(email, password, api_key):
    """
    Create a new test user (if it doesn't exist)
    
    Args:
        email: User email
        password: User password
        api_key: Firebase Web API Key
    """
    
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
    
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        print(f"✅ Test user created: {email}")
        return True
        
    except requests.exceptions.HTTPError as e:
        if "EMAIL_EXISTS" in e.response.text:
            print(f"ℹ️  User already exists: {email}")
            return True
        else:
            print(f"❌ Error creating user: {e}")
            print(f"Response: {e.response.text}")
            return False


if __name__ == "__main__":
    print("="*80)
    print("Firebase ID Token Generator for API Testing")
    print("="*80)
    print()
    
    # Check if API key is set
    if FIREBASE_WEB_API_KEY == "YOUR_FIREBASE_WEB_API_KEY_HERE":
        print("⚠️  Please update FIREBASE_WEB_API_KEY in this script")
        print("\nHow to get your Firebase Web API Key:")
        print("1. Go to Firebase Console: https://console.firebase.google.com")
        print("2. Select your project")
        print("3. Go to Project Settings (gear icon) > General")
        print("4. Scroll down to 'Your apps' section")
        print("5. Find 'Web API Key' and copy it")
        print("\nThen update this script and run again.")
        sys.exit(1)
    
    # Try to get token
    print(f"Attempting to sign in as: {TEST_EMAIL}")
    print()
    
    token = get_firebase_token(TEST_EMAIL, TEST_PASSWORD, FIREBASE_WEB_API_KEY)
    
    if not token:
        print("\n⚠️  Sign-in failed. Would you like to create this test user? (y/n)")
        choice = input().lower()
        
        if choice == 'y':
            if create_test_user(TEST_EMAIL, TEST_PASSWORD, FIREBASE_WEB_API_KEY):
                print("\nTrying to sign in again...")
                token = get_firebase_token(TEST_EMAIL, TEST_PASSWORD, FIREBASE_WEB_API_KEY)
    
    if token:
        print("\n" + "="*80)
        print("USAGE EXAMPLES")
        print("="*80)
        print("\n1. Using curl:")
        print(f'''
curl -X GET "https://mvh38xybk8.us-east-1.awsapprunner.com/api/questions/metadata" \\
  -H "Authorization: Bearer {token[:50]}..." \\
  -H "Content-Type: application/json"
        ''')
        
        print("\n2. Using PowerShell:")
        print(f'''
$headers = @{{
    "Authorization" = "Bearer {token[:50]}..."
    "Content-Type" = "application/json"
}}
Invoke-RestMethod -Uri "https://mvh38xybk8.us-east-1.awsapprunner.com/api/questions/metadata" -Method Get -Headers $headers
        ''')
        
        print("\n3. In Postman:")
        print("   - Set Authorization Type: Bearer Token")
        print(f"   - Token: {token[:50]}...")
        print("   - Or use Header: Authorization: Bearer <token>")
