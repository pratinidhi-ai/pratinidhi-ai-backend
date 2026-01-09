# Mock Submit API - Module-based Structure

## 🎯 Overview

The submit API stores answers **BY MODULE** to accurately reflect the SAT Digital exam structure. Each module is stored separately - **no combining** of Module 1 and Module 2 answers.

## 📍 Endpoint
```
POST /api/mocks/submit/{uid}
```

## 📥 Request Body

```json
{
  "mock_id": "mock_test_001",
  
  "rw_m1": [
    {
      "question_id": "q_rw_m1_001",
      "difficulty": 3,
      "user_answer": {"value": "A", "type": "mcq"},
      "correct_answer": {"value": "A", "type": "mcq"},
      "is_correct": true
    }
  ],
  
  "rw_m2_hard": [
    {
      "question_id": "q_rw_m2_hard_001",
      "difficulty": 4,
      "user_answer": {"value": "B", "type": "mcq"},
      "correct_answer": {"value": "B", "type": "mcq"},
      "is_correct": true
    }
  ],
  
  "math_m1": [
    {
      "question_id": "q_math_m1_001",
      "difficulty": 3,
      "user_answer": {"value": "16", "type": "spr"},
      "correct_answer": {"value": "16", "type": "spr"},
      "is_correct": true
    }
  ],
  
  "math_m2_easy": [
    {
      "question_id": "q_math_m2_easy_001",
      "difficulty": 2,
      "user_answer": {"value": "C", "type": "mcq"},
      "correct_answer": {"value": "C", "type": "mcq"},
      "is_correct": true
    }
  ],
  
  "module2_names": {
    "rw": "rw_m2_hard",
    "math": "math_m2_easy"
  }
}
```

## 📤 Response

```json
{
  "success": true,
  "mock_id": "mock_test_001",
  "attempts": 1,
  "module2_names": {
    "rw": "rw_m2_hard",
    "math": "math_m2_easy"
  },
  "scores": {
    "rw_score": 650,
    "math_score": 600,
    "total_score": 1250,
    "details": {...}
  }
}
```

## 🏗️ Module Structure

### Required Modules (Always Present)
- **`rw_m1`** - Reading & Writing Module 1 answers array
- **`math_m1`** - Math Module 1 answers array

### Module 2 (Mutually Exclusive)

**Reading & Writing Module 2** - Include ONLY ONE:
- **`rw_m2_easy`** - Easy adaptive path
- **`rw_m2_hard`** - Hard adaptive path

**Math Module 2** - Include ONLY ONE:
- **`math_m2_easy`** - Easy adaptive path
- **`math_m2_hard`** - Hard adaptive path

### Metadata
- **`module2_names`** - Object specifying which Module 2 variants were taken
  ```json
  {
    "rw": "rw_m2_easy" | "rw_m2_hard",
    "math": "math_m2_easy" | "math_m2_hard"
  }
  ```

## ✅ Validation Rules

| Rule | Enforced | Error |
|------|----------|-------|
| `mock_id` required | ✅ | `mock_id_required` |
| `module2_names` required | ✅ | `module2_names_required` |
| `module2_names.rw` must exist | ✅ | `module2_names_must_contain_rw` |
| `module2_names.math` must exist | ✅ | `module2_names_must_contain_math` |
| `rw_m1` key must exist in body | ✅ | `rw_m1_required_in_body` |
| `math_m1` key must exist in body | ✅ | `math_m1_required_in_body` |
| RW Module 2 key must exist in body | ✅ | `{module_name}_required_in_body` |
| Math Module 2 key must exist in body | ✅ | `{module_name}_required_in_body` |
| `rw_m1` must be array | ✅ | `rw_m1_must_be_list` |
| `math_m1` must be array | ✅ | `math_m1_must_be_list` |
| RW Module 2 must be array | ✅ | `{module_name}_must_be_list` |
| Math Module 2 must be array | ✅ | `{module_name}_must_be_list` |
| RW Module 2 = easy OR hard | ✅ | `rw_module2_must_be_rw_m2_easy_or_rw_m2_hard` |
| Math Module 2 = easy OR hard | ✅ | `math_module2_must_be_math_m2_easy_or_math_m2_hard` |
| User exists | ✅ | `user_not_found_for_uid` |

