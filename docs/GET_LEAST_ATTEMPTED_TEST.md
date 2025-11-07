# Get My Least Attempted - Postman Test

## Quick Copy-Paste for Postman

### Endpoint
```
POST https://your-app-runner-url.com/api/analytics/get-my-least-attempted
```

### Headers
```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjdlYTA5ZDA1NzI2MmU2M2U2MmZmNzNmMDNlMDRhZDI5ZDg5Zjg5MmEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vZWR1Y2Fkby1haSIsImF1ZCI6ImVkdWNhZG8tYWkiLCJhdXRoX3RpbWUiOjE3NjIwNTIwNjksInVzZXJfaWQiOiI5VHc3NHVvMFkyVlFLOG9XczhicjI1TkZIbWUyIiwic3ViIjoiOVR3NzR1bzBZMlZRSzhvV3M4YnIyNU5GSG1lMiIsImlhdCI6MTc2MjA1MjA2OSwiZXhwIjoxNzYyMDU1NjY5LCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZW1haWwiOlsidGVzdEBleGFtcGxlLmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6InBhc3N3b3JkIn19.xxNYh4FmFZ7nvbvjq6FG8LS2HGuysh8MNDAmmdfNsS8_a9gKPiJTqvTlVujjm7lRd-Q6GG8y1qi_xso2d04kiGDDQN43VTWGHUWmawts41iVGU9dQgX4ymYU7KPngiPfRJQLPrXV9i5wYngzKLehVXDv0se2ba4wH1sMcWwS-15FAvYBKC5u13VmBsT1J0vS0zMaLGwWxHaxiP_gDLEUWBXqHLLVobiMNY5kf_Q7TQXn_Gz5m_SuW1LI9z8HPNaArFZfJozyPzvknVFMQ_7YAAzhsCq0JE4_hhRa3m7EhvuPcKPUNeicK9xkhsfq7Hl99yc0HHLqBkhX48kVfFPZjQ
Content-Type: application/json
```

### Body (Math)
```json
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "math"
}
```

### Body (Reading & Writing)
```json
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "reading-and-writing"
}
```

---

## Expected Responses

### Success (With Data)
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

### Success (No Data Yet)
```json
{
  "success": true,
  "least_attempted": ""
}
```

### Error - Missing Fields
```json
{
  "error": "Missing required fields",
  "message": "user_id and subject are required"
}
```

### Error - User Not Found
```json
{
  "error": "User not found",
  "message": "Student with ID xyz does not exist"
}
```

---

## What This API Does

1. **Finds the tag with minimum attempts** in the specified subject
2. **Returns any one tag** if multiple tags have 0 attempts
3. **Returns empty string** if user has no analytics data yet
4. **Helps identify** topics the student hasn't explored

---

## Use Case Example

```javascript
// Get least attempted tag
const response = await fetch('/api/analytics/get-my-least-attempted', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    user_id: userId,
    subject: 'math'
  })
});

const data = await response.json();

if (data.least_attempted && data.least_attempted !== "") {
  // Show recommendation to practice this topic
  showRecommendation({
    title: "Try something new!",
    message: `You haven't practiced ${data.least_attempted.tag} yet`,
    action: "Start Quiz",
    topic: data.least_attempted
  });
}
```

---

## Testing Strategy

### 1. Test with No Data
Call the API before submitting any quizzes:
```json
POST /api/analytics/get-my-least-attempted
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "math"
}

Expected: {"success": true, "least_attempted": ""}
```

### 2. Submit a Quiz
Submit a quiz covering only some tags:
```json
POST /api/analytics/submit-quiz
{
  "student_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "math",
  "sub_category": "algebra",
  "tag_wise_details": [
    {"tag": "linear-equations", "total_questions": 5, "correct_answers": 4},
    {"tag": "systems-of-equations", "total_questions": 5, "correct_answers": 3}
  ],
  ...
}
```

### 3. Check Least Attempted Again
Now it should return a tag that hasn't been attempted:
```json
POST /api/analytics/get-my-least-attempted
{
  "user_id": "9Tw74uo0Y2VQK8oWs8br25NFHme2",
  "subject": "math"
}

Expected: Returns a tag from a different sub-category or unused tag in algebra
```

### 4. Submit More Quizzes
Submit quizzes covering more tags, and see the least attempted change.

---

## Comparison of 3 APIs

| API | Purpose | Algorithm |
|-----|---------|-----------|
| **get-my-strength** | Find best performing tag | Highest combined score (percentage × 0.7 + score × 0.3) |
| **get-my-weakness** | Find worst performing tag | Lowest combined score (percentage × 0.7 + score × 0.3) |
| **get-my-least-attempted** | Find least practiced tag | Minimum total_questions_attempted |

**When to use each:**
- **Strength**: To award badges, show achievements, build confidence
- **Weakness**: To recommend improvement topics, targeted practice
- **Least Attempted**: To encourage exploration, diversify practice

---

## Integration Example

```javascript
// Complete student insight
async function getStudentInsights(userId, subject) {
  const [strength, weakness, leastAttempted] = await Promise.all([
    getMyStrength(userId, subject),
    getMyWeakness(userId, subject),
    getMyLeastAttempted(userId, subject)
  ]);
  
  return {
    strength: strength.tag,          // "You're great at linear-equations!"
    weakness: weakness.tag,          // "Let's work on circle-equations"
    unexplored: leastAttempted.tag   // "Haven't tried probability yet?"
  };
}

// Display on dashboard
const insights = await getStudentInsights("user123", "math");
displayDashboard(insights);
```

---

## Valid Input Values

### Subjects
- `"math"`
- `"reading-and-writing"`

### Math Sub-Categories
- `"algebra"` (15 tags)
- `"advanced-math"` (15 tags)
- `"problem-solving-and-data-analysis"` (15 tags)
- `"geometry-and-trigonometry"` (15 tags)

### Reading & Writing Sub-Categories
- `"craft-and-structure"` (15 tags)
- `"information-and-ideas"` (15 tags)
- `"standard-english-conventions"` (15 tags)
- `"expression-of-ideas"` (15 tags)

**Total**: 120 unique tags across all subjects and sub-categories

---

## Notes

1. ✅ Returns tag with minimum questions attempted
2. ✅ If multiple tags have 0 attempts, returns any one
3. ✅ Updates immediately after each quiz submission
4. ✅ Subject-specific (separate tracking per subject)
5. ✅ Returns empty string if no data exists
6. ✅ Useful for encouraging topic diversification
