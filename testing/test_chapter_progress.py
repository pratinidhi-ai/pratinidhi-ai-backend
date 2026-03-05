"""
Test script for per-chapter progress tracking
Demonstrates new analytics endpoints and database methods
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.session_db import get_session_db
from database.firebase_client import get_firestore_client
import json

# ============================================================================
# CONFIGURATION
# ============================================================================
TEST_USER_ID = "test_user_123"  # Change to actual user ID
TEST_CHAPTER_ID = "chapter_1"   # Change to actual chapter ID

# ============================================================================
# DATABASE TESTING
# ============================================================================

def test_chapter_progress():
    """Test the get_chapter_progress method"""
    print("\n" + "="*80)
    print("TESTING: Get Chapter Progress")
    print("="*80)
    
    session_db = get_session_db()
    
    # Test 1: Get progress for all chapters
    print("\n1. Get progress for ALL chapters:")
    all_progress = session_db.get_chapter_progress(TEST_USER_ID)
    print(json.dumps(all_progress, indent=2))
    
    # Test 2: Get progress for specific chapter
    print(f"\n2. Get progress for specific chapter ({TEST_CHAPTER_ID}):")
    chapter_progress = session_db.get_chapter_progress(TEST_USER_ID, TEST_CHAPTER_ID)
    print(json.dumps(chapter_progress, indent=2))
    
    # Test 3: Overall session analytics
    print("\n3. Get overall session analytics:")
    analytics = session_db.get_session_analytics(TEST_USER_ID)
    print(json.dumps(analytics, indent=2))


def test_task_completion_validation():
    """Test that AI tutor task can be completed with any finished session"""
    print("\n" + "="*80)
    print("TESTING: Task Completion Validation (No 15-min requirement)")
    print("="*80)
    
    db = get_firestore_client()
    
    # Check if user has any completed sessions for the chapter
    sessions_ref = (
        db.collection('session_summary')
        .document(TEST_USER_ID)
        .collection('sessions')
        .where('lecture_chapter', '==', TEST_CHAPTER_ID)
        .where('is_active', '==', False)
        .limit(1)
        .stream()
    )
    
    has_completed_session = any(True for _ in sessions_ref)
    
    print(f"\nUser ID: {TEST_USER_ID}")
    print(f"Chapter ID: {TEST_CHAPTER_ID}")
    print(f"Has completed session: {has_completed_session}")
    
    if has_completed_session:
        print("\n✓ Task CAN be marked as complete (has at least 1 finished session)")
    else:
        print("\n✗ Task CANNOT be marked as complete (no finished sessions for this chapter)")


def print_session_summary():
    """Print summary of all sessions for the test user"""
    print("\n" + "="*80)
    print("SESSION SUMMARY")
    print("="*80)
    
    session_db = get_session_db()
    sessions = session_db.get_user_sessions(TEST_USER_ID)
    
    if not sessions:
        print(f"\nNo sessions found for user {TEST_USER_ID}")
        return
    
    print(f"\nTotal sessions: {len(sessions)}")
    print("\nSession details:")
    print("-" * 80)
    
    for i, session in enumerate(sessions, 1):
        print(f"\n{i}. Session ID: {session.get('id', 'N/A')}")
        print(f"   Chapter: {session.get('lecture_chapter', 'N/A')}")
        print(f"   Duration: {session.get('duration_minutes', 0)} minutes")
        print(f"   Active: {session.get('is_active', True)}")
        print(f"   Created: {session.get('created_at', 'N/A')}")
        if session.get('summary'):
            print(f"   Summary: {session.get('summary')[:100]}...")


# ============================================================================
# API ENDPOINT EXAMPLES (for use with curl or Postman)
# ============================================================================

def print_api_examples():
    """Print example API calls for the new endpoints"""
    print("\n" + "="*80)
    print("API ENDPOINT EXAMPLES")
    print("="*80)
    
    print("""
# 1. Get overall session analytics
GET /api/tutor/{user_id}/analytics
Authorization: Bearer <token>

