# Frontend API Integration Guide - Recent Changes

## Overview
This document outlines all API changes that require frontend updates, including new endpoints, modified behavior, and integration examples.

---

## 1. Task APIs - Modified Behavior

### 1.1 GET `/api/tasks/user/{user_id}/tasks` - **ENHANCED**

**What Changed:**
- Added optional query parameter `include_completed`
- Default behavior unchanged (returns only incomplete tasks)
- New option to fetch ALL tasks (completed + incomplete) in current week

**Endpoint:**
```
GET /api/tasks/user/{user_id}/tasks?include_completed={true|false}
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_completed` | boolean | `false` | If true, returns both completed and incomplete tasks |

**Response:**
```json
{
  "success": true,
  "tasks": [
    {
      "task_id": "task_123",
      "title": "Quiz: Algebra - Linear Equations",
      "type_of_task": "QUIZ",
      "is_completed": false,
      "priority": "HIGH",
      "due_date": "2026-03-10T23:59:59Z",
      "task_number": 1,
      "quiz_related_attributes": {
        "subject": "Math",
        "num_questions": 10,
        "area": "unexplored"
      }
    }
  ],
  "count": 5
}
```

**Frontend Integration Examples:**

```javascript
// Example 1: Get only incomplete tasks (default behavior - no change needed)
async function getIncompleteTasks(userId, token) {
  const response = await fetch(`/api/tasks/user/${userId}/tasks`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await response.json();
  return data.tasks; // Only incomplete tasks
}

// Example 2: Get ALL tasks (new - use for progress tracking UI)
async function getAllCurrentTasks(userId, token) {
  const response = await fetch(`/api/tasks/user/${userId}/tasks?include_completed=true`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await response.json();
  return data.tasks; // Both completed and incomplete
}

// Example 3: Display completion progress
async function showWeeklyProgress(userId, token) {
  const allTasks = await getAllCurrentTasks(userId, token);
  const completedCount = allTasks.filter(t => t.is_completed).length;
  const totalCount = allTasks.length;
  
  console.log(`Progress: ${completedCount}/${totalCount} tasks completed`);
  // Update UI: progress bar, percentage, etc.
}
```

**React Example:**
```jsx
import { useState, useEffect } from 'react';

function TasksOverview({ userId, token }) {
  const [allTasks, setAllTasks] = useState([]);
  const [incompleteTasks, setIncompleteTasks] = useState([]);

  useEffect(() => {
    // Fetch all tasks for progress display
    fetch(`/api/tasks/user/${userId}/tasks?include_completed=true`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setAllTasks(data.tasks));

    // Fetch incomplete tasks for to-do list
    fetch(`/api/tasks/user/${userId}/tasks`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setIncompleteTasks(data.tasks));
  }, [userId, token]);

  const completedCount = allTasks.filter(t => t.is_completed).length;
  const progressPercent = (completedCount / allTasks.length) * 100;

  return (
    <div>
      <h2>Weekly Progress: {completedCount}/{allTasks.length}</h2>
      <ProgressBar percent={progressPercent} />
      
      <h3>To-Do ({incompleteTasks.length} remaining)</h3>
      <TaskList tasks={incompleteTasks} />
    </div>
  );
}
```

---

### 1.2 POST `/api/tasks/complete` - **BEHAVIOR CHANGED**

**What Changed:**
- **AI Tutorial tasks** no longer require 15-minute minimum duration
- Now accepts ANY completed session for the chapter (regardless of duration)
- Response now includes `next_tasks_assigned` count

**Endpoint:**
```
POST /api/tasks/complete
```

**Request Body:**
```json
{
  "user_id": "user_123",
  "task_id": "task_456",
  "score": 8,           // For QUIZ tasks (number of correct answers)
  "num_questions": 10   // For QUIZ tasks
}
```

