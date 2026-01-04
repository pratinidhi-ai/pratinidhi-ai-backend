# mockTestSection/mock_store.py
from typing import Dict, List, Optional
from datetime import datetime
from database.firebase_client import get_firestore_client

MODULE_KEYS = {
    ("rw", "module1_balanced"): "rw_m1",
    ("rw", "module2_easy"): "rw_m2_easy",
    ("rw", "module2_hard"): "rw_m2_hard",
    ("math", "module1_balanced"): "math_m1",
    ("math", "module2_easy"): "math_m2_easy",
    ("math", "module2_hard"): "math_m2_hard",
}


def create_mock_parent(
    mock_id: str,
    exam: str = "SAT",
    name: Optional[str] = None,
) -> str:
    """
    Create the parent document for a mock.
    Uses mock_id as the document name (no random names).
    Includes id, exam, name, and created_at fields for efficient querying.
    """
    db = get_firestore_client()

    doc = {
        "id": mock_id,
        "exam": exam,
        "name": name or mock_id,  # Use provided name or default to mock_id
        "created_at": datetime.utcnow(),
    }

    # 🔹 mock_id = Firestore document name
    ref = db.collection("mock_tests").document(mock_id)
    ref.set(doc)
    return ref.id


def save_module_questions(mock_id: str, section: str, module_key: str, questions: List[Dict]) -> int:
    """
    Write full question docs into the parent mock's subcollection.
    Each question is stored with its sequence number as the document ID.
    question_no field ensures deterministic ordering.
    
    CRITICAL DESIGN:
    - Document ID = str(idx) where idx is 1, 2, 3...
    - question_no = idx (same number as int)
    - This ensures doc.id matches question_no for consistent identification
    - Frontend should use question_no for display and doc.id for answer matching
    """
    db = get_firestore_client()
    subcoll = MODULE_KEYS[(section, module_key)]
    parent = db.collection("mock_tests").document(mock_id)
    batch = db.batch()

    count = 0
    for idx, q in enumerate(questions, start=1):
        # Use sequence number as document ID (1, 2, 3, ...)
        ref = parent.collection(subcoll).document(str(idx))
        data = dict(q)
        
        # ✅ CRITICAL FIX: Remove any 'id' field from question bank to avoid confusion
        # The 'id' field will be set by the API based on doc.id (which is the sequence number)
        if 'id' in data:
            data.pop('id')
        
        data["__section"] = section
        data["__module_key"] = module_key
        data["question_no"] = idx  # Source of truth for question numbering
        batch.set(ref, data)
        count += 1
        if count % 400 == 0:
            batch.commit()
            batch = db.batch()

    if count % 400 != 0:
        batch.commit()

    return count
