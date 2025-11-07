# API Testing Commands

## Prerequisites
Replace `YOUR_TOKEN` with your actual authentication token.
Replace `http://localhost:8080` with your actual API URL if different.

---

## 1. Test Metadata API

### Using curl (Bash/PowerShell)
```bash
curl -X GET "http://localhost:8080/api/questions/metadata" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### Using PowerShell
```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_TOKEN"
    "Content-Type" = "application/json"
}

Invoke-RestMethod -Uri "http://localhost:8080/api/questions/metadata" `
    -Method Get `
    -Headers $headers | ConvertTo-Json -Depth 10
```

### Expected Response:
```json
{
  "success": true,
  "total_categories": 7,
  "metadata": {
    "math|algebra": { ... },
    ...
  }
}
```

---

## 2. Test Fetch Quiz API (Without Theme)

### Using curl
```bash
curl -X POST "http://localhost:8080/api/questions/fetch-quiz" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_name": "math",
    "sub_category": "algebra",
    "selected_difficulty_level": 3,
    "number_of_questions": 5
  }'
```

### Using PowerShell
```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_TOKEN"
    "Content-Type" = "application/json"
}

$body = @{
    subject_name = "math"
    sub_category = "algebra"
    selected_difficulty_level = 3
    number_of_questions = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/api/questions/fetch-quiz" `
    -Method Post `
    -Headers $headers `
    -Body $body | ConvertTo-Json -Depth 10
```

---

## 3. Test Fetch Quiz API (With Theme)

### Using curl
```bash
curl -X POST "http://localhost:8080/api/questions/fetch-quiz" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_name": "math",
    "sub_category": "algebra",
    "selected_difficulty_level": 2,
    "number_of_questions": 3,
    "theme": "Harry Potter"
  }'
```

### Using PowerShell
```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_TOKEN"
    "Content-Type" = "application/json"
}

$body = @{
    subject_name = "math"
    sub_category = "algebra"
    selected_difficulty_level = 2
    number_of_questions = 3
    theme = "Harry Potter"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/api/questions/fetch-quiz" `
    -Method Post `
    -Headers $headers `
    -Body $body | ConvertTo-Json -Depth 10
```

---

## 4. Test Different Categories

### Math - Advanced Math
```bash
curl -X POST "http://localhost:8080/api/questions/fetch-quiz" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_name": "math",
    "sub_category": "advanced-math",
    "selected_difficulty_level": 4,
    "number_of_questions": 10
  }'
```

### Reading and Writing - Craft and Structure
```bash
curl -X POST "http://localhost:8080/api/questions/fetch-quiz" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_name": "reading-and-writing",
    "sub_category": "craft-and-structure",
    "selected_difficulty_level": 3,
    "number_of_questions": 5,
    "theme": "Shakespearean Literature"
  }'
```

---

## 5. Test Error Cases

### Missing Required Parameter
```bash
curl -X POST "http://localhost:8080/api/questions/fetch-quiz" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_name": "math",
    "selected_difficulty_level": 3
  }'
```

Expected: 400 Bad Request with missing parameters list

### Invalid Difficulty Level
```bash
curl -X POST "http://localhost:8080/api/questions/fetch-quiz" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_name": "math",
    "sub_category": "algebra",
    "selected_difficulty_level": 10,
    "number_of_questions": 5
  }'
```

Expected: 400 Bad Request - difficulty must be 1-5

### Invalid Number of Questions
```bash
curl -X POST "http://localhost:8080/api/questions/fetch-quiz" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_name": "math",
    "sub_category": "algebra",
    "selected_difficulty_level": 3,
    "number_of_questions": -5
  }'
```

Expected: 400 Bad Request - must be positive integer

---

## Quick Test Script (PowerShell)

Save this as `test-question-apis.ps1`:

```powershell
# Configuration
$baseUrl = "http://localhost:8080"
$token = "YOUR_TOKEN_HERE"

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

Write-Host "Testing Question Bank APIs..." -ForegroundColor Cyan
Write-Host ""

# Test 1: Get Metadata
Write-Host "Test 1: Get Metadata" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/questions/metadata" `
        -Method Get `
        -Headers $headers
    Write-Host "✅ Success! Found $($response.total_categories) categories" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 2: Fetch Quiz (No Theme)
Write-Host "Test 2: Fetch Quiz (No Theme)" -ForegroundColor Yellow
$body = @{
    subject_name = "math"
    sub_category = "algebra"
    selected_difficulty_level = 3
    number_of_questions = 5
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/questions/fetch-quiz" `
        -Method Post `
        -Headers $headers `
        -Body $body
    Write-Host "✅ Success! Fetched $($response.count) questions" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 3: Fetch Quiz (With Theme)
Write-Host "Test 3: Fetch Quiz (With Theme)" -ForegroundColor Yellow
$body = @{
    subject_name = "math"
    sub_category = "algebra"
    selected_difficulty_level = 2
    number_of_questions = 3
    theme = "Harry Potter"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/questions/fetch-quiz" `
        -Method Post `
        -Headers $headers `
        -Body $body
    Write-Host "✅ Success! Fetched $($response.count) themed questions" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Testing Complete!" -ForegroundColor Cyan
```

Run with:
```powershell
.\test-question-apis.ps1
```

---

## Available Test Values

### Subjects
- `math`
- `reading-and-writing`

### Math Subcategories
- `algebra`
- `advanced-math`
- `problem-solving-and-data-analysis`

### Reading and Writing Subcategories
- `craft-and-structure`
- `expression-of-ideas`
- `information-and-ideas`
- `standard-english-conventions`

### Difficulty Levels
- `1` - Easiest
- `2` - Easy
- `3` - Medium
- `4` - Hard
- `5` - Hardest

### Themes (Examples)
- `Harry Potter`
- `Science Fiction`
- `Famous Scientists`
- `Ivy League`
- `Shakespearean Literature`
- `anime`

Note: Not all themes are available in all categories. Check metadata for available themes per category.
