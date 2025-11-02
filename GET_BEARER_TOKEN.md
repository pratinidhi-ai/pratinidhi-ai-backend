# How to Get Your Firebase Bearer Token

## Your API Base URL
```
https://mvh38xybk8.us-east-1.awsapprunner.com
```

## What Token Do You Need?

Your API uses **Firebase Authentication**. You need a **Firebase ID Token** (not an API key!).

---

## Method 1: Using the Python Script (Recommended)

### Step 1: Get Your Firebase Web API Key

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project (pratinidhi-ai or educado-ai)
3. Click the gear icon ⚙️ > **Project Settings**
4. Scroll down to **"Your apps"** section
5. Find **"Web API Key"** and copy it
   - It looks like: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

### Step 2: Update and Run the Script

1. Open `testing/get_firebase_token.py`
2. Update line 16:
   ```python
   FIREBASE_WEB_API_KEY = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Your actual key
   ```
3. Update test user credentials (lines 19-20):
   ```python
   TEST_EMAIL = "your-test-user@example.com"
   TEST_PASSWORD = "your-test-password"
   ```
4. Run:
   ```powershell
   python .\testing\get_firebase_token.py
   ```

The script will:
- Sign in with the test user
- Print the ID token
- Save it to `testing/test_token.txt`
- Show example curl/PowerShell commands

---

## Method 2: Using Firebase Console (Manual)

If you don't have a test user or want to use the Firebase emulator:

1. Go to Firebase Console > Authentication > Users
2. Create a test user if needed
3. Use a Firebase SDK or REST API to sign in:

```bash
curl -X POST "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=YOUR_WEB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "returnSecureToken": true
  }'
```

The response will contain:
```json
{
  "idToken": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ij...",  ← Use this as Bearer token
  "refreshToken": "...",
  "expiresIn": "3600"
}
```

---

## Method 3: Using Postman (Sign In First)

### Step 1: Create a Sign-In Request

1. Create a POST request in Postman
2. URL: `https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=YOUR_WEB_API_KEY`
3. Body (raw JSON):
   ```json
   {
     "email": "test@example.com",
     "password": "testpassword123",
     "returnSecureToken": true
   }
   ```
4. Send → Copy the `idToken` from response

### Step 2: Use Token in Your API Requests

1. In your Question Bank API requests
2. Authorization tab:
   - Type: **Bearer Token**
   - Token: paste the `idToken`
3. Or add Header:
   - Key: `Authorization`
   - Value: `Bearer <idToken>`

---

## Method 4: Using Your Frontend/Mobile App

If you have a web or mobile app that uses Firebase Auth:

1. Sign in a user through your app
2. Get the ID token:

**JavaScript (Web):**
```javascript
import { getAuth } from "firebase/auth";

const auth = getAuth();
const user = auth.currentUser;
if (user) {
  user.getIdToken().then((token) => {
    console.log("ID Token:", token);
    // Use this token in your API calls
  });
}
```

**React Native:**
```javascript
import auth from '@react-native-firebase/auth';

const user = auth().currentUser;
if (user) {
  const token = await user.getIdToken();
  console.log('ID Token:', token);
}
```

---

## Quick Test Commands

Once you have your token, test the APIs:

### Test Metadata API

**PowerShell:**
```powershell
$token = "YOUR_ID_TOKEN_HERE"
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

Invoke-RestMethod -Uri "https://mvh38xybk8.us-east-1.awsapprunner.com/api/questions/metadata" `
    -Method Get `
    -Headers $headers
```

**curl:**
```bash
curl -X GET "https://mvh38xybk8.us-east-1.awsapprunner.com/api/questions/metadata" \
  -H "Authorization: Bearer YOUR_ID_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

### Test Fetch Quiz API

**PowerShell:**
```powershell
$token = "YOUR_ID_TOKEN_HERE"
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}
$body = @{
    subject_name = "math"
    sub_category = "algebra"
    selected_difficulty_level = 3
    number_of_questions = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://mvh38xybk8.us-east-1.awsapprunner.com/api/questions/fetch-quiz" `
    -Method Post `
    -Headers $headers `
    -Body $body
```

---

## Token Expiration

Firebase ID tokens expire after **1 hour** (3600 seconds).

When expired, you'll get:
```json
{
  "error": "The provided token has expired"
}
```

To get a new token:
- **Option 1:** Run the Python script again
- **Option 2:** Use the refresh token (if you saved it)

**Refresh Token API:**
```bash
curl -X POST "https://securetoken.googleapis.com/v1/token?key=YOUR_WEB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "refresh_token",
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

---

## Troubleshooting

### Error: "Missing or invalid token"
- Check that you're using `Bearer ` (with a space) before the token
- Verify the token is not expired
- Make sure you're using the ID token, not the API key

### Error: "The provided token is invalid"
- Token might be malformed or from wrong Firebase project
- Check that the Firebase project in your code matches the one the token was issued from
- Verify the service account key (`educado-ai-private-key.json`) is for the correct project

### Error: "The provided token has expired"
- Get a new token (tokens expire after 1 hour)
- Run the Python script again or use the refresh token

---

## Next Steps

1. **Get your Firebase Web API Key** from Firebase Console
2. **Run the token script:** `python .\testing\get_firebase_token.py`
3. **Copy the ID token** from the output
4. **Test in Postman** or use PowerShell commands above
5. **Token will be saved** to `testing/test_token.txt` for reuse

Need help? Check which Firebase project you're using and verify you have a test user created in Authentication > Users.
