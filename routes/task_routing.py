"""
Task Management API Routes
Handles all task-related endpoints for SAT preparation
"""

from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from database.user_db import get_user_db
from database.task_db import get_task_db
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

task_router = APIRouter(prefix="/api/task", tags=["tasks"])


# Pydantic models for request validation
class CompleteTaskRequest(BaseModel):
    score: Optional[float] = None
    attempt_data: Dict[str, Any] = Field(default_factory=dict)


class UpdateTaskAttemptRequest(BaseModel):
    score: Optional[float] = None
    # Additional fields will be captured in the endpoint


@task_router.post('/admin/assign-weekly', status_code=status.HTTP_200_OK)
async def assign_all_weekly_tasks(x_admin_api_key: str = Header(None)):
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

                if should_assign_new_tasks(user):
                    logger.info(f"Admin: Assigning tasks for user {user.id}...")
                    new_tasks = assign_weekly_tasks(user)

                    if new_tasks:
                        save_success = task_db.create_tasks_batch(new_tasks)
                        if not save_success:
                            raise Exception(f"Failed to save tasks batch for user {user.id}")

                        update_success = user_db.update_user(user.id, {
                            'current_week_start': user.current_week_start.isoformat() if user.current_week_start else None
                        })
                        if not update_success:
                            raise Exception(f"Failed to update current_week_start for user {user.id}")

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
async def get_user_tasks(user_id: str, user: dict = Depends(authenticate_request)):
    """Get all current tasks for a user"""
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
        tasks = task_service.fetch_current_tasks(user_obj)
        
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
async def get_current_task(user_id: str, user: dict = Depends(authenticate_request)):
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
async def mark_task_completed(
    user_id: str,
    task_id: str,
    request_data: CompleteTaskRequest,
    user: dict = Depends(authenticate_request)
):
    """Mark a task as completed"""
    try:
        firestore_client = get_firestore_client()
        task_service = TaskService(firestore_client)
        
        score = request_data.score
        attempt_data = request_data.attempt_data
        
        if score is not None or attempt_data:
            task_service.update_task_attempt(user_id, task_id, score=score, **attempt_data)
        
        success = task_service.mark_task_completed(user_id, task_id)
        
        if success:
            task_ref = (firestore_client.collection('users')
                       .document(user_id)
                       .collection('tasks')
                       .document(task_id))
            
            task_doc = task_ref.get()
            if task_doc.exists:
                task_data = task_doc.to_dict()
                task_obj = Task.from_dict(task_data)
                
                if task_obj.type_of_task == TaskType.AI_TUTORIAL:
                    chapter_id = task_obj.ai_tutorial_related_attributes.get('chapter_id')
                    if chapter_id:
                        user_doc = firestore_client.collection('users').document(user_id).get()
                        if user_doc.exists:
                            user_obj = User.from_dict(user_doc.to_dict())
                            task_service.mark_chapter_completed(user_obj, chapter_id)
            
            return {
                'success': True,
                'message': 'Task marked as completed'
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={'error': 'Failed to mark task as completed'}
            )
            
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
async def update_task_attempt(
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
async def get_user_dashboard(user_id: str, user: dict = Depends(authenticate_request)):
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
async def initialize_tasks(user_id: str, user: dict = Depends(authenticate_request)):
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
async def mark_chapter_completed(user_id: str, chapter_id: str, user: dict = Depends(authenticate_request)):
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
async def get_user_progress(user_id: str, user: dict = Depends(authenticate_request)):
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
async def test_task_assignment(request_data: Dict[str, Any]):
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