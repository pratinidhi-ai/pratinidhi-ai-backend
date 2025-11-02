# Strength, Weakness & Least Attempted API Test Examples

## Overview
Three new endpoints to help students identify their strongest and weakest areas, plus areas they haven't practiced much, based on their quiz performance.

---

## 1. Get My Strength

**Endpoint**: `POST /api/analytics/get-my-strength`

**Description**: Returns the tag where the student performs best in the given subject.

### Algorithm
- Considers both `score_percentage` (70% weight) and `total_score` (30% weight)
- Formula: `combined_score = (score_percentage × 0.7) + (min(total_score, 100) × 0.3)`
- Returns the tag with the highest combined score
- Returns empty string `""` if no data available

### Postman Request

**Method**: `POST`

**Headers**:
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
Content-Type: application/json
```

**Body** (Example 1 - Math):
```json
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "math"
}
```

**Body** (Example 2 - Reading & Writing):
```json
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "reading-and-writing"
}
```

### Response Examples

**Success with data**:
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

**Success but no data yet**:
```json
{
  "success": true,
  "strength": ""
}
```

**Error - User not found**:
```json
{
  "error": "User not found",
  "message": "Student with ID xyz does not exist"
}
```

---

## 2. Get My Weakness

**Endpoint**: `POST /api/analytics/get-my-weakness`

**Description**: Returns the tag where the student needs the most improvement in the given subject.

### Algorithm
- Considers both `score_percentage` (70% weight) and `total_score` (30% weight)
- Formula: `combined_score = (score_percentage × 0.7) + (min(total_score, 100) × 0.3)`
- Returns the tag with the lowest combined score
- Returns empty string `""` if no data available

### Postman Request

**Method**: `POST`

**Headers**:
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
Content-Type: application/json
```

**Body** (Example 1 - Math):
```json
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "math"
}
```

**Body** (Example 2 - Reading & Writing):
```json
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "reading-and-writing"
}
```

### Response Examples

**Success with data**:
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

**Success but no data yet**:
```json
{
  "success": true,
  "weakness": ""
}
```

**Error - Missing fields**:
```json
{
  "error": "Missing required fields",
  "message": "user_id and subject are required"
}
```

---

## 3. Get My Least Attempted

**Endpoint**: `POST /api/analytics/get-my-least-attempted`

**Description**: Returns the tag that the student has attempted the fewest number of questions in the given subject.

### Algorithm
- Finds the tag with the minimum `total_questions_attempted`
- If multiple tags have 0 attempts, returns any one of them
- Returns empty string `""` if no data available

### Postman Request

**Method**: `POST`

