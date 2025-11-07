# Quick Start - Testing Your Deployed APIs

## 🚀 Your API is Live!

**Base URL:** `https://mvh38xybk8.us-east-1.awsapprunner.com`

---

## Step 1: Get Your Firebase Token (3 minutes)

### Option A: Use the Python Script (Easiest)

1. **Get Firebase Web API Key:**
   - Go to [Firebase Console](https://console.firebase.google.com)
   - Select your project
   - Settings (⚙️) > Project Settings > General
   - Copy the **Web API Key**

2. **Update and run the script:**
   ```powershell
   # Edit testing/get_firebase_token.py
   # Update line 16 with your Web API Key
   # Update lines 19-20 with test user credentials
   
   python .\testing\get_firebase_token.py
   ```

3. **Copy the ID token** from output or from `testing/test_token.txt`

### Option B: Get Token via API

```powershell
$apiKey = "YOUR_FIREBASE_WEB_API_KEY"
$body = @{
    email = "test@example.com"
    password = "testpassword123"
    returnSecureToken = $true
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=$apiKey" -Method Post -Body $body -ContentType "application/json"
$token = $response.idToken
Write-Host "Token: $token"
```

---

## Step 2: Test with Postman (2 minutes)

### Import the Collection

1. Open Postman
2. **Import** → **File** → Select `postman/Question_Bank_API.postman_collection.json`
3. The collection will have 6 requests pre-configured

### Set Your Token

In the collection variables (or create an environment):
- `base_url` = `https://mvh38xybk8.us-east-1.awsapprunner.com` ✅ (already set)
- `firebase_token` = Paste your ID token from Step 1

### Run Requests

1. **Get Metadata** - See all question categories
2. **Fetch Quiz - No Theme** - Get 5 math algebra questions
3. **Fetch Quiz - With Theme** - Get themed questions
4. **Test error cases** - See validation in action

---

## Step 3: Test with PowerShell (30 seconds)

Replace `YOUR_TOKEN` with your Firebase ID token:

```powershell
$token = "YOUR_TOKEN_HERE"
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Test Metadata
Invoke-RestMethod -Uri "https://mvh38xybk8.us-east-1.awsapprunner.com/api/questions/metadata" -Method Get -Headers $headers

# Test Fetch Quiz
$body = @{
    subject_name = "math"
    sub_category = "algebra"
    selected_difficulty_level = 3
    number_of_questions = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://mvh38xybk8.us-east-1.awsapprunner.com/api/questions/fetch-quiz" -Method Post -Headers $headers -Body $body
```

---

## What You Should See

### Metadata Response (200 OK)
```json
{
  "success": true,
  "total_categories": 7,
  "metadata": {
    "math|algebra": {
      "total_questions": 1948,
      "difficulty_distribution": {...},
      "theme_distribution": {...}
    },
    ...
  }
}
```

### Fetch Quiz Response (200 OK)
```json
{
  "success": true,
  "count": 5,
  "filters": {
    "subject_name": "math",
    "sub_category": "algebra",
    "difficulty_level": 3,
    "requested_count": 5
  },
  "questions": [
    {
      "id": "doc_id_here",
      "question_id": "unique_id",
      "question_text": "...",
      "options": [...],
      "correct_answer": "...",
      ...
    }
  ]
}
```

---

## Common Issues

### ❌ "Missing or invalid token"
- Make sure you're using `Bearer ` (with space) before token
- Check token hasn't expired (1 hour lifetime)

### ❌ "The provided token is invalid"
- Verify you're using the Firebase project that matches your service account
- Token must be from same Firebase project as `educado-ai-private-key.json`

### ❌ Connection errors
- Verify App Runner service is running:
  ```powershell
  aws apprunner describe-service --service-arn "arn:aws:apprunner:us-east-1:613820096948:service/Backend-AppRunner/20c56a0386754f7b8d196151179e2566" --region us-east-1 --query "Service.Status"
  ```
- Should return "RUNNING"

---

## Files Created for You

✅ `GET_BEARER_TOKEN.md` - Complete guide on getting Firebase tokens  
✅ `testing/get_firebase_token.py` - Automated token generator script  
✅ `postman/Question_Bank_API.postman_collection.json` - Ready-to-import Postman collection  
✅ `API_TEST_COMMANDS.md` - All test commands (curl, PowerShell, Postman)  
✅ `QUESTION_BANK_API.md` - Complete API documentation  

---

## Next Steps

1. ✅ Get your Firebase token (see Step 1)
2. ✅ Import Postman collection and test (see Step 2)
3. ✅ Run all 6 requests in the collection
4. ✅ Check that metadata returns 7 categories
5. ✅ Check that fetch-quiz returns randomized questions
6. ✅ Test with different themes and subjects

**Happy Testing! 🎉**
