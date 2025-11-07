# Question Bank API Documentation

## Overview
The Question Bank APIs provide access to question metadata and quiz question fetching functionality based on the new database structure.

**Base URL:** `/api/questions`

---

## API Endpoints

### 1. Get Metadata

Get all question bank metadata including subjects, subcategories, question counts, and distributions.

**Endpoint:** `GET /api/questions/metadata`

**Authentication:** Required (Bearer token)

**Request:**
```http
GET /api/questions/metadata
Authorization: Bearer <your_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "total_categories": 7,
  "metadata": {
    "math|algebra": {
      "subject": "math",
      "sub_category": "algebra",
      "total_questions": 1948,
      "difficulty_distribution": {
        "1": 436,
        "2": 401,
        "3": 402,
        "4": 328,
        "5": 381
      },
      "theme_distribution": {
        "Ivy League": 331,
        "Science Fiction": 241,
        "Harry Potter": 331,
        "Famous Scientists": 290
      },
      "created_at": "2025-10-27T04:39:32.753918+00:00",
      "updated_at": "2025-10-30T03:59:34.952684+00:00"
    },
    "math|advanced-math": { ... },
    "math|problem-solving-and-data-analysis": { ... },
    "reading-and-writing|craft-and-structure": { ... },
    "reading-and-writing|expression-of-ideas": { ... },
    "reading-and-writing|information-and-ideas": { ... },
    "reading-and-writing|standard-english-conventions": { ... }
  }
}
```

**Error Responses:**
- **500 Internal Server Error:** Database connection failed
```json
{
  "error": "Database connection failed",
  "message": "Unable to connect to question bank database"
}
```

---

### 2. Fetch Quiz

Fetch quiz questions based on specific criteria including subject, subcategory, difficulty, and optional theme.

**Endpoint:** `POST /api/questions/fetch-quiz`

**Authentication:** Required (Bearer token)

**Request:**
```http
POST /api/questions/fetch-quiz
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "subject_name": "math",
  "sub_category": "algebra",
  "selected_difficulty_level": 3,
  "number_of_questions": 10,
  "theme": "Harry Potter"  // Optional
}
```

