# Daily Progress API Documentation

## Overview
The Daily Progress feature tracks student's daily quiz activity and provides comparative analytics between today and yesterday. All date/time calculations use **Indian Standard Time (IST)**.

## Features

### 📊 Tracked Metrics
1. **Quizzing Time Today** - Total time spent on quizzes (in seconds)
2. **Number of Quizzes Taken Today** - Count of completed quizzes
3. **Accuracy Today** - Overall percentage of correct answers
4. **Hot Topic Today** - Most attempted tag/topic
5. **Streak** - Consecutive days of activity

### 🔄 Auto-Update Mechanism
- **Background Processing**: Daily progress is updated automatically when a quiz is submitted
- **Non-blocking**: Updates happen in a separate thread, doesn't block API response
- **IST Timezone**: All date calculations use Indian Standard Time
- **Automatic Rollover**: Yesterday's stats are preserved, today's stats reset at midnight (IST)

## Database Structure

**Location**: `users/{student_id}/analytics/daily_progress`

```json
{
  "student_id": "user123",
  "today": {
    "date": "2025-11-04",
    "total_time_spent": 1200,
    "total_quizzes": 5,
    "total_questions": 50,
    "total_correct": 42,
    "accuracy": 84.0,
    "hot_topic": "linear-equations",
    "hot_topic_count": 15,
    "tags": {
      "linear-equations": 15,
      "quadratic-equations": 10,
      "systems-of-equations": 8
    }
  },
  "yesterday": {
    "date": "2025-11-03",
    "total_time_spent": 900,
    "total_quizzes": 3,
    "total_questions": 30,
    "total_correct": 25,
    "accuracy": 83.33,
    "hot_topic": "systems-of-equations",
    "hot_topic_count": 12,
    "tags": {...}
  },
  "streak": 5,
  "last_activity_date": "2025-11-04",
  "last_updated": "2025-11-04T10:30:45.123Z"
}
```

## API Endpoints

### 1. Get Daily Progress

**Endpoint**: `GET /analytics/daily-progress/<student_id>`

**Authentication**: Required (Bearer token)

**URL Parameters**:
- `student_id` (string, required): The student's user ID

**Response**:
```json
{
  "success": true,
  "daily_progress": {
    "today": {
      "date": "2025-11-04",
      "total_time_spent": 1200,
      "total_quizzes": 5,
      "total_questions": 50,
      "total_correct": 42,
      "accuracy": 84.0,
      "hot_topic": "linear-equations",
      "hot_topic_count": 15,
      "tags": {...}
    },
    "yesterday": {
      "date": "2025-11-03",
      "total_time_spent": 900,
      "total_quizzes": 3,
      "total_questions": 30,
      "total_correct": 25,
      "accuracy": 83.33,
      "hot_topic": "systems-of-equations",
      "hot_topic_count": 12,
      "tags": {...}
    },
    "streak": 5,
    "last_activity_date": "2025-11-04"
  }
}
```

**Error Responses**:
- `404`: User not found
- `500`: Server error

### 2. Submit Quiz (Auto-updates Daily Progress)

**Endpoint**: `POST /analytics/submit-quiz`

**Note**: This endpoint now runs in the background and automatically updates daily progress after storing quiz analytics.

**Response** (Immediate):
```json
{
  "success": true,
  "message": "Quiz submission received and is being processed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "estimated_score": 42,
  "estimated_total_possible_score": 50,
  "estimated_accuracy": 84.0,
  "subject": "math",
  "sub_category": "algebra",
  "difficulty_level": 3
}
```

**Status Code**: `202 Accepted` (indicates asynchronous processing)

## Streak Calculation Logic

### Streak Rules:
1. **First Activity**: Streak = 1
2. **Consecutive Day**: If yesterday had activity and today has activity → Streak += 1
3. **Gap in Activity**: If more than 1 day gap → Streak resets to 1
4. **Same Day**: Multiple quizzes on same day don't affect streak

### Examples:

| Scenario | Last Activity | Current Activity | Result |
|----------|---------------|------------------|--------|
| First time user | None | 2025-11-04 | Streak = 1 |
| Consecutive days | 2025-11-03 | 2025-11-04 | Streak += 1 |
| Gap of 1+ days | 2025-11-02 | 2025-11-04 | Streak = 1 |
| Same day activity | 2025-11-04 | 2025-11-04 | Streak unchanged |

## Usage Examples

### cURL Example
```bash
# Get daily progress
curl -X GET "http://localhost:5000/analytics/daily-progress/user123" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Python Example
```python
import requests

# Get daily progress
url = "http://localhost:5000/analytics/daily-progress/user123"
headers = {
    "Authorization": "Bearer YOUR_TOKEN_HERE"
}

response = requests.get(url, headers=headers)
data = response.json()

if data['success']:
    progress = data['daily_progress']
    
    # Compare today vs yesterday
    today_quizzes = progress['today']['total_quizzes']
    yesterday_quizzes = progress['yesterday'].get('total_quizzes', 0)
    
    print(f"Today: {today_quizzes} quizzes")
    print(f"Yesterday: {yesterday_quizzes} quizzes")
    print(f"Current streak: {progress['streak']} days")
    print(f"Hot topic: {progress['today']['hot_topic']}")
```

### JavaScript Example
```javascript
// Get daily progress
fetch('http://localhost:5000/analytics/daily-progress/user123', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN_HERE'
  }
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    const progress = data.daily_progress;
    
    // Display comparison
    console.log('Today:', progress.today.total_quizzes, 'quizzes');
    console.log('Yesterday:', progress.yesterday.total_quizzes || 0, 'quizzes');
    console.log('Streak:', progress.streak, 'days');
    console.log('Accuracy today:', progress.today.accuracy, '%');
  }
});
```

## Implementation Details

### Background Processing
The daily progress update happens in a separate thread after quiz submission:

```python
# In analytics_routing.py - background thread
def process_quiz_submission_background(submission_data, request_id):
    # ... submit analytics ...
    
    # Update daily progress (non-blocking)
    analytics_db.update_daily_progress(student_id, submission)
```

### Timezone Handling
All date calculations use IST timezone:

```python
import pytz
from datetime import datetime

IST = pytz.timezone('Asia/Kolkata')

# Get current IST date
now_ist = datetime.now(IST)
today_date = now_ist.date().isoformat()  # "2025-11-04"
```

### Day Rollover Logic
```python
# Check if new day (IST)
if last_activity_date != today_date:
    yesterday_ist = (now_ist - timedelta(days=1)).date().isoformat()
    
    if last_activity_date == yesterday_ist:
        # Consecutive day - increment streak
        streak += 1
        # Move today -> yesterday
    else:
        # Gap - reset streak
        streak = 1
        # Clear yesterday data
    
    # Reset today's data
```

## Benefits

✅ **Real-time Updates**: Automatic background processing  
✅ **Non-blocking**: Doesn't slow down quiz submission  
✅ **IST Timezone**: Accurate for Indian users  
✅ **Comparative Analytics**: Easy today vs yesterday comparison  
✅ **Streak Motivation**: Encourages daily practice  
✅ **Hot Topic Tracking**: Identifies focus areas  

## Error Handling

- Database connection failures are logged
- Failed updates don't block quiz submission
- Graceful degradation if daily progress update fails
- Empty structure returned if no data available

## Future Enhancements

- [ ] Weekly/Monthly aggregations
- [ ] Streak milestones and achievements
- [ ] Comparison with peer averages
- [ ] Time-of-day analytics
- [ ] Performance trends over time
