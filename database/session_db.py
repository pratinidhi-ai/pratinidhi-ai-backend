"""
Session database operations
Handles all database interactions related to tutor sessions
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from database.firebase_client import get_firestore_client
from models.tutor_session_schema import TutorSession

logger = logging.getLogger(__name__)

class SessionDatabase:
    """Database operations for session management"""
    
    def __init__(self):
        self.db = get_firestore_client()
    
    def save_session_summary(self, session: TutorSession) -> bool:
        """Save session summary to database"""
        try:
            user_ref = self.db.collection('session_summary').document(session.user_id)
            session_ref = user_ref.collection('sessions').document(session.session_id)
            
            # Get session data without messages for summary
            summary_data = session.to_dict()
            if 'messages' in summary_data:
                del summary_data['messages']
            
            session_ref.set(summary_data)
            
            logger.info(f"Successfully saved session summary for user {session.user_id}, session {session.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session summary: {str(e)}")
            return False
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        try:
            # Get reference to user's sessions collection
            sessions_ref = self.db.collection('session_summary').document(user_id).collection('sessions')
            
            # Order by created_at descending to get most recent first
            query = sessions_ref.order_by('created_at', direction='DESCENDING')
            sessions = query.stream()
            
            sessions_list = []
            for session in sessions:
                session_data = session.to_dict()
                session_data['id'] = session.id  # Add document ID
                sessions_list.append(session_data)
            
            logger.info(f"Successfully fetched {len(sessions_list)} sessions for user {user_id}")
            return sessions_list
            
        except Exception as e:
            logger.error(f"Error fetching sessions for user {user_id}: {str(e)}")
            return []
    
    def get_session_by_id(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific session by ID"""
        try:
            session_ref = (self.db.collection('session_summary')
                          .document(user_id)
                          .collection('sessions')
                          .document(session_id))
            
            doc = session_ref.get()
            
            if doc.exists:
                session_data = doc.to_dict()
                session_data['id'] = doc.id
                return session_data
            
            logger.info(f"Session {session_id} not found for user {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting session {session_id} for user {user_id}: {str(e)}")
            return None
    
    def update_session(self, user_id: str, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Update session data"""
        try:
            session_ref = (self.db.collection('session_summary')
                          .document(user_id)
                          .collection('sessions')
                          .document(session_id))
            
            # Add updated timestamp
            update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            session_ref.update(update_data)
            
            logger.info(f"Successfully updated session {session_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {str(e)}")
            return False
    
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """Delete a session"""
        try:
            session_ref = (self.db.collection('session_summary')
                          .document(user_id)
                          .collection('sessions')
                          .document(session_id))
            
            session_ref.delete()
            
            logger.info(f"Successfully deleted session {session_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    def get_recent_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent sessions for a user"""
        try:
            sessions_ref = self.db.collection('session_summary').document(user_id).collection('sessions')
            query = (sessions_ref
                    .order_by('created_at', direction='DESCENDING')
                    .limit(limit))
            
            sessions = query.stream()
            sessions_list = []
            
            for session in sessions:
                session_data = session.to_dict()
                session_data['id'] = session.id
                sessions_list.append(session_data)
            
            logger.info(f"Retrieved {len(sessions_list)} recent sessions for user {user_id}")
            return sessions_list
            
        except Exception as e:
            logger.error(f"Error getting recent sessions for user {user_id}: {str(e)}")
            return []
    
    def get_session_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get session analytics for a user"""
        try:
            sessions = self.get_user_sessions(user_id)
            
            if not sessions:
                return {
                    'total_sessions': 0,
                    'total_duration_minutes': 0,
                    'average_duration_minutes': 0,
                    'last_session_date': None,
                    'sessions_this_week': 0,
                    'sessions_this_month': 0
                }
            
            # Calculate analytics
            total_sessions = len(sessions)
            total_duration = sum(session.get('duration_minutes', 0) for session in sessions)
            average_duration = total_duration / total_sessions if total_sessions > 0 else 0
            
            # Get current date boundaries
            now = datetime.now(timezone.utc)
            week_start = now - timedelta(days=now.weekday())
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            sessions_this_week = 0
            sessions_this_month = 0
            
            for session in sessions:
                if session.get('created_at'):
                    try:
                        session_date = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00'))
                        if session_date >= week_start:
                            sessions_this_week += 1
                        if session_date >= month_start:
                            sessions_this_month += 1
                    except (ValueError, TypeError):
                        continue
            
            # Get last session date
            last_session_date = None
            if sessions:
                last_session = sessions[0]  # Most recent (already ordered by created_at DESC)
                last_session_date = last_session.get('created_at')
            
            return {
                'total_sessions': total_sessions,
                'total_duration_minutes': total_duration,
                'average_duration_minutes': round(average_duration, 2),
                'last_session_date': last_session_date,
                'sessions_this_week': sessions_this_week,
                'sessions_this_month': sessions_this_month
            }
            
        except Exception as e:
            logger.error(f"Error getting session analytics for user {user_id}: {str(e)}")
            return {}

# Convenience functions for backward compatibility and easy access
_session_db_instance = None

def get_session_db() -> SessionDatabase:
    """Get singleton instance of SessionDatabase"""
    global _session_db_instance
    if _session_db_instance is None:
        _session_db_instance = SessionDatabase()
    return _session_db_instance

# Legacy function wrappers for backward compatibility
def saveSessionSummary(session: TutorSession) -> bool:
    """Legacy wrapper for save_session_summary"""
    return get_session_db().save_session_summary(session)

def _getUserSessions(user_id: str) -> List[Dict[str, Any]]:
    """Legacy wrapper for get_user_sessions"""
    return get_session_db().get_user_sessions(user_id)