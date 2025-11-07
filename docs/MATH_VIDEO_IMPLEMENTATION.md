# Math Tutor Video Generation - Implementation Guide

## Overview
The Math Tutor now supports AI-powered video generation using Knolify's Grant API. This feature generates engaging video explanations for math problems alongside the text-based step-by-step solutions.

## Architecture

```
User Request
    ↓
Flask API (/math-tutor/solve-with-video)
    ↓
generate_math_tutor_response() → Text solution
    ↓
generate_math_ai_video() → Video explanation
    ↓
Knolify WebSocket API (Grant)
    ↓
Response: Solution + Video Link + VTT Subtitles
```

## Components

### 1. Video Generator Module
**File:** `math_tutor/math_ai_video_generator.py`

**Key Functions:**
- `generate_math_ai_video(math_problem, solution, api_key=None)`
  - Generates video using Knolify's Grant API
  - Uses WebSocket for real-time progress updates
  - Returns video link and VTT subtitle file

**Features:**
- Async WebSocket connection to Knolify
- Real-time progress tracking
- Comprehensive error handling
- Automatic API key retrieval from environment

### 2. API Endpoint
**File:** `routes/math_tutor_routing.py`

**New Endpoint:** `POST /math-tutor/solve-with-video`

**Request:**
```json
{
  "problem": "Solve for x: 2x + 5 = 15",
  "max_tokens": 4000,
  "temperature": 0.3,
  "generate_video": true
}
```

**Response (Success):**
```json
{
  "success": true,
  "problem": "Solve for x: 2x + 5 = 15",
  "solution": "Step-by-step solution...",
  "video": {
    "video_link": "https://knowlify-videos1.s3.us-west-2.amazonaws.com/video.mp4",
    "vtt_file": "https://knowlify-videos1.s3.us-west-2.amazonaws.com/subtitles.vtt",
    "status": "completed"
  }
}
```

**Response (Video Failed, Solution Still Returned):**
```json
{
  "success": true,
  "problem": "Solve for x: 2x + 5 = 15",
  "solution": "Step-by-step solution...",
  "video": {
    "status": "failed",
    "error": "Error message"
  }
}
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install websockets==14.1
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variable
```bash
# PowerShell
$env:KNOLIFY_API_KEY='your-knolify-api-key'

# Bash/Linux
export KNOLIFY_API_KEY='your-knolify-api-key'
```

### 3. Verify Setup
```bash
python testing/test_math_video.py
```

## Knolify Integration Details

### API Details
- **Service:** Knolify Grant API
- **Type:** WebSocket-based
- **Endpoint:** `wss://50fa8sjxo9.execute-api.us-west-2.amazonaws.com/production`
- **Generation Time:** 20-30 seconds
- **Action Type:** `finetuned_live_gen`

### WebSocket Flow
1. Connect to WebSocket endpoint
2. Send JSON payload with task, action, and API key
3. Receive progress updates (type: "progress")
4. Receive completion response with video link and VTT file
5. Handle errors if any

### Progress Updates
```json
{
  "type": "progress",
  "message": "Generating video...",
  "progress": 45
}
```

### Completion Response
```json
{
  "video_link": "https://...",
  "vtt_file": "https://...",
  "status": "completed"
}
```

## Usage Examples

### Example 1: Generate Solution with Video
```python
import requests

url = "http://localhost:8080/math-tutor/solve-with-video"
headers = {
    "Authorization": "Bearer YOUR_FIREBASE_TOKEN",
    "Content-Type": "application/json"
}
payload = {
    "problem": "Solve for x: 2x + 5 = 15",
    "generate_video": True
}

response = requests.post(url, headers=headers, json=payload)
result = response.json()

print("Solution:", result["solution"])
print("Video Link:", result["video"]["video_link"])
print("Subtitles:", result["video"]["vtt_file"])
```

### Example 2: Skip Video Generation
```python
payload = {
    "problem": "Find the derivative of f(x) = x^2",
    "generate_video": False
}

response = requests.post(url, headers=headers, json=payload)
result = response.json()

# Only solution returned, no video
print("Solution:", result["solution"])
```

### Example 3: cURL Request
```bash
curl -X POST http://localhost:8080/math-tutor/solve-with-video \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "Solve for x: 2x + 5 = 15",
    "generate_video": true
  }'
```

## Error Handling

### Video Generation Errors
If video generation fails, the API still returns the text solution:
- The `video.status` field will be `"failed"`
- The `video.error` field contains the error message
- The main response `success` remains `true` (solution succeeded)

### Common Errors
1. **Missing API Key**
   - Error: "KNOLIFY_API_KEY not found in environment variables"
   - Solution: Set the environment variable

2. **WebSocket Connection Error**
   - Error: "Connection closed before completion"
   - Solution: Check network connectivity, verify API key

3. **Authentication Failed**
   - Error: "Invalid API key"
   - Solution: Verify your Knolify API key

## Testing

### Run Tests
```bash
python testing/test_math_video.py
```

### Test Checklist
- ✅ Environment variable set
- ✅ Firebase token valid
- ✅ Video generation with solution
- ✅ Solution without video
- ✅ Error handling

## Performance Considerations

### Video Generation Time
- Expected: 20-30 seconds
- Progress updates sent in real-time
- Async processing prevents blocking

### Recommendations
- Use `generate_video: false` for faster responses
- Enable video only when needed
- Consider caching video links

## VTT Subtitle Files

### What is VTT?
WebVTT (Web Video Text Tracks) format for displaying synchronized captions with video playback.

### Usage
```html
<video controls>
  <source src="video_link" type="video/mp4">
  <track src="vtt_file" kind="subtitles" srclang="en" label="English">
</video>
```

## Future Enhancements

Potential improvements:
- [ ] Async/background video generation with webhooks
- [ ] Video caching for repeated problems
- [ ] Custom video settings (language, voice, quality)
- [ ] Support for Prism API (higher quality, slower)
- [ ] Video thumbnail generation
- [ ] Progress tracking via separate endpoint

## Files Modified/Created

### Created
- `math_tutor/math_ai_video_generator.py` - Video generation logic
- `testing/test_math_video.py` - Test suite
- `MATH_VIDEO_IMPLEMENTATION.md` - This file

### Modified
- `routes/math_tutor_routing.py` - Added `/solve-with-video` endpoint
- `requirements.txt` - Added `websockets==14.1`

## API Reference Summary

| Endpoint | Method | Auth | Video |
|----------|--------|------|-------|
| `/math-tutor/solve` | POST | Required | No |
| `/math-tutor/solve-with-video` | POST | Required | Optional |
| `/math-tutor/health` | GET | None | N/A |

## Support

For issues or questions:
- Check Knolify documentation: https://docs.knowlify.com
- Review logs for detailed error messages
- Verify environment variables are set correctly
