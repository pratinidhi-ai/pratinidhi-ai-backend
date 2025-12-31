"""
SAT Score Calculator Module

This module implements the realistic Digital SAT scoring algorithm.
It provides a deterministic, side-effect-free scoring function that:
- Calculates raw scores based on correct answers
- Applies adaptive module path adjustments
- Rewards higher difficulty question correctness
- Caps scores realistically based on module path

Constants:
- Reading & Writing: 54 total questions
- Math: 44 total questions
- Score range: 200-800 per section
- Easy path max: 620 per section
"""

from typing import List, Dict, Any


def compute_section_score(answers: List[Dict[str, Any]], module2_path: str) -> int:
    """
    Compute the SAT section score based on answers and adaptive module path.
    
    Args:
        answers: List of answered questions for ONE section (RW or Math).
                 Each item must have:
                 {
                     "question_id": str,
                     "difficulty": int (1-5),
                     "is_correct": bool
                 }
        module2_path: "hard" or "easy" - indicates which Module 2 the student received
        
    Returns:
        int: Final section score (200-800, or 200-620 for easy path)
        
    Scoring Logic:
        1. Raw Score: Count of correct answers (no negative marking)
        2. Base Scaling: 200 + 600 * (raw/total) * path_factor
           - path_factor = 1.0 for "hard", 0.7 for "easy"
        3. Difficulty Adjustment: (avg_difficulty - 3.0) * 20
           - Only considers correct answers
           - Defaults to 3.0 if no correct answers
        4. Final Score: base_score + difficulty_bonus
        5. Clamping:
           - Minimum: 200
           - Maximum: 800 (hard) or 620 (easy)
    """
    total_questions = len(answers)
    
    # Handle edge case: no answers provided
    if total_questions == 0:
        return 200
    
    # Step 1: Calculate raw score (number of correct answers)
    raw_correct = sum(1 for a in answers if a.get("is_correct", False))
    
    # Step 2: Calculate average difficulty of correct answers only
    if raw_correct > 0:
        correct_answers = [a for a in answers if a.get("is_correct", False)]
        avg_difficulty = sum(a.get("difficulty", 3) for a in correct_answers) / raw_correct
    else:
        # If no correct answers, use neutral difficulty
        avg_difficulty = 3.0
    
    # Step 3: Apply path factor based on Module 2 difficulty
    path_factor = 1.0 if module2_path == "hard" else 0.7
    
    # Step 4: Calculate base score
    # Base formula: 200 + 600 * (proportion correct) * path_factor
    base_score = 200 + 600 * (raw_correct / total_questions) * path_factor
    
    # Step 5: Calculate difficulty bonus
    # Rewards answering harder questions correctly
    difficulty_bonus = (avg_difficulty - 3.0) * 20
    
    # Step 6: Combine base score and difficulty bonus
    score = base_score + difficulty_bonus
    
    # Step 7: Apply minimum score constraint
    score = max(score, 200)
    
    # Step 8: Apply maximum score constraint based on path
    if module2_path == "easy":
        score = min(score, 620)
    else:
        score = min(score, 800)
    
    # Step 9: Round to nearest integer
    return round(score)


def compute_total_sat_score(
    rw_answers: List[Dict[str, Any]],
    math_answers: List[Dict[str, Any]],
    rw_module2_path: str,
    math_module2_path: str
) -> Dict[str, Any]:
    """
    Compute complete SAT scores for both sections.
    
    Args:
        rw_answers: List of Reading & Writing answers
        math_answers: List of Math answers
        rw_module2_path: "hard" or "easy" for RW Module 2
        math_module2_path: "hard" or "easy" for Math Module 2
        
    Returns:
        Dict containing:
        {
            "rw_score": int,
            "math_score": int,
            "total_score": int,
            "details": {
                "rw": {
                    "raw_correct": int,
                    "total_questions": int,
                    "module2": str
                },
                "math": {
                    "raw_correct": int,
                    "total_questions": int,
                    "module2": str
                }
            }
        }
    """
    # Compute individual section scores
    rw_score = compute_section_score(rw_answers, rw_module2_path)
    math_score = compute_section_score(math_answers, math_module2_path)
    
    # Calculate raw correct counts for details
    rw_raw_correct = sum(1 for a in rw_answers if a.get("is_correct", False))
    math_raw_correct = sum(1 for a in math_answers if a.get("is_correct", False))
    
    # Compute total SAT score (sum of both sections)
    total_score = rw_score + math_score
    
    return {
        "rw_score": rw_score,
        "math_score": math_score,
        "total_score": total_score,
        "details": {
            "rw": {
                "raw_correct": rw_raw_correct,
                "total_questions": len(rw_answers),
                "module2": rw_module2_path
            },
            "math": {
                "raw_correct": math_raw_correct,
                "total_questions": len(math_answers),
                "module2": math_module2_path
            }
        }
    }