Example Response:
{
  "message": "Analytics retrieved successfully",
  "analytics": {
    "total_sessions": 5,
    "total_duration_minutes": 87.5,
    "average_duration_minutes": 17.5,
    "last_session_date": "2026-03-05T10:30:00Z",
    "sessions_this_week": 3,
    "sessions_this_month": 5
  }
}

# 2. Get progress for all chapters
GET /api/tutor/{user_id}/chapter-progress
Authorization: Bearer <token>

Example Response:
{
  "message": "Progress retrieved for 3 chapters",
  "total_chapters": 3,
  "progress": {
    "chapters": {
      "chapter_1": {
        "chapter_id": "chapter_1",
        "lecture_subject": "SAT",
        "total_sessions": 2,
        "total_duration_minutes": 35.5,
        "average_duration_minutes": 17.75,
        "completed_sessions": 2,
        "first_session_date": "2026-03-01T14:20:00Z",
        "last_session_date": "2026-03-04T16:45:00Z",
        "sessions": [...]
      },
      "chapter_2": {...}
    }
  }
}

# 3. Get progress for specific chapter
GET /api/tutor/{user_id}/chapter-progress?chapter_id=chapter_1
Authorization: Bearer <token>

Example Response:
{
  "message": "Chapter progress retrieved successfully",
  "progress": {
    "chapter_id": "chapter_1",
    "lecture_subject": "SAT",
    "total_sessions": 2,
    "total_duration_minutes": 35.5,
    "average_duration_minutes": 17.75,
    "completed_sessions": 2,
    "first_session_date": "2026-03-01T14:20:00Z",
    "last_session_date": "2026-03-04T16:45:00Z",
    "sessions": [
      {
        "session_id": "abc123",
        "created_at": "2026-03-04T16:45:00Z",
        "duration_minutes": 20.5,
        "is_active": false,
        "summary": "Discussed quadratic equations..."
      }
    ]
  }
}

# PowerShell examples:
# ==================

# Get analytics
Invoke-RestMethod -Uri "http://localhost:8000/api/tutor/test_user_123/analytics" `
  -Method GET `
  -Headers @{"Authorization"="Bearer YOUR_TOKEN"}

# Get all chapter progress
Invoke-RestMethod -Uri "http://localhost:8000/api/tutor/test_user_123/chapter-progress" `
  -Method GET `
  -Headers @{"Authorization"="Bearer YOUR_TOKEN"}

# Get specific chapter progress
Invoke-RestMethod -Uri "http://localhost:8000/api/tutor/test_user_123/chapter-progress?chapter_id=chapter_1" `
  -Method GET `
  -Headers @{"Authorization"="Bearer YOUR_TOKEN"}
""")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("AI TUTOR PER-CHAPTER PROGRESS TRACKING - TEST SCRIPT")
    print("="*80)
    print(f"\nTest User: {TEST_USER_ID}")
    print(f"Test Chapter: {TEST_CHAPTER_ID}")
    print("\nNOTE: Update TEST_USER_ID and TEST_CHAPTER_ID at the top of this file")
    
    try:
        # Run tests
        print_session_summary()
        test_chapter_progress()
        test_task_completion_validation()
        print_api_examples()
        
        print("\n" + "="*80)
        print("SUMMARY OF CHANGES")
        print("="*80)
        print("""
✓ REMOVED: 15-minute minimum requirement for AI tutor task completion
✓ ADDED: Per-chapter progress tracking in database
✓ ADDED: GET /api/tutor/{user_id}/analytics (overall session stats)
✓ ADDED: GET /api/tutor/{user_id}/chapter-progress (per-chapter stats)
✓ UPDATED: Task completion now requires ANY completed session (not 15min)

NEW COMPLETION CRITERIA:
- AI tutor task is complete when user has at least ONE finished session 
  (is_active == False) for that chapter
- Duration doesn't matter - any completed session counts
- All session data is tracked for analytics purposes

TRACKING DATA PER CHAPTER:
- Total sessions
- Total duration (cumulative across all sessions)
- Average duration per session
- Number of completed vs active sessions  
- First and last session dates
- Individual session details (duration, summary, timestamps)
""")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
