from fastapi import APIRouter, HTTPException, Query, Body, Depends
from typing import Optional, Dict, Any, List
import random
import logging
from google.cloud import firestore
from google.cloud import firestore as gcfs

from database.firebase_client import get_firestore_client
from helper.middleware import authenticate_request
from mockTestSection.score_calculator import compute_total_sat_score

logger = logging.getLogger(__name__)

mock_router = APIRouter(prefix="/api/mocks", tags=["mock"])

MODULE_KEYS = {
    "rw_m1": "rw_m1",
    "rw_m2_easy": "rw_m2_easy",
    "rw_m2_hard": "rw_m2_hard",
    "math_m1": "math_m1",
    "math_m2_easy": "math_m2_easy",
    "math_m2_hard": "math_m2_hard",
}


def _doc_to_dict(doc):
    """Convert Firestore DocumentSnapshot to dict with id + safe timestamps"""
    data = doc.to_dict() or {}
    if "created_at" in data and hasattr(data["created_at"], "isoformat"):
        data["created_at"] = data["created_at"].isoformat()
    data["id"] = doc.id
    return data


# ------------------ ROUTES ------------------ #

@mock_router.get("")
def list_mocks(
    limit: int = Query(20, ge=1, le=50, description="Number of mocks to return"),
    start_after: Optional[str] = Query(None, description="Document ID for pagination"),
    user: dict = Depends(authenticate_request)
):
    """List available mock tests - optimized to fetch only necessary fields"""
    db = get_firestore_client()

    # Optimize: Only fetch id, name, exam, created_at fields instead of entire documents
    coll = (db.collection("mock_tests")
            .select(["id", "name", "exam", "created_at"])
            .order_by("created_at", direction=firestore.Query.DESCENDING))
    
    if start_after:
        # For pagination, we still need to get the start_after document
        start_doc = db.collection("mock_tests").document(start_after).get()
        if start_doc.exists:
            coll = coll.start_after(start_doc)

    docs = coll.limit(limit).stream()
    items = [_doc_to_dict(d) for d in docs]
    return {"success": True, "items": items, "count": len(items)}


@mock_router.get("/{mock_id}/module/{module_key}")
def get_mock_module(
    mock_id: str,
    module_key: str,
    limit: Optional[int] = Query(None, description="Number of questions to return"),
    shuffle: bool = Query(False, description="Whether to shuffle questions (deprecated - use sequence for consistent numbering)"),
    user: dict = Depends(authenticate_request)
):
    """
    Fetch all questions from a specific module in a single optimized batch request.
    
    Questions are stored complete in the subcollection, so no additional fetching needed.
    Returns all question data (text, options, metadata, difficulty) in one response.
    
    IMPORTANT: Questions are returned sorted by sequence number to maintain consistent
    question numbering across exam view and result view. The sequence number stored
    in the database is the authoritative question number.
    """
    if module_key not in MODULE_KEYS:
        raise HTTPException(status_code=400, detail="invalid_module_key")

    db = get_firestore_client()
    
    # ✅ Step 1: Quick existence check (fetch only 'id' field)
    parent_ref = db.collection("mock_tests").document(mock_id)
    if not parent_ref.get(["id"]).exists:
        raise HTTPException(status_code=404, detail="mock_not_found")

    # ✅ Step 2: Batch fetch ALL questions from the module subcollection
    # Questions are already stored complete in the subcollection - no need to fetch from question_bank
    subref = parent_ref.collection(module_key)
    
    # Use stream() to efficiently fetch all documents in batch
    # Firestore automatically batches these requests
    question_docs = list(subref.stream())
    
    # Convert to dictionaries with doc_id and sequence
    items = []
    for qdoc in question_docs:
        q = qdoc.to_dict() or {}
        q["doc_id"] = qdoc.id
        # Ensure sequence is present (use doc_id as fallback for backward compatibility)
        if "sequence" not in q:
            q["sequence"] = int(qdoc.id) if qdoc.id.isdigit() else 0
        items.append(q)
    
    # ✅ Step 3: ALWAYS sort by sequence number to maintain consistent question numbering
    # This ensures question numbers remain the same across exam view and result view
    items.sort(key=lambda x: x.get("sequence", 0))
    
    # Apply limit if requested (but do NOT shuffle to maintain question number consistency)
    if limit and limit > 0:
        items = items[:limit]

    return {
        "success": True,
        "module": module_key,
        "count": len(items),
        "questions": items
    }


