# Analytics System Quick Reference

## Overview
Complete analytics system for tracking student performance across subjects, sub-categories, and tags.

## File Structure

```
models/
  └── analytics_schema.py          # Data models for analytics

database/
  └── analytics_db.py               # Database operations

routes/
  └── analytics_routing.py          # API endpoints

testing/
  └── test_analytics_api.py         # Test script

ANALYTICS_API.md                    # Full API documentation
```

## Key Concepts

### Hierarchy
```
Student → Subject → Sub-Category → Tag
```

### Scoring
- Each question worth points = difficulty level
- Difficulty 1: 1 point per question
- Difficulty 3: 3 points per question
- Difficulty 5: 5 points per question

### Database Structure
```
users/{student_id}/
  ├── analytics/
  │   ├── performance_summary      # Aggregated stats
  │   ├── correct_questions        # Correct question IDs
  │   └── incorrect_questions      # Incorrect question IDs
  └── activity_logs/
      └── {session_id}             # Individual quiz logs
```

## Quick Start

### 1. Submit Quiz Results
```bash
POST /api/analytics/submit-quiz
```

**Minimal Request:**
```json
{
  "student_id": "user123",
  "time_spent": 1200,
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
    }
  ],
  "correct_question_ids": ["q1", "q2", "q3"],
  "incorrect_question_ids": ["q4", "q5"]
}
```

### 2. Get Performance Summary
```bash
GET /api/analytics/performance-summary/{student_id}
```

### 3. Get Quick Stats
```bash
GET /api/analytics/stats/{student_id}
```

## Common Use Cases

### 1. Show Student Dashboard
```python
# Get quick overview
response = requests.get(
    f"/api/analytics/stats/{student_id}",
    headers={"Authorization": f"Bearer {token}"}
)
stats = response.json()['stats']

# Display:
# - Total quizzes taken
# - Overall accuracy
# - Subject-wise performance
```

### 2. Identify Weak Topics
```python
# Get full performance summary
response = requests.get(
    f"/api/analytics/performance-summary/{student_id}",
    headers={"Authorization": f"Bearer {token}"}
)
summary = response.json()['summary']

# Find tags with accuracy < 70%
weak_tags = []
for subject in summary['subjects'].values():
    for sub_cat in subject['sub_categories'].values():
        for tag, perf in sub_cat['tags'].items():
            if perf['accuracy'] < 70:
                weak_tags.append(tag)
```

### 3. Create Practice Quiz from Mistakes
```python
# Get incorrect questions for a subject
response = requests.get(
    f"/api/analytics/incorrect-questions/{student_id}",
    params={"subject": "math", "sub_category": "algebra"},
    headers={"Authorization": f"Bearer {token}"}
)
incorrect_ids = response.json()['incorrect_questions']

# Use these IDs to fetch questions for retry practice
```

### 4. Track Progress Over Time
```python
# Get recent activity logs
response = requests.get(
    f"/api/analytics/activity-logs/{student_id}",
    params={"limit": 30},
    headers={"Authorization": f"Bearer {token}"}
)
logs = response.json()['logs']

# Plot accuracy over time
accuracies = [log['accuracy'] for log in logs]
timestamps = [log['timestamp'] for log in logs]
```

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/analytics/submit-quiz` | POST | Submit quiz results |
| `/api/analytics/performance-summary/<id>` | GET | Get aggregated performance |
| `/api/analytics/activity-logs/<id>` | GET | Get quiz history |
| `/api/analytics/correct-questions/<id>` | GET | Get correct question IDs |
| `/api/analytics/incorrect-questions/<id>` | GET | Get incorrect question IDs |
| `/api/analytics/stats/<id>` | GET | Get quick stats overview |

## Filters

### Performance Summary
```bash
# Filter by subject
GET /api/analytics/performance-summary/{id}?subject=math