**Request Body Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subject_name` | string | Yes | Subject name (e.g., "math", "reading-and-writing") |
| `sub_category` | string | Yes | Subcategory (e.g., "algebra", "craft-and-structure") |
| `selected_difficulty_level` | integer | Yes | Difficulty level (1-5) |
| `number_of_questions` | integer | Yes | Number of questions to fetch (positive integer) |
| `theme` | string | No | Theme filter (e.g., "Harry Potter", "Science Fiction") |

**Response (200 OK):**
```json
{
  "success": true,
  "count": 10,
  "filters": {
    "subject_name": "math",
    "sub_category": "algebra",
    "difficulty_level": 3,
    "requested_count": 10,
    "theme": "Harry Potter"
  },
  "questions": [
    {
      "id": "question_doc_id_1",
      "question_id": "unique_question_id_1",
      "question_type": "multiple_choice",
      "question_theme": "Harry Potter",
      "question_standard": "10",
      "subject": "math",
      "sub_category": "algebra",
      "difficulty": 3,
      "random_value": 0.7234,
      "tags": ["linear_equations", "problem_solving"],
      "question_text": "...",
      "options": [...],
      "correct_answer": "...",
      "explanation": "...",
      "created_at": "2025-10-27T04:39:32.753918+00:00",
      "updated_at": "2025-10-30T03:59:34.952684+00:00"
    },
    // ... more questions
  ]
}
```

**Error Responses:**

- **400 Bad Request:** Missing or invalid parameters
```json
{
  "error": "Missing required parameters",
  "missing": ["subject_name", "sub_category"]
}
```

```json
{
  "error": "Invalid difficulty level",
  "message": "Must be an integer between 1 and 5"
}
```

```json
{
  "error": "Invalid number_of_questions",
  "message": "Must be a positive integer"
}
```

- **404 Not Found:** No questions match the criteria
```json
{
  "success": false,
  "message": "No questions found matching the criteria",
  "questions": [],
  "count": 0,
  "filters": { ... }
}
```

- **500 Internal Server Error:** Database or server error
```json
{
  "error": "Failed to fetch questions",
  "message": "Error details..."
}
```

---

## Database Structure

The questions are stored in Firestore with the following hierarchy:

```
question_bank (collection)
├── math|algebra (document)
│   ├── metadata fields (subject, total_questions, difficulty_distribution, etc.)
│   └── difficulty_levels (subcollection)
│       ├── 1 (document)
│       │   └── questions (subcollection)
│       │       ├── question_doc_1 (document with full question data)
│       │       ├── question_doc_2 (document with full question data)
│       │       └── ...
│       ├── 2 (document)
│       ├── 3 (document)
│       ├── 4 (document)
│       └── 5 (document)
├── math|advanced-math (document)
├── math|problem-solving-and-data-analysis (document)
├── reading-and-writing|craft-and-structure (document)
└── ...
```

---

## Available Categories

### Math
- **algebra** - 1,948 questions
- **advanced-math** - 2,071 questions
- **problem-solving-and-data-analysis** - 2,378 questions

### Reading and Writing
- **craft-and-structure** - 1,977 questions
- **expression-of-ideas** - 1,825 questions
- **information-and-ideas** - 2,613 questions
- **standard-english-conventions** - 2,793 questions

---

## Available Themes

- **Harry Potter**
- **Science Fiction**
- **Famous Scientists**
- **Ivy League**
- **Shakespearean Literature**
- **anime**

*(Note: Not all themes are available in all categories)*

---

## Question Randomization

Questions are selected randomly using a two-pass approach:

1. **First Pass:** Select questions with `random_value >= random()` up to the requested count
2. **Second Pass:** If more questions are needed, select from `random_value < random()` to fill the remaining slots
3. **Shuffle:** Results are shuffled for additional randomness

This ensures:
- Random distribution across the question pool
- Different questions on each request
- No bias toward specific questions

---

## Example Usage

### Example 1: Get Metadata
```bash
curl -X GET "https://your-api-domain.com/api/questions/metadata" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Example 2: Fetch Math Algebra Questions (No Theme)
```bash
curl -X POST "https://your-api-domain.com/api/questions/fetch-quiz" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_name": "math",
    "sub_category": "algebra",
    "selected_difficulty_level": 3,
    "number_of_questions": 5
  }'
```

### Example 3: Fetch Reading Questions with Theme
```bash
curl -X POST "https://your-api-domain.com/api/questions/fetch-quiz" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_name": "reading-and-writing",
    "sub_category": "craft-and-structure",
    "selected_difficulty_level": 4,
    "number_of_questions": 10,
    "theme": "Harry Potter"
  }'
```

---

## Migration from Old API

### Old Endpoints (Deprecated)
- `GET /get-metadata` → **Use** `GET /api/questions/metadata`
- `GET /get-questions` → **Use** `POST /api/questions/fetch-quiz`

### Parameter Mapping

**Old `/get-questions` parameters:**
- `subject` → `subject_name`
- `subcategory` → `sub_category`
- `difficulty` → `selected_difficulty_level`
- `standard` → **Removed** (now filtered at question level)
- `nques` → `number_of_questions`
- `tags` → **Deprecated** (use `theme` instead)
- `exam` → **Deprecated**

**Key Changes:**
1. Changed from `GET` to `POST` for better parameter handling
2. Parameters now in JSON body instead of query string
3. `standard` parameter removed (questions are filtered by standard internally)
4. `theme` replaces `tags` for filtering
5. Response format includes `success` flag and `filters` object

---

## Notes

- All endpoints require authentication via Bearer token
- Questions are returned in random order
- Each question includes a unique `id` (Firestore document ID)
- Datetime fields are in ISO 8601 format
- The API automatically handles datetime serialization
- If fewer questions than requested exist, all available questions are returned

---

## Support

For issues or questions, please contact the development team or refer to the project documentation.
