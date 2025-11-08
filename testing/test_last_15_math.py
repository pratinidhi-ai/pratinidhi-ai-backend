"""
Test script for Last 15 Math Questions API
Tests the automatic tracking and retrieval of last 15 math questions
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000/api"
STUDENT_ID = "test_user_last15_math"  # Use a test user ID

# Get your bearer token from the GET_BEARER_TOKEN.md guide
BEARER_TOKEN = "your_token_here"  # Replace with actual token

headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json"
}


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def submit_math_quiz(quiz_num, num_questions=5):
    """Submit a test math quiz"""
    print(f"📤 Submitting Math Quiz #{quiz_num} ({num_questions} questions)...")
    
    quiz_data = {
        "student_id": STUDENT_ID,
        "subject": "math",
        "sub_category": "algebra",
        "difficulty_level": 3,
        "number_of_questions": num_questions,
        "number_of_correct_answers": num_questions - 2,  # 2 wrong answers
        "time_spent": 300,
        "tag_wise_details": [
            {
                "tag": "linear-equations",
                "total_questions": 3,
                "correct_answers": 2
            },
            {
                "tag": "quadratic-equations",
                "total_questions": 2,
                "correct_answers": 1
            }
        ],
        "correct_question_ids": [f"q{quiz_num}_{i}" for i in range(1, num_questions - 1)],
        "incorrect_question_ids": [f"q{quiz_num}_{num_questions - 1}", f"q{quiz_num}_{num_questions}"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/analytics/submit-quiz",
            headers=headers,
            json=quiz_data,
            timeout=10
        )
        
        if response.status_code == 202:  # Accepted
            data = response.json()
            print(f"✅ Quiz #{quiz_num} submitted successfully!")
            print(f"   Request ID: {data.get('request_id')}")
            print(f"   Estimated Accuracy: {data.get('estimated_accuracy')}%")
            return True
        else:
            print(f"❌ Failed to submit quiz: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error submitting quiz: {str(e)}")
        return False


def get_last_15_math_questions():
    """Get the last 15 math questions for the student"""
    print(f"\n📥 Fetching last 15 math questions for student: {STUDENT_ID}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/analytics/last-15-math-questions/{STUDENT_ID}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                questions_data = data.get('data', {})
                questions = questions_data.get('questions', [])
                count = questions_data.get('count', 0)
                last_updated = questions_data.get('last_updated')
                
                print(f"\n✅ Successfully retrieved last 15 math questions!")
                print(f"   Total Questions: {count}")
                print(f"   Last Updated: {last_updated}")
                
                if count > 0:
                    print(f"\n📊 Questions Summary:")
                    print(f"   {'#':<4} {'Question ID':<15} {'Correct':<10} {'Diff':<6} {'Sub-Category':<20} {'Tags'}")
                    print(f"   {'-'*4} {'-'*15} {'-'*10} {'-'*6} {'-'*20} {'-'*30}")
                    
                    correct_count = 0
                    for idx, q in enumerate(questions, 1):
                        status = "✓" if q['is_correct'] else "✗"
                        if q['is_correct']:
                            correct_count += 1
                        
                        tags_str = ", ".join(q['tags'][:2])  # Show first 2 tags
                        if len(q['tags']) > 2:
                            tags_str += f" (+{len(q['tags']) - 2} more)"
                        
                        print(f"   {idx:<4} {q['question_id']:<15} {status:<10} {q['difficulty_level']:<6} {q['sub_category']:<20} {tags_str}")
                    
                    accuracy = (correct_count / count * 100) if count > 0 else 0
                    print(f"\n   Overall Accuracy: {accuracy:.1f}% ({correct_count}/{count})")
                    print(f"   Correct: {correct_count}, Incorrect: {count - correct_count}")
                else:
                    print(f"\n📝 No math questions found yet.")
                
                return questions
            else:
                print(f"❌ API returned success=false")
                print(f"   Message: {data.get('message')}")
                return None
        else:
            print(f"❌ Failed to get questions: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting questions: {str(e)}")
        return None


def test_scenario_1():
    """Test Scenario 1: First Quiz - Should show 5 questions"""
    print_section("TEST SCENARIO 1: First Math Quiz")
    print("Expected: Should return 5 questions")
    
    # Submit first quiz
    if submit_math_quiz(1, num_questions=5):
        import time
        time.sleep(2)  # Wait for async processing
        questions = get_last_15_math_questions()
        
        if questions and len(questions) == 5:
            print("\n✅ TEST PASSED: Got exactly 5 questions as expected!")
            return True
        else:
            print(f"\n❌ TEST FAILED: Expected 5 questions, got {len(questions) if questions else 0}")
            return False
    return False


def test_scenario_2():
    """Test Scenario 2: Multiple Quizzes - Should track up to 15"""
    print_section("TEST SCENARIO 2: Multiple Quizzes")
    print("Expected: Should track up to 15 questions")
    
    # Submit 2 more quizzes (5 questions each = 10 more questions, total 15)
    success = True
    for i in range(2, 4):  # Quiz 2 and 3
        if not submit_math_quiz(i, num_questions=5):
            success = False
            break
        import time
        time.sleep(1)
    
    if success:
        import time
        time.sleep(2)  # Wait for async processing
        questions = get_last_15_math_questions()
        
        if questions and len(questions) == 15:
            print("\n✅ TEST PASSED: Got exactly 15 questions as expected!")
            return True
        else:
            print(f"\n❌ TEST FAILED: Expected 15 questions, got {len(questions) if questions else 0}")
            return False
    return False


def test_scenario_3():
    """Test Scenario 3: Rolling Window - Should drop oldest"""
    print_section("TEST SCENARIO 3: Rolling Window (15+ questions)")
    print("Expected: Should maintain only 15 questions (drop oldest)")
    
    # Submit one more quiz (3 questions)
    if submit_math_quiz(4, num_questions=3):
        import time
        time.sleep(2)  # Wait for async processing
        questions = get_last_15_math_questions()
        
        if questions and len(questions) == 15:
            print("\n✅ TEST PASSED: Still 15 questions (oldest 3 were dropped)!")
            
            # Check that newest questions are present
            newest_ids = [f"q4_1", "q4_2", "q4_3"]
            found_newest = [q for q in questions if q['question_id'] in newest_ids]
            
            if len(found_newest) == 3:
                print(f"✅ Newest questions are present: {[q['question_id'] for q in found_newest]}")
            else:
                print(f"⚠️  Warning: Some newest questions not found")
            
            return True
        else:
            print(f"\n❌ TEST FAILED: Expected 15 questions, got {len(questions) if questions else 0}")
            return False
    return False


def test_scenario_4():
    """Test Scenario 4: Data Quality Check"""
    print_section("TEST SCENARIO 4: Data Quality Check")
    print("Expected: All questions should have required fields")
    
    questions = get_last_15_math_questions()
    
    if not questions:
        print("❌ No questions to validate")
        return False
    
    required_fields = ['question_id', 'is_correct', 'difficulty_level', 'tags', 'sub_category', 'timestamp']
    all_valid = True
    
    for idx, q in enumerate(questions, 1):
        missing_fields = [field for field in required_fields if field not in q]
        if missing_fields:
            print(f"❌ Question #{idx} missing fields: {missing_fields}")
            all_valid = False
        
        # Validate data types
        if not isinstance(q.get('is_correct'), bool):
            print(f"❌ Question #{idx}: 'is_correct' should be boolean, got {type(q.get('is_correct'))}")
            all_valid = False
        
        if not isinstance(q.get('difficulty_level'), int) or not (1 <= q.get('difficulty_level', 0) <= 5):
            print(f"❌ Question #{idx}: 'difficulty_level' should be 1-5, got {q.get('difficulty_level')}")
            all_valid = False
        
        if not isinstance(q.get('tags'), list) or len(q.get('tags', [])) == 0:
            print(f"❌ Question #{idx}: 'tags' should be non-empty list")
            all_valid = False
    
    if all_valid:
        print(f"\n✅ TEST PASSED: All {len(questions)} questions have valid data!")
        return True
    else:
        print(f"\n❌ TEST FAILED: Some questions have invalid data")
        return False


def run_all_tests():
    """Run all test scenarios"""
    print("\n" + "🚀" * 40)
    print("  LAST 15 MATH QUESTIONS API TEST SUITE")
    print("🚀" * 40)
    
    print(f"\nConfiguration:")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Student ID: {STUDENT_ID}")
    print(f"  Token: {'Set ✓' if BEARER_TOKEN != 'your_token_here' else 'NOT SET ✗'}")
    
    if BEARER_TOKEN == "your_token_here":
        print("\n❌ ERROR: Please set your BEARER_TOKEN in the script!")
        print("   See docs/GET_BEARER_TOKEN.md for instructions")
        return
    
    results = {
        "Scenario 1 (First Quiz)": test_scenario_1(),
        "Scenario 2 (Multiple Quizzes)": test_scenario_2(),
        "Scenario 3 (Rolling Window)": test_scenario_3(),
        "Scenario 4 (Data Quality)": test_scenario_4()
    }
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status} - {test_name}")
    
    print(f"\n  Overall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")


if __name__ == "__main__":
    run_all_tests()
