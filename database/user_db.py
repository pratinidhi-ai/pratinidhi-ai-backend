"""
User database operations
Handles all database interactions related to users
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from database.firebase_client import get_firestore_client
from models.users_schema import User
from threading import Thread

logger = logging.getLogger(__name__)

class UserDatabase:
	"""Database operations for user management"""
	
	def __init__(self):
		self.db = get_firestore_client()
	
	def _check_connection(self) -> bool:
		"""Check if database connection is available"""
		if self.db is None:
			logger.error("Firestore client is not initialized")
			return False
		return True
	
	def get_users(self, active_only: bool = True) -> List[Dict[str, Any]]:
		"""Get all users, optionally filtered by active status"""
		try:
			if self.db is None:
				logger.error("Firestore client is not initialized")
				return []
				
			users_collection = self.db.collection('users')
			
			if active_only:
				users_collection = users_collection.where('active', '==', True)
			
			docs = users_collection.stream()
			users_list = []
			
			for doc in docs:
				user_data = doc.to_dict()
				user_data['id'] = doc.id  # Ensure ID is included
				users_list.append(user_data)
			
			logger.info(f"Retrieved {len(users_list)} users")
			return users_list
			
		except Exception as e:
			logger.error(f"Error getting users: {str(e)}")
			return []
	
	def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
		"""Get a user by their ID"""
		try:
			if self.db is None:
				logger.error("Firestore client is not initialized")
				return None
				
			# First try to get by document ID
			doc_ref = self.db.collection('users').document(user_id)
			doc = doc_ref.get()
			
			if doc.exists:
				user_data = doc.to_dict()
				if user_data is not None:
					user_data['id'] = doc.id
					return user_data
			
			# Fallback: query by id field (for backward compatibility)
			users_collection = self.db.collection('users').where('id', '==', user_id)
			docs = users_collection.limit(1).stream()
			
			for doc in docs:
				user_data = doc.to_dict()
				if 'id' not in user_data:
					user_data['id'] = user_id
				return user_data
			
			logger.info(f"User not found: {user_id}")
			return None
			
		except Exception as e:
			logger.error(f"Error getting user {user_id}: {str(e)}")
			return None
	
	def create_user(self, user_data: Dict[str, Any]) -> bool:
		"""Create a new user"""
		try:
			user_id = user_data['id']
			
			# Check if user already exists
			if self.user_exists(user_id):
				logger.warning(f"User {user_id} already exists, skipping creation")
				return False
			
			# Add timestamp fields if not present
			current_time = datetime.now(timezone.utc).isoformat()
			
			if 'created_at' not in user_data:
				user_data['created_at'] = current_time
			if 'updated_at' not in user_data:
				user_data['updated_at'] = current_time
			
			# Use document ID as the user ID for better querying
			self.db.collection('users').document(user_id).set(user_data)
			
			logger.info(f"Successfully created user: {user_id}")
			return True
			
		except Exception as e:
			logger.error(f"Error creating user: {str(e)}")
			return False
	
	def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
		"""Update an existing user"""
		try:
			# Add updated timestamp
			update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
			
			doc_ref = self.db.collection('users').document(user_id)
			doc_ref.update(update_data)
			
			logger.info(f"Successfully updated user: {user_id}")
			return True
			
		except Exception as e:
			logger.error(f"Error updating user {user_id}: {str(e)}")
			return False
	
	def user_exists(self, user_id: str) -> bool:
		"""Check if a user exists"""
		try:
			doc_ref = self.db.collection('users').document(user_id)
			doc = doc_ref.get()
			return doc.exists
			
		except Exception as e:
			logger.error(f"Error checking if user exists: {str(e)}")
			return False
	
	def delete_user(self, user_id: str) -> bool:
		"""Delete a user (soft delete by setting active=False)"""
		try:
			doc_ref = self.db.collection('users').document(user_id)
			doc_ref.update({
				'active': False,
				'updated_at': datetime.now(timezone.utc).isoformat()
			})
			
			logger.info(f"Successfully deactivated user: {user_id}")
			return True
			
		except Exception as e:
			logger.error(f"Error deactivating user {user_id}: {str(e)}")
			return False
	
	def update_last_login(self, user_id: str) -> bool:
		"""Update user's last login timestamp"""
		try:
			doc_ref = self.db.collection('users').document(user_id)
			doc_ref.update({
				'last_login': datetime.now(timezone.utc).isoformat(),
				'updated_at': datetime.now(timezone.utc).isoformat()
			})
			
			logger.info(f"Updated last login for user: {user_id}")
			return True
			
		except Exception as e:
			logger.error(f"Error updating last login for user {user_id}: {str(e)}")
			return False
	
	def mark_chapter_completed(self, user_id: str, chapter_id: str) -> bool:
		"""Mark a chapter as completed for a user"""
		try:
			# Get current user data
			user_data = self.get_user_by_id(user_id)
			if not user_data:
				logger.error(f"User {user_id} not found")
				return False
			
			# Get current completed chapters
			completed_chapters = user_data.get('completed_chapters', [])
			
			# Add chapter if not already completed
			if chapter_id not in completed_chapters:
				completed_chapters.append(chapter_id)
				
				# Update user
				self.update_user(user_id, {
					'completed_chapters': completed_chapters
				})
				
				logger.info(f"Marked chapter {chapter_id} as completed for user {user_id}")
			
			return True
			
		except Exception as e:
			logger.error(f"Error marking chapter completed for user {user_id}: {str(e)}")
			return False
	
	def get_user_progress(self, user_id: str) -> Dict[str, Any]:
		"""Get user's overall progress"""
		try:
			user_data = self.get_user_by_id(user_id)
			if not user_data:
				return {}
			
			completed_chapters = user_data.get('completed_chapters', [])
			total_chapters = 7  # Based on lecture_notes.json
			
			progress = {
				'completed_chapters': completed_chapters,
				'total_chapters': total_chapters,
				'completion_percentage': (len(completed_chapters) / total_chapters * 100) if total_chapters > 0 else 0,
				'current_week_start': user_data.get('current_week_start'),
				'last_login': user_data.get('last_login'),
				'onboarding_completed': user_data.get('onboarding_completed', False)
			}
			
			return progress
			
		except Exception as e:
			logger.error(f"Error getting user progress for {user_id}: {str(e)}")
			return {}
	
	def update_user_tags_quiz(self, user_id:str , tags: list[str]) -> bool:
		user_data = self.get_user_by_id(user_id)
		if not user_data:
			logger.error(f"User {user_id} not found")
			return False
		user = User.from_dict(user_data)
		for tag in tags:
			user.mark_quiz_tag(tag)
		self.update_user(user_id, user.to_dict())
		return True

