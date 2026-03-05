"""
Manual task assignment script.
Usage: python run_assign_tasks.py [user_id]
"""

import sys
import os
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.firebase_client import get_firestore_client
from database.task_db import TaskDatabase
from database.user_db import UserDatabase
from models.users_schema import User
from helper.task_assignment import assign_weekly_tasks, should_assign_new_tasks

# ── Config ────────────────────────────────────────────────────────────────────
DEFAULT_USER_ID = "yRCWRMoaelWqsAhWhsxPCRdpGqs2"
FORCE_REASSIGN  = True    # Set True to bypass should_assign_new_tasks() check
DELETE_EXISTING = True    # Set True to wipe all existing tasks before assigning
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
    print("[1/5] Fetching user from Firestore...")
    user_data = user_db.get_user_by_id(user_id)
    if not user_data:
        print(f"  ✗  No user found with ID: {user_id}")
        sys.exit(1)

    user = User.from_dict(user_data)
    print(f"  ✓  Found user: {getattr(user, 'name', user_id)}")
    print(f"       predicted_score.total    : {user.predicted_score.total_score}")
    print(f"       completed_quiz_tags count: {len(user.completed_quiz_tags)}")
    print(f"       completed_quiz_tags      : {dict(user.completed_quiz_tags)}")
    print(f"       current_week_start       : {user.current_week_start}")
    print(f"       sat_score_test_given     : {getattr(user, 'sat_score_test_given', 'MISSING')}")
    print(f"       analytics_viewed         : {getattr(user, 'analytics_viewed', 'MISSING')}")

    # 3. Check whether tasks should be assigned
    print("\n[2/5] Checking assignment eligibility...")
    if not FORCE_REASSIGN and not should_assign_new_tasks(user):
        print("  ⚠  Tasks already exist for the current week.")
        print("     Set FORCE_REASSIGN = True in the script to override.")
        sys.exit(0)
    print("  ✓  Eligible — proceeding with assignment.")

    # 4. Delete existing tasks if requested
    if DELETE_EXISTING:
        print("\n[3/5] Deleting existing tasks for user...")
        existing_tasks = task_db.get_user_tasks(user_id)
        deleted = 0
        for existing_task in existing_tasks:
            if task_db.delete_task(user_id, existing_task.id):
                deleted += 1
        print(f"  ✓  Deleted {deleted} existing task(s).")
    else:
        print("\n[3/5] Skipping deletion (DELETE_EXISTING=False).")

    # 5. Generate tasks
    print("\n[4/5] Generating tasks with assign_weekly_tasks()...")
    current_date = datetime.now(timezone.utc)
    tasks = assign_weekly_tasks(user, current_date=current_date)

    if not tasks:
        print("  ⚠  assign_weekly_tasks() returned an empty list — nothing to save.")
        sys.exit(0)

    print(f"  ✓  Generated {len(tasks)} task(s):")
    for i, t in enumerate(tasks, 1):
        task_type = getattr(t.type_of_task, 'value', str(getattr(t, 'type_of_task', 'unknown')))
        title     = getattr(t, 'title', 'untitled')
        due_date  = getattr(t, 'due_date', 'N/A')
        task_id   = getattr(t, 'id', 'N/A')
        quiz_attrs = getattr(t, 'quiz_related_attributes', {})
        extra = f"  area={quiz_attrs.get('area','')} topic={quiz_attrs.get('topic','')} sub={quiz_attrs.get('subcategory','')}" if quiz_attrs else ""
        print(f"       {i:>2}. [{task_type}] {title}{extra}  (due: {due_date})  id: {task_id}")

    # 6. Persist tasks to Firestore
    print("\n[5/5] Saving tasks to Firestore...")
    success = task_db.create_tasks_batch(tasks)
    if not success:
        print("  ✗  Batch write failed — check logs above for details.")
        sys.exit(1)
    print(f"  ✓  {len(tasks)} task(s) written successfully.")

    # 7. Update user metadata
    print("\n[6/6] Updating user metadata...")
    week_start_iso = current_date.replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()
    total_mock = user_data.get('total_mock_tests_assigned', 0)
    updated = user_db.update_user(user_id, {
        'current_week_start': week_start_iso,
        'total_mock_tests_assigned': total_mock,
    })
    if updated:
        print(f"  ✓  current_week_start        = {week_start_iso}")
        print(f"  ✓  total_mock_tests_assigned = {total_mock}")
    else:
        print("  ⚠  User update failed (tasks were still saved).")

    print(f"\n{'='*60}")
    print("  Done! All tasks assigned successfully.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