**Response:**
```json
{
  "success": true,
  "completed": true,
  "message": "Task marked as completed",
  "next_tasks_assigned": 12
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the request succeeded |
| `completed` | boolean | Whether task was marked complete (false if validation failed) |
| `message` | string | Success message or failure reason |
| `next_tasks_assigned` | number | Number of new tasks auto-assigned (0 if no new set) |

**Validation Changes by Task Type:**

#### QUIZ Tasks (Unchanged)
- **Unexplored:** 40% accuracy required (4/10 questions)
- **Weakness:** 60% accuracy required (6/10 questions)
- **Strength:** 80% accuracy required (8/10 questions)

#### AI_TUTORIAL Tasks (**CHANGED**)

**OLD Behavior:**
```
❌ Required: Session with duration_minutes >= 15
Example: 8-minute session = rejected, 20-minute session = accepted
```

**NEW Behavior:**
```
✅ Required: ANY completed session (is_active == False) for the chapter
Example: 5-minute session = accepted, 60-minute session = accepted
```

**Frontend Impact:**
- **Remove** any UI that mentions "15 minutes required"
- **Update** task instructions to say "Complete at least one AI tutor session for this chapter"
- **Show** cumulative time across multiple sessions (see Chapter Progress APIs below)

#### SAT_PREDICTOR Tasks (Unchanged)
- Requires submission to sat_predictor_performance collection

#### MOCK_TEST Tasks (Unchanged)
- Requires mock_attempts document for the specific mock_id

**Frontend Example:**

```javascript
async function completeTask(userId, taskId, taskType, score = null, numQuestions = null) {
  const payload = {
    user_id: userId,
    task_id: taskId
  };

  // Add score data for quiz tasks
  if (taskType === 'QUIZ' && score !== null && numQuestions !== null) {
    payload.score = score;
    payload.num_questions = numQuestions;
  }

  const response = await fetch('/api/tasks/complete', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  const data = await response.json();

  if (data.completed) {
    console.log('✓ Task completed successfully');
    
    // Check if new tasks were auto-assigned
    if (data.next_tasks_assigned > 0) {
      console.log(`🎉 All tasks done! ${data.next_tasks_assigned} new tasks assigned`);
      // Refresh task list, show celebration animation, etc.
      await refreshTasks();
    }
  } else {
    // Task validation failed
    console.error('Task completion failed:', data.message);
    alert(data.message); // Show user-friendly error
  }
}
```

**React Example:**
```jsx
function TaskCompleteButton({ task, userId, token, onComplete }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleComplete = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/tasks/complete', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: userId,
          task_id: task.task_id,
          // Include score if quiz task
          ...(task.type_of_task === 'QUIZ' && {
            score: task.userScore,
            num_questions: task.quiz_related_attributes.num_questions
          })
        })
      });

      const data = await response.json();

      if (data.completed) {
        // Show success
        if (data.next_tasks_assigned > 0) {
          showCelebration(`Week complete! ${data.next_tasks_assigned} new tasks unlocked`);
        }
        onComplete();
      } else {
        // Show validation error
        setError(data.message);
      }
    } catch (err) {
      setError('Failed to complete task. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={handleComplete} disabled={loading}>
        {loading ? 'Completing...' : 'Mark Complete'}
      </button>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
```

---

## 2. AI Tutor APIs - NEW ENDPOINTS

### 2.1 GET `/api/tutor/{user_id}/analytics` - **NEW**

Get overall session analytics for a user.

**Endpoint:**
```
GET /api/tutor/{user_id}/analytics
```

**Headers:**
```
Authorization: Bearer {firebase_token}
```

**Response:**
```json
{
  "message": "Analytics retrieved successfully",
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

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `total_sessions` | number | Total completed sessions (all time) |
| `total_duration_minutes` | number | Cumulative time across all sessions |
| `average_duration_minutes` | number | Average session length |
| `last_session_date` | string (ISO) | Timestamp of most recent session |
| `sessions_this_week` | number | Sessions in current week (Mon-Sun) |
| `sessions_this_month` | number | Sessions in current month |

**Frontend Example:**

```javascript
async function getTutorAnalytics(userId, token) {
  const response = await fetch(`/api/tutor/${userId}/analytics`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await response.json();
  return data.analytics;
}

// Usage
const analytics = await getTutorAnalytics('user_123', token);
console.log(`Total learning time: ${analytics.total_duration_minutes} minutes`);
console.log(`This week: ${analytics.sessions_this_week} sessions`);
```

**React Component Example:**
```jsx
function TutorStats({ userId, token }) {
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    fetch(`/api/tutor/${userId}/analytics`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setAnalytics(data.analytics));
  }, [userId, token]);

  if (!analytics) return <div>Loading...</div>;

  return (
    <div className="tutor-stats">
      <h3>AI Tutor Statistics</h3>
      <div className="stat-card">
        <span className="stat-value">{analytics.total_sessions}</span>
        <span className="stat-label">Total Sessions</span>
      </div>
      <div className="stat-card">
        <span className="stat-value">{Math.round(analytics.total_duration_minutes)}</span>
        <span className="stat-label">Minutes Learned</span>
      </div>
      <div className="stat-card">
        <span className="stat-value">{analytics.sessions_this_week}</span>
        <span className="stat-label">This Week</span>
      </div>
    </div>
  );
}
```

---

### 2.2 GET `/api/tutor/{user_id}/chapter-progress` - **NEW**

Get per-chapter learning progress for a user.

**Endpoint:**
```
GET /api/tutor/{user_id}/chapter-progress?chapter_id={chapter_id}
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chapter_id` | string | No | Filter by specific chapter. If omitted, returns all chapters. |

**Headers:**
```
Authorization: Bearer {firebase_token}
```

**Response (All Chapters):**
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
        "first_session_date": "2026-03-01T14:00:00+00:00",
        "last_session_date": "2026-03-05T09:30:00+00:00",
        "sessions": [
          {
            "session_id": "session_abc123",
            "created_at": "2026-03-05T09:30:00+00:00",
            "duration_minutes": 18.5,
            "is_active": false,
            "summary": "Discussed quadratic equations and factoring methods..."
          },
          {
            "session_id": "session_def456",
            "created_at": "2026-03-03T16:20:00+00:00",
            "duration_minutes": 12.0,
            "is_active": false,
            "summary": "Reviewed parabola graphing techniques..."
          }
        ]
      },
      "chapter_2": {
        "chapter_id": "chapter_2",
        "lecture_subject": "SAT",
        "total_sessions": 1,
        "total_duration_minutes": 8.5,
        "average_duration_minutes": 8.5,
        "completed_sessions": 1,
        "first_session_date": "2026-03-04T11:00:00+00:00",
        "last_session_date": "2026-03-04T11:00:00+00:00",
        "sessions": [...]
      }
    }
  }
}
```

**Response (Single Chapter):**
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
    "first_session_date": "2026-03-01T14:00:00+00:00",
    "last_session_date": "2026-03-05T09:30:00+00:00",
    "sessions": [...]
  }
}
```

