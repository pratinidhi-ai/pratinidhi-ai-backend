"""
Task Management API Routes
Handles all task-related endpoints for SAT preparation
"""

from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from database.task_db import get_task_db
from database.user_db import get_user_db
from helper.task_assignment import assign_weekly_tasks, should_assign_new_tasks
import traceback
import logging
from dotenv import load_dotenv
import os

from models.task_schema import Task, TaskType
from models.users_schema import User
from helper.middleware import authenticate_request
from helper.task_service import (
    TaskService,
    fetch_current_task_for_user,
    initialize_user_tasks,
    get_user_dashboard_data
)
from database.firebase_client import get_firestore_client

load_dotenv()
logger = logging.getLogger(__name__)

task_router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# Pydantic models for request validation
class CompleteTaskRequest(BaseModel):
    score: Optional[float] = None
    attempt_data: Dict[str, Any] = Field(default_factory=dict)


class UpdateTaskAttemptRequest(BaseModel):
    score: Optional[float] = None
    # Additional fields will be captured in the endpoint


@task_router.post('/admin/assign-weekly', status_code=status.HTTP_200_OK)
def assign_all_weekly_tasks(x_admin_api_key: str = Header(None)):
    """
    ADMIN Endpoint: Triggers weekly task assignment for all active users
    Requires a valid X-Admin-API-Key header.
    """
    expected_key = os.environ.get('ADMIN_API_KEY')

    if not expected_key:
        logger.info("ADMIN_API_KEY environment variable is not set!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'error': 'Configuration error'}
        )

    if not x_admin_api_key or x_admin_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'error': 'Unauthorized'}
        )

    logger.info("Admin: Starting weekly task assignment process...")
    processed_count = 0
    skipped_count = 0
    error_count = 0
    errors_list = []

    try:
        user_db = get_user_db()
        task_db = get_task_db()
        task_service = TaskService()

        all_users_data = user_db.get_users(active_only=True)
        logger.info(f"Admin: Found {len(all_users_data)} active users.")

        for user_data in all_users_data:
            user_id = user_data.get('id')
            if not user_id:
                logger.info("Warning: Found user data without an ID, skipping.")
                skipped_count += 1
                continue

            try:
                user = User.from_dict(user_data)
                # Check whether user has any incomplete tasks
                incomplete = task_db.get_incomplete_tasks(user.id)

                if should_assign_new_tasks(user, has_incomplete_tasks=len(incomplete) > 0):
                    logger.info(f"Admin: Assigning tasks for user {user.id}...")
                    new_tasks = assign_weekly_tasks(user)

                    if new_tasks:
                        save_success = task_db.create_tasks_batch(new_tasks)
                        if not save_success:
                            raise Exception(f"Failed to save tasks batch for user {user.id}")

                        update_success = user_db.update_user(user.id, {
                            'current_week_start': user.current_week_start.isoformat() if user.current_week_start else None,
                            'math_subcategory_index': getattr(user, 'math_subcategory_index', 0),
                            'english_subcategory_index': getattr(user, 'english_subcategory_index', 0),
                            'completed_task_sets': getattr(user, 'completed_task_sets', 0),
                        })
                        if not update_success:
                            raise Exception(f"Failed to update task state for user {user.id}")

                        logger.info(f"Admin: Successfully assigned {len(new_tasks)} tasks to user {user.id}.")
                        processed_count += 1
                    else:
                        logger.info(f"Admin: No new tasks generated for user {user.id}.")
                        user_db.update_user(user.id, {
                            'current_week_start': user.current_week_start.isoformat() if user.current_week_start else None
                        })
                        skipped_count += 1
                else:
                    skipped_count += 1

            except Exception as user_error:
                logger.info(f"Admin: Error processing user {user_id}: {str(user_error)}")
                error_count += 1
                errors_list.append({'user_id': user_id, 'error': str(user_error)})

        summary_message = f"Weekly task assignment finished. Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}."
        logger.info(f"Admin: {summary_message}")
        return {
            'success': True,
            'message': summary_message,
            'processed_users': processed_count,
            'skipped_users': skipped_count,
            'users_with_errors': error_count,
            'error_details': errors_list
        }

    except Exception as e:
        logger.error(f"Admin: Critical error during weekly task assignment: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'error': 'Internal server error during task assignment'}
        )