**Headers**:
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
Content-Type: application/json
```

**Body** (Example 1 - Math):
```json
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "math"
}
```

**Body** (Example 2 - Reading & Writing):
```json
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "reading-and-writing"
}
```

### Response Examples

**Success with data**:
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

**Success but no data yet**:
```json
{
  "success": true,
  "least_attempted": ""
}
```

**Error - User not found**:
```json
{
  "error": "User not found",
  "message": "Student with ID xyz does not exist"
}
}
```

---

## Testing Workflow

### Step 1: Submit Some Quiz Data First
Before you can get strength/weakness/least-attempted, you need to submit at least one quiz:

```bash
POST /api/analytics/submit-quiz
```
(Use the quiz submission body from previous examples)

### Step 2: Check Strength
```bash
POST /api/analytics/get-my-strength
Body: {"user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2", "subject": "math"}
```

### Step 3: Check Weakness
```bash
POST /api/analytics/get-my-weakness
Body: {"user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2", "subject": "math"}
```

### Step 4: Check Least Attempted
```bash
POST /api/analytics/get-my-least-attempted
Body: {"user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2", "subject": "math"}
```

---

## Complete Test Scenario

### 1. Submit Multiple Quizzes with Different Performance

**Quiz 1 - Algebra (Good Performance)**:
```json
POST /api/analytics/submit-quiz
{
  "student_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "time_spent": 1200,
  "number_of_questions": 10,
  "number_of_correct_answers": 9,
  "subject": "math",
  "sub_category": "algebra",
  "difficulty_level": 3,
  "tag_wise_details": [
    {
      "tag": "linear-equations",
      "total_questions": 5,
      "correct_answers": 5
    },
    {
      "tag": "systems-of-equations",
      "total_questions": 5,
      "correct_answers": 4
    }
  ],
  "correct_question_ids": ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9"],
  "incorrect_question_ids": ["q10"]
}
```

**Quiz 2 - Geometry (Poor Performance)**:
```json
POST /api/analytics/submit-quiz
{
  "student_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "time_spent": 1500,
  "number_of_questions": 10,
  "number_of_correct_answers": 4,
  "subject": "math",
  "sub_category": "geometry-and-trigonometry",
  "difficulty_level": 3,
  "tag_wise_details": [
    {
      "tag": "circle-equations",
      "total_questions": 5,
      "correct_answers": 2
    },
    {
      "tag": "pythagorean-theorem",
      "total_questions": 5,
      "correct_answers": 2
    }
  ],
  "correct_question_ids": ["g1", "g2", "g5", "g8"],
  "incorrect_question_ids": ["g3", "g4", "g6", "g7", "g9", "g10"]
}
```

**Quiz 3 - Algebra Again (Excellent Performance)**:
```json
POST /api/analytics/submit-quiz
{
  "student_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "time_spent": 900,
  "number_of_questions": 8,
  "number_of_correct_answers": 8,
  "subject": "math",
  "sub_category": "algebra",
  "difficulty_level": 4,
  "tag_wise_details": [
    {
      "tag": "linear-equations",
      "total_questions": 4,
      "correct_answers": 4
    },
    {
      "tag": "quadratic-equations",
      "total_questions": 4,
      "correct_answers": 4
    }
  ],
  "correct_question_ids": ["q11", "q12", "q13", "q14", "q15", "q16", "q17", "q18"],
  "incorrect_question_ids": []
}
```

### 2. Now Test Strength API

```bash
POST /api/analytics/get-my-strength
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "math"
}
```

**Expected Result**: Should return `linear-equations` (best performance across quizzes)

### 3. Test Weakness API

```bash
POST /api/analytics/get-my-weakness
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "math"
}
```

**Expected Result**: Should return `circle-equations` or `pythagorean-theorem` (worst performance)

---

## Valid Subject Values

Based on your taxonomy:
- `"math"`
- `"reading-and-writing"`

## Valid Sub-Categories

### For Math:
- `"algebra"`
- `"advanced-math"`
- `"problem-solving-and-data-analysis"`
- `"geometry-and-trigonometry"`

### For Reading & Writing:
- `"craft-and-structure"`
- `"information-and-ideas"`
- `"standard-english-conventions"`
- `"expression-of-ideas"`

---

## Use Cases

### 1. Personalized Study Recommendations
```javascript
// Get weakness and suggest practice
const weakness = await getMyWeakness(userId, "math");
if (weakness.tag) {
  showPracticeRecommendation(weakness);
  // "Practice more on circle-equations in geometry"
}
```

### 2. Achievement Badges
```javascript
// Get strength and award badges
const strength = await getMyStrength(userId, "math");
if (strength.score_percentage > 90) {
  awardBadge(userId, `${strength.tag}-master`);
}
```

### 3. Adaptive Quiz Generation
```javascript
// Create quiz focusing on weakness
const weakness = await getMyWeakness(userId, subject);
const quiz = generateQuiz({
  subject: weakness.subject,
  sub_category: weakness.sub_category,
  tags: [weakness.tag],
  difficulty_level: 2  // Start easy to build confidence
});
```

### 4. Dashboard Display
```javascript
// Show strengths and weaknesses side by side
const [strength, weakness] = await Promise.all([
  getMyStrength(userId, "math"),
  getMyWeakness(userId, "math")
]);

displayDashboard({
  bestAt: strength.tag,
  needsWork: weakness.tag
});
```

---

## Error Handling

All endpoints return consistent error formats:

**400 - Bad Request**:
```json
{
  "error": "Invalid request",
  "message": "Request body must be JSON"
}
```

**404 - User Not Found**:
```json
{
  "error": "User not found",
  "message": "Student with ID xyz does not exist"
}
```

**500 - Server Error**:
```json
{
  "error": "Failed to get strength/weakness",
  "message": "Detailed error message"
}
```

---

## Notes

1. **Initial State**: Returns `""` when user has no quiz data yet
2. **Scoring Logic**: Balances mastery (percentage) with practice volume (total score)
3. **Minimum Data**: At least one quiz with non-zero scores needed
4. **Subject Specific**: Results are calculated per subject independently
5. **Real-time**: Updates immediately after each quiz submission
6. **Authentication**: Requires valid Firebase token in Authorization header

---

## Postman Collection Variables

You can set these as collection variables in Postman:

```javascript
// Collection Variables
base_url: https://your-app-runner-url.com
firebase_token: YOUR_FIREBASE_TOKEN
user_id: 9Tw74uo0Y2VQK8oWs8br25NFHme2
```

Then use in requests:
```
URL: {{base_url}}/api/analytics/get-my-strength
Header: Authorization: Bearer {{firebase_token}}
Body: {"user_id": "{{user_id}}", "subject": "math"}
```