# Filter by sub-category
GET /api/analytics/performance-summary/{id}?subject=math&sub_category=algebra
```

### Question Lists
```bash
# All incorrect questions
GET /api/analytics/incorrect-questions/{id}

# Filter by subject
GET /api/analytics/incorrect-questions/{id}?subject=math

# Filter by sub-category
GET /api/analytics/incorrect-questions/{id}?subject=math&sub_category=algebra
```

## Testing

### Setup
1. Get a Firebase ID token:
```bash
cd testing
python get_firebase_token.py
```

2. Update test file with token:
```python
# In test_analytics_api.py
FIREBASE_TOKEN = "your_actual_token_here"
STUDENT_ID = "your_test_user_id"
```

3. Run tests:
```bash
python testing/test_analytics_api.py
```

## Integration Tips

### Frontend Integration
```javascript
// Submit quiz after completion
const submitQuiz = async (quizData) => {
  const response = await fetch('/api/analytics/submit-quiz', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${firebaseToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(quizData)
  });
  return response.json();
};

// Show dashboard stats
const loadDashboard = async (studentId) => {
  const response = await fetch(`/api/analytics/stats/${studentId}`, {
    headers: {
      'Authorization': `Bearer ${firebaseToken}`
    }
  });
  const { stats } = await response.json();
  displayStats(stats);
};
```

### Mobile App Integration
```dart
// Flutter example
Future<Map<String, dynamic>> submitQuiz(QuizData quiz) async {
  final response = await http.post(
    Uri.parse('$baseUrl/api/analytics/submit-quiz'),
    headers: {
      'Authorization': 'Bearer $firebaseToken',
      'Content-Type': 'application/json',
    },
    body: jsonEncode(quiz.toJson()),
  );
  return jsonDecode(response.body);
}
```

## Performance Considerations

1. **Caching**: Cache quick stats on client side (update after each quiz)
2. **Pagination**: Use limit parameter for activity logs
3. **Filtering**: Filter by subject/sub-category to reduce response size
4. **Async Processing**: Analytics submission is synchronous but fast
5. **Retry Logic**: Implement retry for failed submissions

## Metrics Available

### Overall Level
- Total quizzes taken
- Total time spent
- Overall accuracy

### Subject Level
- Questions attempted
- Correct answers
- Score and score percentage
- Accuracy
- Time spent
- Quiz count

### Sub-Category Level
- All subject metrics
- Tag-level breakdown

### Tag Level
- Questions attempted
- Correct answers
- Score and score percentage
- Accuracy

## Example Calculations

### Accuracy
```
accuracy = (correct_answers / total_questions) × 100
```

### Score
```
score = correct_answers × difficulty_level
total_possible = total_questions × difficulty_level
score_percentage = (score / total_possible) × 100
```

### Time Metrics
```
time_spent_minutes = time_spent_seconds / 60
time_spent_hours = time_spent_seconds / 3600
avg_time_per_question = time_spent_seconds / total_questions
```

## Error Handling

All endpoints return consistent error format:
```json
{
  "error": "Error type",
  "message": "Detailed message"
}
```

Common errors:
- 400: Invalid input data
- 404: Student not found
- 500: Server error

## Best Practices

1. ✅ Submit analytics immediately after quiz completion
2. ✅ Include all tag_wise_details for granular tracking
3. ✅ Use correct subject/sub-category names from taxonomy
4. ✅ Handle network errors gracefully (retry logic)
5. ✅ Cache frequently accessed data (quick stats)
6. ✅ Filter requests when possible to reduce bandwidth
7. ✅ Validate data on client side before submission

## Additional Resources

- **Full API Documentation**: See `ANALYTICS_API.md`
- **Tag Taxonomy**: See `resources/sat_tag_taxonomy.json`
- **Test Script**: See `testing/test_analytics_api.py`
- **Question Bank API**: See `QUESTION_BANK_API.md`

## Support

For issues or questions:
1. Check error messages in response
2. Review API documentation
3. Test with the provided test script
4. Verify Firebase authentication token
