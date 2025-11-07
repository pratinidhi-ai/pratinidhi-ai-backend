# Math Tutor API Documentation

## Overview
The Math Tutor API provides step-by-step solutions to math problems using advanced language models. It generates detailed explanations in LaTeX format to help users understand mathematical concepts.

## Base URL
```
http://localhost:8080/math-tutor
```

## Authentication
All endpoints (except health check) require Firebase authentication. Include the Firebase ID token in the Authorization header:
```
Authorization: Bearer <your-firebase-id-token>
```

## Endpoints

### 1. Health Check
Check if the math tutor service is running.

**Endpoint:** `GET /math-tutor/health`

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "service": "math-tutor"
}
```

### 2. Solve Math Problem
Generate a step-by-step solution for a math problem.

**Endpoint:** `POST /math-tutor/solve`

**Authentication:** Required

**Request Body:**
```json
{
  "problem": "Solve for x: 2x + 5 = 15",
  "max_tokens": 4000,        // Optional, default: 4000
  "temperature": 0.3         // Optional, default: 0.3
}
```

**Request Parameters:**
- `problem` (string, required): The math problem to solve
- `max_tokens` (integer, optional): Maximum tokens for the response. Default: 4000
- `temperature` (float, optional): Controls randomness (0.0 - 1.0). Default: 0.3

**Note:** The API uses `gpt-4o` model from OpenAI by default. These settings are configured server-side and cannot be changed via the API.

**Success Response (200 OK):**
```json
{
  "success": true,
  "problem": "Solve for x: 2x + 5 = 15",
  "solution": "Let's solve the equation step by step:\n\n1. Start with the equation:\n   $$2x + 5 = 15$$\n\n2. Subtract 5 from both sides:\n   $$2x = 10$$\n\n3. Divide both sides by 2:\n   $$x = 5$$\n\nTherefore, the solution is $x = 5$."
}
```

**Error Responses:**

*400 Bad Request - Missing problem field:*
```json
{
  "error": "Problem field is required"
}
```

*400 Bad Request - Empty problem:*
```json
{
  "error": "Validation error",
  "details": "Math problem cannot be empty"
}
```

*401 Unauthorized - Missing or invalid token:*
```json
{
  "error": "Missing or invalid token"
}
```

*500 Internal Server Error:*
```json
{
  "error": "Failed to solve math problem",
  "details": "Error message details"
}
```

## Usage Examples

### cURL Example
```bash
curl -X POST http://localhost:8080/math-tutor/solve \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "Find the derivative of f(x) = 3x^2 + 2x - 5"
  }'
```

### Python Example
```python
import requests
import json

url = "http://localhost:8080/math-tutor/solve"
headers = {
    "Authorization": "Bearer YOUR_FIREBASE_TOKEN",
    "Content-Type": "application/json"
}
payload = {
    "problem": "Solve for x: 2x + 5 = 15",
    "max_tokens": 4000,
    "temperature": 0.3
}

response = requests.post(url, headers=headers, json=payload)
result = response.json()

if response.status_code == 200:
    print("Problem:", result["problem"])
    print("Solution:", result["solution"])
else:
    print("Error:", result)
```

### JavaScript/Node.js Example
```javascript
const axios = require('axios');

const url = 'http://localhost:8080/math-tutor/solve';
const headers = {
    'Authorization': 'Bearer YOUR_FIREBASE_TOKEN',
    'Content-Type': 'application/json'
};
const data = {
    problem: 'Solve for x: 2x + 5 = 15',
    max_tokens: 4000,
    temperature: 0.3
};

axios.post(url, data, { headers })
    .then(response => {
        console.log('Problem:', response.data.problem);
        console.log('Solution:', response.data.solution);
    })
    .catch(error => {
        console.error('Error:', error.response.data);
    });
```

## LLM Configuration

The Math Tutor API uses the following fixed configuration:
- **Provider:** OpenAI
- **Model:** gpt-4o

These settings are configured in `math_tutor/math_tutor_response.py` and ensure consistent, high-quality responses for all users. The configuration uses a specialized prompt optimized for accurate mathematical calculations and step-by-step explanations.

## Response Format

The solution is provided in LaTeX format for proper mathematical notation rendering. Common LaTeX elements include:

- Inline math: `$x = 5$`
- Display math: `$$2x + 5 = 15$$`
- Fractions: `$$\frac{numerator}{denominator}$$`
- Exponents: `$$x^2$$`
- Roots: `$$\sqrt{x}$$`

## Testing

Use the provided test script to verify the API:

```bash
python testing/test_math_tutor.py
```

Before running tests, obtain a Firebase token:
```bash
python testing/get_firebase_token.py
```

## Notes

- The API uses a specialized math prompt to ensure accurate calculations
- Solutions are concise and focused on step-by-step explanations
- Lower temperature (0.3) is used for more deterministic and accurate results
- All endpoints require proper authentication except the health check
