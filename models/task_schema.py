from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid

def _get_utc_now():
    return datetime.now(timezone.utc)

class TaskType(Enum):
    QUIZ = "quiz"
    AI_TUTORIAL = "AI Tutorial"

class TaskFrequency(Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class Subject(Enum):
    MATH = "Math"
    READING = "Reading"
    WRITING = "Writing"
    READING_WRITING = "Reading & Writing"

@dataclass
class Task:
    # Required fields
    id: str
    title: str
    description: str
    due_date: datetime
    completed: bool
    type_of_task: TaskType
    created_at: datetime
    frequency: TaskFrequency
    task_number: int
    user_id: str
    subject: Subject
    
    # Optional date fields for tracking periods
    start_date_of_week: Optional[datetime] = None
    start_date_of_month: Optional[datetime] = None
    
    # Task-specific attributes
    quiz_related_attributes: Dict[str, Any] = field(default_factory=dict)
    ai_tutorial_related_attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Attempts tracking
    attempts_info: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default values after object creation"""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if not isinstance(self.type_of_task, TaskType):
            self.type_of_task = TaskType(self.type_of_task)
        
        if not isinstance(self.frequency, TaskFrequency):
            self.frequency = TaskFrequency(self.frequency)
            
        if not isinstance(self.subject, Subject):
            self.subject = Subject(self.subject)
    
    @classmethod
    def create_quiz_task(
        cls,
        title: str,
        description: str,
        due_date: datetime,
        task_number: int,
        user_id: str,
        subject: Subject,
        facet: str,
        tags: list,
        num_questions: int = 10,
        difficulty_level: int = 3,
        duration_minutes: int = 10,
        passing_score: float = 70.0,
        start_date_of_week: Optional[datetime] = None,
        **kwargs
    ) -> 'Task':
        """Create a quiz task with default quiz attributes"""
        quiz_attributes = {
            'facet': facet,
            'tags': tags,
            'num_questions': num_questions,
            'difficulty_level': difficulty_level,
            'duration_minutes': duration_minutes,
            'passing_score': passing_score,
            **kwargs
        }
        
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            due_date=due_date,
            completed=False,
            type_of_task=TaskType.QUIZ,
            created_at=_get_utc_now(),
            frequency=TaskFrequency.WEEKLY,
            task_number=task_number,
            user_id=user_id,
            subject=subject,
            start_date_of_week=start_date_of_week,
            quiz_related_attributes=quiz_attributes,
            attempts_info={'attempts': 0, 'best_score': None, 'last_attempt': None}
        )
    
    @classmethod
    def create_ai_tutorial_task(
        cls,
        title: str,
        description: str,
        due_date: datetime,
        task_number: int,
        user_id: str,
        chapter_id: str,
        chapter_title: str,
        start_date_of_week: Optional[datetime] = None,
        **kwargs
    ) -> 'Task':
        """Create an AI tutorial task with default tutorial attributes"""
        ai_tutorial_attributes = {
            'chapter_id': chapter_id,
            'chapter_title': chapter_title,
            'estimated_duration_minutes': kwargs.get('estimated_duration_minutes', 30),
            **kwargs
        }
        
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            due_date=due_date,
            completed=False,
            type_of_task=TaskType.AI_TUTORIAL,
            created_at=_get_utc_now(),
            frequency=TaskFrequency.WEEKLY,
            task_number=task_number,
            user_id=user_id,
            subject=Subject.READING,  # Default for tutorials, can be overridden
            start_date_of_week=start_date_of_week,
            ai_tutorial_related_attributes=ai_tutorial_attributes,
            attempts_info={'attempts': 0, 'completed_sections': [], 'last_session': None}
        )
    
    def mark_completed(self) -> None:
        """Mark the task as completed"""
        self.completed = True
    
    def update_task_details(self, **kwargs) -> None:
        """Update task details with provided key-value pairs"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def add_attempt(self, score: Optional[float] = None, **attempt_data) -> None:
        """Add an attempt record to the task"""
        if 'attempts' not in self.attempts_info:
            self.attempts_info['attempts'] = 0
        
        self.attempts_info['attempts'] += 1
        self.attempts_info['last_attempt'] = _get_utc_now().isoformat()
        
        if score is not None:
            if self.attempts_info.get('best_score') is None or score > self.attempts_info['best_score']:
                self.attempts_info['best_score'] = score
        
        # Store additional attempt data
        for key, value in attempt_data.items():
            self.attempts_info[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Task object to dictionary for Firestore storage"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed': self.completed,
            'type_of_task': self.type_of_task.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'frequency': self.frequency.value,
            'task_number': self.task_number,
            'start_date_of_week': self.start_date_of_week.isoformat() if self.start_date_of_week else None,
            'start_date_of_month': self.start_date_of_month.isoformat() if self.start_date_of_month else None,
            'quiz_related_attributes': self.quiz_related_attributes,
            'ai_tutorial_related_attributes': self.ai_tutorial_related_attributes,
            'user_id': self.user_id,
            'subject': self.subject.value,
            'attempts_info': self.attempts_info
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create Task object from dictionary (Firestore data)"""
        return cls(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else _get_utc_now(),
            completed=data.get('completed', False),
            type_of_task=TaskType(data['type_of_task']),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else _get_utc_now(),
            frequency=TaskFrequency(data['frequency']),
            task_number=data['task_number'],
            start_date_of_week=datetime.fromisoformat(data['start_date_of_week']) if data.get('start_date_of_week') else None,
            start_date_of_month=datetime.fromisoformat(data['start_date_of_month']) if data.get('start_date_of_month') else None,
            quiz_related_attributes=data.get('quiz_related_attributes', {}),
            ai_tutorial_related_attributes=data.get('ai_tutorial_related_attributes', {}),
            user_id=data['user_id'],
            subject=Subject(data['subject']),
            attempts_info=data.get('attempts_info', {})
        )
    
    def is_overdue(self) -> bool:
        """Check if the task is overdue"""
        if not self.due_date:
            return False
        return _get_utc_now() > self.due_date and not self.completed
    
    def get_days_until_due(self) -> Optional[int]:
        """Get number of days until task is due"""
        if not self.due_date:
            return None
        
        delta = self.due_date.date() - _get_utc_now().date()
        return delta.days
    
    def __str__(self) -> str:
        return f"Task({self.id}): {self.title} - {self.type_of_task.value} - Due: {self.due_date}"
    
    def __repr__(self) -> str:
        return self.__str__()