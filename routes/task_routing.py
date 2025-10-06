"""
Task Management API Routes
Handles all task-related endpoints for SAT preparation
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from typing import Dict, Any
import traceback

from models.task_schema import Task, TaskType
from models.users_schema import User
from helper.task_service import (
    TaskService,
    fetch_current_task_for_user,
    initialize_user_tasks,
    get_user_dashboard_data
)
from database.firebase_client import get_firestore_client

task_bp = Blueprint('task', __name__)

@task_bp.route('/user/<user_id>/tasks', methods=['GET'])
async def get_user_tasks(user_id: str):
    """Get all current tasks for a user"""
    try:
        firestore_client = get_firestore_client()
        
        # Fetch user from Firestore
        user_doc = firestore_client.collection('users').document(user_id).get()
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
        
        user = User.from_dict(user_doc.to_dict())
        
        # Get task service and fetch tasks
        task_service = TaskService(firestore_client)
        tasks = await task_service.fetch_current_tasks(user)
        
        return jsonify({
            'success': True,
            'tasks': [task.to_dict() for task in tasks],
            'count': len(tasks)
        }), 200
        
    except Exception as e:
        print(f"Error getting user tasks: {e}")
        print(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@task_bp.route('/user/<user_id>/tasks/current', methods=['GET'])
async def get_current_task(user_id: str):
    """Get the current (next) task for a user"""
    try:
        firestore_client = get_firestore_client()
        
        # Fetch user from Firestore
        user_doc = firestore_client.collection('users').document(user_id).get()
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
        
        user = User.from_dict(user_doc.to_dict())
        
        # Fetch current task
        current_task = await fetch_current_task_for_user(user, firestore_client)
        
        if not current_task:
            return jsonify({
                'success': True,
                'current_task': None,
                'message': 'No tasks available'
            }), 200
        
        return jsonify({
            'success': True,
            'current_task': current_task.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Error getting current task: {e}")
        print(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@task_bp.route('/user/<user_id>/tasks/<task_id>/complete', methods=['POST'])
async def mark_task_completed(user_id: str, task_id: str):
    """Mark a task as completed"""
    try:
        firestore_client = get_firestore_client()
        task_service = TaskService(firestore_client)
        
        # Get additional data from request
        data = request.get_json() or {}
        score = data.get('score')
        attempt_data = data.get('attempt_data', {})
        
        # Update task attempt info if provided
        if score is not None or attempt_data:
            await task_service.update_task_attempt(user_id, task_id, score=score, **attempt_data)
        
        # Mark task as completed
        success = await task_service.mark_task_completed(user_id, task_id)
        
        if success:
            # Check if this was an AI tutorial task and mark chapter as completed
            task_ref = (firestore_client.collection('users')
                       .document(user_id)
                       .collection('tasks')
                       .document(task_id))
            
            task_doc = task_ref.get()
            if task_doc.exists:
                task_data = task_doc.to_dict()
                task = Task.from_dict(task_data)
                
                if task.type_of_task == TaskType.AI_TUTORIAL:
                    chapter_id = task.ai_tutorial_related_attributes.get('chapter_id')
                    if chapter_id:
                        # Fetch user and mark chapter completed
                        user_doc = firestore_client.collection('users').document(user_id).get()
                        if user_doc.exists:
                            user = User.from_dict(user_doc.to_dict())
                            await task_service.mark_chapter_completed(user, chapter_id)
            
            return jsonify({
                'success': True,
                'message': 'Task marked as completed'
            }), 200
        else:
            return jsonify({'error': 'Failed to mark task as completed'}), 500
            
    except Exception as e:
        print(f"Error marking task completed: {e}")
        print(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@task_bp.route('/user/<user_id>/tasks/<task_id>/attempt', methods=['POST'])
async def update_task_attempt(user_id: str, task_id: str):
    """Update task attempt information"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        firestore_client = get_firestore_client()
        task_service = TaskService(firestore_client)
        
        score = data.get('score')
        attempt_data = {k: v for k, v in data.items() if k != 'score'}
        
        success = await task_service.update_task_attempt(user_id, task_id, score=score, **attempt_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Task attempt updated'
            }), 200
        else:
            return jsonify({'error': 'Failed to update task attempt'}), 500
            
    except Exception as e:
        print(f"Error updating task attempt: {e}")
        print(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@task_bp.route('/user/<user_id>/dashboard', methods=['GET'])
async def get_user_dashboard(user_id: str):
    """Get comprehensive dashboard data for a user"""
    try:
        firestore_client = get_firestore_client()
        
        # Fetch user from Firestore
        user_doc = firestore_client.collection('users').document(user_id).get()
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
        
        user = User.from_dict(user_doc.to_dict())
        
        # Get dashboard data
        dashboard_data = await get_user_dashboard_data(user, firestore_client)
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        }), 200
        
    except Exception as e:
        print(f"Error getting user dashboard: {e}")
        print(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@task_bp.route('/user/<user_id>/tasks/initialize', methods=['POST'])
async def initialize_tasks(user_id: str):
    """Initialize tasks for a user (useful for new users or manual initialization)"""
    try:
        firestore_client = get_firestore_client()
        
        # Fetch user from Firestore
        user_doc = firestore_client.collection('users').document(user_id).get()
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
        
        user = User.from_dict(user_doc.to_dict())
        
        # Initialize tasks
        tasks = await initialize_user_tasks(user, firestore_client)
        
        return jsonify({
            'success': True,
            'message': f'Initialized {len(tasks)} tasks for user',
            'tasks': [task.to_dict() for task in tasks]
        }), 200
        
    except Exception as e:
        print(f"Error initializing tasks: {e}")
        print(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@task_bp.route('/user/<user_id>/chapters/<chapter_id>/complete', methods=['POST'])
async def mark_chapter_completed(user_id: str, chapter_id: str):
    """Mark a chapter as completed for a user"""
    try:
        firestore_client = get_firestore_client()
        task_service = TaskService(firestore_client)
        
        # Fetch user from Firestore
        user_doc = firestore_client.collection('users').document(user_id).get()
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
        
        user = User.from_dict(user_doc.to_dict())
        
        # Mark chapter as completed
        success = await task_service.mark_chapter_completed(user, chapter_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Chapter {chapter_id} marked as completed'
            }), 200
        else:
            return jsonify({'error': 'Failed to mark chapter as completed'}), 500
            
    except Exception as e:
        print(f"Error marking chapter completed: {e}")
        print(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@task_bp.route('/user/<user_id>/progress', methods=['GET'])
async def get_user_progress(user_id: str):
    """Get user's overall progress including completed chapters and task analytics"""
    try:
        firestore_client = get_firestore_client()
        
        # Fetch user from Firestore
        user_doc = firestore_client.collection('users').document(user_id).get()
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
        
        user = User.from_dict(user_doc.to_dict())
        
        # Get dashboard data which includes analytics
        dashboard_data = await get_user_dashboard_data(user, firestore_client)
        
        # Add chapter progress
        total_chapters = 7  # Based on lecture_notes.json
        completed_chapters = len(user.completed_chapters)
        chapter_progress = (completed_chapters / total_chapters) * 100 if total_chapters > 0 else 0
        
        return jsonify({
            'success': True,
            'progress': {
                'chapters': {
                    'completed': completed_chapters,
                    'total': total_chapters,
                    'percentage': round(chapter_progress, 2),
                    'completed_list': user.completed_chapters,
                    'next_chapter': user.get_next_chapter()
                },
                'tasks': dashboard_data['analytics'],
                'current_week_start': user.current_week_start.isoformat() if user.current_week_start else None
            }
        }), 200
        
    except Exception as e:
        print(f"Error getting user progress: {e}")
        print(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

# Helper endpoint for testing/admin purposes
@task_bp.route('/admin/tasks/test-assignment', methods=['POST'])
async def test_task_assignment():
    """Test endpoint to see what tasks would be assigned (admin/testing only)"""
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'error': 'user_id required'}), 400
        
        # Create a mock user for testing
        user = User(
            id=data['user_id'],
            email='test@example.com',
            name='Test User',
            completed_chapters=data.get('completed_chapters', [])
        )
        
        from helper.task_assignment import assign_weekly_tasks
        
        # Get what tasks would be assigned
        mock_tasks = assign_weekly_tasks(user)
        
        return jsonify({
            'success': True,
            'message': 'Mock task assignment (not saved)',
            'tasks': [task.to_dict() for task in mock_tasks],
            'count': len(mock_tasks)
        }), 200
        
    except Exception as e:
        print(f"Error in test task assignment: {e}")
        print(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500