@task_router.get('/user/{user_id}/tasks', status_code=status.HTTP_200_OK)
def get_user_tasks(
    user_id: str,
    include_completed: bool = False,
    user: dict = Depends(authenticate_request)
):
    """
    Get tasks for a user.
    - include_completed=false (default): only incomplete tasks
    - include_completed=true: all tasks in the current set (completed + incomplete)
    """
    try:
        firestore_client = get_firestore_client()
        
        user_doc = firestore_client.collection('users').document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={'error': 'User not found'}
            )
        
        user_obj = User.from_dict(user_doc.to_dict())
        
        task_service = TaskService(firestore_client)
        if include_completed:
            tasks = task_service.fetch_all_current_tasks(user_obj)
        else:
            tasks = task_service.fetch_assigned_tasks_only(user_obj)
        
        return {
            'success': True,
            'tasks': [task.to_dict() for task in tasks],
            'count': len(tasks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'error': 'Internal server error'}
        )


@task_router.get('/user/{user_id}/tasks/current', status_code=status.HTTP_200_OK)
def get_current_task(user_id: str, user: dict = Depends(authenticate_request)):
    """Get the current (next) task for a user"""
    try:
        firestore_client = get_firestore_client()
        
        user_doc = firestore_client.collection('users').document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={'error': 'User not found'}
            )
        
        user_obj = User.from_dict(user_doc.to_dict())
        current_task = fetch_current_task_for_user(user_obj, firestore_client)
        
        if not current_task:
            return {
                'success': True,
                'current_task': None,
                'message': 'No tasks available'
            }
        
        return {
            'success': True,
            'current_task': current_task.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.info(f"Error getting current task: {e}")
        logger.info(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'error': 'Internal server error'}
        )


