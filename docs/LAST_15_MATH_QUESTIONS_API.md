# Last 15 Math Questions API

## Overview
This API provides access to the last 15 math questions attempted by a user. The system automatically maintains a rolling list of the most recent 15 math questions in the database for fast retrieval.

## Features
- **Automatic Tracking**: Questions are automatically tracked when users submit math quizzes
- **Rolling List**: Maintains only the last 15 questions to keep data fresh and relevant
- **Rich Metadata**: Each question includes correctness, difficulty, tags, sub-category, and timestamp
- **Fast Retrieval**: Pre-aggregated data for quick API responses

## How It Works

### 1. Data Collection (Automatic)
When a user submits a math quiz via the `/analytics/submit-quiz` endpoint:
- The system checks if `subject` is "math"
- If yes, it creates/updates a document called `last_15_math_questions` in the user's analytics subcollection
- New questions are added to the front of the list (most recent first)
- The list is trimmed to maintain exactly 15 questions maximum

### 2. Data Structure
The `last_15_math_questions` document stores:

```json
{
  "student_id": "user123",
  "questions": [
    {
      "question_id": "q123",
      "question_text": "Solve for x: 2x + 5 = 15",
      "option_a": "x = 5",
      "option_b": "x = 10",
      "option_c": "x = 15",
      "option_d": "x = 20",
      "correct_answer": "A",
      "is_answered_correctly": true,
      "difficulty_level": 3,
      "tags": ["linear-equations", "slope-intercept"],
      "sub_category": "algebra",
      "timestamp": "2025-11-07T12:34:56.789Z"
    },
    {
      "question_id": "q124",
      "question_text": "Factor: x² - 5x + 6",
      "option_a": "(x - 2)(x - 3)",
      "option_b": "(x - 1)(x - 6)",
      "option_c": "(x + 2)(x + 3)",
      "option_d": "(x - 6)(x + 1)",
      "correct_answer": "A",
      "is_answered_correctly": false,
      "difficulty_level": 4,
      "tags": ["quadratic-equations", "factoring"],
      "sub_category": "advanced-math",
      "timestamp": "2025-11-07T12:35:12.345Z"
    }
  ],
  "last_updated": "2025-11-07T12:35:12.345Z"
}
```

### 3. Database Location
```
users/{student_id}/analytics/last_15_math_questions
```

## API Endpoint

### GET `/api/analytics/last-15-math-questions/<student_id>`

Retrieves the last 15 math questions attempted by a student.

#### URL Parameters
- `student_id` (string, required): The student's user ID

#### Headers
```
Authorization: Bearer <token>
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "student_id": "user123",
    "questions": [
      {
        "question_id": "q123",
        "question_text": "Solve for x: 2x + 5 = 15",
        "options": {
          "A": "x = 5",
          "B": "x = 10",
          "C": "x = 15",
          "D": "x = 20"
        },
        "correct_answer": "A",
        "is_answered_correctly": true,
        "difficulty_level": 3,
        "tags": ["linear-equations", "slope-intercept"],
        "sub_category": "algebra",
        "timestamp": "2025-11-07T12:34:56.789Z"
      },
      {
        "question_id": "q124",
        "question_text": "Factor: x² - 5x + 6",
        "options": {
          "A": "(x - 2)(x - 3)",
          "B": "(x - 1)(x - 6)",
          "C": "(x + 2)(x + 3)",
          "D": "(x - 6)(x + 1)"
        },
        "correct_answer": "A",
        "is_answered_correctly": false,
        "difficulty_level": 4,
        "tags": ["quadratic-equations", "factoring"],
        "sub_category": "advanced-math",
        "timestamp": "2025-11-07T12:35:12.345Z"
      }
    ],
    "count": 2,
    "last_updated": "2025-11-07T12:35:12.345Z"
  }
}
```

#### Empty Response (200)
When no math questions have been attempted yet:
```json
{
  "success": true,
  "message": "No math questions found for this student",
  "data": {
    "student_id": "user123",
    "questions": [],
    "count": 0,
    "last_updated": null
  }
}
```

#### Error Responses

**User Not Found (404)**
```json
{
  "error": "User not found",
  "message": "Student with ID user123 does not exist"
}
```

**Server Error (500)**
```json
{
  "error": "Failed to get last 15 math questions",
  "message": "Error details..."
}
```

## Usage Examples

### cURL Example
```bash
curl -X GET \
  "http://localhost:5000/api/analytics/last-15-math-questions/user123" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Python Example
```python
import requests

BASE_URL = "http://localhost:5000/api"
STUDENT_ID = "user123"
TOKEN = "your_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

