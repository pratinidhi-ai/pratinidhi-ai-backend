# API Test Commands for Last 15 Math Questions

## Prerequisites
1. Get your bearer token (see `GET_BEARER_TOKEN.md`)
2. Replace `YOUR_TOKEN_HERE` with your actual token
3. Replace `test_user` with your student ID

## Test Commands

### 1. Submit a Math Quiz (Creates Data)

```bash
curl -X POST http://localhost:5000/api/analytics/submit-quiz \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "student_id": "test_user",
    "subject": "math",
    "sub_category": "algebra",
    "difficulty_level": 3,
    "number_of_questions": 5,
    "number_of_correct_answers": 3,
    "time_spent": 300,
    "tag_wise_details": [
      {
        "tag": "linear-equations",
        "total_questions": 3,
        "correct_answers": 2
      },
      {
        "tag": "quadratic-equations",
        "total_questions": 2,
        "correct_answers": 1
      }
    ],
    "correct_question_ids": ["q1", "q2", "q3"],
    "incorrect_question_ids": ["q4", "q5"]
  }'
```

**Expected Response (202):**
```json
{
  "success": true,
  "message": "Quiz submission received and is being processed",
  "request_id": "uuid...",
  "estimated_accuracy": 60.0,
  ...
}
```

---

### 2. Get Last 15 Math Questions

```bash
curl -X GET http://localhost:5000/api/analytics/last-15-math-questions/test_user \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected Response (200):**
```json
{
  "success": true,
  "data": {
    "student_id": "test_user",
    "questions": [
      {
        "question_id": "q1",
        "is_correct": true,
        "difficulty_level": 3,
        "tags": ["linear-equations", "quadratic-equations"],
        "sub_category": "algebra",
        "timestamp": "2025-11-07T..."
      },
      ...
    ],
    "count": 5,
    "last_updated": "2025-11-07T..."
  }
}
```

---

### 3. Submit Multiple Math Quizzes (Test Rolling Window)

#### Quiz 2
```bash
curl -X POST http://localhost:5000/api/analytics/submit-quiz \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "student_id": "test_user",
    "subject": "math",
    "sub_category": "geometry-and-trigonometry",
    "difficulty_level": 4,
    "number_of_questions": 5,
    "number_of_correct_answers": 4,
    "time_spent": 400,
    "tag_wise_details": [
      {
        "tag": "pythagorean-theorem",
        "total_questions": 3,
        "correct_answers": 3
      },
      {
        "tag": "area-of-polygons",
        "total_questions": 2,
        "correct_answers": 1
      }
    ],
    "correct_question_ids": ["q6", "q7", "q8", "q9"],
    "incorrect_question_ids": ["q10"]
  }'
```

#### Quiz 3
```bash
curl -X POST http://localhost:5000/api/analytics/submit-quiz \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "student_id": "test_user",
    "subject": "math",
    "sub_category": "advanced-math",
    "difficulty_level": 5,
    "number_of_questions": 5,
    "number_of_correct_answers": 2,
    "time_spent": 500,
    "tag_wise_details": [
      {
        "tag": "exponential-equations",
        "total_questions": 3,
        "correct_answers": 1
      },
      {
        "tag": "radical-equations",
        "total_questions": 2,
        "correct_answers": 1
      }
    ],
    "correct_question_ids": ["q11", "q12"],
    "incorrect_question_ids": ["q13", "q14", "q15"]
  }'
```

**After these 3 quizzes, you should have 15 total questions**

---

### 4. Submit One More Quiz (Test That Oldest Are Dropped)

```bash
curl -X POST http://localhost:5000/api/analytics/submit-quiz \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "student_id": "test_user",
    "subject": "math",
    "sub_category": "problem-solving-and-data-analysis",
    "difficulty_level": 2,
    "number_of_questions": 3,
    "number_of_correct_answers": 3,
    "time_spent": 200,
    "tag_wise_details": [
      {
        "tag": "percentage-calculation",
        "total_questions": 2,
        "correct_answers": 2
      },
      {
        "tag": "ratio-proportion",
        "total_questions": 1,
        "correct_answers": 1
      }
    ],
    "correct_question_ids": ["q16", "q17", "q18"],
    "incorrect_question_ids": []
  }'