**Note:** Empty arrays are allowed (e.g., if user didn't answer any questions in a module). An empty module will result in minimum score (200) for that section.

## 📦 Stored Document Structure

```json
{
  "mock_id": "mock_test_001",
  
  "rw_m1": [...normalized answers...],
  "rw_m2_hard": [...normalized answers...],
  
  "math_m1": [...normalized answers...],
  "math_m2_easy": [...normalized answers...],
  
  "module2_names": {
    "rw": "rw_m2_hard",
    "math": "math_m2_easy"
  },
  
  "scores": {
    "rw_score": 650,
    "math_score": 600,
    "total_score": 1250,
    "details": {...}
  },
  
  "attempts": 1,
  "updated_at": "2026-01-04T12:30:00Z"
}
```

## 🚨 Important Rules

### ❌ Do NOT Combine Modules
```json
// ❌ WRONG - Do not combine modules
{
  "rw_answers": [...m1 + m2 combined...],
  "math_answers": [...m1 + m2 combined...]
}
```

```json
// ✅ CORRECT - Store modules separately
{
  "rw_m1": [...],
  "rw_m2_hard": [...],
  "math_m1": [...],
  "math_m2_easy": [...]
}
```

### ❌ Do NOT Include Both Module 2 Variants
```json
// ❌ WRONG - Cannot have both easy and hard
{
  "rw_m2_easy": [...],
  "rw_m2_hard": [...],  // ❌ Mutually exclusive!
}
```

```json
// ✅ CORRECT - Only one Module 2 per section
{
  "rw_m2_hard": [...]  // ✅ Only hard path
}
```

### ✅ Always Include module2_names
```json
// ✅ CORRECT - Explicitly declare which Module 2
{
  "module2_names": {
    "rw": "rw_m2_hard",
    "math": "math_m2_easy"
  }
}
```

## 💡 Benefits of Module-based Storage

1. **Accurate Exam Representation** - Matches actual SAT structure
2. **Module-specific Analysis** - Can analyze performance per module
3. **Adaptive Path Tracking** - Clear record of easy vs hard paths
4. **Review Accuracy** - Students see exactly which module each question came from
5. **Future-safe** - Supports potential changes to module structure
6. **No Data Loss** - Module boundaries preserved

## 🧪 Quick Test

```bash
curl -X POST "http://localhost:8000/api/mocks/submit/user123" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mock_id": "mock_001",
    "rw_m1": [{
      "question_id": "q_rw_m1_001",
      "difficulty": 3,
      "user_answer": {"value": "A", "type": "mcq"},
      "correct_answer": {"value": "A", "type": "mcq"},
      "is_correct": true
    }],
    "rw_m2_hard": [{
      "question_id": "q_rw_m2_hard_001",
      "difficulty": 4,
      "user_answer": {"value": "B", "type": "mcq"},
      "correct_answer": {"value": "B", "type": "mcq"},
      "is_correct": true
    }],
    "math_m1": [],
    "math_m2_hard": [],
    "module2_names": {
      "rw": "rw_m2_hard",
      "math": "math_m2_hard"
    }
  }'
```

## 🔍 Review API

The stored module-based structure is returned as-is:

```bash
GET /api/mocks/attempt/{uid}/{mock_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "mock_id": "mock_001",
    "rw_m1": [...],
    "rw_m2_hard": [...],
    "math_m1": [...],
    "math_m2_hard": [...],
    "module2_names": {
      "rw": "rw_m2_hard",
      "math": "math_m2_hard"
    },
    "scores": {...},
    "attempts": 1
  }
}
```

---

**Status:** ✅ Production Ready  
**Version:** 2.0 (Module-based)  
**Date:** 2026-01-04
