# Daily Progress - Quick Reference

## 🚀 Quick Start

### 1. Get Token
```bash
python testing/get_firebase_token.py
```

### 2. Test Daily Progress
```bash
python testing/test_daily_progress.py
```

## 📡 API Endpoints

### Get Daily Progress
```bash
GET /analytics/daily-progress/{student_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "daily_progress": {
    "today": {
      "date": "2025-11-04",
      "total_quizzes": 5,
      "total_questions": 50,
      "total_correct": 42,
      "accuracy": 84.0,
      "total_time_spent": 1200,
      "hot_topic": "linear-equations",
      "hot_topic_count": 15
    },
    "yesterday": { /* similar structure */ },
    "streak": 5
  }
}
```

### Submit Quiz (Auto-updates Daily Progress)
```bash
POST /analytics/submit-quiz
Content-Type: application/json
Authorization: Bearer {token}

{
  "student_id": "user123",
  "time_spent": 300,
  "number_of_questions": 10,
  "number_of_correct_answers": 8,
  "subject": "math",
  "sub_category": "algebra",
  "difficulty_level": 3,
  "tag_wise_details": [...],
  "correct_question_ids": [...],
  "incorrect_question_ids": [...]
}
```

**Response (Immediate - 202):**
```json
{
  "success": true,
  "message": "Quiz submission received and is being processed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "estimated_score": 24,
  "estimated_accuracy": 80.0
}
```

## 📊 Metrics Explained

| Metric | Description |
|--------|-------------|
| **total_quizzes** | Number of quizzes completed today |
| **total_questions** | Total questions attempted today |
| **total_correct** | Total correct answers today |
| **accuracy** | (total_correct / total_questions) * 100 |
| **total_time_spent** | Time in seconds spent on quizzes |
| **hot_topic** | Most attempted tag today |
| **streak** | Consecutive days with activity |

## 🔥 Streak Logic

```
First activity ever     → Streak = 1
Yesterday + Today       → Streak += 1
Gap > 1 day            → Streak = 1 (reset)
Multiple quizzes today → Streak unchanged
```

## ⏰ Timezone

- **All dates use IST** (Indian Standard Time)
- Day boundary: Midnight IST
- Rollover: Yesterday's data preserved, today's reset

## 🧪 Testing

```bash
# Test the feature
python testing/test_daily_progress.py

# Expected output:
# ✅ Quiz accepted for processing
# ✅ Daily progress retrieved successfully
# 📊 TODAY'S STATS: (shows metrics)
# 📊 YESTERDAY'S STATS: (shows metrics)
# 🔥 STREAK: X days
```

## 💡 Key Features

✅ **Non-blocking** - Updates in background  
✅ **IST timezone** - Accurate for Indian users  
✅ **Auto-rollover** - Yesterday preserved at midnight  
✅ **Streak tracking** - Motivates daily practice  
✅ **Hot topic** - Shows focus areas  

## 📂 Database Location

```
Firestore Path:
users/{student_id}/analytics/daily_progress

Document Structure:
{
  "today": {...},
  "yesterday": {...},
  "streak": number,
  "last_activity_date": "YYYY-MM-DD"
}
```

## 🔗 Related Files

- `database/analytics_db.py` - Database methods
- `routes/analytics_routing.py` - API endpoints
- `DAILY_PROGRESS_API.md` - Full documentation
- `testing/test_daily_progress.py` - Test script

## 🎯 Use Cases

1. **Daily Dashboard** - Show user their daily progress
2. **Streak Motivation** - Display streak badges
3. **Comparison View** - Today vs Yesterday charts
4. **Hot Topic Badge** - Highlight most practiced topic
5. **Time Tracking** - Monitor study time