**Response Fields (Per Chapter):**
| Field | Type | Description |
|-------|------|-------------|
| `chapter_id` | string | Chapter identifier |
| `lecture_subject` | string | Subject (e.g., "SAT", "Math") |
| `total_sessions` | number | Number of sessions for this chapter |
| `total_duration_minutes` | number | Cumulative time across all sessions |
| `average_duration_minutes` | number | Average session duration |
| `completed_sessions` | number | Sessions that have ended (is_active == false) |
| `first_session_date` | string (ISO) | First session timestamp |
| `last_session_date` | string (ISO) | Most recent session timestamp |
| `sessions` | array | Individual session details (see below) |

**Session Object:**
| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Session identifier |
| `created_at` | string (ISO) | Session start timestamp |
| `duration_minutes` | number | Session duration in minutes |
| `is_active` | boolean | Whether session is ongoing (should be false) |
| `summary` | string | AI-generated conversation summary |

**Frontend Examples:**

```javascript
// Example 1: Get progress for all chapters
async function getAllChapterProgress(userId, token) {
  const response = await fetch(`/api/tutor/${userId}/chapter-progress`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await response.json();
  return data.progress.chapters;
}

// Example 2: Get progress for specific chapter
async function getChapterProgress(userId, chapterId, token) {
  const response = await fetch(
    `/api/tutor/${userId}/chapter-progress?chapter_id=${chapterId}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  const data = await response.json();
  return data.progress;
}

// Example 3: Check if chapter task can be completed
async function canCompleteChapterTask(userId, chapterId, token) {
  const progress = await getChapterProgress(userId, chapterId, token);
  return progress.completed_sessions > 0;
}

