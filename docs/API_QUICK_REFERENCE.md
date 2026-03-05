# API Quick Reference - What Changed

## 🔄 Modified APIs

### 1. GET `/api/tasks/user/{user_id}/tasks`
```javascript
// NEW: Optional query parameter
GET /api/tasks/user/{user_id}/tasks?include_completed=true

// Returns all tasks (completed + incomplete)
{ "tasks": [...], "count": 12 }
```

### 2. POST `/api/tasks/complete`
```javascript
// NEW: Response includes auto-assignment count
{
  "success": true,
  "completed": true,
  "message": "Task marked as completed",
  "next_tasks_assigned": 12  // ← NEW FIELD
}

// CHANGED: AI Tutor validation
// OLD: Required >= 15 minute session
// NEW: Requires ANY completed session (no time limit)
```

---

## ✨ New APIs

### 1. GET `/api/tutor/{user_id}/analytics`
```javascript
// Overall session statistics
{
  "analytics": {
    "total_sessions": 12,
    "total_duration_minutes": 245.5,
    "average_duration_minutes": 20.46,
    "last_session_date": "2026-03-05T10:30:00+00:00",
    "sessions_this_week": 5,
    "sessions_this_month": 12
  }
}
```

### 2. GET `/api/tutor/{user_id}/chapter-progress`
```javascript
// Per-chapter progress tracking

// All chapters
GET /api/tutor/{user_id}/chapter-progress

// Specific chapter
GET /api/tutor/{user_id}/chapter-progress?chapter_id=chapter_1

// Response
{
  "progress": {
    "chapters": {
      "chapter_1": {
        "total_sessions": 3,
        "total_duration_minutes": 45.5,
        "completed_sessions": 3,
        "sessions": [...]
      }
    }
  }
}
```

---

## 📋 Quick Code Examples

### Get All Tasks (Include Completed)
```javascript
const res = await fetch(`/api/tasks/user/${userId}/tasks?include_completed=true`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { tasks } = await res.json();
```

### Complete Task & Handle Auto-Assignment
```javascript
const res = await fetch('/api/tasks/complete', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: userId, task_id: taskId })
});
const data = await res.json();

if (data.next_tasks_assigned > 0) {
  alert(`🎉 ${data.next_tasks_assigned} new tasks unlocked!`);
}
```

### Get Tutor Analytics
```javascript
const res = await fetch(`/api/tutor/${userId}/analytics`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { analytics } = await res.json();
```

### Get Chapter Progress
```javascript
// All chapters
const res = await fetch(`/api/tutor/${userId}/chapter-progress`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { progress } = await res.json();
const chapters = progress.chapters;

// Single chapter
const res2 = await fetch(`/api/tutor/${userId}/chapter-progress?chapter_id=chapter_1`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const chapterData = await res2.json();
const canComplete = chapterData.progress.completed_sessions > 0;
```

---

## ⚡ Priority Changes

| What | Action | Priority |
|------|--------|----------|
| **AI Tutor Task Text** | Remove "15 minutes required" | 🔴 HIGH |
| **Task Instructions** | Update to "Complete at least one session" | 🔴 HIGH |
| **Chapter Progress UI** | Add new dashboard using `/chapter-progress` endpoint | 🔴 HIGH |
| **Progress Tracking** | Use `include_completed=true` param | 🟡 MEDIUM |
| **Analytics Dashboard** | Add using `/analytics` endpoint | 🟡 MEDIUM |
| **Week Completion** | Show celebration when `next_tasks_assigned > 0` | 🟢 LOW |

---

## 🧪 Test Checklist

- [ ] Fetch all tasks with `?include_completed=true`
- [ ] Complete AI tutor task (any session duration)
- [ ] Verify `next_tasks_assigned` response field
- [ ] Fetch overall tutor analytics
- [ ] Fetch all chapter progress
- [ ] Fetch single chapter progress
- [ ] Show celebration when week complete

---

## 📄 Full Documentation

See [FRONTEND_API_CHANGES.md](./FRONTEND_API_CHANGES.md) for:
- Detailed request/response examples
- React/Vue component examples
- Error handling patterns
- Migration timeline