```

**Now check again - should still have 15 questions, but q1, q2, q3 should be dropped**

```bash
curl -X GET http://localhost:5000/api/analytics/last-15-math-questions/test_user \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 5. Test Non-Math Subject (Should Not Affect Last 15)

```bash
curl -X POST http://localhost:5000/api/analytics/submit-quiz \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "student_id": "test_user",
    "subject": "reading-and-writing",
    "sub_category": "craft-and-structure",
    "difficulty_level": 3,
    "number_of_questions": 5,
    "number_of_correct_answers": 4,
    "time_spent": 300,
    "tag_wise_details": [
      {
        "tag": "word-in-context",
        "total_questions": 3,
        "correct_answers": 3
      },
      {
        "tag": "main-purpose",
        "total_questions": 2,
        "correct_answers": 1
      }
    ],
    "correct_question_ids": ["r1", "r2", "r3", "r4"],
    "incorrect_question_ids": ["r5"]
  }'
```

**Then check last 15 math questions - should be unchanged**

```bash
curl -X GET http://localhost:5000/api/analytics/last-15-math-questions/test_user \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 6. Test Error Cases

#### Non-Existent User
```bash
curl -X GET http://localhost:5000/api/analytics/last-15-math-questions/nonexistent_user \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected Response (404):**
```json
{
  "error": "User not found",
  "message": "Student with ID nonexistent_user does not exist"
}
```

#### Missing Authorization
```bash
curl -X GET http://localhost:5000/api/analytics/last-15-math-questions/test_user
```

**Expected Response (401 or 403):**
```json
{
  "error": "Unauthorized",
  ...
}
```

---

## PowerShell Versions (for Windows)

### Submit Math Quiz
```powershell
$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer YOUR_TOKEN_HERE"
}

$body = @{
    student_id = "test_user"
    subject = "math"
    sub_category = "algebra"
    difficulty_level = 3
    number_of_questions = 5
    number_of_correct_answers = 3
    time_spent = 300
    tag_wise_details = @(
        @{
            tag = "linear-equations"
            total_questions = 3
            correct_answers = 2
        },
        @{
            tag = "quadratic-equations"
            total_questions = 2
            correct_answers = 1
        }
    )
    correct_question_ids = @("q1", "q2", "q3")
    incorrect_question_ids = @("q4", "q5")
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:5000/api/analytics/submit-quiz" -Method Post -Headers $headers -Body $body
```

### Get Last 15 Math Questions
```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_TOKEN_HERE"
}

Invoke-RestMethod -Uri "http://localhost:5000/api/analytics/last-15-math-questions/test_user" -Method Get -Headers $headers
```

---

## Python Test Script

For automated testing, use the provided test script:

```bash
cd testing
python test_last_15_math.py
```

**Remember to update `BEARER_TOKEN` in the script first!**

---

## Verification Checklist

- [ ] Submit first math quiz → Should return 5 questions
- [ ] Submit 2 more quizzes → Should return 15 questions total
- [ ] Submit 1 more quiz → Should still return 15 (oldest 3 dropped)
- [ ] Submit reading quiz → Last 15 math should be unchanged
- [ ] Check all questions have required fields
- [ ] Check questions are ordered newest → oldest
- [ ] Check accuracy calculations are correct
- [ ] Test with non-existent user → Should return 404
- [ ] Test without authorization → Should return 401/403

---

## Expected Data Flow

1. **First Quiz (5 questions)**: `count: 5`
2. **Second Quiz (5 questions)**: `count: 10`
3. **Third Quiz (5 questions)**: `count: 15`
4. **Fourth Quiz (3 questions)**: `count: 15` (3 oldest dropped)

The list maintains **FIFO** behavior with a max size of 15.

---

## Notes

- Wait 2-3 seconds after submitting a quiz before checking (async processing)
- Questions are stored newest-first
- Only `subject: "math"` quizzes are tracked
- Document is created on first math quiz submission
- All timestamps are in UTC (ISO 8601 format)