@task_router.post('/user/{user_id}/tasks/{task_id}/complete', status_code=status.HTTP_200_OK)
def mark_task_completed(
    user_id: str,
    task_id: str,
    request_data: CompleteTaskRequest,
    user: dict = Depends(authenticate_request)
):
    """
    Mark a task as completed based on task-type-specific criteria:

    QUIZ (topic_category in quiz_related_attributes):
        unexplored : score >= 40% of num_questions  (e.g. 4/10)
        weak       : score >= 60% of num_questions  (e.g. 6/10)
        strength   : score >= 80% of num_questions  (e.g. 8/10)

    AI_TUTORIAL   : always completed when this endpoint is called (session done).
    SAT_PREDICTOR : completed only when a sat_predictor_performance document exists for the user.
    MOCK_TEST     : completed only when a mock_attempt exists for the task's mock_id.
    """
    try:
        firestore_client = get_firestore_client()
        task_service = TaskService(firestore_client)

        # ── Fetch the task ─────────────────────────────────────────────────
        task_ref = (
            firestore_client.collection('users')
            .document(user_id)
            .collection('tasks')
            .document(task_id)
        )
        task_doc = task_ref.get()
        if not task_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={'error': 'Task not found'}
            )

        task_data = task_doc.to_dict()
        task_obj = Task.from_dict(task_data)

        score = request_data.score
        attempt_data = request_data.attempt_data

        # ── Record the attempt ─────────────────────────────────────────────
        if score is not None or attempt_data:
            task_service.update_task_attempt(user_id, task_id, score=score, **attempt_data)

        # ── Evaluate completion criteria ───────────────────────────────────
        can_complete = False
        failure_reason = None

        if task_obj.type_of_task == TaskType.QUIZ:
            quiz_attrs = task_obj.quiz_related_attributes
            area = quiz_attrs.get('area') or quiz_attrs.get('topic_category', 'unexplored')
            num_questions = quiz_attrs.get('num_questions', 10)

            THRESHOLDS = {
                'strength':  0.80,
                'weak':      0.60,
                'weakness':  0.60,
                'unexplored': 0.40,
            }
            threshold_pct = THRESHOLDS.get(area, 0.40)
            required_score = threshold_pct * num_questions

            if score is None:
                failure_reason = 'Score is required to complete a quiz task.'
            elif score >= required_score:
                can_complete = True
            else:
                failure_reason = (
                    f"Score {score}/{num_questions} does not meet the "
                    f"passing threshold for a '{area}' task "
                    f"({int(required_score)}/{num_questions} required)."
                )

        elif task_obj.type_of_task == TaskType.AI_TUTORIAL:
            # Completed when user has a session with completion_percentage >= 80% for this chapter
            MIN_COMPLETION_PERCENTAGE = 80.0
            chapter_id = task_obj.ai_tutorial_related_attributes.get('chapter_id')
            if not chapter_id:
                can_complete = True  # No chapter linked — allow completion
            else:
                # Check if any session with sufficient completion exists for this chapter
                sessions_ref = (
                    firestore_client.collection('session_summary')
                    .document(user_id)
                    .collection('sessions')
                    .where('lecture_chapter', '==', chapter_id)
                    .where('is_active', '==', False)
                    .stream()
                )
                qualifying_sessions = [
                    s for s in sessions_ref
                    if (s.to_dict() or {}).get('completion_percentage', 0) >= MIN_COMPLETION_PERCENTAGE
                ]
                if qualifying_sessions:
                    can_complete = True
                else:
                    failure_reason = (
                        f"Please complete at least {int(MIN_COMPLETION_PERCENTAGE)}% of the AI Tutor "
                        f"session for this chapter before marking this task as done."
                    )

        elif task_obj.type_of_task == TaskType.SAT_PREDICTOR:
            # Completed only when the user has actually submitted the predictor test
            # (at least one document exists in sat_predictor_performance subcollection)
            perf_docs = (
                firestore_client.collection('users')
                .document(user_id)
                .collection('sat_predictor_performance')
                .limit(1)
                .stream()
            )
            if any(True for _ in perf_docs):
                can_complete = True
            else:
                failure_reason = (
                    'Please complete and submit the SAT Score Predictor test '
                    'before marking this task as done.'
                )

        elif task_obj.type_of_task == TaskType.MOCK_TEST:
            # Completed when a mock_attempt document exists for this mock_id
            mock_id = task_obj.quiz_related_attributes.get('mock_id')
            if not mock_id:
                failure_reason = 'Mock test task has no associated mock_id.'
            else:
                attempt_doc = (
                    firestore_client.collection('users')
                    .document(user_id)
                    .collection('mock_attempts')
                    .document(mock_id)
                    .get()
                )
                if attempt_doc.exists:
                    can_complete = True
                else:
                    failure_reason = (
                        f"No completed attempt found for mock test '{mock_id}'. "
                        "Please submit the mock test before marking this task complete."
                    )
        else:
            # Unknown task type — allow completion
            can_complete = True

        if not can_complete:
            return {
                'success': False,
                'completed': False,
                'message': failure_reason or 'Completion criteria not met.',
            }

        # ── Mark completed ─────────────────────────────────────────────────
        success = task_service.mark_task_completed(user_id, task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={'error': 'Failed to mark task as completed'}
            )

        # ── Task-type side-effects ─────────────────────────────────────────────
        if task_obj.type_of_task == TaskType.AI_TUTORIAL:
            chapter_id = task_obj.ai_tutorial_related_attributes.get('chapter_id')
            if chapter_id:
                user_doc = firestore_client.collection('users').document(user_id).get()
                if user_doc.exists:
                    user_obj_data = User.from_dict(user_doc.to_dict())
                    task_service.mark_chapter_completed(user_obj_data, chapter_id)

        elif task_obj.type_of_task == TaskType.SAT_PREDICTOR:
            # Flag that the user has now taken the SAT Predictor
            firestore_client.collection('users').document(user_id).update(
                {'sat_score_test_given': True}
            )
            # Auto-generate the first full task set (Stage 1 → Stage 2 transition)
            try:
                user_doc = firestore_client.collection('users').document(user_id).get()
                if user_doc.exists:
                    updated_user = User.from_dict(user_doc.to_dict())
                    new_tasks = task_service._assign_new_weekly_tasks(updated_user)
                    logger.info(f"Auto-assigned {len(new_tasks)} tasks after SAT Predictor completion for user {user_id}")
            except Exception as auto_err:
                logger.error(f"Failed to auto-assign tasks after SAT Predictor for user {user_id}: {auto_err}")

        # ── If all tasks in the current set are done, rotate and assign next set ──
        # (SAT_PREDICTOR handles its own first-set assignment above — skip here)
        next_tasks_count = 0
        if task_obj.type_of_task != TaskType.SAT_PREDICTOR:
            try:
                task_db_instance = get_task_db()
                remaining = task_db_instance.get_incomplete_tasks(user_id)
                if len(remaining) == 0:
                    # Every task completed — advance rotation indices and create next set
                    user_doc = firestore_client.collection('users').document(user_id).get()
                    if user_doc.exists:
                        next_user = User.from_dict(user_doc.to_dict())
                        next_user.math_subcategory_index = getattr(next_user, 'math_subcategory_index', 0) + 1
                        next_user.english_subcategory_index = getattr(next_user, 'english_subcategory_index', 0) + 1
                        next_user.completed_task_sets = getattr(next_user, 'completed_task_sets', 0) + 1
                        # Persist indices before assignment so assign_weekly_tasks reads the new values
                        firestore_client.collection('users').document(user_id).update({
                            'math_subcategory_index': next_user.math_subcategory_index,
                            'english_subcategory_index': next_user.english_subcategory_index,
                            'completed_task_sets': next_user.completed_task_sets,
                        })
                        new_tasks = task_service._assign_new_weekly_tasks(next_user)
                        next_tasks_count = len(new_tasks)
                        logger.info(
                            f"All tasks done for user {user_id} — assigned set "
                            f"#{next_user.completed_task_sets} ({next_tasks_count} tasks). "
                            f"Math idx={next_user.math_subcategory_index}, "
                            f"English idx={next_user.english_subcategory_index}"
                        )
            except Exception as set_err:
                logger.error(f"Failed to auto-assign next task set for user {user_id}: {set_err}")

        return {
            'success': True,
            'completed': True,
            'message': 'Task marked as completed',
            'next_tasks_assigned': next_tasks_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.info(f"Error marking task completed: {e}")
        logger.info(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'error': 'Internal server error'}
        )