response = requests.get(
    f"{BASE_URL}/analytics/last-15-math-questions/{STUDENT_ID}",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    questions = data['data']['questions']
    print(f"Found {len(questions)} recent math questions")
    
    for q in questions:
        status = "✓" if q['is_answered_correctly'] else "✗"
        print(f"{status} {q['question_id']} - {q['question_text'][:50]}...")
        print(f"   Difficulty: {q['difficulty_level']} - {q['sub_category']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### JavaScript/Fetch Example
```javascript
const BASE_URL = 'http://localhost:5000/api';
const STUDENT_ID = 'user123';
const TOKEN = 'your_token_here';

fetch(`${BASE_URL}/analytics/last-15-math-questions/${STUDENT_ID}`, {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${TOKEN}`
  }
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    const questions = data.data.questions;
    console.log(`Found ${questions.length} recent math questions`);
    
    questions.forEach(q => {
      const status = q.is_answered_correctly ? '✓' : '✗';
      console.log(`${status} ${q.question_id} - ${q.question_text.substring(0, 50)}...`);
      console.log(`   Difficulty: ${q.difficulty_level} - ${q.sub_category}`);
    });
  } else {
    console.error('Error:', data.message);
  }
})
.catch(error => console.error('Request failed:', error));
```

## Use Cases

### 1. Show Recent Performance
Display a user's most recent math questions to show their current performance trend.

### 2. Review Wrong Answers
Filter and display only incorrect questions (`is_correct: false`) for review purposes.

### 3. Track Difficulty Progression
Monitor how difficulty levels change over time in the user's recent attempts.

### 4. Identify Weak Areas
Analyze the tags of incorrect questions to identify areas needing improvement.

### 5. Prevent Question Repetition
Check if a question ID exists in the last 15 before showing it to the user again.

## Response Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `question_id` | string | Unique identifier for the question |
| `question_text` | string | The full text of the math question |
| `options` | object | Answer choices with keys A, B, C, D |
| `correct_answer` | string | The correct answer (A, B, C, or D) |
| `is_answered_correctly` | boolean | Whether the user answered correctly |
| `difficulty_level` | integer | Question difficulty (1-5) |
| `tags` | array | List of concept tags for the question |
| `sub_category` | string | Math sub-category (algebra, geometry, etc.) |
| `timestamp` | string | ISO 8601 timestamp when question was attempted |
| `count` | integer | Total number of questions in the list |
| `last_updated` | string | ISO 8601 timestamp of last update |

## Implementation Details

### Database Updates
- Updates happen **automatically** during quiz submission
- Only triggers for `subject: "math"`
- Non-blocking: Failures won't prevent quiz submission
- Uses efficient list operations (prepend + slice)

### Performance Characteristics
- **Read Performance**: O(1) - Single document read
- **Write Performance**: O(n) where n ≤ 15 - Array manipulation
- **Storage**: Minimal - Only 15 questions per user

### Limitations
- Only tracks **math** questions (by design)
- Maximum of **15 questions** (older ones are dropped)
- Questions from the same quiz share the same tag list
- No filtering by sub-category or difficulty in this endpoint

## Testing

### Test Scenario 1: First Math Quiz
1. Submit a math quiz with 5 questions
2. Call the API
3. Should return exactly 5 questions

### Test Scenario 2: Multiple Quizzes
1. Submit 3 math quizzes (5 questions each = 15 total)
2. Call the API
3. Should return exactly 15 questions
4. Submit 1 more quiz (3 questions)
5. Call the API
6. Should still return 15 questions (3 oldest dropped)

### Test Scenario 3: Mixed Subjects
1. Submit a reading quiz (should not affect this)
2. Submit a math quiz
3. Call the API
4. Should only show math questions

## Integration with Existing System

This feature integrates seamlessly with:
- ✅ `/analytics/submit-quiz` - Automatically populates data
- ✅ `performance_summary` - Complementary analytics
- ✅ `activity_logs` - Full quiz history available
- ✅ `daily_progress` - Today's activity tracking

## Future Enhancements
- [ ] Filter by date range
- [ ] Filter by sub-category or tags
- [ ] Configurable list size (e.g., last 20, last 30)
- [ ] Separate tracking for reading questions
- [ ] Include question text and options (if available)
- [ ] Performance metrics (average difficulty, accuracy trend)

## Troubleshooting

### No Data Returned
- **Cause**: User hasn't attempted any math quizzes yet
- **Solution**: Normal behavior, returns empty list

### Missing Recent Questions
- **Cause**: Only last 15 are kept
- **Solution**: Check `activity_logs` for full history

### Questions from Other Subjects
- **Cause**: Only math questions are tracked
- **Solution**: Intended behavior, use other endpoints for reading/writing
