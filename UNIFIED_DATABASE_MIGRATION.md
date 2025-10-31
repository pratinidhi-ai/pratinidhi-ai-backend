# Unified Database Migration Guide

## What Changed?

Your project has been migrated from a **dual-database setup** to a **single unified database**.

### Before (Dual Database)
```
┌─────────────────────────────────────┐
│  p-ai-private-key.json              │
│  ├── users collection               │
│  ├── tasks (subcollection)          │
│  └── session_summary collection     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  educado-ai-private-key.json        │
│  └── question_bank collection       │
└─────────────────────────────────────┘
```

### After (Unified Database)
```
┌─────────────────────────────────────┐
│  educado-ai-private-key.json        │
│  ├── users collection               │
│  ├── tasks (subcollection)          │
│  ├── session_summary collection     │
│  └── question_bank collection       │
└─────────────────────────────────────┘
```

## Files Modified

### ✅ Updated
- `database/firebase_client.py` - Now uses only `educado-ai-private-key.json`
- `.gitignore` - Removed `p-ai-private-key.json` reference
- `DATABASE_MIGRATION_SUMMARY.md` - Updated documentation

### ❌ Deleted
- `helper/firebase.py` - Legacy file (was not being used)

### 📝 No Changes Needed
- `database/user_db.py` - Uses `get_firestore_client()`
- `database/task_db.py` - Uses `get_firestore_client()`
- `database/session_db.py` - Uses `get_firestore_client()`
- `database/question_db.py` - Uses `get_question_db_client()` (now points to same DB)

## About `_QDB_APP_NAME` (Your Question)

**Q: What is the purpose of `_QDB_APP_NAME`?**

**A:** The `_QDB_APP_NAME` was used to create a **named Firebase app instance** when connecting to multiple Firebase projects simultaneously. 

- Firebase Admin SDK allows multiple connections in one application
- Even if both databases have a "(default)" database name in their Firebase projects, your **Python code** needs different app names to distinguish them
- `[DEFAULT]` app → connected to first database
- `questionDB` app → connected to second database

**Since you now use only ONE database, the named app setup has been removed.** The `get_question_db_client()` function still exists for backward compatibility, but now it simply returns the same client as `get_firestore_client()`.

## Data Migration Required?

### ⚠️ IMPORTANT: You need to migrate your data!

The code now points to `educado-ai-private-key.json` for ALL operations. If your Users, Tasks, and Sessions data are still in the old database (`p-ai-private-key.json`), you need to:

**Option 1: Copy Data to New Database** (Recommended)
```python
# Migration script to copy data from old DB to new DB
# Run this ONCE before deploying

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize old database
old_cred = credentials.Certificate('p-ai-private-key.json')
old_app = firebase_admin.initialize_app(old_cred, name='old_db')
old_db = firestore.client(app=old_app)

# Initialize new database
new_cred = credentials.Certificate('educado-ai-private-key.json')
new_app = firebase_admin.initialize_app(new_cred, name='new_db')
new_db = firestore.client(app=new_app)

# Copy users collection
print("Copying users...")
users = old_db.collection('users').stream()
for user in users:
    new_db.collection('users').document(user.id).set(user.to_dict())
    
    # Copy tasks subcollection
    tasks = old_db.collection('users').document(user.id).collection('tasks').stream()
    for task in tasks:
        new_db.collection('users').document(user.id).collection('tasks').document(task.id).set(task.to_dict())

# Copy session_summary collection
print("Copying session summaries...")
sessions = old_db.collection('session_summary').stream()
for session_doc in sessions:
    # Copy session document
    new_db.collection('session_summary').document(session_doc.id).set(session_doc.to_dict())
    
    # Copy sessions subcollection
    sessions_sub = old_db.collection('session_summary').document(session_doc.id).collection('sessions').stream()
    for sess in sessions_sub:
        new_db.collection('session_summary').document(session_doc.id).collection('sessions').document(sess.id).set(sess.to_dict())

print("Migration complete!")
```

**Option 2: Update Firebase Project**
If both databases are in the same Firebase project, you might just need to ensure the service account key has access to all collections.

## Testing Checklist

After migration, test:
- [ ] User authentication works
- [ ] User creation and retrieval
- [ ] Task creation and assignment
- [ ] Session saving
- [ ] Question fetching
- [ ] All API endpoints respond correctly

## Rollback Plan

If you need to revert:
1. Keep `p-ai-private-key.json` file (don't delete it yet)
2. Restore `database/firebase_client.py` from git history
3. Restore `helper/firebase.py` from git history

## Next Steps

1. **Backup your data** before any changes
2. **Run data migration** if needed (see Option 1 above)
3. **Test thoroughly** in a development environment
4. **Deploy** to production
5. **Monitor logs** for any database connection errors
6. Once confirmed working, you can **delete `p-ai-private-key.json`** from the project root

## Questions?

- The unified database simplifies configuration and reduces connection overhead
- All database operations now go through a single Firebase app instance
- Backward compatibility is maintained - existing code doesn't need changes
- Only the underlying connection configuration changed