@task_router.post('/user/{user_id}/tasks/{task_id}/attempt', status_code=status.HTTP_200_OK)
def update_task_attempt(
    user_id: str,
    task_id: str,
    request_data: Dict[str, Any],
    user: dict = Depends(authenticate_request)
):
    """Update task attempt information"""
    try:
        firestore_client = get_firestore_client()
        task_service = TaskService(firestore_client)
        
        score = request_data.get('score')
        attempt_data = {k: v for k, v in request_data.items() if k != 'score'}

        if score is not None and not isinstance(score, (int, float)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={'error': 'Invalid data type', 'message': 'Field "score" must be a number.'}
            )
        
        success = task_service.update_task_attempt(user_id, task_id, score=score, **attempt_data)
        
        if success:
            return {
                'success': True,
                'message': 'Task attempt updated'
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={'error': 'Failed to update task attempt'}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.info(f"Error updating task attempt: {e}")
        logger.info(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'error': 'Internal server error'}
        )


@task_router.get('/user/{user_id}/dashboard', status_code=status.HTTP_200_OK)
def get_user_dashboard(user_id: str, user: dict = Depends(authenticate_request)):
    """Get comprehensive dashboard data for a user"""
    try:
        firestore_client = get_firestore_client()
        
        user_doc = firestore_client.collection('users').document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={'error': 'User not found'}
            )
        
        user_obj = User.from_dict(user_doc.to_dict())
        dashboard_data = get_user_dashboard_data(user_obj, firestore_client)
        
        return {
            'success': True,
            'dashboard': dashboard_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.info(f"Error getting user dashboard: {e}")
        logger.info(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'error': 'Internal server error'}
        )