// Example 4: Display chapter cards with progress
async function displayChapterProgress(userId, token) {
  const chapters = await getAllChapterProgress(userId, token);
  
  Object.values(chapters).forEach(chapter => {
    console.log(`
      Chapter: ${chapter.chapter_id}
      Sessions: ${chapter.completed_sessions}
      Total Time: ${chapter.total_duration_minutes} mins
      Avg Duration: ${chapter.average_duration_minutes} mins
      Can Complete Task: ${chapter.completed_sessions > 0 ? '✓' : '✗'}
    `);
  });
}
```

**React Component Example:**
```jsx
function ChapterProgressDashboard({ userId, token }) {
  const [chapters, setChapters] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/tutor/${userId}/chapter-progress`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => {
        setChapters(data.progress.chapters || {});
        setLoading(false);
      });
  }, [userId, token]);

  if (loading) return <div>Loading chapters...</div>;

  return (
    <div className="chapter-grid">
      {Object.values(chapters).map(chapter => (
        <ChapterCard key={chapter.chapter_id} chapter={chapter} />
      ))}
    </div>
  );
}

function ChapterCard({ chapter }) {
  const canCompleteTask = chapter.completed_sessions > 0;
  
  return (
    <div className="chapter-card">
      <h3>{chapter.chapter_id}</h3>
      <div className="progress-stats">
        <div className="stat">
          <span className="value">{chapter.completed_sessions}</span>
          <span className="label">Sessions</span>
        </div>
        <div className="stat">
          <span className="value">{Math.round(chapter.total_duration_minutes)}</span>
          <span className="label">Minutes</span>
        </div>
      </div>
      
      {canCompleteTask ? (
        <div className="status-complete">✓ Task can be completed</div>
      ) : (
        <div className="status-incomplete">Complete a session to unlock task</div>
      )}
      
      <div className="session-history">
        <h4>Recent Sessions</h4>
        {chapter.sessions.slice(0, 3).map(session => (
          <div key={session.session_id} className="session-item">
            <span>{new Date(session.created_at).toLocaleDateString()}</span>
            <span>{session.duration_minutes} mins</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Vue.js Example:**
```vue
<template>
  <div class="chapter-progress">
    <h2>Chapter Progress</h2>
    
    <div v-if="loading">Loading...</div>
    
    <div v-else class="chapter-list">
      <div 
        v-for="chapter in chapters" 
        :key="chapter.chapter_id"
        class="chapter-item"
      >
        <h3>{{ chapter.chapter_id }}</h3>
        <p>{{ chapter.completed_sessions }} sessions, {{ chapter.total_duration_minutes }} mins</p>
        <span v-if="chapter.completed_sessions > 0" class="badge-success">
          ✓ Unlocked
        </span>
        <span v-else class="badge-locked">🔒 Locked</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: ['userId', 'token'],
  data() {
    return {
      chapters: [],
      loading: true
    };
  },
  async mounted() {
    const response = await fetch(`/api/tutor/${this.userId}/chapter-progress`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    const data = await response.json();
    this.chapters = Object.values(data.progress.chapters || {});
    this.loading = false;
  }
};
</script>
```

---

## 3. Summary of Frontend Changes Required

### 3.1 Immediate Action Items

| Component | Action | Priority |
|-----------|--------|----------|
| **Task List Page** | Add `include_completed=true` param to show all tasks | Medium |
| **Progress Dashboard** | Display weekly progress using all tasks endpoint | High |
| **Task Detail Page** | Remove "15 minutes required" text for AI Tutor tasks | High |
| **Task Instructions** | Update to "Complete at least one session" | High |
| **Tutor Dashboard** | Add overall analytics display (new endpoint) | Medium |
| **Chapter Cards** | Add per-chapter progress (new endpoint) | High |
| **Task Complete Handler** | Handle `next_tasks_assigned` response field | Medium |
| **Celebration Modal** | Show when all tasks done and new set assigned | Low |

### 3.2 UI/UX Recommendations

#### Task Completion Messages
```
OLD: "Complete a 15-minute AI tutor session for this chapter"
NEW: "Complete at least one AI tutor session for this chapter"

OLD: "Session too short (8 mins). Minimum 15 minutes required."
NEW: [Remove this validation - backend handles it]
```

#### Progress Display
```javascript
// Show cumulative progress across multiple sessions
function displayTutorProgress(chapterProgress) {
  return `
    <div class="tutor-progress">
      <h4>${chapterProgress.chapter_id}</h4>
      <p>${chapterProgress.completed_sessions} sessions completed</p>
      <p>${chapterProgress.total_duration_minutes} total minutes</p>
      <p>Average: ${chapterProgress.average_duration_minutes} mins/session</p>
      ${chapterProgress.completed_sessions > 0 
        ? '<span class="status-unlocked">✓ Task can be completed</span>'
        : '<span class="status-locked">Complete a session to unlock</span>'
      }
    </div>
  `;
}
```

#### Weekly Task Completion Celebration
```javascript
// After completing a task
async function handleTaskCompletion(taskId) {
  const result = await completeTask(taskId);
  
  if (result.next_tasks_assigned > 0) {
    // Show celebration modal
    showModal({
      title: "🎉 Week Complete!",
      message: `Amazing work! You've completed all tasks for this week.`,
      details: `${result.next_tasks_assigned} new tasks are now available.`,
      action: "View New Tasks"
    });
  }
}
```

---

## 4. Testing Checklist

### 4.1 Task APIs Testing

- [ ] Fetch incomplete tasks (default behavior)
- [ ] Fetch all tasks with `include_completed=true`
- [ ] Verify completed tasks show `is_completed: true`
- [ ] Complete a quiz task with correct score
- [ ] Complete an AI tutor task (any session duration)
- [ ] Verify error message when task validation fails
- [ ] Verify `next_tasks_assigned` when completing last task
- [ ] Verify new tasks appear after completing all tasks

### 4.2 Tutor Analytics Testing

- [ ] Fetch overall analytics for user
- [ ] Verify total sessions count is accurate
- [ ] Verify total duration calculation
- [ ] Check sessions_this_week updates correctly
- [ ] Fetch progress for all chapters
- [ ] Fetch progress for specific chapter
- [ ] Verify chapter progress shows all sessions
- [ ] Check that completed_sessions count is accurate
- [ ] Verify task can be completed with any finished session

### 4.3 Edge Cases

- [ ] User with no sessions (analytics should return zeros)
- [ ] User with no sessions for specific chapter
- [ ] Complete task immediately after completing session
- [ ] Multiple short sessions (5 mins each) count correctly
- [ ] Session started but not ended (is_active=true) doesn't count

---

## 5. Code Snippets - Copy & Paste Ready

### Fetch All Tasks (Completed + Incomplete)
```javascript
const response = await fetch(`/api/tasks/user/${userId}/tasks?include_completed=true`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { tasks } = await response.json();
```

### Get Overall Tutor Analytics
```javascript
const response = await fetch(`/api/tutor/${userId}/analytics`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { analytics } = await response.json();
console.log(`Total: ${analytics.total_sessions} sessions, ${analytics.total_duration_minutes} mins`);
```

### Get All Chapter Progress
```javascript
const response = await fetch(`/api/tutor/${userId}/chapter-progress`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { progress } = await response.json();
Object.values(progress.chapters).forEach(ch => {
  console.log(`${ch.chapter_id}: ${ch.completed_sessions} sessions`);
});
```

### Get Specific Chapter Progress
```javascript
const response = await fetch(`/api/tutor/${userId}/chapter-progress?chapter_id=chapter_1`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { progress } = await response.json();
const canComplete = progress.completed_sessions > 0;
```

### Complete Task with Auto-Refresh
```javascript
async function completeTaskAndRefresh(userId, taskId, token) {
  const response = await fetch('/api/tasks/complete', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ user_id: userId, task_id: taskId })
  });
  
  const result = await response.json();
  
  if (result.completed && result.next_tasks_assigned > 0) {
    alert(`🎉 Week complete! ${result.next_tasks_assigned} new tasks unlocked`);
    window.location.reload(); // Or update state/refetch data
  }
  
  return result;
}
```

---

## 6. API Reference Summary

| Endpoint | Method | What Changed | Frontend Impact |
|----------|--------|--------------|-----------------|
| `/api/tasks/user/{user_id}/tasks` | GET | Added `include_completed` param | Optional: Use to show completed tasks |
| `/api/tasks/complete` | POST | AI tutor validation changed, added `next_tasks_assigned` | Update task instructions, handle auto-assignment |
| `/api/tutor/{user_id}/analytics` | GET | **NEW** | Add analytics dashboard |
| `/api/tutor/{user_id}/chapter-progress` | GET | **NEW** | Add per-chapter progress tracking |

---

## 7. Migration Timeline

### Phase 1: Critical Updates (Immediate)
1. Update AI tutor task instructions (remove "15 minutes")
2. Handle task completion validation errors gracefully
3. Test task completion flow end-to-end

### Phase 2: Enhanced Features (Week 1)
1. Implement `include_completed` param for progress views
2. Add tutor analytics dashboard
3. Add per-chapter progress cards

### Phase 3: UX Improvements (Week 2)
1. Add celebration modal for week completion
2. Show cumulative session time per chapter
3. Add visual progress indicators
4. Implement session history view per chapter

---

## Questions or Issues?

If you encounter any problems or need clarification:
1. Check [CHAPTER_PROGRESS_TRACKING.md](./CHAPTER_PROGRESS_TRACKING.md) for detailed backend logic
2. Run [test_chapter_progress.py](../testing/test_chapter_progress.py) to verify backend behavior
3. Test endpoints using the examples in this document
