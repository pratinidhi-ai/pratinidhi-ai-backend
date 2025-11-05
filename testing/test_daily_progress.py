"""
Quick test script for Daily Progress API
Tests the daily progress calculation and retrieval
"""

import requests
import json
from datetime import datetime
import pytz

# Configuration
BASE_URL = "http://localhost:5000"
TOKEN_FILE = "testing/test_token.txt"

# Read token
try:
    with open(TOKEN_FILE, 'r') as f:
        TOKEN = f.read().strip()
except FileNotFoundError:
    print(f"❌ Token file not found: {TOKEN_FILE}")
    print("Run 'python testing/get_firebase_token.py' first")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Test student ID
STUDENT_ID = "test_user_123"

def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def get_ist_time():
    """Get current IST time"""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist)

def test_submit_quiz():
    """Submit a test quiz to trigger daily progress update"""
    print_section("1. Submitting Test Quiz")
    
    payload = {
        "student_id": STUDENT_ID,
        "time_spent": 300,  # 5 minutes
        "number_of_questions": 10,
        "number_of_correct_answers": 8,
        "subject": "math",
        "sub_category": "algebra",
        "difficulty_level": 3,
        "tag_wise_details": [
            {
                "tag": "linear-equations",
                "total_questions": 5,
                "correct_answers": 4
            },
            {
                "tag": "quadratic-equations",
                "total_questions": 5,
                "correct_answers": 4
            }
        ],
        "correct_question_ids": ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8"],
        "incorrect_question_ids": ["q9", "q10"]
    }
    
    print(f"📤 Submitting quiz for student: {STUDENT_ID}")
    print(f"⏰ Current IST time: {get_ist_time().strftime('%Y-%m-%d %H:%M:%S')}")
    
    response = requests.post(
        f"{BASE_URL}/analytics/submit-quiz",
        headers=HEADERS,
        json=payload
    )
    
    if response.status_code == 202:
        data = response.json()
        print(f"✅ Quiz accepted for processing")
        print(f"   Request ID: {data.get('request_id')}")
        print(f"   Estimated Score: {data.get('estimated_score')}/{data.get('estimated_total_possible_score')}")
        print(f"   Estimated Accuracy: {data.get('estimated_accuracy')}%")
        print("\n   ⏳ Processing in background (including daily progress update)...")
        return True
    else:
        print(f"❌ Failed to submit quiz: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_get_daily_progress():
    """Get daily progress for the student"""
    print_section("2. Getting Daily Progress")
    
    print(f"📥 Fetching daily progress for student: {STUDENT_ID}")
    
    # Wait a moment for background processing
    import time
    print("   ⏳ Waiting 2 seconds for background processing...")
    time.sleep(2)
    
    response = requests.get(
        f"{BASE_URL}/analytics/daily-progress/{STUDENT_ID}",
        headers=HEADERS
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if not data['success']:
            print(f"❌ Failed to get daily progress")
            return
        
        progress = data['daily_progress']
        
        print(f"✅ Daily progress retrieved successfully\n")
        
        # Today's stats
        today = progress.get('today', {})
        print("📊 TODAY'S STATS:")
        print(f"   Date: {today.get('date')}")
        print(f"   Quizzes Taken: {today.get('total_quizzes', 0)}")
        print(f"   Questions Attempted: {today.get('total_questions', 0)}")
        print(f"   Correct Answers: {today.get('total_correct', 0)}")
        print(f"   Accuracy: {today.get('accuracy', 0)}%")
        print(f"   Time Spent: {today.get('total_time_spent', 0)} seconds ({today.get('total_time_spent', 0)/60:.1f} minutes)")
        print(f"   Hot Topic: {today.get('hot_topic', 'N/A')}")
        print(f"   Hot Topic Count: {today.get('hot_topic_count', 0)}")
        
        # Yesterday's stats
        yesterday = progress.get('yesterday', {})
        if yesterday:
            print("\n📊 YESTERDAY'S STATS:")
            print(f"   Date: {yesterday.get('date')}")
            print(f"   Quizzes Taken: {yesterday.get('total_quizzes', 0)}")
            print(f"   Questions Attempted: {yesterday.get('total_questions', 0)}")
            print(f"   Correct Answers: {yesterday.get('total_correct', 0)}")
            print(f"   Accuracy: {yesterday.get('accuracy', 0)}%")
            print(f"   Time Spent: {yesterday.get('total_time_spent', 0)} seconds ({yesterday.get('total_time_spent', 0)/60:.1f} minutes)")
            print(f"   Hot Topic: {yesterday.get('hot_topic', 'N/A')}")
        else:
            print("\n📊 YESTERDAY'S STATS: No data")
        
        # Streak
        print(f"\n🔥 STREAK: {progress.get('streak', 0)} days")
        print(f"📅 Last Activity: {progress.get('last_activity_date')}")
        
        # Comparison
        if yesterday:
            print("\n📈 COMPARISON (Today vs Yesterday):")
            quiz_diff = today.get('total_quizzes', 0) - yesterday.get('total_quizzes', 0)
            accuracy_diff = today.get('accuracy', 0) - yesterday.get('accuracy', 0)
            
            print(f"   Quizzes: {'+' if quiz_diff >= 0 else ''}{quiz_diff}")
            print(f"   Accuracy: {'+' if accuracy_diff >= 0 else ''}{accuracy_diff:.2f}%")
        
        return True
    else:
        print(f"❌ Failed to get daily progress: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def main():
    """Run all tests"""
    print("\n🧪 Daily Progress API Test")
    print(f"⏰ Current IST Time: {get_ist_time().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"🔗 Base URL: {BASE_URL}")
    print(f"👤 Test Student: {STUDENT_ID}")
    
    # Test 1: Submit quiz
    if not test_submit_quiz():
        print("\n❌ Quiz submission failed, stopping tests")
        return
    
    # Test 2: Get daily progress
    if not test_get_daily_progress():
        print("\n❌ Failed to get daily progress")
        return
    
    print_section("✅ All Tests Completed")
    print("\n💡 Notes:")
    print("   - Daily progress updates in background (non-blocking)")
    print("   - All dates use IST timezone")
    print("   - Streak increases on consecutive days")
    print("   - Hot topic is the most attempted tag today")

if __name__ == "__main__":
    main()
