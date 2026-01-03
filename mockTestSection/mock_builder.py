# mockTestSection/mock_builder.py
import random
import datetime
from typing import Dict, List, Optional

from mockTestSection.sat_blueprint import SAT_BLUEPRINT
from mockTestSection.mock_selector import build_module_docs
from mockTestSection.mock_store import create_mock_parent, save_module_questions


# SPR (Student Provided Response) limits per module
# Total SPR questions in a mock test = 11 (5 in M1 + 6 in M2)
SPR_LIMIT_MATH_M1 = 5
SPR_LIMIT_MATH_M2 = 6


def _apply_spr_limits(questions: List[Dict], spr_limit: int) -> List[Dict]:
    """
    Apply SPR (Student Provided Response) limits to a list of questions.
    
    Only the first `spr_limit` questions that have is_spr_candidate=True from the
    question bank will retain that flag. All other questions will have 
    is_spr_candidate set to False.
    
    Args:
        questions: List of question dicts from the question bank
        spr_limit: Maximum number of SPR questions allowed in this module
        
    Returns:
        List of questions with is_spr_candidate properly set
    """
    spr_count = 0
    result = []
    
    for q in questions:
        q_copy = dict(q)  # Make a copy to avoid modifying original
        
        # Check if this question is an SPR candidate from the question bank
        is_spr_from_bank = q_copy.get("is_spr_candidate", False)
        
        if is_spr_from_bank and spr_count < spr_limit:
            # Keep is_spr_candidate as True
            q_copy["is_spr_candidate"] = True
            spr_count += 1
        else:
            # Set is_spr_candidate to False (either not a candidate or limit reached)
            q_copy["is_spr_candidate"] = False
        
        result.append(q_copy)
    
    return result


def build_and_store_one_mock(
    name: str,
    seed: Optional[int] = None,
    filters: Optional[Dict] = None,
) -> str:
    """
    Build one mock using the SAT blueprint, fetch FULL question docs (incl. answers),
    and store them under a single parent document with 6 subcollections.
    Returns the parent mock_id (same as the mock name).
    
    SPR (Student Provided Response) Questions:
    - Math Module 1: Max 5 SPR questions
    - Math Module 2 (easy/hard): Max 6 SPR questions each
    - Total SPR questions in mock: 11 (5 + 6)
    - RW modules: No SPR questions (is_spr_candidate always False)
    """
    rng = random.Random(seed)
    filters = filters or {}
    theme = filters.get("theme")
    tags = filters.get("tags")
    tag = filters.get("tag")

    bp = SAT_BLUEPRINT

    # 1️⃣ Create parent document with 'name' as ID
    mock_id = name  # doc name = mock name

    create_mock_parent(
        mock_id=mock_id,
        exam="SAT",
        name=name,  # Explicitly pass name for display
    )

    # 2️⃣ Build all 6 modules
    rw_m1 = build_module_docs(bp["rw"]["module1_balanced"], rng, theme, tags, tag)
    rw_m2_e = build_module_docs(bp["rw"]["module2_easy"], rng, theme, tags, tag)
    rw_m2_h = build_module_docs(bp["rw"]["module2_hard"], rng, theme, tags, tag)
    math_m1 = build_module_docs(bp["math"]["module1_balanced"], rng, theme, tags, tag)
    math_m2_e = build_module_docs(bp["math"]["module2_easy"], rng, theme, tags, tag)
    math_m2_h = build_module_docs(bp["math"]["module2_hard"], rng, theme, tags, tag)

    # 3️⃣ Apply SPR limits to math modules
    # Math M1: Allow max 5 SPR questions
    math_m1 = _apply_spr_limits(math_m1, SPR_LIMIT_MATH_M1)
    # Math M2 (easy): Allow max 6 SPR questions
    math_m2_e = _apply_spr_limits(math_m2_e, SPR_LIMIT_MATH_M2)
    # Math M2 (hard): Allow max 6 SPR questions
    math_m2_h = _apply_spr_limits(math_m2_h, SPR_LIMIT_MATH_M2)

    # 4️⃣ Save all modules
    save_module_questions(mock_id, "rw", "module1_balanced", rw_m1)
    save_module_questions(mock_id, "rw", "module2_easy", rw_m2_e)
    save_module_questions(mock_id, "rw", "module2_hard", rw_m2_h)

    save_module_questions(mock_id, "math", "module1_balanced", math_m1)
    save_module_questions(mock_id, "math", "module2_easy", math_m2_e)
    save_module_questions(mock_id, "math", "module2_hard", math_m2_h)

    return mock_id
