# CRITICAL: AI Tutor Session End API Change

## 🚨 Breaking Change Alert

The **POST /api/tutor/{session_id}/end** endpoint now **requires a request body**.

---

## What You Need to Change

### BEFORE (Old - Will Fail Now)
```javascript
// ❌ This will fail with 422 error
await fetch(`/api/tutor/${sessionId}/end`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

### AFTER (New - Required)
```javascript
// ✅ Must include completion_percentage
await fetch(`/api/tutor/${sessionId}/end`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    completion_percentage: 85.0  // 0-100, REQUIRED
  })
});
```

---

## Quick Fix

Replace all instances of session end calls with:

```javascript
async function endTutorSession(sessionId, completionPercent, token) {
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
  
  return await response.json();
}

// Usage
await endTutorSession('session_abc', 85.0, userToken);
```

---

## How to Calculate completion_percentage

**Option 1: Simple (Use Time)**
```javascript
const expectedMinutes = 30; // Expected chapter duration
const actualMinutes = 20;   // Actual session duration
const completion = Math.min((actualMinutes / expectedMinutes) * 100, 100);
```

**Option 2: Topic-based**
```javascript
const totalTopics = 5;
const coveredTopics = 4;
const completion = (coveredTopics / totalTopics) * 100;
```

**Option 3: User Input (Simplest)**
```html
<input type="range" min="0" max="100" step="5" 
       onchange="completionPercent = this.value">
<button onclick="endSession(sessionId, completionPercent, token)">
  End Session
</button>
```

---

## Why This Changed

- Tasks now require **80% completion** minimum
- Tracks actual learning progress, not just time spent
- Prevents marking tasks complete without finishing content

---

## New Response Format

```json
{
  "success": true,
  "summary": "Discussed quadratic equations...",
  "total_messages": 8,
  "duration_minutes": 18.5,
  "completion_percentage": 85.0  // ← NEW FIELD
}
```

---

## Task Completion Impact

**OLD:** Any ended session → task can be marked complete  
**NEW:** Session with ≥80% completion → task can be marked complete

```javascript
// Check if task can be completed
const sessionData = await endSession(sessionId, 85.0, token);

if (sessionData.completion_percentage >= 80) {
  showMessage('✓ Task unlocked! You can now mark it as complete.');
} else {
  showMessage(`Complete ${80 - sessionData.completion_percentage}% more to unlock task`);
}
```

---

## Testing Commands

**PowerShell:**
```powershell
$body = @{ completion_percentage = 85.0 } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/tutor/$sessionId/end" `
  -Method POST `
  -Headers @{"Authorization"="Bearer $token"; "Content-Type"="application/json"} `
  -Body $body
```

**cURL:**
```bash
curl -X POST "http://localhost:8000/api/tutor/session_123/end" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"completion_percentage": 85.0}'
```

---

## Full Documentation

See [TUTOR_COMPLETION_TRACKING.md](./TUTOR_COMPLETION_TRACKING.md) for:
- Detailed implementation examples
- React/Vue components
- UI/UX recommendations
- Error handling
- Chapter progress API updates

---

## Questions?

1. **Q: What if I don't track completion?**  
   A: Send a reasonable estimate (e.g., based on time spent)

2. **Q: Can I send 0%?**  
   A: Yes, but task won't unlock until you have a session ≥80%

3. **Q: What's the valid range?**  
   A: 0.0 to 100.0 (validated by backend)

4. **Q: Do old sessions still work?**  
   A: Yes, but they have 0% completion (won't unlock tasks)

---

## Action Items

- [ ] Update all session end API calls to include `completion_percentage`
- [ ] Add Content-Type header: `application/json`
- [ ] Implement completion tracking in your app
- [ ] Test with various completion values (0, 50, 80, 100)
- [ ] Update UI to show when 80% threshold is reached
