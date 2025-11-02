# Strength, Weakness & Least Attempted APIs - Quick Reference

## ✅ Three New Endpoints Added

### 1. **Get My Strength** 
`POST /api/analytics/get-my-strength`

**Purpose**: Find the tag where student performs best in a subject

**Request Body**:
```json
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "math"
}
```

**Response**:
```json
{
  "success": true,
  "strength": {
    "subject": "math",
    "sub_category": "algebra",
    "tag": "linear-equations",
    "total_score": 120,
    "score_percentage": 95.5,
    "total_questions_attempted": 25,
    "accuracy": 96.0
  }
}
```

**Returns `""` if no data available**

---

### 2. **Get My Weakness**
`POST /api/analytics/get-my-weakness`

**Purpose**: Find the tag where student needs most improvement in a subject

**Request Body**:
```json
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "math"
}
```

**Response**:
```json
{
  "success": true,
  "weakness": {
    "subject": "math",
    "sub_category": "geometry-and-trigonometry",
    "tag": "circle-equations",
    "total_score": 15,
    "score_percentage": 45.0,
    "total_questions_attempted": 10,
    "accuracy": 50.0
  }
}
```

**Returns `""` if no data available**

---

### 3. **Get My Least Attempted**
`POST /api/analytics/get-my-least-attempted`

**Purpose**: Find the tag with fewest questions attempted by student in a subject

**Request Body**:
```json
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "math"
}
```

**Response**:
```json
{
  "success": true,
  "least_attempted": {
    "subject": "math",
    "sub_category": "problem-solving-and-data-analysis",
    "tag": "probability",
    "total_score": 0,
    "score_percentage": 0,
    "total_questions_attempted": 0,
    "accuracy": 0
  }
}
```

**Returns `""` if no data available**

---

## 🎯 Scoring Algorithms

### Strength & Weakness Endpoints
Both endpoints use the same combined scoring formula:

```
combined_score = (score_percentage × 0.7) + (min(total_score, 100) × 0.3)
```

**Why this formula?**
- **70% weight on percentage**: Prioritizes mastery/accuracy
- **30% weight on total score**: Considers practice volume (capped at 100)
- **Strength**: Tag with HIGHEST combined score
- **Weakness**: Tag with LOWEST combined score

**Example Calculation**:
```
Tag A: 90% accuracy, 60 total score
combined = (90 × 0.7) + (60 × 0.3) = 63 + 18 = 81

Tag B: 80% accuracy, 100 total score  
combined = (80 × 0.7) + (100 × 0.3) = 56 + 30 = 86

Tag B is stronger (higher combined score)
```

### Least Attempted Endpoint
Simple algorithm:

```
Find tag with minimum total_questions_attempted
If multiple tags have 0 attempts, return any one
```

**Purpose**: Identify areas the student hasn't practiced yet

---

## 📋 Testing in Postman

### Step 1: Set Headers
```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjdlYTA5ZDA1NzI2MmU2M2U2MmZmNzNmMDNlMDRhZDI5ZDg5Zjg5MmEiLCJ0eXAiOiJKV1QifQ...
Content-Type: application/json
```

### Step 2: Test Get My Strength
**URL**: `POST https://your-url/api/analytics/get-my-strength`

**Body**:
```json
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "math"
}
```

### Step 3: Test Get My Weakness
**URL**: `POST https://your-url/api/analytics/get-my-weakness`

**Body**:
```json
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "math"
}
```

---

## 🔄 Complete Test Flow

### 1. Submit Quiz Data (if you haven't already)
```json
POST /api/analytics/submit-quiz
{
  "student_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "time_spent": 1200,
  "number_of_questions": 10,
  "number_of_correct_answers": 7,
  "subject": "math",
  "sub_category": "algebra",
  "difficulty_level": 3,
  "tag_wise_details": [
    {"tag": "linear-equations", "total_questions": 5, "correct_answers": 4},
    {"tag": "systems-of-equations", "total_questions": 5, "correct_answers": 3}
  ],
  "correct_question_ids": ["q1", "q2", "q3", "q4", "q5", "q6", "q7"],
  "incorrect_question_ids": ["q8", "q9", "q10"]
}
```

### 2. Check Strength
```json
POST /api/analytics/get-my-strength
{"user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2", "subject": "math"}
```

### Step 3: Check Weakness
```json
POST /api/analytics/get-my-weakness
{"user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2", "subject": "math"}
```

### Step 4: Check Least Attempted
```json
POST /api/analytics/get-my-least-attempted
{"user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2", "subject": "math"}
```

---

## 📊 Valid Input Values

### Subjects:
- `"math"`
- `"reading-and-writing"`

### Math Sub-Categories:
- `"algebra"`
- `"advanced-math"`
- `"problem-solving-and-data-analysis"`
- `"geometry-and-trigonometry"`

### Reading & Writing Sub-Categories:
- `"craft-and-structure"`
- `"information-and-ideas"`
- `"standard-english-conventions"`
- `"expression-of-ideas"`

---

## 🎯 Use Cases

1. **Personalized Recommendations**: Show students what to practice based on weakness or least attempted
2. **Adaptive Learning**: Generate quizzes focusing on weak or unexplored areas
3. **Achievement System**: Award badges for mastery of strong areas
4. **Progress Tracking**: Monitor improvement in weak areas over time
5. **Study Planner**: Suggest optimal study topics (balance weakness and least attempted)
6. **Diversification**: Encourage students to practice least attempted topics

---

## ⚠️ Important Notes

1. **Returns `""` when no data**: If user hasn't taken any quizzes, all endpoints return empty string
2. **Subject-specific**: Results calculated separately for each subject
3. **Real-time updates**: Results update immediately after quiz submission
4. **Authentication required**: Must include valid Firebase token
5. **Tag-level granularity**: Returns specific tag (not just sub-category)
6. **Least attempted with 0s**: If multiple tags have 0 attempts, returns any one of them

---

## 🚀 Ready to Deploy

All three endpoints are:
- ✅ Implemented in `routes/analytics_routing.py`
- ✅ Integrated with existing analytics system
- ✅ Using the same authentication middleware
- ✅ Following consistent error handling
- ✅ Documented in `STRENGTH_WEAKNESS_API_GUIDE.md`

**No additional deployment needed** - just redeploy your backend and the endpoints will be live at:
- `POST /api/analytics/get-my-strength`
- `POST /api/analytics/get-my-weakness`
- `POST /api/analytics/get-my-least-attempted`
