from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from models.task_schema import Task
from models.users_schema import User
from helper.task_assignment import (
    get_or_assign_user_tasks,
    should_assign_new_tasks,
    assign_weekly_tasks,
    calculate_task_priority,
    get_current_week_tasks_query_filter,
    get_user_task_analytics
)

class TaskService:
    """Service class to handle all task-related operations"""
    
    def __init__(self, firestore_client=None):
        # Keep firestore_client for backward compatibility, but use database classes
        self.firestore_client = firestore_client
        from database.task_db import get_task_db
        from database.user_db import get_user_db
        self.task_db = get_task_db()
        self.user_db = get_user_db()
    
    async def fetch_current_tasks(self, user: User) -> List[Task]:
        """
        Fetch currently assigned tasks for a user.
        If no tasks are assigned for the current week, assign new tasks.
        
        Args:
            user: User object
            
        Returns:
            List of tasks for the current week, sorted by priority
        """
        try:
            # Check if we should assign new tasks
            if should_assign_new_tasks(user):
                return await self._assign_new_weekly_tasks(user)
            
            # Fetch existing tasks for current week
            existing_tasks = await self._get_existing_weekly_tasks(user)
            
            if not existing_tasks:
                # No tasks found, assign new ones
                return await self._assign_new_weekly_tasks(user)
            
            # Sort tasks by priority
            existing_tasks.sort(key=lambda t: calculate_task_priority(t))
            return existing_tasks
            
        except Exception as e:
            print(f"Error fetching current tasks for user {user.id}: {e}")
            return []
    
    async def _assign_new_weekly_tasks(self, user: User) -> List[Task]:
        """Assign new tasks for the current week"""
        try:
            new_tasks = assign_weekly_tasks(user)
            
            # Save tasks to Firestore
            if self.firestore_client and new_tasks:
                await self._save_tasks_to_firestore(new_tasks)
                # Update user's current_week_start in Firestore
                await self._update_user_week_start(user)
            
            return sorted(new_tasks, key=lambda t: calculate_task_priority(t))
            
        except Exception as e:
            print(f"Error assigning new weekly tasks for user {user.id}: {e}")
            return []
    
    async def _get_existing_weekly_tasks(self, user: User) -> List[Task]:
        """Fetch existing tasks for the current week"""
        try:
            # Use task database to get tasks by week
            from helper.task_assignment import get_week_start
            week_start = get_week_start()
            return self.task_db.get_tasks_by_week(user.id, week_start)
            
        except Exception as e:
            print(f"Error fetching existing weekly tasks for user {user.id}: {e}")
            return []
    
    async def _save_tasks_to_firestore(self, tasks: List[Task]) -> bool:
        """Save tasks using task database"""
        try:
            return self.task_db.create_tasks_batch(tasks)
            
        except Exception as e:
            print(f"Error saving tasks: {e}")
            return False
    
    async def _update_user_week_start(self, user: User) -> bool:
        """Update user's current_week_start using user database"""
        try:
            return self.user_db.update_user(user.id, {
                'current_week_start': user.current_week_start.isoformat() if user.current_week_start else None
            })
            
        except Exception as e:
            print(f"Error updating user week start: {e}")
            return False
    
    async def mark_task_completed(self, user_id: str, task_id: str) -> bool:
        """Mark a specific task as completed"""
        try:
            return self.task_db.mark_task_completed(user_id, task_id)
            
        except Exception as e:
            print(f"Error marking task {task_id} as completed: {e}")
            return False
    
    async def update_task_attempt(self, user_id: str, task_id: str, score: Optional[float] = None, **attempt_data) -> bool:
        """Update task with attempt information"""
        try:
            return self.task_db.update_task_attempt(user_id, task_id, score=score, **attempt_data)
            
        except Exception as e:
            print(f"Error updating task attempt for {task_id}: {e}")
            return False
    
    async def mark_chapter_completed(self, user: User, chapter_id: str) -> bool:
        """Mark a chapter as completed for the user"""
        try:
            # Update user object
            user.mark_chapter_completed(chapter_id)
            
            # Update in database
            return self.user_db.mark_chapter_completed(user.id, chapter_id)
            
        except Exception as e:
            print(f"Error marking chapter {chapter_id} as completed: {e}")
            return False
    
    async def get_user_task_summary(self, user: User) -> Dict[str, Any]:
        """Get comprehensive task summary for a user"""
        try:
            tasks = await self.fetch_current_tasks(user)
            analytics = get_user_task_analytics(tasks)
            
            # Get next task
            next_task = None
            incomplete_tasks = [t for t in tasks if not t.completed]
            if incomplete_tasks:
                incomplete_tasks.sort(key=lambda t: calculate_task_priority(t))
                next_task = incomplete_tasks[0]
            
            return {
                'analytics': analytics,
                'next_task': next_task.to_dict() if next_task else None,
                'all_tasks': [t.to_dict() for t in tasks],
                'upcoming_due_dates': self._get_upcoming_due_dates(tasks)
            }
            
        except Exception as e:
            print(f"Error getting user task summary: {e}")
            return {
                'analytics': get_user_task_analytics([]),
                'next_task': None,
                'all_tasks': [],
                'upcoming_due_dates': []
            }
    
    def _get_upcoming_due_dates(self, tasks: List[Task]) -> List[Dict[str, Any]]:
        """Get upcoming due dates for incomplete tasks"""
        incomplete_tasks = [t for t in tasks if not t.completed and t.due_date]
        incomplete_tasks.sort(key=lambda t: t.due_date)
        
        return [
            {
                'task_id': task.id,
                'title': task.title,
                'due_date': task.due_date.isoformat(),
                'days_until_due': task.get_days_until_due(),
                'is_overdue': task.is_overdue()
            }
            for task in incomplete_tasks[:5]  # Next 5 upcoming tasks
        ]

# Convenience functions for easy integration

async def fetch_current_task_for_user(user: User, firestore_client=None) -> Optional[Task]:
    """
    Convenience function to fetch the current (next) task for a user.
    This is the main function to call when a user is created or logs in.
    """
    task_service = TaskService(firestore_client)
    tasks = await task_service.fetch_current_tasks(user)
    
    if not tasks:
        return None
    
    # Return the highest priority incomplete task
    incomplete_tasks = [t for t in tasks if not t.completed]
    if incomplete_tasks:
        return incomplete_tasks[0]
    
    return tasks[0] if tasks else None

async def initialize_user_tasks(user: User, firestore_client=None) -> List[Task]:
    """
    Initialize tasks for a new user.
    This should be called when a user is first created.
    """
    task_service = TaskService(firestore_client)
    return await task_service.fetch_current_tasks(user)

async def get_user_dashboard_data(user: User, firestore_client=None) -> Dict[str, Any]:
    """
    Get complete dashboard data for a user including tasks and analytics.
    """
    task_service = TaskService(firestore_client)
    return await task_service.get_user_task_summary(user)