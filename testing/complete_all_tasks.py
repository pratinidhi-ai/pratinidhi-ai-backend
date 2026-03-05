"""
Utility script: mark ALL tasks as completed for a specific user.
Usage: python complete_all_tasks.py
"""

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.firebase_client import get_firestore_client

# ── Config ─────────────────────────────────────────────────────────────────
USER_ID              = "yRCWRMoaelWqsAhWhsxPCRdpGqs2"
MARK_COMPLETED       = True   # set False to mark all tasks as incomplete
LEAVE_ONE_INCOMPLETE = True   # set True to leave exactly one task incomplete
# ───────────────────────────────────────────────────────────────────────────


def main():
    print(f"\n{'='*60}")
    
    print(f"  Complete All Tasks")
    print(f"  User: {USER_ID}")
    print(f"{'='*60}\n")

    db = get_firestore_client()
    tasks_ref = db.collection('users').document(USER_ID).collection('tasks')

    docs = list(tasks_ref.stream())
    if not docs:
        print("  ⚠  No tasks found for this user.")
        return

    # Pick one quiz task to leave incomplete (fallback: highest non-AI task)
    leave_doc_id = None
    if MARK_COMPLETED and LEAVE_ONE_INCOMPLETE:
        enriched = []
        quiz_candidates = []
        non_ai_candidates = []
        for doc in docs:
            data = doc.to_dict()
            task_number = data.get('task_number', 0)
            enriched.append((task_number, doc.id))
            task_type = str(data.get('type_of_task', '')).upper()
            is_quiz = 'QUIZ' in task_type
            is_ai_tutor = 'AI_TUTOR' in task_type
            if is_quiz:
                quiz_candidates.append((task_number, doc.id))
            if not is_ai_tutor:
                non_ai_candidates.append((task_number, doc.id))
        quiz_candidates.sort(key=lambda x: x[0], reverse=True)
        if quiz_candidates:
            leave_doc_id = quiz_candidates[0][1]
        non_ai_candidates.sort(key=lambda x: x[0], reverse=True)
        if not leave_doc_id and non_ai_candidates:
            leave_doc_id = non_ai_candidates[0][1]
        enriched.sort(key=lambda x: x[0], reverse=True)
        if not leave_doc_id and enriched:
            leave_doc_id = enriched[0][1]

    action_label = "completed" if MARK_COMPLETED else "incomplete"
    print(f"  Found {len(docs)} task(s). Marking all as {action_label}...\n")

    completed_at = datetime.now(timezone.utc).isoformat()
    batch = db.batch()

    for doc in docs:
        data = doc.to_dict()
        title = data.get('title', doc.id)
        already = data.get('completed', False)
        if leave_doc_id and doc.id == leave_doc_id:
            status = "→ leaving incomplete"
            print(f"  {status:>14}  |  {title}")
            batch.update(doc.reference, {
                'completed': False,
                'completed_at': completed_at,
            })
            continue

        if MARK_COMPLETED:
            status = "already done" if already else "→ marking done"
        else:
            status = "already reset" if not already else "→ resetting"
        print(f"  {status:>14}  |  {title}")
        batch.update(doc.reference, {
            'completed': MARK_COMPLETED,
            'completed_at': completed_at,
        })

    batch.commit()

    print(f"\n  ✓  {len(docs)} task(s) marked {action_label}.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
