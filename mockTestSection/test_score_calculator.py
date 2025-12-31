"""
Test the SAT Score Calculator

This script tests the scoring logic with various scenarios to ensure
it produces realistic and expected results.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mockTestSection.score_calculator import compute_section_score, compute_total_sat_score


def test_perfect_score_hard_path():
    """Test perfect score on hard path"""
    # 27 questions, all correct, all difficulty 5, hard path
    answers = [
        {"question_id": f"q{i}", "difficulty": 5, "is_correct": True}
        for i in range(27)
    ]
    score = compute_section_score(answers, "hard")
    print(f"Perfect score (hard path, all diff 5): {score}")
    assert 750 <= score <= 800, f"Expected ~800, got {score}"


def test_perfect_score_easy_path():
    """Test perfect score on easy path (should be capped at 620)"""
    answers = [
        {"question_id": f"q{i}", "difficulty": 3, "is_correct": True}
        for i in range(27)
    ]
    score = compute_section_score(answers, "easy")
    print(f"Perfect score (easy path): {score}")
    assert score <= 620, f"Easy path should cap at 620, got {score}"


def test_zero_correct():
    """Test with no correct answers"""
    answers = [
        {"question_id": f"q{i}", "difficulty": 3, "is_correct": False}
        for i in range(27)
    ]
    score = compute_section_score(answers, "hard")
    print(f"Zero correct (hard path): {score}")
    assert score == 200, f"Expected 200, got {score}"


def test_half_correct_hard():
    """Test with 50% correct on hard path"""
    answers = []
    for i in range(27):
        answers.append({
            "question_id": f"q{i}",
            "difficulty": 3,
            "is_correct": i % 2 == 0  # Every other one correct
        })
    score = compute_section_score(answers, "hard")
    print(f"50% correct (hard path, diff 3): {score}")
    assert 450 <= score <= 550, f"Expected ~500, got {score}"


def test_high_difficulty_bonus():
    """Test difficulty bonus - answering hard questions correctly"""
    # 20 correct, difficulty 5 vs difficulty 1
    hard_answers = [
        {"question_id": f"q{i}", "difficulty": 5, "is_correct": True}
        for i in range(20)
    ] + [
        {"question_id": f"q{i}", "difficulty": 3, "is_correct": False}
        for i in range(7)
    ]
    
    easy_answers = [
        {"question_id": f"q{i}", "difficulty": 1, "is_correct": True}
        for i in range(20)
    ] + [
        {"question_id": f"q{i}", "difficulty": 3, "is_correct": False}
        for i in range(7)
    ]
    
    hard_score = compute_section_score(hard_answers, "hard")
    easy_score = compute_section_score(easy_answers, "hard")
    
    print(f"20/27 correct (diff 5): {hard_score}")
    print(f"20/27 correct (diff 1): {easy_score}")
    print(f"Difficulty bonus effect: {hard_score - easy_score} points")
    
    assert hard_score > easy_score, "Higher difficulty should give higher score"


def test_full_sat_calculation():
    """Test complete SAT score calculation"""
    # RW: 40/54 correct, hard path, mixed difficulty
    rw_answers = []
    for i in range(54):
        is_correct = i < 40  # First 40 are correct
        diff = (i % 5) + 1  # Cycle through difficulties 1-5
        rw_answers.append({
            "question_id": f"rw_q{i}",
            "difficulty": diff,
            "is_correct": is_correct
        })
    
    # Math: 30/44 correct, easy path, mixed difficulty
    math_answers = []
    for i in range(44):
        is_correct = i < 30  # First 30 are correct
        diff = (i % 5) + 1
        math_answers.append({
            "question_id": f"math_q{i}",
            "difficulty": diff,
            "is_correct": is_correct
        })
    
    result = compute_total_sat_score(
        rw_answers=rw_answers,
        math_answers=math_answers,
        rw_module2_path="hard",
        math_module2_path="easy"
    )
    
    print("\n=== Full SAT Score Test ===")
    print(f"RW Score: {result['rw_score']}")
    print(f"Math Score: {result['math_score']}")
    print(f"Total Score: {result['total_score']}")
    print(f"Details: {result['details']}")
    
    assert 200 <= result['rw_score'] <= 800
    assert 200 <= result['math_score'] <= 620  # Easy path capped
    assert 400 <= result['total_score'] <= 1420


if __name__ == "__main__":
    print("Running SAT Score Calculator Tests...\n")
    
    try:
        test_perfect_score_hard_path()
        test_perfect_score_easy_path()
        test_zero_correct()
        test_half_correct_hard()
        test_high_difficulty_bonus()
        test_full_sat_calculation()
        
        print("\n✅ All tests passed!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
