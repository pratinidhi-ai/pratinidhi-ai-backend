# Math Tutor Video Generation - Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Dependencies
```bash
pip install websockets
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### Step 2: Set Environment Variable
Get your Knolify API key and set it:

**PowerShell:**
```powershell
$env:KNOLIFY_API_KEY='your-knolify-api-key-here'
```

**Bash/Linux:**
```bash
export KNOLIFY_API_KEY='your-knolify-api-key-here'
```

**Add to .env file (recommended):**
```
KNOLIFY_API_KEY=your-knolify-api-key-here
```

### Step 3: Get Firebase Token
```bash
python testing/get_firebase_token.py
```

### Step 4: Test the Feature
```bash
python testing/test_math_video.py
```

## 📝 API Usage

### Endpoint
```
POST /math-tutor/solve-with-video
```

### Simple Request (with video)
```json
{
  "problem": "Solve for x: 2x + 5 = 15"
}
```

### Without Video
```json
{
  "problem": "Solve for x: 2x + 5 = 15",
  "generate_video": false
}
```

### Response
```json
{
  "success": true,
  "problem": "Solve for x: 2x + 5 = 15",
  "solution": "Step-by-step solution in LaTeX...",
  "video": {
    "video_link": "https://knowlify-videos1.s3.us-west-2.amazonaws.com/video.mp4",
    "vtt_file": "https://knowlify-videos1.s3.us-west-2.amazonaws.com/subtitles.vtt",
    "status": "completed"
  }
}
```

## 🧪 Quick Test with cURL

```bash
curl -X POST http://localhost:8080/math-tutor/solve-with-video \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"problem": "Solve for x: 2x + 5 = 15"}'
```

## ⏱️ Expected Timings

- **Text Solution Only:** 2-5 seconds
- **Solution + Video:** 20-35 seconds (video generation)
- **Video Generation:** ~20-30 seconds (via Knolify)

## 🎯 Example Problems to Test

1. **Linear Equation**
   ```json
   {"problem": "Solve for x: 2x + 5 = 15"}
   ```

2. **Quadratic**
   ```json
   {"problem": "Solve: x^2 - 5x + 6 = 0"}
   ```

3. **Calculus**
   ```json
   {"problem": "Find the derivative of f(x) = 3x^2 + 2x - 5"}
   ```

4. **Trigonometry**
   ```json
   {"problem": "If sin(θ) = 0.5, find θ"}
   ```

## 🎬 Video Output

### Video Link
- Direct MP4 video URL
- Can be embedded or downloaded
- Hosted on AWS S3

### VTT Subtitle File
- WebVTT format
- Synchronized captions
- Works with HTML5 video player

### Using in HTML
```html
<video controls width="640" height="480">
  <source src="{{video_link}}" type="video/mp4">
  <track src="{{vtt_file}}" kind="subtitles" srclang="en" label="English">
</video>
```

## 🔧 Troubleshooting

### "KNOLIFY_API_KEY not found"
**Solution:** Set the environment variable
```powershell
$env:KNOLIFY_API_KEY='your-key'
```

### "Import websockets could not be resolved"
**Solution:** Install the package
```bash
pip install websockets
```

### Video generation fails but solution succeeds
**Expected behavior:** The API prioritizes returning the solution. Video failure doesn't break the response.

### Connection timeout
**Solution:** Check internet connection and Knolify API status

## 📊 Comparison: With vs Without Video

| Feature | `/solve` | `/solve-with-video` |
|---------|----------|---------------------|
| Text Solution | ✅ | ✅ |
| Video Explanation | ❌ | ✅ (optional) |
| VTT Subtitles | ❌ | ✅ |
| Response Time | 2-5s | 20-35s |
| Use Case | Quick answers | Full learning |

## 🎛️ Optional Parameters

```json
{
  "problem": "Solve for x: 2x + 5 = 15",
  "max_tokens": 4000,        // LLM response length
  "temperature": 0.3,        // LLM creativity (0-1)
  "generate_video": true     // Enable/disable video
}
```

## 📚 Documentation Files

- **Full Implementation:** `MATH_VIDEO_IMPLEMENTATION.md`
- **API Reference:** `MATH_TUTOR_API.md`
- **Quick Reference:** `MATH_TUTOR_QUICK_REFERENCE.md`
- **This Guide:** `MATH_VIDEO_QUICK_START.md`

## ✅ Checklist

Before deploying:
- [ ] `websockets` package installed
- [ ] `KNOLIFY_API_KEY` environment variable set
- [ ] Firebase authentication configured
- [ ] Test suite passes
- [ ] Video generation tested manually
- [ ] Error handling verified

## 🔗 Related Endpoints

- `GET /math-tutor/health` - Health check
- `POST /math-tutor/solve` - Solution only (no video)
- `POST /math-tutor/solve-with-video` - Solution + video

## 💡 Pro Tips

1. **For Development:** Use `"generate_video": false` to speed up testing
2. **For Production:** Cache video links to avoid regenerating identical problems
3. **For UI:** Show progress indicator (video takes 20-30 seconds)
4. **For Mobile:** Provide both video and text options
5. **For Accessibility:** Always include VTT subtitles

## 🚀 Next Steps

1. Test locally with the provided test script
2. Integrate into your frontend application
3. Set up proper environment variables in production
4. Consider implementing video caching
5. Monitor Knolify API usage and costs
