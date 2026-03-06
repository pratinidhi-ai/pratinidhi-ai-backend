# AI Tutor Completion Tracking - Frontend Integration

## 🎯 What Changed

AI Tutor task completion now requires **completion percentage tracking**. Frontend must send completion progress when ending a session.

---

## ⚡ Critical Changes

### 1. End Session API - **REQUEST BODY ADDED**

**OLD Behavior:**
```javascript
// No request body needed
POST /api/tutor/{session_id}/end
```

**NEW Behavior:**
```javascript
// MUST send completion_percentage in request body
POST /api/tutor/{session_id}/end

Body:
{
  "completion_percentage": 85.0  // 0-100, required
}
```

### 2. Task Completion Logic Changed

**OLD:** Any completed session → task can be completed  
**NEW:** Session with **≥80% completion** → task can be completed

---

## 📋 API Reference

### POST `/api/tutor/{session_id}/end` - **UPDATED**

**Request Body:**
```json
{
  "completion_percentage": 85.0
}
```

**Request Body Schema:**
| Field | Type | Required | Range | Description |
|-------|------|----------|-------|-------------|
| `completion_percentage` | float | Yes | 0-100 | Percentage of tutorial/chapter completed |

**Response:**
```json
{
  "success": true,
  "summary": "Discussed quadratic equations and factoring...",
  "total_messages": 8,
  "duration_minutes": 18.5,
  "completion_percentage": 85.0
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether session ended successfully |
| `summary` | string | AI-generated conversation summary |
| `total_messages` | number | Number of messages exchanged |
| `duration_minutes` | number | Session duration in minutes |
| `completion_percentage` | number | Echo of completion percentage sent |

---

## 💻 Frontend Implementation

### JavaScript Example
```javascript
async function endTutorSession(sessionId, completionPercentage, token) {
  const response = await fetch(`/api/tutor/${sessionId}/end`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      completion_percentage: completionPercentage
    })
  });
  
  const data = await response.json();
  
  if (data.success) {
    console.log(`Session ended: ${data.completion_percentage}% complete`);
    
    // Check if user can now complete the task
    if (data.completion_percentage >= 80) {
      showMessage("✓ Task can now be completed!");
    } else {
      showMessage(`Complete ${80 - data.completion_percentage}% more to unlock task`);
    }
  }
  
  return data;
}

// Usage
await endTutorSession('session_abc123', 85.0, userToken);
```

### React Component Example
```jsx
import { useState } from 'react';

