# Per-Chapter Progress Tracking for AI Tutor

## Overview

The AI tutor task completion system has been updated to track **per-chapter progress** instead of enforcing a rigid 15-minute minimum duration requirement.

## Changes Made

### 1. ✅ Removed 15-Minute Requirement

**Previous behavior:**
- AI tutor tasks required at least one session with `duration_minutes >= 15`
- Shorter sessions (even if completed) didn't count toward task completion

**New behavior:**
- **ANY completed session** (where `is_active == False`) for the chapter allows task completion
- Duration doesn't affect completion validation
- All session data is still tracked for analytics

**Files modified:**
- [`routes/task_routing.py`](../routes/task_routing.py#L308-L330) - Task completion validation

### 2. ✅ Added Per-Chapter Progress Tracking

**New database method:**
```python
SessionDatabase.get_chapter_progress(user_id: str, chapter_id: str = None) -> Dict
```

**Returns data per chapter:**
- `chapter_id` - Chapter identifier
- `lecture_subject` - Subject (e.g., "SAT")
- `total_sessions` - Total number of sessions for this chapter
- `total_duration_minutes` - Cumulative time spent (all sessions combined)
- `average_duration_minutes` - Average session length
- `completed_sessions` - Number of finished sessions (is_active == False)
- `first_session_date` - Timestamp of first session
- `last_session_date` - Timestamp of most recent session
- `sessions[]` - Array of individual session details

**Files modified:**
- [`database/session_db.py`](../database/session_db.py#L205-L285) - Added `get_chapter_progress()` method

### 3. ✅ New Analytics API Endpoints

#### **GET** `/api/tutor/{user_id}/analytics`
Returns overall session statistics for a user.

**Response:**
```json
{
  "message": "Analytics retrieved successfully",
  "analytics": {
    "total_sessions": 12,
    "total_duration_minutes": 245.5,
    "average_duration_minutes": 20.46,
    "last_session_date": "2026-03-05T10:30:00Z",
    "sessions_this_week": 5,
    "sessions_this_month": 12
  }
}
```

#### **GET** `/api/tutor/{user_id}/chapter-progress`
Returns progress data for all chapters.

**Response:**
```json
{
  "message": "Progress retrieved for 3 chapters",
  "total_chapters": 3,
  "progress": {
    "chapters": {
      "chapter_1": {
        "chapter_id": "chapter_1",
        "lecture_subject": "SAT",
        "total_sessions": 3,
        "total_duration_minutes": 45.5,
        "average_duration_minutes": 15.17,
        "completed_sessions": 3,
        "first_session_date": "2026-03-01T14:00:00Z",
        "last_session_date": "2026-03-05T09:30:00Z",
        "sessions": [
          {
            "session_id": "abc123",
            "created_at": "2026-03-05T09:30:00Z",
            "duration_minutes": 18.5,
            "is_active": false,
            "summary": "Discussed quadratic equations..."
          }
        ]
      }
    }
  }
}
```

#### **GET** `/api/tutor/{user_id}/chapter-progress?chapter_id={chapter_id}`
Returns progress data for a specific chapter only.

**Query Parameters:**
- `chapter_id` (optional) - Filter by specific chapter

**Response:**
```json
{
  "message": "Chapter progress retrieved successfully",
  "progress": {
    "chapter_id": "chapter_1",
    "lecture_subject": "SAT",
    "total_sessions": 3,
    "total_duration_minutes": 45.5,
    "average_duration_minutes": 15.17,
    "completed_sessions": 3,
    "first_session_date": "2026-03-01T14:00:00Z",
    "last_session_date": "2026-03-05T09:30:00Z",
    "sessions": [...]
  }
}
```

**Files modified:**
- [`routes/tutor_routing.py`](../routes/tutor_routing.py#L258-L353) - Added two new endpoints

## Task Completion Logic

### AI Tutorial Task Completion

**Location:** [`routes/task_routing.py`](../routes/task_routing.py#L308-L330)

**New validation logic:**
```python
# Check if any completed session exists for this chapter
sessions_ref = (
    firestore_client.collection('session_summary')
    .document(user_id)
    .collection('sessions')
    .where('lecture_chapter', '==', chapter_id)
    .where('is_active', '==', False)
    .limit(1)
    .stream()
)

if any(True for _ in sessions_ref):
    can_complete = True  # ✓ Task can be marked complete
else:
    failure_reason = "Please complete at least one AI Tutor session..."
```

**Completion criteria:**
1. Task must have a `chapter_id` in `ai_tutorial_related_attributes`
2. User must have at least **one session** where:
   - `lecture_chapter == chapter_id`
   - `is_active == False` (session has been ended)
3. **Duration is irrelevant** - 5 minutes counts the same as 60 minutes

## Frontend Integration

### Display Per-Chapter Progress

```javascript
// Fetch all chapter progress
const response = await fetch(`/api/tutor/${userId}/chapter-progress`, {
  headers: { 'Authorization': `Bearer ${token}` }
});

const data = await response.json();
const chapters = data.progress.chapters;

// Display chapter cards
Object.values(chapters).forEach(chapter => {
  console.log(`${chapter.chapter_id}: ${chapter.completed_sessions} sessions, ${chapter.total_duration_minutes} mins`);
});
```

### Check Task Completion Eligibility

```javascript
// Check if user can complete a specific chapter task
const response = await fetch(`/api/tutor/${userId}/chapter-progress?chapter_id=chapter_1`, {
  headers: { 'Authorization': `Bearer ${token}` }
});

const data = await response.json();
const canComplete = data.progress.completed_sessions > 0;

if (canComplete) {
  enableCompleteButton();
}
```

## Testing

### Run Test Script

```powershell
# Update TEST_USER_ID and TEST_CHAPTER_ID in the script first
cd testing
python test_chapter_progress.py
```

### Manual API Testing

```powershell
# Get bearer token
cd testing
python get_firebase_token.py

# Test endpoints (replace USER_ID and TOKEN)
$token = "YOUR_FIREBASE_TOKEN"
$userId = "test_user_123"

# Overall analytics
Invoke-RestMethod -Uri "http://localhost:8000/api/tutor/$userId/analytics" `
  -Headers @{"Authorization"="Bearer $token"}

# All chapter progress
Invoke-RestMethod -Uri "http://localhost:8000/api/tutor/$userId/chapter-progress" `
  -Headers @{"Authorization"="Bearer $token"}

# Specific chapter
Invoke-RestMethod -Uri "http://localhost:8000/api/tutor/$userId/chapter-progress?chapter_id=chapter_1" `
  -Headers @{"Authorization"="Bearer $token"}
```

## Migration Notes

### Impact on Existing Data

✅ **No data migration needed** - All existing sessions remain valid

**Before (15-min requirement):**
- Session 1: 8 minutes → ❌ Didn't count
- Session 2: 20 minutes → ✓ Counted
- **Result:** Task could be completed

**After (any completed session):**
- Session 1: 8 minutes, is_active=False → ✓ Counts
- Session 2: 20 minutes, is_active=False → ✓ Counts
- **Result:** Task can be completed (same outcome, easier to achieve)

### Behavioral Changes

1. **Easier task completion** - Users no longer need to maintain 15-minute sessions
2. **More flexible learning** - Short, focused sessions (5-10 mins) now count
3. **Better analytics** - Frontend can show cumulative progress across multiple sessions
4. **No breaking changes** - Existing completed tasks remain valid

## Summary

| Feature | Before | After |
|---------|--------|-------|
| **Completion Requirement** | ≥15 min session | Any completed session |
| **Progress Tracking** | Session-level only | Per-chapter aggregation |
| **Analytics API** | ❌ Not exposed | ✅ Two new endpoints |
| **Frontend Visibility** | Limited | Full chapter progress |
| **Validation Logic** | Duration-based | Completion-based |

**Key Benefits:**
- More user-friendly (short sessions count)
- Better progress visibility for students
- Richer analytics for instructors
- Flexible learning patterns supported
