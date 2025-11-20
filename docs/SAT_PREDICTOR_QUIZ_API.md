# SAT Predictor Quiz API

## Overview
The SAT Predictor Quiz API provides a curated mix of 24 questions designed to assess student performance across different SAT topics and difficulty levels.

## Endpoint

### GET `/api/questions/sat_predictor_quiz`

Returns a specially composed quiz with questions from various categories and difficulty levels.

**Authentication:** Required (Bearer token)

## Response Format

```json
{
  "success": true,
  "questions": [
    {
      "id": "question_doc_id",
      "question_id": "q_20251116_042834_0470",
      "question_text": "...",
      "options": [...],
      "correct_option": "C",
      "explanation": "...",
      "hint": "...",
      "subject": "math",
      "sub_category": "algebra",
      "question_difficulty_level": 5,
      "theme": "Famous Scientists",
      "tags": ["tag1", "tag2"]
    },
    // ... 23 more questions
  ],
  "count": 24,
  "composition": [
    {
      "subject": "math",
      "subcategory": "algebra",
      "difficulty_level": 5,
      "requested": 3,
      "fetched": 3
    },
    // ... composition for all 14 categories
  ]
}
```

**Note:** The response has been optimized to exclude unnecessary metadata fields like `question_exam`, `math_validation_result`, `validation_results`, `created_at`, `random_value`, `updated_at`, `is_correct`, `question_standard`, and `llm_model_used` to reduce payload size.

## Quiz Composition

The quiz consists of 24 questions with the following breakdown:

### Math Questions (12 total)
**High Difficulty (Level 5) - 8 questions:**
- 3 questions: `math|algebra` (difficulty 5)
- 3 questions: `math|advanced_math` (difficulty 5)
- 2 questions: `math|problem_solving` (difficulty 5)

**Low Difficulty (Level 1) - 4 questions:**
- 2 questions: `math|algebra` (difficulty 1)
- 1 question: `math|advanced_math` (difficulty 1)
- 1 question: `math|problem_solving` (difficulty 1)

### Reading & Writing Questions (12 total)
**High Difficulty (Level 5) - 8 questions:**
- 2 questions: `reading-and-writing|craft-and-structure` (difficulty 5)
- 2 questions: `reading-and-writing|expression-of-ideas` (difficulty 5)
- 2 questions: `reading-and-writing|information-and-ideas` (difficulty 5)
- 2 questions: `reading-and-writing|standard-english-conventions` (difficulty 5)

**Low Difficulty (Level 1) - 4 questions:**
- 1 question: `reading-and-writing|craft-and-structure` (difficulty 1)
- 1 question: `reading-and-writing|expression-of-ideas` (difficulty 1)
- 1 question: `reading-and-writing|information-and-ideas` (difficulty 1)
- 1 question: `reading-and-writing|standard-english-conventions` (difficulty 1)

## Testing

### Using cURL

```bash
# Get your bearer token first (see GET_BEARER_TOKEN.md)
export TOKEN="your_bearer_token_here"

# Fetch SAT Predictor Quiz
curl -X GET "http://localhost:8000/api/questions/sat_predictor_quiz" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

### Using PowerShell

```powershell
# Set your bearer token
$TOKEN = "your_bearer_token_here"

# Fetch SAT Predictor Quiz
$headers = @{
    "Authorization" = "Bearer $TOKEN"
    "Content-Type" = "application/json"
}

Invoke-RestMethod -Uri "http://localhost:8000/api/questions/sat_predictor_quiz" `
    -Method Get `
    -Headers $headers
```

### Using Python

```python
import requests

TOKEN = "your_bearer_token_here"
BASE_URL = "http://localhost:8000"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Fetch SAT Predictor Quiz
response = requests.get(
    f"{BASE_URL}/api/questions/sat_predictor_quiz",
    headers=headers
)

quiz_data = response.json()
print(f"Success: {quiz_data['success']}")
print(f"Total questions: {quiz_data['count']}")
print(f"Composition: {quiz_data['composition']}")
```

## Features

1. **Randomized Selection**: Questions are randomly selected from each category on every request
2. **Shuffled Order**: All questions are shuffled after selection for unpredictable ordering
3. **Balanced Difficulty**: Mix of high (level 5) and low (level 1) difficulty questions
4. **Comprehensive Coverage**: Covers all major SAT topics in both Math and Reading & Writing
5. **Composition Tracking**: Response includes details about how many questions were fetched from each category

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Invalid or missing authentication token"
}
```

### 404 Not Found
```json
{
  "success": false,
  "message": "No questions found for SAT predictor quiz",
  "questions": [],
  "count": 0,
  "composition": [...]
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to generate SAT predictor quiz",
  "message": "Error details..."
}
```

## Notes

- Questions are fetched from the Firestore `question_bank` collection
- The endpoint requires authentication via Bearer token
- Questions are returned in the same format as the `/api/questions/fetch-quiz` endpoint
- The quiz composition is fixed but questions are randomly selected each time
- If fewer questions are available than requested for a category, the API will return as many as possible
- All datetime fields are converted to ISO format strings for JSON serialization
