"""
Task database operations
Handles all database interactions related to tasks
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from database.firebase_client import get_firestore_client
from models.task_schema import Task

logger = logging.getLogger(__name__)

class TaskDatabase:
    """Database operations for task management"""
    
    def __init__(self):
        self.db = get_firestore_client()
    
    def get_user_tasks(self, user_id: str, start_date: Optional[datetime] = None, 
                      end_date: Optional[datetime] = None) -> List[Task]:
        """Get all tasks for a user, optionally filtered by date range"""
        try:
            tasks_ref = self.db.collection('users').document(user_id).collection('tasks')
            
            query = tasks_ref
            
            # Apply date filters if provided
            if start_date:
                query = query.where('due_date', '>=', start_date.isoformat())
            if end_date:
                query = query.where('due_date', '<=', end_date.isoformat())
            
            # Order by due date
            query = query.order_by('due_date')
            
            docs = query.stream()
            tasks = []
            
            for doc in docs:
                task_data = doc.to_dict()
                task_data['id'] = doc.id  # Ensure ID is set
                task = Task.from_dict(task_data)
                tasks.append(task)
            
            logger.info(f"Retrieved {len(tasks)} tasks for user {user_id}")
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting tasks for user {user_id}: {str(e)}")
            return []
    
    def get_tasks_by_week(self, user_id: str, week_start: datetime) -> List[Task]:
        """Get tasks for a specific week"""
        try:
            week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
            
            tasks_ref = self.db.collection('users').document(user_id).collection('tasks')
            query = tasks_ref.where('start_date_of_week', '==', week_start.isoformat())
            
            docs = query.stream()
            tasks = []
            
            for doc in docs:
                task_data = doc.to_dict()
                task_data['id'] = doc.id
                task = Task.from_dict(task_data)
                tasks.append(task)
            
            logger.info(f"Retrieved {len(tasks)} tasks for user {user_id} for week starting {week_start.date()}")
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting weekly tasks for user {user_id}: {str(e)}")
            return []
    
    def get_task_by_id(self, user_id: str, task_id: str) -> Optional[Task]:
        """Get a specific task by ID"""
        try:
            task_ref = (self.db.collection('users')
                       .document(user_id)
                       .collection('tasks')
                       .document(task_id))
            
            doc = task_ref.get()
            
            if doc.exists:
                task_data = doc.to_dict()
                task_data['id'] = doc.id
                return Task.from_dict(task_data)
            
            logger.info(f"Task {task_id} not found for user {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting task {task_id} for user {user_id}: {str(e)}")
            return None
    
    def create_task(self, task: Task) -> bool:
        """Create a new task"""
        try:
            task_ref = (self.db.collection('users')
                       .document(task.user_id)
                       .collection('tasks')
                       .document(task.id))
            
            task_ref.set(task.to_dict())
            
            logger.info(f"Successfully created task {task.id} for user {task.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return False
    
    def create_tasks_batch(self, tasks: List[Task]) -> bool:
        """Create multiple tasks in a batch"""
        if not tasks:
            return True
        
        try:
            batch = self.db.batch()
            
            for task in tasks:
                task_ref = (self.db.collection('users')
                           .document(task.user_id)
                           .collection('tasks')
                           .document(task.id))
                
                batch.set(task_ref, task.to_dict())
            
            batch.commit()
            
            logger.info(f"Successfully created {len(tasks)} tasks in batch")
            return True
            
        except Exception as e:
            logger.error(f"Error creating tasks in batch: {str(e)}")
            return False
    
    def update_task(self, user_id: str, task_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing task"""
        try:
            task_ref = (self.db.collection('users')
                       .document(user_id)
                       .collection('tasks')
                       .document(task_id))
            
            # Add updated timestamp
            update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            task_ref.update(update_data)
            
            logger.info(f"Successfully updated task {task_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {str(e)}")
            return False
    
    def mark_task_completed(self, user_id: str, task_id: str) -> bool:
        """Mark a task as completed"""
        return self.update_task(user_id, task_id, {
            'completed': True,
            'completed_at': datetime.now(timezone.utc).isoformat()
        })
    
    def update_task_attempt(self, user_id: str, task_id: str, score: Optional[float] = None, 
                           **attempt_data) -> bool:
        """Update task with attempt information"""
        try:
            # Get current task data
            task = self.get_task_by_id(user_id, task_id)
            if not task:
                logger.error(f"Task {task_id} not found for user {user_id}")
                return False
            
            # Update attempt info
            task.add_attempt(score=score, **attempt_data)
            
            # Update in database
            return self.update_task(user_id, task_id, {
                'attempts_info': task.attempts_info
            })
            
        except Exception as e:
            logger.error(f"Error updating task attempt for {task_id}: {str(e)}")
            return False
    
    def delete_task(self, user_id: str, task_id: str) -> bool:
        """Delete a task"""
        try:
            task_ref = (self.db.collection('users')
                       .document(user_id)
                       .collection('tasks')
                       .document(task_id))
            
            task_ref.delete()
            
            logger.info(f"Successfully deleted task {task_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {str(e)}")
            return False
    
    def get_overdue_tasks(self, user_id: str) -> List[Task]:
        """Get all overdue tasks for a user"""
        try:
            current_time = datetime.now(timezone.utc)
            
            tasks_ref = self.db.collection('users').document(user_id).collection('tasks')
            query = (tasks_ref
                    .where('completed', '==', False)
                    .where('due_date', '<', current_time.isoformat()))
            
            docs = query.stream()
            tasks = []
            
            for doc in docs:
                task_data = doc.to_dict()
                task_data['id'] = doc.id
                task = Task.from_dict(task_data)
                tasks.append(task)
            
            logger.info(f"Retrieved {len(tasks)} overdue tasks for user {user_id}")
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting overdue tasks for user {user_id}: {str(e)}")
            return []
    
    def get_pending_tasks(self, user_id: str, limit: Optional[int] = None) -> List[Task]:
        """Get pending (incomplete) tasks for a user"""
        try:
            tasks_ref = self.db.collection('users').document(user_id).collection('tasks')
            query = (tasks_ref
                    .where('completed', '==', False)
                    .order_by('due_date'))
            
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            tasks = []
            
            for doc in docs:
                task_data = doc.to_dict()
                task_data['id'] = doc.id
                task = Task.from_dict(task_data)
                tasks.append(task)
            
            logger.info(f"Retrieved {len(tasks)} pending tasks for user {user_id}")
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting pending tasks for user {user_id}: {str(e)}")
            return []
    
    def get_completed_tasks(self, user_id: str, limit: Optional[int] = None) -> List[Task]:
        """Get completed tasks for a user"""
        try:
            tasks_ref = self.db.collection('users').document(user_id).collection('tasks')
            query = (tasks_ref
                    .where('completed', '==', True)
                    .order_by('due_date', direction='DESCENDING'))
            
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            tasks = []
            
            for doc in docs:
                task_data = doc.to_dict()
                task_data['id'] = doc.id
                task = Task.from_dict(task_data)
                tasks.append(task)
            
            logger.info(f"Retrieved {len(tasks)} completed tasks for user {user_id}")
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting completed tasks for user {user_id}: {str(e)}")
            return []
    
    def get_task_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get task analytics for a user"""
        try:
            all_tasks = self.get_user_tasks(user_id)
            
            if not all_tasks:
                return {
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'pending_tasks': 0,
                    'overdue_tasks': 0,
                    'completion_rate': 0.0,
                    'quiz_tasks': 0,
                    'tutorial_tasks': 0
                }
            
            from models.task_schema import TaskType
            
            total_tasks = len(all_tasks)
            completed_tasks = len([t for t in all_tasks if t.completed])
            pending_tasks = total_tasks - completed_tasks
            overdue_tasks = len([t for t in all_tasks if t.is_overdue()])
            quiz_tasks = len([t for t in all_tasks if t.type_of_task == TaskType.QUIZ])
            tutorial_tasks = len([t for t in all_tasks if t.type_of_task == TaskType.AI_TUTORIAL])
            
            completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0.0
            
            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'pending_tasks': pending_tasks,
                'overdue_tasks': overdue_tasks,
                'completion_rate': round(completion_rate, 2),
                'quiz_tasks': quiz_tasks,
                'tutorial_tasks': tutorial_tasks
            }
            
        except Exception as e:
            logger.error(f"Error getting task analytics for user {user_id}: {str(e)}")
            return {}

# Convenience function for easy access
_task_db_instance = None

def get_task_db() -> TaskDatabase:
    """Get singleton instance of TaskDatabase"""
    global _task_db_instance
    if _task_db_instance is None:
        _task_db_instance = TaskDatabase()
    return _task_db_instance