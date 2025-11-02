"""
Test Analytics API
Quick test script to verify analytics endpoints
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8080"
# Replace with actual Firebase ID token for testing
FIREBASE_TOKEN = "YOUR_FIREBASE_ID_TOKEN_HERE"

HEADERS = {
    "Authorization": f"Bearer {FIREBASE_TOKEN}",
    "Content-Type": "application/json"
}

# Test student ID (replace with actual user ID)
STUDENT_ID = "test_user_123"


def test_submit_quiz():
    """Test submitting quiz analytics"""
    print("\n" + "="*60)
    print("TEST 1: Submit Quiz Analytics")
    print("="*60)
    
    quiz_data = {
        "student_id": STUDENT_ID,
        "time_spent": 1200,  # 20 minutes
        "number_of_questions": 10,
        "number_of_correct_answers": 7,
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
                "tag": "systems-of-equations",
                "total_questions": 5,
                "correct_answers": 3
            }
        ],
        "correct_question_ids": [
            "q1", "q2", "q3", "q4", "q5", "q6", "q7"
        ],
        "incorrect_question_ids": [
            "q8", "q9", "q10"
        ]
    }
    
    print(f"\nSubmitting quiz for student: {STUDENT_ID}")
    print(f"Subject: {quiz_data['subject']}")
    print(f"Sub-category: {quiz_data['sub_category']}")
    print(f"Difficulty: {quiz_data['difficulty_level']}")
    print(f"Questions: {quiz_data['number_of_questions']}")
    print(f"Correct: {quiz_data['number_of_correct_answers']}")
    
    response = requests.post(
        f"{BASE_URL}/api/analytics/submit-quiz",
        headers=HEADERS,
        json=quiz_data
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json().get('session_id')


def test_performance_summary():
    """Test getting performance summary"""
    print("\n" + "="*60)
    print("TEST 2: Get Performance Summary")
    print("="*60)
    
    print(f"\nFetching performance summary for: {STUDENT_ID}")
    
    response = requests.get(
        f"{BASE_URL}/api/analytics/performance-summary/{STUDENT_ID}",
        headers=HEADERS
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_performance_summary_filtered():
    """Test getting filtered performance summary"""
    print("\n" + "="*60)
    print("TEST 3: Get Performance Summary (Filtered by Subject)")
    print("="*60)
    
    print(f"\nFetching math performance for: {STUDENT_ID}")
    
    response = requests.get(
        f"{BASE_URL}/api/analytics/performance-summary/{STUDENT_ID}?subject=math",
        headers=HEADERS
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_activity_logs():
    """Test getting activity logs"""
    print("\n" + "="*60)
    print("TEST 4: Get Activity Logs")
    print("="*60)
    
    print(f"\nFetching recent activity logs for: {STUDENT_ID}")
    
    response = requests.get(
        f"{BASE_URL}/api/analytics/activity-logs/{STUDENT_ID}?limit=5",
        headers=HEADERS
    )
    
    print(f"\nStatus Code: {response.status_code}")
    result = response.json()
    print(f"Total logs: {result.get('count', 0)}")
    print(f"Response: {json.dumps(result, indent=2)}")


def test_correct_questions():
    """Test getting correct questions"""
    print("\n" + "="*60)
    print("TEST 5: Get Correct Questions")
    print("="*60)
    
    print(f"\nFetching correct questions for: {STUDENT_ID}")
    
    response = requests.get(
        f"{BASE_URL}/api/analytics/correct-questions/{STUDENT_ID}",
        headers=HEADERS
    )
    
    print(f"\nStatus Code: {response.status_code}")
    result = response.json()
    if result.get('success'):
        correct_qs = result.get('correct_questions', {})
        print(f"Total categories: {len(correct_qs)}")
        for category, questions in correct_qs.items():
            print(f"  {category}: {len(questions)} questions")
    print(f"\nFull Response: {json.dumps(result, indent=2)}")


def test_incorrect_questions():
    """Test getting incorrect questions"""
    print("\n" + "="*60)
    print("TEST 6: Get Incorrect Questions")
    print("="*60)
    
    print(f"\nFetching incorrect questions for: {STUDENT_ID}")
    
    response = requests.get(
        f"{BASE_URL}/api/analytics/incorrect-questions/{STUDENT_ID}",
        headers=HEADERS
    )
    
    print(f"\nStatus Code: {response.status_code}")
    result = response.json()
    if result.get('success'):
        incorrect_qs = result.get('incorrect_questions', {})
        print(f"Total categories: {len(incorrect_qs)}")
        for category, questions in incorrect_qs.items():
            print(f"  {category}: {len(questions)} questions")
    print(f"\nFull Response: {json.dumps(result, indent=2)}")


def test_quick_stats():
    """Test getting quick stats"""
    print("\n" + "="*60)
    print("TEST 7: Get Quick Stats")
    print("="*60)
    
    print(f"\nFetching quick stats for: {STUDENT_ID}")
    
    response = requests.get(
        f"{BASE_URL}/api/analytics/stats/{STUDENT_ID}",
        headers=HEADERS
    )
    
    print(f"\nStatus Code: {response.status_code}")
    result = response.json()
    if result.get('success') and result.get('stats'):
        stats = result['stats']
        print(f"\nQuick Stats Summary:")
        print(f"  Total Quizzes: {stats.get('total_quizzes', 0)}")
        print(f"  Total Time: {stats.get('total_time_spent_hours', 0)} hours")
        print(f"  Overall Accuracy: {stats.get('overall_accuracy', 0)}%")
        print(f"\nSubject Performance:")
        for subject, perf in stats.get('subjects', {}).items():
            print(f"  {subject}:")
            print(f"    Accuracy: {perf.get('accuracy', 0)}%")
            print(f"    Quizzes: {perf.get('quizzes_taken', 0)}")
            print(f"    Score: {perf.get('score_percentage', 0)}%")
    print(f"\nFull Response: {json.dumps(result, indent=2)}")


def test_multiple_quizzes():
    """Test submitting multiple quizzes to build up analytics"""
    print("\n" + "="*60)
    print("TEST 8: Submit Multiple Quizzes")
    print("="*60)
    
    quizzes = [
        {
            "subject": "math",
            "sub_category": "geometry-and-trigonometry",
            "difficulty_level": 2,
            "correct": 8,
            "total": 10,
            "tags": [
                {"tag": "pythagorean-theorem", "total_questions": 5, "correct_answers": 4},
                {"tag": "area-of-polygons", "total_questions": 5, "correct_answers": 4}
            ]
        },
        {
            "subject": "reading-and-writing",
            "sub_category": "craft-and-structure",
            "difficulty_level": 3,
            "correct": 6,
            "total": 8,
            "tags": [
                {"tag": "word-in-context", "total_questions": 4, "correct_answers": 3},
                {"tag": "main-purpose", "total_questions": 4, "correct_answers": 3}
            ]
        }
    ]
    
    for i, quiz in enumerate(quizzes, 1):
        print(f"\nSubmitting quiz {i}: {quiz['subject']} - {quiz['sub_category']}")
        
        quiz_data = {
            "student_id": STUDENT_ID,
            "time_spent": 900,
            "number_of_questions": quiz['total'],
            "number_of_correct_answers": quiz['correct'],
            "subject": quiz['subject'],
            "sub_category": quiz['sub_category'],
            "difficulty_level": quiz['difficulty_level'],
            "tag_wise_details": quiz['tags'],
            "correct_question_ids": [f"q{j}" for j in range(1, quiz['correct'] + 1)],
            "incorrect_question_ids": [f"q{j}" for j in range(quiz['correct'] + 1, quiz['total'] + 1)]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/submit-quiz",
            headers=HEADERS,
            json=quiz_data
        )
        
        print(f"  Status: {response.status_code}")
        if response.status_code == 201:
            print(f"  Session ID: {response.json().get('session_id')}")


def run_all_tests():
    """Run all analytics API tests"""
    print("\n" + "="*80)
    print(" ANALYTICS API TEST SUITE")
    print("="*80)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Student ID: {STUDENT_ID}")
    
    if FIREBASE_TOKEN == "YOUR_FIREBASE_ID_TOKEN_HERE":
        print("\n⚠️  WARNING: Please set a valid Firebase ID token in the FIREBASE_TOKEN variable")
        print("You can get a token using the get_firebase_token.py script in the testing folder")
        return
    
    try:
        # Test 1: Submit a quiz
        test_submit_quiz()
        
        # Test 2: Get full performance summary
        test_performance_summary()
        
        # Test 3: Get filtered performance summary
        test_performance_summary_filtered()
        
        # Test 4: Get activity logs
        test_activity_logs()
        
        # Test 5: Get correct questions
        test_correct_questions()
        
        # Test 6: Get incorrect questions
        test_incorrect_questions()
        
        # Test 7: Get quick stats
        test_quick_stats()
        
        # Test 8: Submit multiple quizzes
        test_multiple_quizzes()
        
        # Final summary after multiple quizzes
        print("\n" + "="*60)
        print("FINAL: Quick Stats After Multiple Quizzes")
        print("="*60)
        test_quick_stats()
        
        print("\n" + "="*80)
        print(" ALL TESTS COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run individual tests or all tests
    
    # Option 1: Run all tests
    run_all_tests()
    
    # Option 2: Run individual tests (uncomment as needed)
    # test_submit_quiz()
    # test_performance_summary()
    # test_quick_stats()
