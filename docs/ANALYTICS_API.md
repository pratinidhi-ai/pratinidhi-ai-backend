# Student Analytics API Documentation

## Overview

The Analytics API provides comprehensive performance tracking for students taking SAT preparation quizzes. It captures detailed data at multiple levels (subject, sub-category, and tag) and maintains historical activity logs.

## Architecture

### Database Structure

The analytics system uses Firestore subcollections under each user document:

```
users/{student_id}/
  ├── analytics/
  │   ├── performance_summary    # Aggregated performance metrics
  │   ├── correct_questions      # List of correctly answered question IDs
  │   └── incorrect_questions    # List of incorrectly answered question IDs
  └── activity_logs/
      ├── {session_id_1}        # Individual quiz session data
      ├── {session_id_2}
      └── ...
```

### Hierarchical Data Model

Analytics data is organized hierarchically:

```
Student
  └── Subject (e.g., "math", "reading-and-writing")
      └── Sub-Category (e.g., "algebra", "craft-and-structure")
          └── Tag (e.g., "linear-equations", "word-in-context")
```

At each level, the system tracks:
- Total questions attempted
- Total correct answers
- Score (based on difficulty level)
- Total possible score
- Accuracy percentage
- Time spent (at subject and sub-category levels)
- Quiz count

## API Endpoints

### 1. Submit Quiz Results

**POST** `/api/analytics/submit-quiz`

Submit quiz results after a student completes a quiz or practice test.

#### Request Headers
```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

#### Request Body

```json
{
  "student_id": "user123",
  "time_spent": 1800,
  "number_of_questions": 10,
  "number_of_correct_answers": 7,
  "subject": "math",
  "sub_category": "algebra",
  "difficulty_level": 3,
  "tag_wise_details": [
    {
      "tag": "linear-equations",
      "total_questions": 5,
      "correct_answers": 4
    },
    {
      "tag": "systems-of-equations",
      "total_questions": 5,
      "correct_answers": 3
    }
  ],
  "correct_question_ids": [
    "q1", "q2", "q3", "q4", "q5", "q6", "q7"
  ],
  "incorrect_question_ids": [
    "q8", "q9", "q10"
  ]
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_id` | string | Yes | Unique user identifier |
| `time_spent` | integer | Yes | Time spent on quiz in seconds |
| `number_of_questions` | integer | Yes | Total number of questions in quiz |
| `number_of_correct_answers` | integer | Yes | Number of correctly answered questions |
| `subject` | string | Yes | Subject name (e.g., "math", "reading-and-writing") |
| `sub_category` | string | Yes | Sub-category from sat_tag_taxonomy.json |
| `difficulty_level` | integer | Yes | Difficulty level (1-5) |
| `tag_wise_details` | array | Yes | Performance breakdown by tag |
| `correct_question_ids` | array | Yes | List of correctly answered question IDs |
| `incorrect_question_ids` | array | Yes | List of incorrectly answered question IDs |

#### Scoring System

- Each question is worth points equal to its difficulty level
- Score = number_of_correct_answers × difficulty_level
- Total possible score = number_of_questions × difficulty_level

Examples:
- Difficulty 1: 1 mark per correct answer
- Difficulty 3: 3 marks per correct answer
- Difficulty 5: 5 marks per correct answer

#### Response

```json
{
  "success": true,
  "message": "Quiz analytics submitted successfully",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "summary": {
    "score": 21,
    "total_possible_score": 30,
    "accuracy": 70.0,
    "time_spent_minutes": 30.0,
    "subject": "math",
    "sub_category": "algebra",
    "difficulty_level": 3
  }
}
```

#### Error Responses

**400 Bad Request** - Missing required fields
```json
{
  "error": "Missing required fields",
  "missing": ["student_id", "time_spent"]
}
```

**400 Bad Request** - Invalid data
```json
{
  "error": "Invalid data",
  "message": "Difficulty level must be between 1 and 5"
}
```

**404 Not Found** - User doesn't exist
```json
{
  "error": "User not found",
  "message": "Student with ID user123 does not exist"
}
```

---

### 2. Get Performance Summary

**GET** `/api/analytics/performance-summary/<student_id>`

Retrieve aggregated performance data for a student.

#### Request Headers
```
Authorization: Bearer <firebase_id_token>
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subject` | string | No | Filter by specific subject |
| `sub_category` | string | No | Filter by sub-category (requires subject) |

#### Response - Full Summary

```json
{
  "success": true,
  "summary": {
    "student_id": "user123",
    "total_time_spent": 7200,
    "total_quizzes": 15,
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
              }
            }
          }
        }
      }
    },
    "last_updated": "2025-11-02T10:30:00Z"
  }
}
```

#### Response - Filtered by Subject

**GET** `/api/analytics/performance-summary/user123?subject=math`

```json
{
  "success": true,
  "summary": {
    "student_id": "user123",
    "subject": "math",
    "data": {
      "subject": "math",
      "total_questions_attempted": 150,
      "total_correct_answers": 120,
      "accuracy": 80.0,
      "sub_categories": { ... }
    }
  }
}
```

---

### 3. Get Activity Logs

**GET** `/api/analytics/activity-logs/<student_id>`

Retrieve historical quiz sessions for a student.

#### Request Headers
```
Authorization: Bearer <firebase_id_token>
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Maximum logs to return (default: 50, max: 100) |

#### Response

```json
{
  "success": true,
  "logs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "student_id": "user123",
      "subject": "math",
      "sub_category": "algebra",
      "difficulty_level": 3,
      "number_of_questions": 10,
      "number_of_correct_answers": 7,
      "score": 21,
      "total_possible_score": 30,
      "accuracy": 70.0,
      "time_spent": 1800,
      "timestamp": "2025-11-02T10:30:00Z",
      "tag_wise_details": [ ... ]
    }
  ],
  "count": 1
}
```