def _normalize_answer(answer: Dict[str, Any], question_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Normalize answer to consistent schema with backward compatibility.
    
    Accepts:
    - Legacy: {"question_id": str, "difficulty": int, "is_correct": bool}
    - New: {"question_id": str, "difficulty": int, "user_answer": {...}, "correct_answer": {...}, "is_correct": bool}
    
    Returns normalized format with option_no and actual answer values.
    
    Args:
        answer: User's answer data
        question_data: Optional question data from database to extract correct answer details
    """
    normalized = {
        "question_id": answer.get("question_id"),
        "difficulty": answer.get("difficulty", 1),
        "is_correct": answer.get("is_correct", False),
    }
    
    # Handle user_answer
    if "user_answer" in answer and answer["user_answer"] is not None:
        user_ans = answer["user_answer"]
        answer_type = user_ans.get("type", "mcq")
        normalized["user_answer"] = {
            "type": answer_type
        }
        
        # For MCQ, check if frontend already provided both option_no and value
        if answer_type == "mcq":
            # Check if option_no is already provided (new format)
            if "option_no" in user_ans and user_ans.get("option_no"):
                # Frontend sent both option_no and value - use them directly
                normalized["user_answer"]["option_no"] = user_ans.get("option_no")
                normalized["user_answer"]["value"] = user_ans.get("value")
            else:
                # Legacy format: value contains option letter, need to fetch text
                option_no = user_ans.get("value")  # This is A, B, C, D in legacy format
                normalized["user_answer"]["option_no"] = option_no
                
                # Try to get actual answer text from question_data
                if question_data and option_no and "options" in question_data:
                    options = question_data["options"]
                    # Options can be stored as array ["text1", "text2", "text3", "text4"]
                    if isinstance(options, list):
                        option_index = ord(option_no.upper()) - ord('A') if option_no and len(option_no) == 1 else -1
                        if 0 <= option_index < len(options):
                            normalized["user_answer"]["value"] = options[option_index]
                        else:
                            normalized["user_answer"]["value"] = option_no
                    # Or as dict {"A": "text1", "B": "text2", ...}
                    elif isinstance(options, dict):
                        normalized["user_answer"]["value"] = options.get(option_no, option_no)
                    else:
                        normalized["user_answer"]["value"] = option_no
                else:
                    normalized["user_answer"]["value"] = option_no
        else:
            # For SPR (student produced response), value is the answer itself
            normalized["user_answer"]["value"] = user_ans.get("value")
            normalized["user_answer"]["option_no"] = None
    else:
        # Backward compatibility: if no user_answer, use null
        normalized["user_answer"] = {
            "value": None,
            "option_no": None,
            "type": "mcq"
        }
    
    # Handle correct_answer
    # Try to get from question_data first, fallback to submitted answer
    if question_data and "correct_answer" in question_data and question_data.get("correct_answer"):
        # Extract correct answer from question data
        correct_option_no = question_data.get("correct_answer")
        question_type = question_data.get("type", "mcq")
        
        normalized["correct_answer"] = {
            "type": question_type,
            "option_no": correct_option_no if question_type == "mcq" else None
        }
        
        # Get actual answer text for MCQ
        if question_type == "mcq" and "options" in question_data and correct_option_no:
            options = question_data["options"]
            # Options can be stored as array ["text1", "text2", "text3", "text4"]
            if isinstance(options, list):
                option_index = ord(correct_option_no.upper()) - ord('A') if correct_option_no and len(correct_option_no) == 1 else -1
                if 0 <= option_index < len(options):
                    normalized["correct_answer"]["value"] = options[option_index]
                else:
                    normalized["correct_answer"]["value"] = correct_option_no
            # Or as dict {"A": "text1", "B": "text2", ...}
            elif isinstance(options, dict):
                normalized["correct_answer"]["value"] = options.get(correct_option_no, correct_option_no)
            else:
                normalized["correct_answer"]["value"] = correct_option_no
        else:
            # For SPR or when options not available
            normalized["correct_answer"]["value"] = correct_option_no
    elif "correct_answer" in answer and answer["correct_answer"] is not None:
        # Use provided correct_answer from frontend (fallback when question_data incomplete)
        corr_ans = answer["correct_answer"]
        answer_type = corr_ans.get("type", "mcq")
        normalized["correct_answer"] = {
            "type": answer_type
        }
        
        if answer_type == "mcq":
            # Check if option_no is already provided (new format)
            if "option_no" in corr_ans and corr_ans.get("option_no"):
                # Frontend sent both option_no and value - use them directly
                normalized["correct_answer"]["option_no"] = corr_ans.get("option_no")
                normalized["correct_answer"]["value"] = corr_ans.get("value")
            else:
                # Legacy format: value contains option letter
                option_no = corr_ans.get("value")
                normalized["correct_answer"]["option_no"] = option_no
                
                # Try to get option text from question_data if available
                if question_data and "options" in question_data and option_no:
                    options = question_data["options"]
                    if isinstance(options, list):
                        option_index = ord(option_no.upper()) - ord('A') if option_no and len(option_no) == 1 else -1
                        if 0 <= option_index < len(options):
                            normalized["correct_answer"]["value"] = options[option_index]
                        else:
                            normalized["correct_answer"]["value"] = option_no
                    elif isinstance(options, dict):
                        normalized["correct_answer"]["value"] = options.get(option_no, option_no)
                    else:
                        normalized["correct_answer"]["value"] = option_no
                else:
                    # Can't get text without question_data, use option letter
                    normalized["correct_answer"]["value"] = option_no
        else:
            # SPR type
            normalized["correct_answer"]["value"] = corr_ans.get("value")
            normalized["correct_answer"]["option_no"] = None
    else:
        # Backward compatibility: if no correct_answer, use null
        normalized["correct_answer"] = {
            "value": None,
            "option_no": None,
            "type": "mcq"
        }
    
    return normalized


@mock_router.post("/submit/{uid}")
def save_mock_attempt(
    uid: str,
    body: Dict[str, Any] = Body(...),
    user: dict = Depends(authenticate_request)
):
    """
    Save user's mock attempt and calculate SAT scores.
    
    Request Body (Module-based Schema):
    {
        "mock_id": str,
        "rw_m1": [{
            "question_id": str,
            "difficulty": int,
            "user_answer": {"value": "A" | "42" | null, "type": "mcq" | "spr"},
            "correct_answer": {"value": "A" | "42", "type": "mcq" | "spr"},
            "is_correct": bool
        }, ...],
        "rw_m2_easy": [...] OR "rw_m2_hard": [...],  // Only one Module 2
        "math_m1": [...],
        "math_m2_easy": [...] OR "math_m2_hard": [...],  // Only one Module 2
        "module2_names": {
            "rw": "rw_m2_easy" | "rw_m2_hard",
            "math": "math_m2_easy" | "math_m2_hard"
        }
    }
    
    Note: Each module is stored separately. Do NOT combine Module 1 and Module 2.
    Module 2 paths are mutually exclusive (only one easy OR hard per section).
    
    Response:
    {
        "success": true,
        "mock_id": str,
        "attempts": int,
        "module2_names": {
            "rw": "rw_m2_easy" | "rw_m2_hard",
            "math": "math_m2_easy" | "math_m2_hard"
        },
        "scores": {
            "rw_score": int,
            "math_score": int,
            "total_score": int,
            "details": {...}
        }
    }
    """
    db = get_firestore_client()

    # Extract required fields - DO NOT reject if extra fields present
    mock_id = body.get("mock_id")
    module2_names = body.get("module2_names", {})
    
    # Extract module-based answers
    rw_m1 = body.get("rw_m1", [])
    math_m1 = body.get("math_m1", [])
    
    # Determine which Module 2 was taken based on module2_names
    rw_module2_key = module2_names.get("rw", "rw_m2_hard")
    math_module2_key = module2_names.get("math", "math_m2_hard")
    
    # Get Module 2 answers
    rw_m2 = body.get(rw_module2_key, [])
    math_m2 = body.get(math_module2_key, [])

    # Validate inputs
    if not mock_id:
        raise HTTPException(status_code=400, detail="mock_id_required")
    
    if not isinstance(rw_m1, list):
        raise HTTPException(status_code=400, detail="rw_m1_must_be_list")
    
    if not isinstance(math_m1, list):
        raise HTTPException(status_code=400, detail="math_m1_must_be_list")
    
    if not isinstance(rw_m2, list):
        raise HTTPException(status_code=400, detail=f"{rw_module2_key}_must_be_list")
    
    if not isinstance(math_m2, list):
        raise HTTPException(status_code=400, detail=f"{math_module2_key}_must_be_list")
    
    if rw_module2_key not in ["rw_m2_easy", "rw_m2_hard"]:
        raise HTTPException(status_code=400, detail="rw_module2_must_be_rw_m2_easy_or_rw_m2_hard")
    
    if math_module2_key not in ["math_m2_easy", "math_m2_hard"]:
        raise HTTPException(status_code=400, detail="math_module2_must_be_math_m2_easy_or_math_m2_hard")
    
    # Fetch question data from mock test to get correct answers and options
    # This allows us to store complete answer information
    mock_ref = db.collection("mock_tests").document(mock_id)
    
    # Create a mapping of question_id -> question_data for all modules
    question_map = {}
    
    # Fetch questions from all 4 modules
    for module_key in ["rw_m1", rw_module2_key, "math_m1", math_module2_key]:
        try:
            module_questions = mock_ref.collection(module_key).stream()
            for q_doc in module_questions:
                q_data = q_doc.to_dict()
                if q_data:
                    question_map[q_doc.id] = q_data
        except Exception as e:
            logger.warning(f"Could not fetch questions from {module_key}: {str(e)}")
    
    # Log if any submitted questions are missing from question_map
    all_submitted_ids = set()
    for ans_list in [rw_m1, rw_m2, math_m1, math_m2]:
        for ans in ans_list:
            q_id = ans.get("question_id")
            if q_id:
                all_submitted_ids.add(q_id)
    
    missing_questions = [q_id for q_id in all_submitted_ids if q_id not in question_map]
    if missing_questions:
        logger.warning(f"Questions not found in mock test {mock_id}: {missing_questions}")
    
    # Normalize all answers to consistent schema (per module) with question data
    normalized_rw_m1 = [
        _normalize_answer(ans, question_map.get(ans.get("question_id")))
        for ans in rw_m1
    ]
    normalized_rw_m2 = [
        _normalize_answer(ans, question_map.get(ans.get("question_id")))
        for ans in rw_m2
    ]
    normalized_math_m1 = [
        _normalize_answer(ans, question_map.get(ans.get("question_id")))
        for ans in math_m1
    ]
    normalized_math_m2 = [
        _normalize_answer(ans, question_map.get(ans.get("question_id")))
        for ans in math_m2
    ]

    # Compute SAT scores using normalized answers
    # Combine Module 1 and Module 2 for scoring calculation only
    # Note: Score calculator still uses original logic (question_id, difficulty, is_correct)
    # which is present in normalized answers, so it remains compatible
    combined_rw_answers = normalized_rw_m1 + normalized_rw_m2
    combined_math_answers = normalized_math_m1 + normalized_math_m2
    
    # Determine module2_path from module2_names
    rw_module2_path = "easy" if rw_module2_key == "rw_m2_easy" else "hard"
    math_module2_path = "easy" if math_module2_key == "math_m2_easy" else "hard"
    
    try:
        scores = compute_total_sat_score(
            rw_answers=combined_rw_answers,
            math_answers=combined_math_answers,
            rw_module2_path=rw_module2_path,
            math_module2_path=math_module2_path
        )
    except Exception as e:
        logger.error(f"Error computing scores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"score_calculation_error: {str(e)}")

    # ✅ Find user by inner field 'id'
    user_query = db.collection("users").where("id", "==", uid).limit(1).stream()
    user_doc = next(user_query, None)

    if not user_doc:
        raise HTTPException(
            status_code=404,
            detail=f"user_not_found_for_uid: {uid}"
        )

    user_doc_ref = db.collection("users").document(user_doc.id)
    attempt_ref = user_doc_ref.collection("mock_attempts").document(mock_id)

    # Get previous attempts count
    snap = attempt_ref.get()
    prev_attempts = snap.to_dict().get("attempts", 0) if snap.exists else 0
    new_attempts = prev_attempts + 1

    # Prepare payload with scores and full answer context
    # Store answers BY MODULE (not combined) for:
    # - Accurate review screens
    # - Auditing capabilities
    # - Future re-scoring safety
    # - Reflecting actual exam structure
    # - Module-specific analysis
    payload = {
        "mock_id": mock_id,
        "rw_m1": normalized_rw_m1,
        rw_module2_key: normalized_rw_m2,  # Only store the Module 2 that was taken
        "math_m1": normalized_math_m1,
        math_module2_key: normalized_math_m2,  # Only store the Module 2 that was taken
        "module2_names": {
            "rw": rw_module2_key,
            "math": math_module2_key
        },
        "scores": scores,
        "attempts": new_attempts,
        "updated_at": gcfs.SERVER_TIMESTAMP,
    }

    # Save to Firestore
    attempt_ref.set(payload, merge=True)

    return {
        "success": True,
        "mock_id": mock_id,
        "attempts": new_attempts,
        "module2_names": {
            "rw": rw_module2_key,
            "math": math_module2_key
        },
        "scores": scores
    }


@mock_router.get("/attempt/{uid}/{mock_id}")
def get_mock_attempt(uid: str, mock_id: str, user: dict = Depends(authenticate_request)):
    """Fetch a specific user's saved mock attempt — matched strictly by inner field 'id'"""
    db = get_firestore_client()

    # ✅ Always match using 'id' field
    user_query = db.collection("users").where("id", "==", uid).limit(1).stream()
    user_doc = next(user_query, None)
    if not user_doc:
        raise HTTPException(
            status_code=404,
            detail=f"user_not_found_for_uid: {uid}"
        )

    user_doc_ref = db.collection("users").document(user_doc.id)
    ref = user_doc_ref.collection("mock_attempts").document(mock_id)
    snap = ref.get()

    if not snap.exists:
        raise HTTPException(status_code=404, detail="not_found")

    data = snap.to_dict() or {}
    if "updated_at" in data and hasattr(data["updated_at"], "isoformat"):
        data["updated_at"] = data["updated_at"].isoformat()

    return {"success": True, "data": data}


@mock_router.get("/attempts/{uid}")
def get_all_mock_attempts(uid: str, user: dict = Depends(authenticate_request)):
    """Fetch all mock attempts for a given user, strictly matched by inner field 'id'"""
    db = get_firestore_client()

    # ✅ Find user by 'id' field only
    user_query = db.collection("users").where("id", "==", uid).limit(1).stream()
    user_doc = next(user_query, None)
    if not user_doc:
        raise HTTPException(
            status_code=404,
            detail=f"user_not_found_for_uid: {uid}"
        )

    user_doc_ref = db.collection("users").document(user_doc.id)
    attempts_ref = user_doc_ref.collection("mock_attempts")
    docs = list(attempts_ref.stream())

    attempts = {
        d.id: {
            "attempts": d.to_dict().get("attempts", 0),
            "updated_at": (
                d.to_dict().get("updated_at").isoformat()
                if hasattr(d.to_dict().get("updated_at"), "isoformat")
                else None
            ),
        }
        for d in docs
    }

    return {
        "success": True,
        "attempts": attempts,
        "count": len(attempts)
    }
