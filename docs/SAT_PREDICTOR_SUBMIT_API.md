# SAT Predictor Submit API

## Overview
The SAT Predictor Submit API processes completed SAT predictor quiz submissions, calculates SAT scores, provides detailed analytics, and stores performance data for tracking progress over time.

## Endpoint

### POST `/api/analytics/sat_predictor_submit`

Submits SAT predictor quiz results with 24 questions (12 math + 12 reading & writing).

**Authentication:** Required (Bearer token)

**Status Code:** 202 Accepted (asynchronous processing)

## Request Format

```json
{
  "student_id": "user123",
  "time_spent": 1800,
  "math_correct": 9,
  "math_total": 12,
  "math_questions": [
    {
      "id": "q_doc_id_1",
      "question_id": "q_20251116_042834_0470",
      "subject": "math",
      "sub_category": "algebra",
      "difficulty_level": 5,
      "tags": ["linear-equations", "word-problems"],
      "is_correct": true
    },
    // ... 11 more math questions
  ],
  "rw_correct": 10,
  "rw_total": 12,
  "rw_questions": [
    {
      "id": "q_doc_id_13",
      "question_id": "q_20251116_042834_0471",
      "subject": "reading-and-writing",
      "sub_category": "craft-and-structure",
      "difficulty_level": 5,
      "tags": ["text-structure", "purpose"],
      "is_correct": true
    },
    // ... 11 more R&W questions
  ]
}
```

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_id` | string | Yes | User ID submitting the quiz |
| `time_spent` | integer | Yes | Total time spent in seconds |
| `math_correct` | integer | Yes | Number of correct math answers (0-12) |
| `math_total` | integer | Yes | Total math questions (must be 12) |
| `math_questions` | array | Yes | Array of 12 math question objects |
| `rw_correct` | integer | Yes | Number of correct R&W answers (0-12) |
| `rw_total` | integer | Yes | Total R&W questions (must be 12) |
| `rw_questions` | array | Yes | Array of 12 R&W question objects |

### Question Object Structure

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Firestore document ID |
| `question_id` | string | Original question ID |
| `subject` | string | Subject (math or reading-and-writing) |
| `sub_category` | string | Subcategory (algebra, craft-and-structure, etc.) |
| `difficulty_level` | integer | Difficulty level (1-5) |
| `tags` | array | Array of tag strings |
| `is_correct` | boolean | Whether the answer was correct |

## Response Format

### Immediate (Synchronous) Response

```json
{
  "success": true,
  "message": "SAT Predictor submission received and is being processed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "scores": {
    "math_score": 650,
    "math_accuracy": 75.0,
    "rw_score": 700,
    "rw_accuracy": 83.33,
    "total_sat_score": 1350,
    "time_bonus_points": 20
  },
  "section_breakdown": {
    "math": {
      "correct": 9,
      "total": 12,
      "score": 650
    },
    "reading_and_writing": {
      "correct": 10,
      "total": 12,
      "score": 700
    }
  },
  "time_info": {
    "time_spent_seconds": 840,
    "target_time_seconds": 900,
    "time_bonus_points": 20,
    "max_time_bonus": 40
  },
  "analytics": {
    "math": {
      "algebra": {
        "total_questions": 5,
        "correct_answers": 4,
        "accuracy": 80.0,
        "tags": {
          "linear-equations": {
            "total_questions": 3,
            "correct_answers": 2,
            "accuracy": 66.67
          },
          "quadratic-equations": {
            "total_questions": 2,
            "correct_answers": 2,
            "accuracy": 100.0
          }
        }
      },
      "advanced_math": {
        "total_questions": 4,
        "correct_answers": 3,
        "accuracy": 75.0,
        "tags": {
          // ... tag-level breakdown
        }
      },
      "problem_solving": {
        "total_questions": 3,
        "correct_answers": 2,
        "accuracy": 66.67,
        "tags": {
          // ... tag-level breakdown
        }
      }
    },
    "reading-and-writing": {
      "craft-and-structure": {
        "total_questions": 3,
        "correct_answers": 3,
        "accuracy": 100.0,
        "tags": {
          // ... tag-level breakdown
        }
      },
      // ... other R&W subcategories
    }
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether submission was accepted |
| `message` | string | Status message |
| `request_id` | string | Unique ID for tracking this submission |
| `scores` | object | SAT score calculations |
| `scores.math_score` | integer | Math section score (200-800) |
| `scores.math_accuracy` | float | Math accuracy percentage |
| `scores.rw_score` | integer | R&W section score (200-800) |
| `scores.rw_accuracy` | float | R&W accuracy percentage |
| `scores.total_sat_score` | integer | Total SAT score (400-1600) |
| `scores.time_bonus_points` | integer | Bonus points earned from time (0-40) |
| `section_breakdown` | object | Per-section summary |
| `time_info` | object | Time-related information |
| `time_info.time_spent_seconds` | integer | Actual time spent |
| `time_info.target_time_seconds` | integer | Target time (900 seconds) |
| `time_info.time_bonus_points` | integer | Bonus points from time |
| `time_info.max_time_bonus` | integer | Maximum possible time bonus (40) |
| `analytics` | object | Detailed performance by subject/subcategory/tag |

## SAT Score Calculation

### Scoring Formula

The API uses a sophisticated scoring system that considers both question difficulty and completion time:

#### Base Points from Questions
- **Difficulty 5 questions:** 65 points each
- **Difficulty 4 questions:** 52.5 points each
- **Difficulty 3 questions:** 40 points each
- **Difficulty 2 questions:** 27.5 points each
- **Difficulty 1 questions:** 15 points each

Formula: `points = 15 + ((difficulty - 1) / 4) × 50`

#### Time Bonus
- **Target time:** 900 seconds (15 minutes)
- **Bonus calculation:** 1 point for every 3 seconds saved
- **Maximum bonus:** 40 points

Formula: `time_bonus = min(40, (900 - time_spent) // 3)` (if time_spent < 900)

#### Final Score Calculation

1. **Calculate base score:** Sum of points from all correct answers based on difficulty
2. **Add time bonus:** If completed under 15 minutes
3. **Scale to SAT range:** Map total points to 200-800 scale

```
max_base_score = 12 questions × 65 points = 780 points
max_total_score = 780 + 40 (time bonus) = 820 points

scaled_score = 200 + (total_score / 820) × 600
final_score = min(800, max(200, scaled_score))
```

### Score Ranges
- **Minimum Score:** 200 per section, 400 total
- **Maximum Score:** 800 per section, 1600 total

### Scoring Examples

#### Example 1: Perfect Score with Time Bonus
- **Math:** 12 correct (all difficulty 5) = 780 points
- **R&W:** 12 correct (all difficulty 5) = 780 points
- **Time:** 780 seconds (2 minutes saved) = 40 points bonus
- **Math Score:** 200 + (820/820) × 600 = **800**
- **R&W Score:** 200 + (820/820) × 600 = **800**
- **Total:** **1600**

#### Example 2: Mixed Difficulty, Good Time
- **Math:** 9 correct (6 diff 5, 3 diff 1) = 6×65 + 3×15 = 435 points
- **R&W:** 10 correct (7 diff 5, 3 diff 1) = 7×65 + 3×15 = 500 points
- **Time:** 840 seconds (1 min saved) = 20 points bonus
- **Math Score:** 200 + (455/820) × 600 = **533**
- **R&W Score:** 200 + (520/820) × 600 = **580**
- **Total:** **1113**

#### Example 3: All Correct, Overtime
- **Math:** 12 correct (all difficulty 5) = 780 points
- **R&W:** 12 correct (all difficulty 5) = 780 points
- **Time:** 960 seconds (over time limit) = 0 bonus
- **Math Score:** 200 + (780/820) × 600 = **771**
- **R&W Score:** 200 + (780/820) × 600 = **771**
- **Total:** **1542**

#### Example 4: Low Score
- **Math:** 3 correct (all difficulty 1) = 45 points
- **R&W:** 4 correct (all difficulty 1) = 60 points
- **Time:** 1000 seconds (over time) = 0 bonus
- **Math Score:** 200 + (45/820) × 600 = **233**
- **R&W Score:** 200 + (60/820) × 600 = **244**
- **Total:** **477**

## Background Processing

After returning the immediate response, the API performs the following operations asynchronously:

### 1. Store SAT Predictor Performance
**Location:** `users/{student_id}/sat_predictor_performance/{session_id}`

Stores complete test performance including:
- All questions and answers
- Calculated scores
- Timestamp
- Performance metrics

### 2. Update Analytics

Updates multiple analytics collections:

#### Performance Summary
**Location:** `users/{student_id}/analytics/performance_summary`

Updates aggregated statistics at:
- Subject level (math, reading-and-writing)
- Subcategory level (algebra, craft-and-structure, etc.)
- Tag level (individual skill tags)

#### Activity Logs
**Location:** `users/{student_id}/activity_logs/{session_id}_{subject}_{subcategory}`

Creates activity log entries for each subcategory tested.

#### Correct Questions
**Location:** `users/{student_id}/analytics/correct_questions`

Tracks all correctly answered question IDs by subject/subcategory.

#### Incorrect Questions
**Location:** `users/{student_id}/analytics/incorrect_questions`

Tracks all incorrectly answered question IDs by subject/subcategory.

#### Last 15 Math Questions
**Location:** `users/{student_id}/analytics/last_15_math_questions`

Updates the last 15 math questions attempted (if applicable).

## Testing

### Using cURL

```bash
# Get your bearer token first
export TOKEN="your_bearer_token_here"

# Submit SAT predictor quiz
curl -X POST "http://localhost:8000/api/analytics/sat_predictor_submit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "user123",
    "time_spent": 1800,
    "math_correct": 9,
    "math_total": 12,
    "math_questions": [
      {
        "id": "q_doc_1",
        "question_id": "q_20251116_042834_0470",
        "subject": "math",
        "sub_category": "algebra",
        "difficulty_level": 5,
        "tags": ["linear-equations"],
        "is_correct": true
      }
      // ... more questions
    ],
    "rw_correct": 10,
    "rw_total": 12,
    "rw_questions": [
      {
        "id": "q_doc_13",
        "question_id": "q_20251116_042834_0471",
        "subject": "reading-and-writing",
        "sub_category": "craft-and-structure",
        "difficulty_level": 5,
        "tags": ["text-structure"],
        "is_correct": true
      }
      // ... more questions
    ]
  }'
```

### Using PowerShell

```powershell
$TOKEN = "your_bearer_token_here"

$body = @{
    student_id = "user123"
    time_spent = 1800
    math_correct = 9
    math_total = 12
    math_questions = @(
        @{
            id = "q_doc_1"
            question_id = "q_20251116_042834_0470"
            subject = "math"
            sub_category = "algebra"
            difficulty_level = 5
            tags = @("linear-equations")
            is_correct = $true
        }
        # ... more questions
    )
    rw_correct = 10
    rw_total = 12
    rw_questions = @(
        @{
            id = "q_doc_13"
            question_id = "q_20251116_042834_0471"
            subject = "reading-and-writing"
            sub_category = "craft-and-structure"
            difficulty_level = 5
            tags = @("text-structure")
            is_correct = $true
        }
        # ... more questions
    )
} | ConvertTo-Json -Depth 10

$headers = @{
    "Authorization" = "Bearer $TOKEN"
    "Content-Type" = "application/json"
}

Invoke-RestMethod -Uri "http://localhost:8000/api/analytics/sat_predictor_submit" `
    -Method Post `
    -Headers $headers `
    -Body $body
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

# Prepare submission data
submission = {
    "student_id": "user123",
    "time_spent": 1800,
    "math_correct": 9,
    "math_total": 12,
    "math_questions": [
        {
            "id": "q_doc_1",
            "question_id": "q_20251116_042834_0470",
            "subject": "math",
            "sub_category": "algebra",
            "difficulty_level": 5,
            "tags": ["linear-equations"],
            "is_correct": True
        }
        # ... more questions (12 total)
    ],
    "rw_correct": 10,
    "rw_total": 12,
    "rw_questions": [
        {
            "id": "q_doc_13",
            "question_id": "q_20251116_042834_0471",
            "subject": "reading-and-writing",
            "sub_category": "craft-and-structure",
            "difficulty_level": 5,
            "tags": ["text-structure"],
            "is_correct": True
        }
        # ... more questions (12 total)
    ]
}

# Submit SAT predictor quiz
response = requests.post(
    f"{BASE_URL}/api/analytics/sat_predictor_submit",
    headers=headers,
    json=submission
)

result = response.json()
print(f"Success: {result['success']}")
print(f"Request ID: {result['request_id']}")
print(f"Total SAT Score: {result['scores']['total_sat_score']}")
print(f"Math Score: {result['scores']['math_score']}")
print(f"R&W Score: {result['scores']['rw_score']}")
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

Common validation errors:
- Math total must be exactly 12
- R&W total must be exactly 12
- Correct answers cannot exceed total questions
- Required fields missing

### 401 Unauthorized
```json
{
  "detail": "Invalid or missing authentication token"
}
```

### 404 Not Found
```json
{
  "detail": "Student with ID {student_id} does not exist"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error message details"
}
```

## Related Endpoints

- **GET `/api/questions/sat_predictor_quiz`** - Fetch SAT predictor quiz questions
- **GET `/api/analytics/performance-summary/{student_id}`** - Get overall performance summary
- **POST `/api/analytics/submit-quiz`** - Submit regular practice quiz

## Database Schema

### SAT Predictor Performance Document
```
users/{student_id}/sat_predictor_performance/{session_id}
{
  "student_id": "user123",
  "time_spent": 1800,
  "math_correct": 9,
  "math_total": 12,
  "math_score": 650,
  "math_accuracy": 75.0,
  "time_bonus_points": 20,
  "rw_correct": 10,
  "rw_total": 12,
  "rw_score": 700,
  "rw_accuracy": 83.33,
  "total_sat_score": 1350,
  "math_questions": [...],
  "rw_questions": [...],
  "timestamp": "2025-11-21T10:30:45.123456",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Notes

- The API returns immediately (202 Accepted) and processes data in the background
- **Scoring considers both difficulty level and completion time**
  - Difficulty 5: 65 points per correct answer
  - Difficulty 1: 15 points per correct answer
  - Time bonus: Up to 40 points for completing under 15 minutes (1 point per 3 seconds saved)
- All timestamps are in UTC
- Session IDs are auto-generated UUIDs
- Analytics are updated incrementally to track progress over time
- Background processing failures are logged but don't affect the immediate response
- Maximum possible raw score: 820 points (780 from questions + 40 from time bonus)