---

### 4. Get Correct Questions

**GET** `/api/analytics/correct-questions/<student_id>`

Retrieve list of correctly answered question IDs.

#### Request Headers
```
Authorization: Bearer <firebase_id_token>
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subject` | string | No | Filter by subject |
| `sub_category` | string | No | Filter by sub-category (requires subject) |

#### Response

```json
{
  "success": true,
  "correct_questions": {
    "math|algebra": ["q1", "q2", "q3", "q5", "q7"],
    "math|geometry-and-trigonometry": ["q10", "q11", "q15"],
    "reading-and-writing|craft-and-structure": ["r1", "r3", "r5"]
  }
}
```

---

### 5. Get Incorrect Questions

**GET** `/api/analytics/incorrect-questions/<student_id>`

Retrieve list of incorrectly answered question IDs (useful for creating targeted practice).

#### Request Headers
```
Authorization: Bearer <firebase_id_token>
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subject` | string | No | Filter by subject |
| `sub_category` | string | No | Filter by sub-category (requires subject) |

#### Response

```json
{
  "success": true,
  "incorrect_questions": {
    "math|algebra": ["q4", "q6", "q8", "q9"],
    "math|geometry-and-trigonometry": ["q12", "q13", "q14"],
    "reading-and-writing|information-and-ideas": ["r2", "r4", "r6"]
  }
}
```

---

### 6. Get Quick Stats

**GET** `/api/analytics/stats/<student_id>`

Get a quick overview of student performance metrics.

#### Request Headers
```
Authorization: Bearer <firebase_id_token>
```

#### Response

```json
{
  "success": true,
  "stats": {
    "total_quizzes": 25,
    "total_time_spent_hours": 12.5,
    "overall_accuracy": 78.5,
    "subjects": {
      "math": {
        "accuracy": 82.0,
        "quizzes_taken": 15,
        "score_percentage": 81.5
      },
      "reading-and-writing": {
        "accuracy": 75.0,
        "quizzes_taken": 10,
        "score_percentage": 74.8
      }
    }
  }
}
```

---

## Usage Examples

### Example 1: Submit a Math Quiz

```bash
curl -X POST http://localhost:8080/api/analytics/submit-quiz \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "user123",
    "time_spent": 1200,
    "number_of_questions": 8,
    "number_of_correct_answers": 6,
    "subject": "math",
    "sub_category": "algebra",
    "difficulty_level": 2,
    "tag_wise_details": [
      {
        "tag": "linear-equations",
        "total_questions": 4,
        "correct_answers": 3
      },
      {
        "tag": "systems-of-equations",
        "total_questions": 4,
        "correct_answers": 3
      }
    ],
    "correct_question_ids": ["q1", "q2", "q3", "q5", "q6", "q7"],
    "incorrect_question_ids": ["q4", "q8"]
  }'
```

### Example 2: Get Performance Summary for a Specific Subject

```bash
curl -X GET "http://localhost:8080/api/analytics/performance-summary/user123?subject=math" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

### Example 3: Get Recent Activity Logs

```bash
curl -X GET "http://localhost:8080/api/analytics/activity-logs/user123?limit=10" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

### Example 4: Get Incorrect Questions for Targeted Practice

```bash
curl -X GET "http://localhost:8080/api/analytics/incorrect-questions/user123?subject=math&sub_category=algebra" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

---

## Data Integration with Tag Taxonomy

The analytics system uses the `resources/sat_tag_taxonomy.json` file as reference for valid tags and sub-categories:

### Math Subject
- **algebra** (15 tags)
- **advanced-math** (15 tags)
- **problem-solving-and-data-analysis** (15 tags)
- **geometry-and-trigonometry** (15 tags)

### Reading and Writing Subject
- **craft-and-structure** (15 tags)
- **information-and-ideas** (15 tags)
- **standard-english-conventions** (15 tags)
- **expression-of-ideas** (15 tags)

---

## Analytics Use Cases

### 1. **Identify Weak Areas**
Query incorrect questions and tag-level performance to identify topics where the student needs more practice.

### 2. **Track Progress Over Time**
Use activity logs to see improvement trends across multiple quiz sessions.

### 3. **Personalized Recommendations**
Based on performance summary, recommend specific difficulty levels and topics for practice.

### 4. **Time Management Insights**
Analyze time_spent data to identify if students are rushing or spending too much time on certain topics.

### 5. **Gamification**
Use score percentages and quiz counts to create leaderboards, badges, and achievement systems.

### 6. **Parent/Teacher Dashboards**
Aggregate analytics across multiple students for classroom or tutoring insights.

---

## Best Practices

1. **Submit analytics immediately after quiz completion** to ensure data freshness
2. **Use tag_wise_details** to provide granular insights at the tag level
3. **Query performance summaries** periodically to update student dashboards
4. **Use incorrect_questions** to generate adaptive learning paths
5. **Implement retry logic** for analytics submission to handle network issues
6. **Cache quick stats** on the client side for faster dashboard loading

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error type",
  "message": "Detailed error message"
}
```

Common HTTP status codes:
- **200 OK** - Successful GET request
- **201 Created** - Successful POST request (quiz submitted)
- **400 Bad Request** - Invalid input data
- **404 Not Found** - Student or resource not found
- **500 Internal Server Error** - Server-side error

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- Question IDs should match those in the question bank
- The system automatically calculates scores based on difficulty levels
- Analytics data is aggregated in real-time during submission
- No duplicate question IDs are stored in correct/incorrect lists
