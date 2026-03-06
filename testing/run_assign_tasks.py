"""
Manual task assignment script.
Usage: python run_assign_tasks.py [user_id]

Assigns the next task set for a user WITHOUT deleting existing tasks.
Use FORCE_REASSIGN=True to skip the eligibility check.
"""

import sys
import os
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.task_db import TaskDatabase
from database.user_db import UserDatabase
from models.users_schema import User
from helper.task_assignment import assign_weekly_tasks, should_assign_new_tasks

# ── Config ────────────────────────────────────────────────────────────────────
DEFAULT_USER_ID = "yRCWRMoaelWqsAhWhsxPCRdpGqs2"
FORCE_REASSIGN  = True    # Set True to bypass should_assign_new_tasks() check
# ─────────────────────────────────────────────────────────────────────────────


def main():
    user_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USER_ID
    print(f"\n{'='*60}")
    print(f"  Task Assignment Script")
    print(f"  User: {user_id}")
    print(f"{'='*60}\n")

    # 1. Init DB clients
    user_db = UserDatabase()
    task_db = TaskDatabase()

    # 2. Fetch user document
    print("[1/4] Fetching user from Firestore...")
    user_data = user_db.get_user_by_id(user_id)
    if not user_data:
        print(f"  ✗  No user found with ID: {user_id}")
        sys.exit(1)

    user = User.from_dict(user_data)
    print(f"  ✓  Found user: {getattr(user, 'name', user_id)}")
    print(f"       predicted_score.total    : {user.predicted_score.total_score}")
    print(f"       completed_quiz_tags count: {len(user.completed_quiz_tags)}")
    print(f"       current_week_start       : {user.current_week_start}")
    print(f"       sat_score_test_given     : {getattr(user, 'sat_score_test_given', 'MISSING')}")
    print(f"       math_subcategory_index   : {getattr(user, 'math_subcategory_index', 0)}")
    print(f"       english_subcategory_index: {getattr(user, 'english_subcategory_index', 0)}")
    print(f"       completed_task_sets      : {getattr(user, 'completed_task_sets', 0)}")

    # 3. Check whether tasks should be assigned
    print("\n[2/4] Checking assignment eligibility...")
    incomplete = task_db.get_incomplete_tasks(user_id)
    has_incomplete = len(incomplete) > 0
    if has_incomplete:
        print(f"  ⚠  User has {len(incomplete)} incomplete task(s) remaining.")
    if not FORCE_REASSIGN and not should_assign_new_tasks(user, has_incomplete_tasks=has_incomplete):
        print("  ⚠  Eligibility check failed — user still has incomplete tasks.")
        print("     Set FORCE_REASSIGN = True to override.")
        sys.exit(0)
    print("  ✓  Eligible — proceeding with assignment.")

    # 4. Advance rotation indices (same as completion handler)
    user.math_subcategory_index = getattr(user, 'math_subcategory_index', 0) + 1
    user.english_subcategory_index = getattr(user, 'english_subcategory_index', 0) + 1
    user.completed_task_sets = getattr(user, 'completed_task_sets', 0) + 1

    # 5. Generate tasks
    print("\n[3/4] Generating tasks with assign_weekly_tasks()...")
    current_date = datetime.now(timezone.utc)
    tasks = assign_weekly_tasks(user, current_date=current_date)

    if not tasks:
        print("  ⚠  assign_weekly_tasks() returned an empty list — nothing to save.")
        sys.exit(0)

    print(f"  ✓  Generated {len(tasks)} task(s):")
    for i, t in enumerate(tasks, 1):
        task_type  = getattr(t.type_of_task, 'value', str(getattr(t, 'type_of_task', 'unknown')))
        title      = getattr(t, 'title', 'untitled')
        due_date   = getattr(t, 'due_date', 'N/A')
        task_id    = getattr(t, 'id', 'N/A')
        quiz_attrs = getattr(t, 'quiz_related_attributes', {})
        extra = (
            f"  area={quiz_attrs.get('area','')} topic={quiz_attrs.get('topic','')} "
            f"sub={quiz_attrs.get('subcategory','')}"
        ) if quiz_attrs else ""
        print(f"       {i:>2}. [{task_type}] {title}{extra}  (due: {due_date})  id: {task_id}")

    # 6. Persist tasks + update user rotation state
    print("\n[4/4] Saving tasks and updating user metadata...")
    success = task_db.create_tasks_batch(tasks)
    if not success:
        print("  ✗  Batch write failed — check logs above for details.")
        sys.exit(1)
    print(f"  ✓  {len(tasks)} task(s) written successfully.")

    updated = user_db.update_user(user_id, {
        'current_week_start': user.current_week_start.isoformat() if user.current_week_start else None,
        'math_subcategory_index': user.math_subcategory_index,
        'english_subcategory_index': user.english_subcategory_index,
        'completed_task_sets': user.completed_task_sets,
    })
    if updated:
        print(f"  ✓  math_subcategory_index    = {user.math_subcategory_index}")
        print(f"  ✓  english_subcategory_index = {user.english_subcategory_index}")
        print(f"  ✓  completed_task_sets        = {user.completed_task_sets}")
        print(f"  ✓  current_week_start         = {user.current_week_start}")
    else:
        print("  ⚠  User metadata update failed (tasks were still saved).")

    print(f"\n{'='*60}")
    print("  Done! Tasks assigned successfully.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
