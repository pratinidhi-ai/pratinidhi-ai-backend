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
    shuffle: bool = Query(True, description="Whether to shuffle questions"),
    user: dict = Depends(authenticate_request)
):
    """
    Fetch all questions from a specific module in a single optimized batch request.
    
    Questions are stored complete in the subcollection, so no additional fetching needed.
    Returns all question data (text, options, metadata, difficulty) in one response.
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
    
    # Convert to dictionaries with doc_id
    items = []
    for qdoc in question_docs:
        q = qdoc.to_dict() or {}
        q["doc_id"] = qdoc.id
        items.append(q)
    
    # ✅ Step 3: Apply shuffle and limit if requested (optional client preferences)
    if shuffle:
        random.shuffle(items)
    if limit and limit > 0:
        items = items[:limit]

    return {
        "success": True,
        "module": module_key,
        "count": len(items),
        "questions": items
    }


@mock_router.post("/submit/{uid}")
def save_mock_attempt(
    uid: str,
    body: Dict[str, Any] = Body(...),
    user: dict = Depends(authenticate_request)
):
    """
    Save user's mock attempt and calculate SAT scores.
    
    Request Body:
    {
        "mock_id": str,
        "rw_answers": [{"question_id": str, "difficulty": int, "is_correct": bool}, ...],
        "math_answers": [{"question_id": str, "difficulty": int, "is_correct": bool}, ...],
        "rw_module2_path": "easy" | "hard",
        "math_module2_path": "easy" | "hard"
    }
    
    Response:
    {
        "success": true,
        "mock_id": str,
        "attempts": int,
        "scores": {
            "rw_score": int,
            "math_score": int,
            "total_score": int,
            "details": {...}
        }
    }
    """
    db = get_firestore_client()

    # Extract required fields
    mock_id = body.get("mock_id")
    rw_answers = body.get("rw_answers", [])
    math_answers = body.get("math_answers", [])
    rw_module2_path = body.get("rw_module2_path", "hard")
    math_module2_path = body.get("math_module2_path", "hard")

    # Validate inputs
    if not mock_id:
        raise HTTPException(status_code=400, detail="mock_id_required")
    
    if not isinstance(rw_answers, list):
        raise HTTPException(status_code=400, detail="rw_answers_must_be_list")
    
    if not isinstance(math_answers, list):
        raise HTTPException(status_code=400, detail="math_answers_must_be_list")
    
    if rw_module2_path not in ["easy", "hard"]:
        raise HTTPException(status_code=400, detail="rw_module2_path_must_be_easy_or_hard")
    
    if math_module2_path not in ["easy", "hard"]:
        raise HTTPException(status_code=400, detail="math_module2_path_must_be_easy_or_hard")

    # Compute SAT scores
    try:
        scores = compute_total_sat_score(
            rw_answers=rw_answers,
            math_answers=math_answers,
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

    # Prepare payload with scores
    payload = {
        "mock_id": mock_id,
        "rw_answers": rw_answers,
        "math_answers": math_answers,
        "rw_module2_path": rw_module2_path,
        "math_module2_path": math_module2_path,
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
