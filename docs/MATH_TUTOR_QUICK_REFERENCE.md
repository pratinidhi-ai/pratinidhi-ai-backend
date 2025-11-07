# Math Tutor API - Quick Reference

## Quick Start

### 1. Start the Server
```bash
python app.py
```

### 2. Get Firebase Token
```bash
python testing/get_firebase_token.py
```

### 3. Test the API
```bash
# Quick test
python testing/test_math_tutor.py
```

## API Endpoint

**POST** `/math-tutor/solve`

### Minimal Request
```json
{
  "problem": "Solve for x: 2x + 5 = 15"
}
```

### Full Request (with all options)
```json
{
  "problem": "Solve for x: 2x + 5 = 15",
  "max_tokens": 4000,
  "temperature": 0.3
}
```

## Quick Test with cURL

```bash
# Replace YOUR_TOKEN with your Firebase token
curl -X POST http://localhost:8080/math-tutor/solve \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"problem": "Solve for x: 2x + 5 = 15"}'
```

## Common Math Problems to Test

1. **Linear Equation**
   ```json
   {"problem": "Solve for x: 2x + 5 = 15"}
   ```

2. **Quadratic Equation**
   ```json
   {"problem": "Solve for x: x^2 - 5x + 6 = 0"}
   ```

3. **Calculus - Derivative**
   ```json
   {"problem": "Find the derivative of f(x) = 3x^2 + 2x - 5"}
   ```

4. **Calculus - Integration**
   ```json
   {"problem": "Find the integral of f(x) = 2x + 3"}
   ```

5. **Trigonometry**
   ```json
   {"problem": "If sin(θ) = 0.5, find θ for 0 ≤ θ ≤ 360°"}
   ```

## LLM Configuration

**Fixed Configuration:**
- Provider: OpenAI
- Model: gpt-4o

These settings are configured in `math_tutor/math_tutor_response.py` as constants:
```python
MATH_TUTOR_LLM = "openai"
MATH_TUTOR_MODEL = "gpt-4o"
```

## Response Format

```json
{
  "success": true,
  "problem": "Your math problem",
  "solution": "Step-by-step solution in LaTeX format"
}
```

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (missing/invalid problem) |
| 401 | Unauthorized (missing/invalid token) |
| 500 | Server Error |

## Files Modified/Created

### Modified
- `math_tutor/math_tutor_response.py` - Core logic
- `app.py` - Blueprint registration

### Created
- `routes/math_tutor_routing.py` - API endpoints
- `testing/test_math_tutor.py` - Test suite
- `MATH_TUTOR_API.md` - Full documentation
- `MATH_TUTOR_QUICK_REFERENCE.md` - This file

## Architecture

```
Request → Flask Route (math_tutor_routing.py)
         ↓
         Authentication (middleware.py)
         ↓
         generate_math_tutor_response (math_tutor_response.py)
         ↓
         generate_gpt_response_from_message (gen_ai_functions.py)
         ↓
         LLM Provider (OpenAI/Anthropic/Gemini/DeepSeek)
         ↓
         Response → User
```
