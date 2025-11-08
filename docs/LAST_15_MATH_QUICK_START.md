# Last 15 Math Questions - Quick Start Guide

## 🚀 Quick Setup (Already Done!)

The feature is **automatically active**. No setup required! ✅

## 📝 How It Works

### Automatic Tracking
Every time a user submits a **math quiz**, the last 15 questions are automatically saved.

```
User submits math quiz → System updates last_15_math_questions → Ready to query!
```

## 🔥 Quick Test

### Step 1: Submit a Math Quiz
```bash
curl -X POST http://localhost:5000/api/analytics/submit-quiz \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
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

### Step 2: Get Last 15 Questions
```bash
curl -X GET http://localhost:5000/api/analytics/last-15-math-questions/test_user \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 3: Check Response
```json
{
  "success": true,
  "data": {
    "student_id": "test_user",
    "questions": [
      {
        "question_id": "q1",
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

## 💡 Common Use Cases

### 1. Show Recent Questions
```python
import requests

response = requests.get(
    f"{BASE_URL}/analytics/last-15-math-questions/{user_id}",
    headers={"Authorization": f"Bearer {token}"}
)
questions = response.json()['data']['questions']
```

### 2. Filter Wrong Answers
```python
wrong_answers = [q for q in questions if not q['is_answered_correctly']]
print(f"Review {len(wrong_answers)} incorrect questions")

# Show each wrong answer with full details
for q in wrong_answers:
    print(f"\nQuestion: {q['question_text']}")
    print(f"Options: {q['options']}")
    print(f"Correct answer: {q['correct_answer']}")
```

### 3. Check Difficulty Trend
```python
difficulties = [q['difficulty_level'] for q in questions]
avg_difficulty = sum(difficulties) / len(difficulties)
print(f"Average difficulty: {avg_difficulty:.1f}")
```

### 4. Avoid Repeating Questions
```python
recent_question_ids = {q['question_id'] for q in questions}
new_questions = [q for q in question_pool if q['id'] not in recent_question_ids]
```

## 📊 What Gets Tracked?

For each question:
- ✅ Question ID
- ✅ **Question Text** (full question)
- ✅ **Options** (A, B, C, D)
- ✅ **Correct Answer**
- ✅ **Is Answered Correctly** (boolean)
- ✅ Difficulty level (1-5)
- ✅ Tags (concepts)
- ✅ Sub-category
- ✅ Timestamp

## ⚡ Key Points

1. **Automatic**: No manual action needed
2. **Math Only**: Only tracks math subject questions
3. **Last 15**: Keeps only most recent 15 questions
4. **Fast**: Pre-aggregated for quick retrieval
5. **Non-blocking**: Won't fail quiz submission if update fails

## 🎯 API Endpoint

```
GET /api/analytics/last-15-math-questions/<student_id>
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "student_id": "...",
    "questions": [...],
    "count": 15,
    "last_updated": "..."
  }
}
```

## 🔍 Database Location

```
Firestore Path:
users/{student_id}/analytics/last_15_math_questions

Document Structure:
{
  student_id: "...",
  questions: [...],
  last_updated: "..."
}
```

## ❓ FAQ

**Q: How do I enable this feature?**  
A: It's already enabled! Just submit math quizzes.

**Q: What if I want more than 15 questions?**  
A: Use `/analytics/activity-logs/<student_id>` for full history.

**Q: Does it track reading questions?**  
A: No, only math. Reading can be added if needed.

**Q: What happens after 15 questions?**  
A: Oldest questions are automatically removed.

**Q: Can I filter by difficulty or tag?**  
A: Not yet. Filter client-side for now.

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| Empty list returned | User hasn't attempted math quizzes yet |
| Missing questions | Only last 15 are kept (by design) |
| Wrong subject questions | Only math is tracked (check subject field) |

## 📚 Related APIs

- **Submit Quiz**: `/analytics/submit-quiz` - Populates the data
- **Activity Logs**: `/analytics/activity-logs/<student_id>` - Full history
- **Performance Summary**: `/analytics/performance-summary/<student_id>` - Overall stats

## 🎓 Example Integration

```javascript
// React Component Example
const RecentQuestions = ({ userId, token }) => {
  const [questions, setQuestions] = useState([]);
  
  useEffect(() => {
    fetch(`/api/analytics/last-15-math-questions/${userId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => setQuestions(data.data.questions))
    .catch(err => console.error(err));
  }, [userId]);
  
  return (
    <div>
      <h2>Recent Math Questions</h2>
      {questions.map(q => (
        <div key={q.question_id} className={q.is_answered_correctly ? 'correct' : 'incorrect'}>
          <h3>{q.is_answered_correctly ? '✓' : '✗'} {q.question_text}</h3>
          <div className="options">
            {Object.entries(q.options).map(([key, value]) => (
              <div key={key}>
                <strong>{key}:</strong> {value}
                {key === q.correct_answer && ' ← Correct'}
              </div>
            ))}
          </div>
          <p>Difficulty: {q.difficulty_level} | {q.sub_category}</p>
        </div>
      ))}
    </div>
  );
};
```

## ✅ Done!

You're ready to use the Last 15 Math Questions API! 🎉

For detailed documentation, see: [LAST_15_MATH_QUESTIONS_API.md](./LAST_15_MATH_QUESTIONS_API.md)
