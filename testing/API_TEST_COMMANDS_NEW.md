# API Test Commands - Copy & Paste

Replace these variables before running:
- `{USER_ID}` - Your test user ID
- `{TOKEN}` - Firebase authentication token (get from `testing/get_firebase_token.py`)
- `{TASK_ID}` - Task ID to complete
- `{CHAPTER_ID}` - Chapter ID (e.g., "chapter_1")

---

## PowerShell Commands (Windows)

### 1. Get Tasks (Incomplete Only - Default)
```powershell
$userId = "test_user_123"
$token = "YOUR_FIREBASE_TOKEN"

Invoke-RestMethod -Uri "http://localhost:8000/api/tasks/user/$userId/tasks" `
  -Method GET `
  -Headers @{"Authorization"="Bearer $token"}
```

### 2. Get ALL Tasks (Include Completed)
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/tasks/user/$userId/tasks?include_completed=true" `
  -Method GET `
  -Headers @{"Authorization"="Bearer $token"}
```

### 3. Complete a Task
```powershell
$body = @{
  user_id = $userId
  task_id = "task_123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/tasks/complete" `
  -Method POST `
  -Headers @{
    "Authorization"="Bearer $token"
    "Content-Type"="application/json"
  } `
  -Body $body
```

### 4. Complete a Quiz Task (With Score)
```powershell
$body = @{
  user_id = $userId
  task_id = "task_123"
  score = 8
  num_questions = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/tasks/complete" `
  -Method POST `
  -Headers @{
    "Authorization"="Bearer $token"
    "Content-Type"="application/json"
  } `
  -Body $body
```

### 5. Get Tutor Analytics
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/tutor/$userId/analytics" `
  -Method GET `
  -Headers @{"Authorization"="Bearer $token"}
```

### 6. Get All Chapter Progress
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/tutor/$userId/chapter-progress" `
  -Method GET `
  -Headers @{"Authorization"="Bearer $token"}
```

### 7. Get Specific Chapter Progress
```powershell
$chapterId = "chapter_1"

Invoke-RestMethod -Uri "http://localhost:8000/api/tutor/$userId/chapter-progress?chapter_id=$chapterId" `
  -Method GET `
  -Headers @{"Authorization"="Bearer $token"}
```

### 8. Pretty Print JSON Response
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/tutor/$userId/analytics" `
  -Method GET `
  -Headers @{"Authorization"="Bearer $token"} | ConvertTo-Json -Depth 10
```

---

## cURL Commands (Mac/Linux/Git Bash)

### 1. Get Tasks (Incomplete Only)
```bash
USER_ID="test_user_123"
TOKEN="YOUR_FIREBASE_TOKEN"

curl -X GET "http://localhost:8000/api/tasks/user/$USER_ID/tasks" \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Get ALL Tasks (Include Completed)
```bash
curl -X GET "http://localhost:8000/api/tasks/user/$USER_ID/tasks?include_completed=true" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Complete a Task
```bash
curl -X POST "http://localhost:8000/api/tasks/complete" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "'$USER_ID'",
    "task_id": "task_123"
  }'
```

### 4. Complete a Quiz Task (With Score)
```bash
curl -X POST "http://localhost:8000/api/tasks/complete" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "'$USER_ID'",
    "task_id": "task_123",
    "score": 8,
    "num_questions": 10
  }'
```

### 5. Get Tutor Analytics
```bash
curl -X GET "http://localhost:8000/api/tutor/$USER_ID/analytics" \
  -H "Authorization: Bearer $TOKEN"
```

### 6. Get All Chapter Progress
```bash
curl -X GET "http://localhost:8000/api/tutor/$USER_ID/chapter-progress" \
  -H "Authorization: Bearer $TOKEN"
```

### 7. Get Specific Chapter Progress
```bash
CHAPTER_ID="chapter_1"

curl -X GET "http://localhost:8000/api/tutor/$USER_ID/chapter-progress?chapter_id=$CHAPTER_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### 8. Pretty Print JSON (with jq)
```bash
curl -X GET "http://localhost:8000/api/tutor/$USER_ID/analytics" \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Postman Collection

### Setup Environment Variables
1. Create environment: `Pratinidhi Local`
2. Add variables:
   - `base_url`: `http://localhost:8000`
   - `user_id`: `test_user_123`
   - `token`: `YOUR_FIREBASE_TOKEN`

### Request 1: Get Incomplete Tasks
```
GET {{base_url}}/api/tasks/user/{{user_id}}/tasks
Headers:
  Authorization: Bearer {{token}}
```

### Request 2: Get All Tasks
```
GET {{base_url}}/api/tasks/user/{{user_id}}/tasks?include_completed=true
Headers:
  Authorization: Bearer {{token}}
```

### Request 3: Complete Task
```
POST {{base_url}}/api/tasks/complete
Headers:
  Authorization: Bearer {{token}}
  Content-Type: application/json
Body (raw JSON):
{
  "user_id": "{{user_id}}",
  "task_id": "task_123"
}
```

### Request 4: Complete Quiz Task
```
POST {{base_url}}/api/tasks/complete
Headers:
  Authorization: Bearer {{token}}
  Content-Type: application/json
Body (raw JSON):
{
  "user_id": "{{user_id}}",
  "task_id": "task_123",
  "score": 8,
  "num_questions": 10
}
```

### Request 5: Get Tutor Analytics
```
GET {{base_url}}/api/tutor/{{user_id}}/analytics
Headers:
  Authorization: Bearer {{token}}
```

### Request 6: Get All Chapter Progress
```
GET {{base_url}}/api/tutor/{{user_id}}/chapter-progress
Headers:
  Authorization: Bearer {{token}}
```

### Request 7: Get Specific Chapter Progress
```
GET {{base_url}}/api/tutor/{{user_id}}/chapter-progress?chapter_id=chapter_1
Headers:
  Authorization: Bearer {{token}}
```

---

## Get Firebase Token

Run this first to get your authentication token:

```powershell
cd testing
python get_firebase_token.py
```

Copy the token from the output and use it in the commands above.

---

## Example Test Flow

### Step 1: Get your token
```powershell
cd testing
python get_firebase_token.py
# Copy the token
```

### Step 2: Set variables
```powershell
$userId = "test_user_123"  # Replace with real user ID
$token = "eyJhbGc..."      # Paste token from step 1
```

### Step 3: Test incomplete tasks
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/tasks/user/$userId/tasks" `
  -Headers @{"Authorization"="Bearer $token"}
```

### Step 4: Test all tasks (with completed)
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/tasks/user/$userId/tasks?include_completed=true" `
  -Headers @{"Authorization"="Bearer $token"}
```

### Step 5: Test chapter progress
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/tutor/$userId/chapter-progress" `
  -Headers @{"Authorization"="Bearer $token"}
```

### Step 6: Complete a task
```powershell
$body = @{
  user_id = $userId
  task_id = "task_123"  # Replace with real task ID
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/tasks/complete" `
  -Method POST `
  -Headers @{
    "Authorization"="Bearer $token"
    "Content-Type"="application/json"
  } `
  -Body $body
```

---

## Expected Responses

### Get Tasks (Success)
```json
{
  "success": true,
  "tasks": [
    {
      "task_id": "task_123",
      "title": "Quiz: Math - Algebra",
      "is_completed": false,
      "task_number": 1
    }
  ],
  "count": 5
}
```

### Complete Task (Success)
```json
{
  "success": true,
  "completed": true,
  "message": "Task marked as completed",
  "next_tasks_assigned": 0
}
```

### Complete Last Task (Week Complete)
```json
{
  "success": true,
  "completed": true,
  "message": "Task marked as completed",
  "next_tasks_assigned": 12
}
```

### Tutor Analytics
```json
{
  "message": "Analytics retrieved successfully",
  "analytics": {
    "total_sessions": 12,
    "total_duration_minutes": 245.5,
    "average_duration_minutes": 20.46,
    "sessions_this_week": 5
  }
}
```

### Chapter Progress (All)
```json
{
  "message": "Progress retrieved for 3 chapters",
  "total_chapters": 3,
  "progress": {
    "chapters": {
      "chapter_1": {
        "total_sessions": 3,
        "completed_sessions": 3,
        "total_duration_minutes": 45.5
      }
    }
  }
}
```

---

## Error Responses

### 401 Unauthorized (Invalid Token)
```json
{
  "detail": "Unauthorized"
}
```

### 404 Not Found (User Doesn't Exist)
```json
{
  "error": "User not found"
}
```

### Task Validation Failed
```json
{
  "success": true,
  "completed": false,
  "message": "Please complete at least one AI Tutor session for this chapter before marking this task as done."
}
```

---

## Production URLs

Replace `http://localhost:8000` with your production URL:

```powershell
# Production
$baseUrl = "https://api.yourdomain.com"
Invoke-RestMethod -Uri "$baseUrl/api/tasks/user/$userId/tasks" `
  -Headers @{"Authorization"="Bearer $token"}
```