@task_router.post('/user/{user_id}/tasks/initialize', status_code=status.HTTP_200_OK)
def initialize_tasks(user_id: str, user: dict = Depends(authenticate_request)):
    """Initialize tasks for a user"""
    try:
        firestore_client = get_firestore_client()
        
        user_doc = firestore_client.collection('users').document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={'error': 'User not found'}
            )
        
        user_obj = User.from_dict(user_doc.to_dict())
        tasks = initialize_user_tasks(user_obj, firestore_client)
        
        return {
            'success': True,
            'message': f'Initialized {len(tasks)} tasks for user',
            'tasks': [task.to_dict() for task in tasks]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.info(f"Error initializing tasks: {e}")
        logger.info(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'error': 'Internal server error'}
        )


@task_router.post('/user/{user_id}/chapters/{chapter_id}/complete', status_code=status.HTTP_200_OK)
def mark_chapter_completed(user_id: str, chapter_id: str, user: dict = Depends(authenticate_request)):
    """Mark a chapter as completed for a user"""
    try:
        firestore_client = get_firestore_client()
        task_service = TaskService(firestore_client)
        
        user_doc = firestore_client.collection('users').document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={'error': 'User not found'}
            )
        
        user_obj = User.from_dict(user_doc.to_dict())
        success = task_service.mark_chapter_completed(user_obj, chapter_id)
        
        if success:
            return {
                'success': True,
                'message': f'Chapter {chapter_id} marked as completed'
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={'error': 'Failed to mark chapter as completed'}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.info(f"Error marking chapter completed: {e}")
        logger.info(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'error': 'Internal server error'}
        )


@task_router.get('/user/{user_id}/progress', status_code=status.HTTP_200_OK)
def get_user_progress(user_id: str, user: dict = Depends(authenticate_request)):
    """Get user's overall progress"""
    try:
        firestore_client = get_firestore_client()
        
        user_doc = firestore_client.collection('users').document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={'error': 'User not found'}
            )
        
        user_obj = User.from_dict(user_doc.to_dict())
        dashboard_data = get_user_dashboard_data(user_obj, firestore_client)
        
        total_chapters = 7
        completed_chapters = len(user_obj.completed_chapters)
        chapter_progress = (completed_chapters / total_chapters) * 100 if total_chapters > 0 else 0
        
        return {
            'success': True,
            'progress': {
                'chapters': {
                    'completed': completed_chapters,
                    'total': total_chapters,
                    'percentage': round(chapter_progress, 2),
                    'completed_list': user_obj.completed_chapters,
                    'next_chapter': user_obj.get_next_chapter()
                },
                'tasks': dashboard_data['analytics'],
                'current_week_start': user_obj.current_week_start.isoformat() if user_obj.current_week_start else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.info(f"Error getting user progress: {e}")
        logger.info(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'error': 'Internal server error'}
        )


@task_router.post('/admin/tasks/test-assignment', status_code=status.HTTP_200_OK)
def test_task_assignment(request_data: Dict[str, Any]):
    """Test endpoint to see what tasks would be assigned"""
    try:
        if 'user_id' not in request_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={'error': 'user_id required'}
            )
        
        user_obj = User(
            id=request_data['user_id'],
            email='test@example.com',
            name='Test User',
            completed_chapters=request_data.get('completed_chapters', [])
        )
        
        from helper.task_assignment import assign_weekly_tasks
        
        mock_tasks = assign_weekly_tasks(user_obj)
        
        return {
            'success': True,
            'message': 'Mock task assignment (not saved)',
            'tasks': [task.to_dict() for task in mock_tasks],
            'count': len(mock_tasks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.info(f"Error in test task assignment: {e}")
        logger.info(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'error': 'Internal server error'}
        )