function TutorSessionEnd({ sessionId, token, onSessionEnd }) {
  const [completionPercent, setCompletionPercent] = useState(0);
  const [loading, setLoading] = useState(false);

  const handleEndSession = async () => {
    setLoading(true);
    
    try {
      const response = await fetch(`/api/tutor/${sessionId}/end`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          completion_percentage: completionPercent
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Show completion status
        if (data.completion_percentage >= 80) {
          alert('🎉 Task unlocked! You can now mark it as complete.');
        } else {
          alert(`Session saved. Complete ${80 - data.completion_percentage}% more to unlock task.`);
        }
        
        onSessionEnd(data);
      }
    } catch (error) {
      console.error('Failed to end session:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h3>End Tutor Session</h3>
      
      <label>
        Completion Progress: {completionPercent}%
        <input
          type="range"
          min="0"
          max="100"
          step="5"
          value={completionPercent}
          onChange={(e) => setCompletionPercent(Number(e.target.value))}
        />
      </label>
      
      <button onClick={handleEndSession} disabled={loading}>
        {loading ? 'Ending Session...' : 'End Session'}
      </button>
      
      {completionPercent >= 80 && (
        <p className="success">✓ This will unlock the task!</p>
      )}
    </div>
  );
}
```

### Vue.js Example
```vue
<template>
  <div class="session-end">
    <h3>End Session</h3>
    
    <div class="completion-slider">
      <label>Completion: {{ completionPercent }}%</label>
      <input
        type="range"
        v-model.number="completionPercent"
        min="0"
        max="100"
        step="5"
      />
    </div>
    
    <button @click="endSession" :disabled="loading">
      {{ loading ? 'Ending...' : 'End Session' }}
    </button>
    
    <p v-if="completionPercent >= 80" class="success">
      ✓ Task will be unlocked
    </p>
  </div>
</template>

<script>
export default {
  props: ['sessionId', 'token'],
  data() {
    return {
      completionPercent: 0,
      loading: false
    };
  },
  methods: {
    async endSession() {
      this.loading = true;
      
      try {
        const response = await fetch(`/api/tutor/${this.sessionId}/end`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            completion_percentage: this.completionPercent
          })
        });
        
        const data = await response.json();
        
        if (data.success) {
          this.$emit('session-ended', data);
          
          if (data.completion_percentage >= 80) {
            alert('🎉 Task unlocked!');
          }
        }
      } catch (error) {
        console.error('Error:', error);
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

---

## 🎨 UI/UX Recommendations

### Completion Tracker UI

```
┌─────────────────────────────────────────────┐
│  Tutor Session: Quadratic Equations         │
├─────────────────────────────────────────────┤
│                                             │
│  Chapter Progress                           │
│  ████████████████████░░░░░  85%            │
│                                             │
│  Topics Covered:                            │
│  ✓ Introduction to quadratics               │
│  ✓ Factoring basics                         │
│  ✓ Completing the square                    │
│  ○ Quadratic formula (next)                 │
│                                             │
│  [Continue Session]  [End Session]          │
└─────────────────────────────────────────────┘

When user clicks "End Session":
┌─────────────────────────────────────────────┐
│  End Session & Save Progress                │
├─────────────────────────────────────────────┤
│                                             │
│  You've completed 85% of this chapter       │
│                                             │
│  ✓ This will unlock the task!               │
│     (≥80% required)                         │
│                                             │
│  [Cancel]  [End & Save (85%)]              │
└─────────────────────────────────────────────┘
```

### Progress Calculation Examples

**Option 1: Topic-based tracking**
```javascript
// Track which topics/sections were covered
const topics = ['intro', 'factoring', 'completing_square', 'quadratic_formula'];
const completedTopics = ['intro', 'factoring', 'completing_square'];

const completionPercent = (completedTopics.length / topics.length) * 100;
// Result: 75%
```

**Option 2: Message-based tracking**
```javascript
// Estimate based on conversation depth
const expectedMessages = 20; // Expected for full coverage
const actualMessages = 15;

const completionPercent = Math.min((actualMessages / expectedMessages) * 100, 100);
// Result: 75%
```

**Option 3: Time-based tracking**
```javascript
// Based on expected chapter duration
const expectedMinutes = 30;
const actualMinutes = 20;

const completionPercent = Math.min((actualMinutes / expectedMinutes) * 100, 100);
// Result: 67%
```

**Option 4: Manual user input**
```javascript
// Let user self-assess
<input type="range" min="0" max="100" step="5" />
```

**Recommended: Hybrid approach**
```javascript
// Combine multiple factors
const topicProgress = (completedTopics.length / totalTopics) * 100;
const timeProgress = Math.min((actualMinutes / expectedMinutes) * 100, 100);

const completionPercent = Math.round((topicProgress * 0.7) + (timeProgress * 0.3));
// 70% weight on topics, 30% on time
```

---

## 📊 Chapter Progress API - Updated Response

### GET `/api/tutor/{user_id}/chapter-progress?chapter_id={chapter_id}`

**Response with completion tracking:**
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
    "max_completion_percentage": 85.0,
    "has_qualifying_session": true,
    "first_session_date": "2026-03-01T14:00:00+00:00",
    "last_session_date": "2026-03-05T09:30:00+00:00",
    "sessions": [
      {
        "session_id": "session_abc123",
        "created_at": "2026-03-05T09:30:00+00:00",
        "duration_minutes": 18.5,
        "is_active": false,
        "completion_percentage": 85.0,
        "summary": "Discussed quadratic equations..."
      },
      {
        "session_id": "session_def456",
        "created_at": "2026-03-03T16:20:00+00:00",
        "duration_minutes": 12.0,
        "is_active": false,
        "completion_percentage": 60.0,
        "summary": "Reviewed factoring basics..."
      }
    ]
  }
}
```

**New Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `max_completion_percentage` | number | Highest completion % achieved across all sessions |
| `has_qualifying_session` | boolean | Whether any session has ≥80% completion |
| `sessions[].completion_percentage` | number | Completion % for each session |

**Frontend Usage:**
```javascript
const progress = await getChapterProgress(userId, chapterId, token);

if (progress.has_qualifying_session) {
  console.log('✓ Task can be completed');
  console.log(`Best session: ${progress.max_completion_percentage}%`);
} else {
  console.log('✗ Need to complete more of the chapter');
  console.log(`Current best: ${progress.max_completion_percentage}%`);
  console.log(`Need: ${80 - progress.max_completion_percentage}% more`);
}
```

---

## 🧪 Testing

### Test End Session with Completion

**PowerShell:**
```powershell
$token = "YOUR_TOKEN"
$sessionId = "session_123"

$body = @{
  completion_percentage = 85.0
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/tutor/$sessionId/end" `
  -Method POST `
  -Headers @{
    "Authorization"="Bearer $token"
    "Content-Type"="application/json"
  } `
  -Body $body
```

**cURL:**
```bash
curl -X POST "http://localhost:8000/api/tutor/session_123/end" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"completion_percentage": 85.0}'
```

### Test Different Completion Levels

```javascript
// Test 1: Below threshold (task NOT unlocked)
await endSession('session_1', 50.0, token);
// Expected: Session saved, task still locked

// Test 2: Exactly at threshold (task unlocked)
await endSession('session_2', 80.0, token);
// Expected: Session saved, task can be completed

// Test 3: Above threshold (task unlocked)
await endSession('session_3', 100.0, token);
// Expected: Session saved, task can be completed
```

### Test Task Completion Validation

```javascript
// After ending session with 85% completion
const completeResult = await fetch('/api/tasks/complete', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    user_id: userId,
    task_id: taskId
  })
});

