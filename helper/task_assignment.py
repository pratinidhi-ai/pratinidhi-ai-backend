from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import random
import json
import os
from models.task_schema import Task, TaskType, Subject
from models.users_schema import User

def get_week_start(date: Optional[datetime] = None) -> datetime:
    """Get the start of the week (Monday) for a given date"""
    if date is None:
        date = datetime.now(timezone.utc)
    
    # Get Monday of the current week
    days_since_monday = date.weekday()  # Monday is 0, Sunday is 6
    week_start = date - timedelta(days=days_since_monday)
    # Set to beginning of the day
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0)

def get_days_left_in_week(date: Optional[datetime] = None) -> int:
    """Get number of days left in the current week (including today)"""
    if date is None:
        date = datetime.now(timezone.utc)
    
    # Sunday is 6, so days left = 6 - current_weekday
    days_left = 6 - date.weekday() + 1  # +1 to include today
    return max(1, days_left)  # At least 1 day

def load_lecture_notes() -> Dict[str, Any]:
    """Load lecture notes from config file"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'lecture_notes.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_quiz_facets() -> List[Dict[str, str]]:
    """Get the predefined quiz facets for SAT preparation"""
    return [
        {"facet": "math|algebra|11", "subject": "Math", "title": "Algebra Quiz"},
        {"facet": "math|data analysis|11", "subject": "Math", "title": "Data Analysis Quiz"},
        {"facet": "reading & writing|grammar|11", "subject": "Reading & Writing", "title": "Grammar Quiz"},
        {"facet": "reading & writing|vocabulary|11", "subject": "Reading & Writing", "title": "Vocabulary Quiz"}
    ]

def get_random_tags_for_facet(facet: str, num_tags: int = 10) -> List[str]:
    """
    Get random tags for a given facet from the question bank.
    Uses the question database to get actual available tags.
    """
    try:
        from database.question_db import get_question_db
        
        question_db = get_question_db()
        tags = question_db.get_random_tags_by_facets(facet, num_tags)
        print(f"Selected tags for facet '{facet}': {tags}")
        return tags
    except ImportError:
        # Fallback: return dummy tags if question_db is not available
        base_tags = facet.split('|') + [f"topic{i}" for i in range(1, 21)]
        return random.sample(base_tags, min(num_tags, len(base_tags)))

def create_quiz_task(
    user_id: str,
    facet_info: Dict[str, str],
    task_number: int,
    due_date: datetime,
    week_start: datetime
) -> Task:
    """Create a quiz task for the given facet"""
    tags = get_random_tags_for_facet(facet_info["facet"], 10)
    
    # Map subject string to Subject enum
    if facet_info["subject"] == "Math":
        subject = Subject.MATH
    elif facet_info["subject"] == "Reading & Writing":
        subject = Subject.READING_WRITING
    else:
        subject = Subject.READING  # Default fallback
    
    description = f"Complete a {facet_info['title']} with 10 questions covering {', '.join(tags[:3])} and more topics."
    
    return Task.create_quiz_task(
        title=facet_info["title"],
        description=description,
        due_date=due_date,
        task_number=task_number,
        user_id=user_id,
        subject=subject,
        facet=facet_info["facet"],
        tags=tags,
        num_questions=10,
        difficulty_level=3,
        duration_minutes=10,
        passing_score=70.0,
        start_date_of_week=week_start
    )

def create_ai_tutorial_task(
    user_id: str,
    chapter_id: str,
    task_number: int,
    due_date: datetime,
    week_start: datetime
) -> Optional[Task]:
    """Create an AI tutorial task for the given chapter"""
    try:
        lecture_notes = load_lecture_notes()
        chapter_info = lecture_notes["SAT"]["chapters"].get(chapter_id)
        
        if not chapter_info:
            return None
        
        description = f"Complete the AI tutorial for {chapter_info['title']}. {chapter_info.get('summary', '')[:100]}..."
        
        return Task.create_ai_tutorial_task(
            title=f"AI Tutorial: {chapter_info['title']}",
            description=description,
            due_date=due_date,
            task_number=task_number,
            user_id=user_id,
            chapter_id=chapter_id,
            chapter_title=chapter_info['title'],
            start_date_of_week=week_start,
            estimated_duration_minutes=30
        )
    except Exception as e:
        print(f"Error creating AI tutorial task: {e}")
        return None

def assign_weekly_tasks(user: User, current_date: Optional[datetime] = None) -> List[Task]:
    """
    Assign tasks for the current week based on remaining days.
    Returns a list of tasks to be created.
    """
    if current_date is None:
        current_date = datetime.now(timezone.utc)
    
    week_start = get_week_start(current_date)
    days_left = get_days_left_in_week(current_date)
    
    # Update user's current week
    user.current_week_start = week_start
    
    tasks = []
    task_number = 1
    
    # Get quiz facets
    quiz_facets = get_quiz_facets()
    
    # Determine task distribution based on days left
    if days_left >= 4:  # Monday to Wednesday - assign all tasks
        num_quiz_tasks = 4
        num_ai_tutorial_tasks = 2
    elif days_left >= 2:  # Thursday to Saturday - reduced tasks
        num_quiz_tasks = 2
        num_ai_tutorial_tasks = 1
    else:  # Sunday - minimal tasks
        num_quiz_tasks = 1
        num_ai_tutorial_tasks = 1
    
    # Distribute tasks evenly across remaining days
    total_tasks = num_quiz_tasks + num_ai_tutorial_tasks
    days_per_task = max(1, days_left // total_tasks)
    
    current_due_date = current_date.replace(hour=23, minute=59, second=59)
    
    # Create quiz tasks
    for i in range(min(num_quiz_tasks, len(quiz_facets))):
        facet_info = quiz_facets[i]
        
        quiz_task = create_quiz_task(
            user_id=user.id,
            facet_info=facet_info,
            task_number=task_number,
            due_date=current_due_date + timedelta(days=(i * days_per_task)),
            week_start=week_start
        )
        
        tasks.append(quiz_task)
        task_number += 1
    
    # Create AI tutorial tasks
    for i in range(num_ai_tutorial_tasks):
        next_chapter = user.get_next_chapter()
        
        if next_chapter:
            ai_tutorial_task = create_ai_tutorial_task(
                user_id=user.id,
                chapter_id=next_chapter,
                task_number=task_number,
                due_date=current_due_date + timedelta(days=((num_quiz_tasks + i) * days_per_task)),
                week_start=week_start
            )
            
            if ai_tutorial_task:
                tasks.append(ai_tutorial_task)
                task_number += 1
    
    return tasks

def should_assign_new_tasks(user: User, current_date: Optional[datetime] = None) -> bool:
    """
    Check if new tasks should be assigned for the current week.
    Returns True if no tasks exist for the current week or if it's a new week.
    """
    if current_date is None:
        current_date = datetime.now(timezone.utc)
    
    current_week_start = get_week_start(current_date)
    
    # If user has no current_week_start or it's a different week, assign new tasks
    if not user.current_week_start:
        return True
    
    return user.current_week_start.date() != current_week_start.date()

def get_current_week_tasks_query_filter(user_id: str, current_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Get Firestore query filter for tasks in the current week.
    This returns the filter that should be used to query tasks collection.
    """
    if current_date is None:
        current_date = datetime.now(timezone.utc)
    
    week_start = get_week_start(current_date)
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    return {
        'user_id': user_id,
        'start_date_of_week': week_start.isoformat(),
        'due_date_range': {
            'start': week_start.isoformat(),
            'end': week_end.isoformat()
        }
    }

