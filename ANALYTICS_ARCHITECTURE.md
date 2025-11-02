# Analytics System Architecture & Data Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Mobile/Web App (Frontend)                    │
│  - Quiz Interface                                                   │
│  - Student Dashboard                                                │
│  - Performance Charts                                               │
└────────────────┬────────────────────────────────┬───────────────────┘
                 │                                │
                 │ Submit Quiz Results            │ Get Analytics
                 │ (POST)                         │ (GET)
                 ▼                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Flask Backend (Python)                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  routes/analytics_routing.py                                 │ │
│  │  - POST /api/analytics/submit-quiz                          │ │
│  │  - GET  /api/analytics/performance-summary/<id>             │ │
│  │  - GET  /api/analytics/activity-logs/<id>                   │ │
│  │  - GET  /api/analytics/correct-questions/<id>               │ │
│  │  - GET  /api/analytics/incorrect-questions/<id>             │ │
│  │  - GET  /api/analytics/stats/<id>                           │ │
│  └────────────┬─────────────────────────────────────────────────┘ │
│               │                                                     │
│               ▼                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  database/analytics_db.py                                    │ │
│  │  - submit_quiz_analytics()                                   │ │
│  │  - get_performance_summary()                                 │ │
│  │  - get_activity_logs()                                       │ │
│  │  - get_correct_questions()                                   │ │
│  │  - get_incorrect_questions()                                 │ │
│  └────────────┬─────────────────────────────────────────────────┘ │
│               │                                                     │
└───────────────┼─────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Firestore Database                             │
│                                                                     │
│  users/{student_id}/                                                │
│    ├── (user data)                                                  │
│    │                                                                │
│    ├── analytics/                         ← Subcollection          │
│    │   ├── performance_summary            ← Document               │
│    │   │   └── {aggregated metrics}                                │
│    │   │                                                            │
│    │   ├── correct_questions              ← Document               │
│    │   │   └── {subject|sub_category: [question_ids]}              │
│    │   │                                                            │
│    │   └── incorrect_questions            ← Document               │
│    │       └── {subject|sub_category: [question_ids]}              │
│    │                                                                │
│    └── activity_logs/                     ← Subcollection          │
│        ├── {session_id_1}                 ← Document               │
│        │   └── {quiz submission data}                              │
│        ├── {session_id_2}                                          │
│        └── {session_id_3}                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow: Submit Quiz

```
┌──────────────┐
│   Student    │
│  Completes   │
│     Quiz     │
└──────┬───────┘
       │
       │ Quiz Data (JSON)
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Validate Data                                      │
│  - Check required fields                                    │
│  - Verify student exists                                    │
│  - Validate difficulty level (1-5)                          │
│  - Check question counts match                              │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Create QuizSubmission Object                       │
│  - Calculate scores (correct × difficulty)                  │
│  - Calculate accuracy                                       │
│  - Generate session_id (UUID)                               │
│  - Convert tag details to TagDetail objects                 │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Store Activity Log                                 │
│  users/{student_id}/activity_logs/{session_id}              │
│  - Full quiz submission data                                │
│  - Timestamp                                                │
│  - All question IDs                                         │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Update Performance Summary                         │
│  users/{student_id}/analytics/performance_summary           │
│                                                             │
│  A. Update Overall Stats:                                   │
│     - total_time_spent += quiz_time                        │
│     - total_quizzes += 1                                   │
│                                                             │
│  B. Update Subject Level:                                   │
│     subjects[subject].total_questions += N                 │
│     subjects[subject].total_correct += M                   │
│     subjects[subject].total_score += score                 │
│     subjects[subject].quiz_count += 1                      │
│                                                             │
│  C. Update Sub-Category Level:                              │
│     sub_categories[sub_cat].total_questions += N           │
│     sub_categories[sub_cat].total_correct += M             │
│     sub_categories[sub_cat].total_score += score           │
│     sub_categories[sub_cat].quiz_count += 1                │
│                                                             │
│  D. Update Tag Level (for each tag):                        │
│     tags[tag].total_questions += tag_N                     │
│     tags[tag].total_correct += tag_M                       │
│     tags[tag].total_score += tag_score                     │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: Update Question Lists                              │
│                                                             │
│  A. Correct Questions:                                      │
│     users/{student_id}/analytics/correct_questions         │
│     - Add IDs to subject|sub_category key                  │
│     - Avoid duplicates (use set union)                     │
│                                                             │
│  B. Incorrect Questions:                                    │
│     users/{student_id}/analytics/incorrect_questions       │
│     - Add IDs to subject|sub_category key                  │
│     - Avoid duplicates (use set union)                     │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 6: Return Response                                    │
│  {                                                          │
│    "success": true,                                         │
│    "session_id": "uuid",                                    │
│    "summary": {                                             │
│      "score": 21,                                           │
│      "accuracy": 70.0,                                      │
│      ...                                                    │
│    }                                                        │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

## Data Structure Example

### Performance Summary Document Structure
```json
{
  "student_id": "user123",
  "total_time_spent": 7200,
  "total_quizzes": 15,
  "last_updated": "2025-11-02T10:30:00Z",
  
  "subjects": {
    "math": {
      "subject": "math",
      "total_questions_attempted": 150,
      "total_correct_answers": 120,
      "total_score": 360,
      "total_possible_score": 450,
      "total_time_spent": 3600,
      "quiz_count": 10,
      "accuracy": 80.0,
      "score_percentage": 80.0,
      
      "sub_categories": {
        "algebra": {
          "sub_category": "algebra",
          "total_questions_attempted": 50,
          "total_correct_answers": 42,
          "total_score": 126,
          "total_possible_score": 150,
          "total_time_spent": 1200,
          "quiz_count": 5,
          "accuracy": 84.0,
          "score_percentage": 84.0,
          
          "tags": {
            "linear-equations": {
              "tag": "linear-equations",
              "total_questions_attempted": 20,
              "total_correct_answers": 18,
              "total_score": 54,
              "total_possible_score": 60,
              "accuracy": 90.0,
              "score_percentage": 90.0
            },
            "systems-of-equations": {
              "tag": "systems-of-equations",
              "total_questions_attempted": 15,
              "total_correct_answers": 12,
              "total_score": 36,
              "total_possible_score": 45,
              "accuracy": 80.0,
              "score_percentage": 80.0
            }
          }
        }
      }
    }
  }
}
```

### Activity Log Document Structure
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "student_id": "user123",
  "timestamp": "2025-11-02T10:30:00Z",
  "subject": "math",
  "sub_category": "algebra",
  "difficulty_level": 3,
  "time_spent": 1200,
  "number_of_questions": 10,
  "number_of_correct_answers": 7,
  "score": 21,
  "total_possible_score": 30,
  "accuracy": 70.0,
  
  "tag_wise_details": [
    {
      "tag": "linear-equations",
      "total_questions": 5,
      "correct_answers": 4,
      "incorrect_answers": 1,
      "score": 12,
      "total_possible_score": 15,
      "accuracy": 80.0
    },
    {
      "tag": "systems-of-equations",
      "total_questions": 5,
      "correct_answers": 3,
      "incorrect_answers": 2,
      "score": 9,
      "total_possible_score": 15,
      "accuracy": 60.0
    }
  ],
  
  "correct_question_ids": ["q1", "q2", "q3", "q4", "q5", "q6", "q7"],
  "incorrect_question_ids": ["q8", "q9", "q10"]
}
```

