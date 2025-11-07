# Quick Reference: Tag Filtering

## Firebase Indexes to Create

### Index 1: Tag Filtering Only
```
Collection: questions (Collection Group)
Fields:
  - tags: Arrays
  - random_value: Ascending
```

### Index 2: Theme + Tag Filtering
```
Collection: questions (Collection Group)
Fields:
  - theme: Ascending
  - tags: Arrays
  - random_value: Ascending
```

## API Usage

### Single Tag
```json
{
  "subject_name": "math",
  "sub_category": "algebra",
  "selected_difficulty_level": 3,
  "number_of_questions": 10,
  "tag": "linear_equations"
}
```

### Multiple Tags (Max 10)
```json
{
  "subject_name": "math",
  "sub_category": "algebra",
  "selected_difficulty_level": 3,
  "number_of_questions": 10,
  "tags": ["linear_equations", "quadratic_equations", "word_problems"]
}
```

### Theme + Tags
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

## Create Index (Easiest Method)

1. Make an API call with tag filtering
2. Firebase returns error with URL like:
   ```
   https://console.firebase.google.com/v1/r/project/.../firestore/indexes?create_composite=...
   ```
3. Click the URL
4. Confirm index creation
5. Wait 5-15 minutes

## Test Script

```bash
cd testing
python test_tag_filtering.py
```

## Files Created
- ✅ `routes/question_routing.py` - Updated with tag filtering
- ✅ `FIREBASE_TAG_INDEX_SETUP.md` - Detailed setup guide
- ✅ `TAG_FILTERING_SUMMARY.md` - Implementation summary
- ✅ `firestore.indexes.json` - Index configuration
- ✅ `testing/test_tag_filtering.py` - Test suite
- ✅ `QUICK_REFERENCE_TAG_FILTERING.md` - This file

## Next Steps
1. Create Firebase indexes (use error URL method)
2. Wait for indexes to build (5-15 min)
3. Run test script
4. Update frontend to send tag parameters
