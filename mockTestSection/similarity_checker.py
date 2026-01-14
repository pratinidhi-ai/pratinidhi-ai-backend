# mockTestSection/similarity_checker.py
"""
LLM-based similarity checker for mock test questions.
Ensures no two questions in a mock paper are too similar.
"""

import json
from typing import List, Dict, Set, Tuple, Optional
from ai_utils.all_llm_model_methods import generate_openai_response


# Default model for similarity checking
DEFAULT_SIMILARITY_MODEL = "gpt-4o"

# Similarity threshold - questions with similarity >= this are considered duplicates
SIMILARITY_THRESHOLD = 0.7

# Maximum questions to check in a single LLM call (to avoid token limits)
BATCH_SIZE = 10


def _extract_question_text(question: Dict) -> str:
    """
    Extract the main text content from a question for comparison.
    Combines question text, options, and any passage/stimulus.
    """
    parts = []
    
    # Main question text
    if question.get("question"):
        parts.append(question["question"])
    if question.get("question_text"):
        parts.append(question["question_text"])
    if question.get("text"):
        parts.append(question["text"])
    
    # Passage or stimulus (for reading questions)
    if question.get("passage"):
        parts.append(f"Passage: {question['passage'][:500]}")  # Truncate long passages
    if question.get("stimulus"):
        parts.append(f"Stimulus: {question['stimulus'][:500]}")
    
    # Options (important for similarity - same question with different options is different)
    options = question.get("options") or question.get("choices") or []
    if options:
        if isinstance(options, list):
            for i, opt in enumerate(options):
                if isinstance(opt, dict):
                    opt_text = opt.get("text") or opt.get("content") or str(opt)
                else:
                    opt_text = str(opt)
                parts.append(f"Option {chr(65+i)}: {opt_text}")
        elif isinstance(options, dict):
            for key, val in options.items():
                parts.append(f"Option {key}: {val}")
    
    return "\n".join(parts)


def _build_similarity_prompt(new_question: Dict, existing_questions: List[Dict]) -> str:
    """Build the prompt for LLM similarity checking."""
    
    new_q_text = _extract_question_text(new_question)
    
    existing_texts = []
    for i, eq in enumerate(existing_questions):
        eq_text = _extract_question_text(eq)
        existing_texts.append(f"[Q{i+1}]\n{eq_text}")
    
    prompt = f"""You are a question similarity detector for educational assessments.

TASK: Check if the NEW QUESTION is too similar to any of the EXISTING QUESTIONS.

Two questions are "too similar" if:
1. They test the exact same concept with nearly identical wording
2. They have the same mathematical setup with only numbers changed
3. They ask about the same passage/text with the same question type
4. They would feel repetitive to a student taking the test

NEW QUESTION:
{new_q_text}

EXISTING QUESTIONS:
{chr(10).join(existing_texts)}

RESPONSE FORMAT (JSON only):
{{
    "is_similar": true/false,
    "similar_to": null or question number (1, 2, 3...),
    "reason": "brief explanation"
}}

Respond with ONLY the JSON, no other text."""

    return prompt


def check_question_similarity(
    new_question: Dict,
    existing_questions: List[Dict],
    model: str = DEFAULT_SIMILARITY_MODEL
) -> Tuple[bool, str]:
    """
    Check if a new question is too similar to any existing questions.
    
    Args:
        new_question: The question to check
        existing_questions: List of questions already in the paper
        model: LLM model to use for checking
        
    Returns:
        Tuple of (is_similar: bool, reason: str)
    """
    if not existing_questions:
        return False, "No existing questions to compare"
    
    # Only check against the most recent questions to limit token usage
    questions_to_check = existing_questions[-BATCH_SIZE:]
    
    prompt = _build_similarity_prompt(new_question, questions_to_check)
    
    messages = [
        {"role": "system", "content": "You are a question similarity detector for educational assessments. Respond only with valid JSON."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = generate_openai_response(
            messages=messages,
            model=model,
            max_tokens=200,
            temperature=0.1  # Low temperature for consistent results
        )
        
        if not response:
            return False, "Empty response from LLM - allowing question"
        
        # Parse JSON response
        response_text = response.strip()
        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        is_similar = result.get("is_similar", False)
        reason = result.get("reason", "Unknown")
        
        return is_similar, reason
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Similarity check JSON parse error: {e}")
        return False, "JSON parse error - allowing question"
    except Exception as e:
        print(f"⚠️ Similarity check error: {e}")
        return False, f"Error: {str(e)} - allowing question"


def filter_similar_questions(
    questions: List[Dict],
    existing_questions: Optional[List[Dict]] = None,
    model: str = DEFAULT_SIMILARITY_MODEL,
    enable_checking: bool = True
) -> Tuple[List[Dict], List[Dict]]:
    """
    Filter out questions that are too similar to existing ones.
    
    Args:
        questions: List of candidate questions to filter
        existing_questions: List of questions already selected
        model: LLM model to use
        enable_checking: If False, skip similarity checking (for speed)
        
    Returns:
        Tuple of (accepted_questions, rejected_questions)
    """
    if not enable_checking:
        return questions, []
    
    existing = list(existing_questions) if existing_questions else []
    accepted = []
    rejected = []
    
    for q in questions:
        is_similar, reason = check_question_similarity(q, existing, model)
        
        if is_similar:
            print(f"🚫 Rejected similar question: {reason}")
            rejected.append(q)
        else:
            accepted.append(q)
            existing.append(q)  # Add to existing for subsequent checks
    
    return accepted, rejected
