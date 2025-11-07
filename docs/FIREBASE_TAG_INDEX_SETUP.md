# Firebase Tag Filtering & Index Setup Guide

## Overview
This guide explains how to filter questions by tags and set up the necessary Firebase indexes.

## How Tag Filtering Works

### Array Field Structure
Each question document has a `tags` field:
```json
{
  "question_id": "Q123",
  "theme": "Harry Potter",
  "tags": ["algebra", "linear_equations", "basic_math"],
  "random_value": 0.742,
  ...
}
```

### Filter Options

#### Option 1: Single Tag (array-contains)
Filter questions containing **one specific tag**:
```json
{
  "subject_name": "math",
  "sub_category": "algebra",
  "selected_difficulty_level": 3,
  "number_of_questions": 10,
  "tag": "linear_equations"
}
```

#### Option 2: Multiple Tags (array-contains-any)
Filter questions containing **ANY** of the specified tags (max 10):
```json
{
  "subject_name": "math",
  "sub_category": "algebra",
  "selected_difficulty_level": 3,
  "number_of_questions": 10,
  "tags": ["linear_equations", "quadratic_equations", "polynomials"]
}
```

#### Option 3: Combine with Theme
```json
{
  "subject_name": "math",
  "sub_category": "algebra",
  "selected_difficulty_level": 3,
  "number_of_questions": 10,
  "theme": "Harry Potter",
  "tags": ["linear_equations", "word_problems"]
}
```

## Firebase Index Requirements

### Scenario 1: Tag Filter Only (WITH random_value ordering)

**Index Needed:**
- **Collection Group:** `questions`
- **Fields Indexed:**
  - `tags` (Arrays)
  - `random_value` (Ascending)

### Scenario 2: Theme + Tag Filter (WITH random_value ordering)

**Index Needed:**
- **Collection Group:** `questions`
- **Fields Indexed:**
  - `theme` (Ascending)
  - `tags` (Arrays)
  - `random_value` (Ascending)

### Scenario 3: Theme Only (Already Working)

**Index Needed:** (You already have this)
- **Collection Group:** `questions`
- **Fields Indexed:**
  - `theme` (Ascending)
  - `random_value` (Ascending)

## How to Create Indexes

### Method 1: Firebase Console (Recommended)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Navigate to **Firestore Database** → **Indexes** tab
4. Click **Create Index**
5. Configure as follows:

**For Tag-Only Index:**
```
Collection ID: questions (Collection group)
Fields to index:
  - tags: Arrays
  - random_value: Ascending
Query scope: Collection group
```

**For Theme + Tag Index:**
```
Collection ID: questions (Collection group)
Fields to index:
  - theme: Ascending
  - tags: Arrays
  - random_value: Ascending
Query scope: Collection group
```

### Method 2: From Error Message (Easiest)

1. Make a test API call with tag filtering
2. Firebase will return an error with a **direct URL** to create the index
3. Click the URL and confirm the index creation
4. Wait 5-10 minutes for the index to build

Example error:
```
The query requires an index. You can create it here: 
https://console.firebase.google.com/v1/r/project/.../firestore/indexes?create_composite=...
```

### Method 3: firestore.indexes.json (Advanced)

Create/update `firestore.indexes.json`:
```json
{
  "indexes": [
    {
      "collectionGroup": "questions",
      "queryScope": "COLLECTION_GROUP",
      "fields": [
        {
          "fieldPath": "tags",
          "arrayConfig": "CONTAINS"
        },
        {
          "fieldPath": "random_value",
          "order": "ASCENDING"
        }
      ]
    },
    {
      "collectionGroup": "questions",
      "queryScope": "COLLECTION_GROUP",
      "fields": [
        {
          "fieldPath": "theme",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "tags",
          "arrayConfig": "CONTAINS"
        },
        {
          "fieldPath": "random_value",
          "order": "ASCENDING"
        }
      ]
    }
  ],
  "fieldOverrides": []
}
```

Deploy with:
```bash
firebase deploy --only firestore:indexes
```

## Testing Examples

### Test 1: Single Tag
```bash
curl -X POST http://localhost:5000/api/questions/fetch-quiz \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "subject_name": "math",
    "sub_category": "algebra",
    "selected_difficulty_level": 3,
    "number_of_questions": 5,
    "tag": "linear_equations"
  }'
```

### Test 2: Multiple Tags
```bash
curl -X POST http://localhost:5000/api/questions/fetch-quiz \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "subject_name": "math",
    "sub_category": "algebra",
    "selected_difficulty_level": 3,
    "number_of_questions": 5,
    "tags": ["linear_equations", "quadratic_equations"]
  }'
```

### Test 3: Theme + Tags
```bash
curl -X POST http://localhost:5000/api/questions/fetch-quiz \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "subject_name": "math",
    "sub_category": "algebra",
    "selected_difficulty_level": 3,
    "number_of_questions": 5,
    "theme": "Harry Potter",
    "tags": ["word_problems", "linear_equations"]
  }'
```

## Important Notes

### Limitations
1. **Maximum 10 tags** when using `array-contains-any`
2. **Cannot use both** `tag` (single) and `tags` (multiple) in same request
3. **Index build time**: 5-15 minutes depending on collection size
4. **Cannot combine** multiple array-contains operations in one query

### Performance Considerations
- Each additional indexed field increases query complexity
- More specific filters = faster queries
- Use single tag (`array-contains`) when possible for better performance

### Array-Contains vs Array-Contains-Any
- **array-contains**: Checks if array contains ONE specific value
  - Use for: Single tag filtering
  - Better performance
  
- **array-contains-any**: Checks if array contains ANY of the provided values
  - Use for: Multiple tag filtering (OR logic)
  - Max 10 values
  - Slightly slower

## Query Logic Flow

```
1. Build base query: subject/subcategory/difficulty/questions
2. Apply theme filter (if provided): .where('theme', '==', theme)
3. Apply tag filter (if provided):
   - Multiple tags: .where('tags', 'array-contains-any', tags)
   - Single tag: .where('tags', 'array-contains', tag)
4. Apply randomization: .where('random_value', '>=', rand).order_by('random_value')
5. Fetch and shuffle results
```

## Troubleshooting

### "Missing Index" Error
- Click the provided URL in the error message
- Wait for index to build (check Indexes tab in Firebase Console)

### No Results Returned
- Check if questions actually have those tags
- Verify tag spelling matches exactly (case-sensitive)
- Try without tag filter to confirm questions exist

### Performance Issues
- Reduce number of tags in filter
- Use single tag instead of multiple when possible
- Check index status in Firebase Console

## Best Practices

1. **Start Simple**: Test with single tag first
2. **Build Indexes Proactively**: Create indexes before deploying to production
3. **Monitor Usage**: Check Firebase Console for slow queries
4. **Consistent Naming**: Use standardized tag names across all questions
5. **Fallback Queries**: API already handles cases where filters are too restrictive

## Next Steps

1. ✅ Code updated to support tag filtering
2. ⏳ Create Firebase indexes (choose your method above)
3. ⏳ Test with sample requests
4. ⏳ Update frontend to send tag filters
5. ⏳ Monitor query performance