def calculate_task_priority(task: Task, current_date: Optional[datetime] = None) -> int:
    """
    Calculate task priority score for sorting.
    Lower score = higher priority.
    """
    if current_date is None:
        current_date = datetime.now(timezone.utc)
    
    priority_score = 0
    
    # Factor 1: Due date (sooner = higher priority)
    if task.due_date:
        days_until_due = (task.due_date.date() - current_date.date()).days
        priority_score += max(0, days_until_due) * 10
    
    # Factor 2: Task number (lower = higher priority)
    priority_score += task.task_number
    
    # Factor 3: Completion status (incomplete = higher priority)
    if task.completed:
        priority_score += 1000  # Completed tasks go to the bottom
    
    # Factor 4: Overdue tasks get highest priority
    if task.is_overdue():
        priority_score = -1000 + task.task_number  # Negative for highest priority
    
    return priority_score

# Example usage functions that would be called from the main application

def get_or_assign_user_tasks(user: User, firestore_client=None) -> List[Task]:
    """
    Main function to get current tasks for a user or assign new ones if needed.
    This function should be called when fetching tasks for a user.
    
    Args:
        user: User object
        firestore_client: Firestore client for database operations
    
    Returns:
        List of tasks for the current week
    """
    # This is a template - actual implementation would require Firestore integration
    
    # 1. Check if new tasks should be assigned
    if should_assign_new_tasks(user):
        # 2. Assign new weekly tasks
        new_tasks = assign_weekly_tasks(user)
        
        # 3. Save tasks to Firestore (implementation needed)
        if firestore_client:
            for task in new_tasks:
                # await save_task_to_firestore(firestore_client, task)
                pass
        
        return new_tasks
    else:
        # 4. Fetch existing tasks for current week (implementation needed)
        if firestore_client:
            # query_filter = get_current_week_tasks_query_filter(user.id)
            # tasks = await fetch_tasks_from_firestore(firestore_client, query_filter)
            # return sorted(tasks, key=calculate_task_priority)
            pass
        
        return []  # Placeholder

def get_user_task_analytics(tasks: List[Task]) -> Dict[str, Any]:
    """
    Generate analytics for user's tasks.
    """
    if not tasks:
        return {
            'total_tasks': 0,
            'completed_tasks': 0,
            'pending_tasks': 0,
            'overdue_tasks': 0,
            'completion_rate': 0.0,
            'quiz_tasks': 0,
            'tutorial_tasks': 0
        }
    
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.completed])
    pending_tasks = total_tasks - completed_tasks
    overdue_tasks = len([t for t in tasks if t.is_overdue()])
    quiz_tasks = len([t for t in tasks if t.type_of_task == TaskType.QUIZ])
    tutorial_tasks = len([t for t in tasks if t.type_of_task == TaskType.AI_TUTORIAL])
    
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