const data = await completeResult.json();
console.log(data.completed); // Should be true
```

---

## ❗ Error Handling

### Missing completion_percentage
```json
// Request
POST /api/tutor/session_123/end
Body: {}

// Response: 422 Unprocessable Entity
{
  "detail": [
    {
      "loc": ["body", "completion_percentage"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Invalid range
```json
// Request
Body: { "completion_percentage": 150.0 }

// Response: 422 Unprocessable Entity
{
  "detail": [
    {
      "loc": ["body", "completion_percentage"],
      "msg": "ensure this value is less than or equal to 100",
      "type": "value_error.number.not_le"
    }
  ]
}
```

### Frontend Error Handling
```javascript
try {
  const response = await fetch(`/api/tutor/${sessionId}/end`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      completion_percentage: completionPercent
    })
  });
  
  if (!response.ok) {
    if (response.status === 422) {
      throw new Error('Invalid completion percentage (must be 0-100)');
    } else if (response.status === 404) {
      throw new Error('Session not found');
    } else if (response.status === 400) {
      throw new Error('Session already ended');
    }
    throw new Error('Failed to end session');
  }
  
  const data = await response.json();
  return data;
} catch (error) {
  console.error('Error ending session:', error.message);
  alert(error.message);
}
```

---

## 📋 Migration Checklist

### Phase 1: Immediate (Breaking Change)
- [ ] Update all end session calls to include `completion_percentage`
- [ ] Implement completion tracking logic in frontend
- [ ] Test session ending with various completion levels
- [ ] Update error handling for new request body

### Phase 2: Enhanced UX
- [ ] Add visual progress tracker during session
- [ ] Show real-time completion percentage
- [ ] Indicate when 80% threshold is reached
- [ ] Show chapter progress with completion stats

### Phase 3: Polish
- [ ] Add celebration when 100% complete
- [ ] Show historical completion rates per chapter
- [ ] Track improvement over time
- [ ] Add progress analytics dashboard

---

## 🎯 Summary

| What | Old | New |
|------|-----|-----|
| **End Session Request** | No body | `{ completion_percentage: 0-100 }` |
| **Task Unlock Criteria** | Any completed session | Session with ≥80% completion |
| **Response** | Basic summary | Includes completion % |
| **Chapter Progress** | Duration only | Duration + completion % |
| **Frontend Tracking** | Not needed | Must track & send completion |

**Key Points:**
- ✅ Frontend MUST send `completion_percentage` when ending session
- ✅ Task requires ≥80% completion to unlock
- ✅ Progress API now shows max completion % per chapter
- ✅ `has_qualifying_session` tells if task can be completed
