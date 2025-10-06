"""
Database package for pratinidhi-ai-backend
Contains all database operations organized by functionality
"""

# Import main database classes for easy access
from .user_db import UserDatabase, get_user_db
from .task_db import TaskDatabase, get_task_db  
from .session_db import SessionDatabase, get_session_db
from .question_db import QuestionDatabase, get_question_db
from .firebase_client import get_firestore_client, get_auth

# Legacy function imports for backward compatibility
from .user_db import getUsers, getUserbyId, createUser, checkUserExists
from .session_db import saveSessionSummary, _getUserSessions
from .question_db import _getMetaData, _getQuestions, getQuestionFromId

__all__ = [
    # Database classes
    'UserDatabase', 'TaskDatabase', 'SessionDatabase', 'QuestionDatabase',
    
    # Singleton getters
    'get_user_db', 'get_task_db', 'get_session_db', 'get_question_db',
    
    # Firebase client functions
    'get_firestore_client', 'get_auth',
    
    # Legacy functions
    'getUsers', 'getUserbyId', 'createUser', 'checkUserExists',
    'saveSessionSummary', '_getUserSessions',
    '_getMetaData', '_getQuestions', 'getQuestionFromId'
]