# Convenience functions for backward compatibility and easy access
_user_db_instance = None





def get_user_db() -> UserDatabase:
	"""Get singleton instance of UserDatabase"""
	global _user_db_instance
	if _user_db_instance is None:
		_user_db_instance = UserDatabase()
	return _user_db_instance

# Legacy function wrappers for backward compatibility
def getUsers() -> List[Dict[str, Any]]:
	"""Legacy wrapper for get_users"""
	return get_user_db().get_users()

def getUserbyId(user_id: str) -> Optional[Dict[str, Any]]:
	"""Legacy wrapper for get_user_by_id"""
	return get_user_db().get_user_by_id(user_id)

def createUser(user_data: Dict[str, Any]) -> bool:
	"""Legacy wrapper for create_user"""
	return get_user_db().create_user(user_data)

def checkUserExists(user_id: str) -> bool:
	"""Legacy wrapper for user_exists"""
	return get_user_db().user_exists(user_id)

def _update_user_async(user: User):
	try:
		user_dict = user.to_dict()
		db = get_user_db()
		db.collection('users').document(user.id).set(user_dict, merge=True)
		logger.info(f"Successfully updated session count for user {user.id}")
	except Exception as e:
		logger.error(f"Failed to update user data in background: {e}")

def userStartSession(user_id : str):
	try:
		user_dict = getUserbyId(user_id=user_id)
		if not user_dict:
			return False
		
		user_obj = User.from_dict(user_dict)
		can_start = user_obj.can_start_session()
		if can_start:
			user_obj.increment_session_count()
			Thread(
				target=_update_user_async,
				args=(user_obj,),
				daemon=True
			).start()
		return can_start
	except Exception as e:
		logger.error(f"Error in userStartSession: {e}")
		return False
	
def _update_user_tags_quiz(user_id:str , tags: list[str]) -> bool:
	return get_user_db().update_user_tags_quiz(user_id, tags)