### Correct Questions Document Structure
```json
{
  "student_id": "user123",
  "last_updated": "2025-11-02T10:30:00Z",
  "math|algebra": ["q1", "q2", "q3", "q5", "q7", "q10"],
  "math|geometry-and-trigonometry": ["q15", "q20", "q25"],
  "reading-and-writing|craft-and-structure": ["r1", "r3", "r5"]
}
```

## Calculation Formulas

### Score Calculation
```
For each question:
  points_per_question = difficulty_level

For a quiz:
  score = correct_answers × difficulty_level
  total_possible_score = total_questions × difficulty_level
  
Example (Difficulty 3):
  10 questions, 7 correct
  score = 7 × 3 = 21 points
  total_possible = 10 × 3 = 30 points
  score_percentage = (21 / 30) × 100 = 70%
```

### Accuracy Calculation
```
accuracy = (correct_answers / total_questions) × 100

Example:
  10 questions, 7 correct
  accuracy = (7 / 10) × 100 = 70%
```

### Aggregation Example
```
Student takes 3 quizzes in Math/Algebra (all difficulty 3):

Quiz 1: 10 questions, 7 correct → score: 21/30
Quiz 2: 8 questions, 6 correct  → score: 18/24
Quiz 3: 12 questions, 10 correct → score: 30/36

Aggregated Results:
  total_questions_attempted = 10 + 8 + 12 = 30
  total_correct_answers = 7 + 6 + 10 = 23
  total_score = 21 + 18 + 30 = 69
  total_possible_score = 30 + 24 + 36 = 90
  accuracy = (23 / 30) × 100 = 76.67%
  score_percentage = (69 / 90) × 100 = 76.67%
```

## Query Patterns

### Get All Analytics
```python
# Get complete performance summary
GET /api/analytics/performance-summary/{student_id}
→ Returns full hierarchy (subjects → sub_categories → tags)
```

### Get Subject-Specific Analytics
```python
# Get only math performance
GET /api/analytics/performance-summary/{student_id}?subject=math
→ Returns math data with all sub_categories and tags
```

### Get Sub-Category-Specific Analytics
```python
# Get only algebra performance
GET /api/analytics/performance-summary/{student_id}?subject=math&sub_category=algebra
→ Returns algebra data with all tags
```

### Get Recent Activity
```python
# Get last 10 quizzes
GET /api/analytics/activity-logs/{student_id}?limit=10
→ Returns 10 most recent quiz sessions
```

### Get Incorrect Questions for Practice
```python
# Get all incorrect algebra questions
GET /api/analytics/incorrect-questions/{student_id}?subject=math&sub_category=algebra
→ Returns list of question IDs to retry
```

## Security & Performance

### Authentication
- All endpoints protected with `@authenticate_request` middleware
- Requires valid Firebase ID token
- Student can only access their own data

### Performance Optimization
1. **Pre-aggregation**: Data aggregated during submission (not query time)
2. **Subcollections**: Use subcollections to avoid document size limits
3. **Indexes**: Firestore auto-indexes timestamp for activity logs
4. **Caching**: Client-side caching recommended for dashboards

### Data Validation
- Difficulty level must be 1-5
- Question counts must match
- Student must exist in users collection
- All required fields validated before processing

## Error Handling Flow

```
Request → Validate Input → Check User Exists → Process Data
   ↓           ↓                  ↓                 ↓
  400        400                404               500
(Bad         (Invalid           (Not             (Server
Request)     Data)              Found)           Error)
```

All errors return consistent format:
```json
{
  "error": "Error Type",
  "message": "Detailed explanation"
}
```
