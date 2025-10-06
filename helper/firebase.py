import firebase_admin
from firebase_admin import credentials , firestore , auth
import os
import logging
import random
from threading import Thread
from models.tutor_session_schema import TutorSession
from models.users_schema import User

dir = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(dir,'..','p-ai-private-key.json')
cred = credentials.Certificate(key_path)
logger = logging.getLogger(__name__)

firebase_admin.initialize_app(cred)

db = firestore.client()

def getUsers() -> list: #dummy method
	users_collection = db.collection('users').where('active', '==', True)
	docs = users_collection.stream()
	users_list = []
	for doc in docs:
		users_list.append(doc.to_dict())
	return users_list

def getUserbyId(user_id : str) :
	try:
		users_collection = db.collection('users').where('id', '==', user_id)
		docs = users_collection.limit(1).stream()
		users_list = []
		for doc in docs:
				user_data = doc.to_dict()
				# Ensure the ID is in the data for from_dict method
				if 'id' not in user_data:
					user_data['id'] = user_id
				return user_data
		return None
	
	except Exception as e:
		logger.error(f"Error getting user from Firestore: {str(e)}")
		raise

def createUser(user_data: dict) -> bool:

	try:
		user_id = user_data['id']
		
		# Check if user already exists before creating
		if checkUserExists(user_id):
			logger.warning(f"User {user_id} already exists, skipping creation")
			return False
		
		# Add timestamp fields if not present
		from datetime import datetime, timezone
		current_time = datetime.now(timezone.utc).isoformat()
		
		if 'created_at' not in user_data:
			user_data['created_at'] = current_time
		if 'updated_at' not in user_data:
			user_data['updated_at'] = current_time
		
		db.collection('users').document(user_id).set(user_data)
		
		logger.info(f"Successfully created user: {user_id}")
		return True
		
	except Exception as e:
		logger.error(f"Error creating user in Firestore: {str(e)}")
		return False
		
	except Exception as e:
		logger.error(f"Error creating user in Firestore: {str(e)}")
		return False


def checkUserExists(user_id: str) -> bool:

	try:
		doc_ref = db.collection('users').document(user_id)
		doc = doc_ref.get()
		return doc.exists
	except Exception as e:
		logger.error(f"Error checking if user exists: {str(e)}")
		return False
	
def _getMetaData() :
	try:
		doc = db.collection('question_bank').document('_metadata').get()
		metaData = doc.to_dict()
		return metaData
	except Exception as e:
		logger.error(e)
		return None

def _update_user_async(user: User):
	try:
		user_dict = user.to_dict()
		db.collection('users').document(user.id).set(user_dict, merge=True)
		logger.info(f"Successfully updated session count for user {user.id}")
	except Exception as e:
		logger.error(f"Failed to update user data in background: {e}")

def _getQuestions(attributes: dict):
	nques = attributes.get('nques')
	if nques is None:
		nques = 5
	else:
		try:
			nques = int(nques)
		except ValueError as e:
			nques = 5
			logger.error(e)
	try:
		if attributes.get('tags') is None:
			if attributes.get('exam') is None:
				sub_path = attributes['subject'] + '|' + attributes['subcategory'] + '|' + attributes['standard']
				collection_ref = db.collection('question_bank')\
							.document(sub_path)\
							.collection('difficulty')\
							.document(attributes['difficulty'])\
							.collection('all')\
							.document('members')\
							.collection('items')
			else:
				sub_path = attributes['subject'] + '|' + attributes['subcategory'] + '|' + attributes['standard']
				collection_ref = db.collection('question_bank')\
							.document(sub_path)\
							.collection('difficulty')\
							.document(attributes['difficulty'])\
							.collection('by_exam')\
							.document(attributes['exam'])\
							.collection('members')
		else:
			if attributes.get('exam') is None:
				sub_path = attributes['subject'] + '|' + attributes['subcategory'] + '|' + attributes['standard']
				collection_ref = db.collection('question_bank')\
							.document(sub_path)\
							.collection('difficulty')\
							.document(attributes['difficulty'])\
							.collection('tags')\
							.document(attributes['tags'])\
							.collection('members')
			else:
				sub_path = attributes['subject'] + '|' + attributes['subcategory'] + '|' + attributes['standard']
				collection_ref = db.collection('question_bank')\
							.document(sub_path)\
							.collection('difficulty')\
							.document(attributes['difficulty'])\
							.collection('tags')\
							.document(attributes['tags'])\
							.collection('by_exam')\
							.document(attributes['exam'])\
							.collection('members')
		# query_newest = collection_ref.order_by(
		# "created_at",  
		# direction=firestore.Query.DESCENDING
		# ).limit(nques)
		rand_value = random.random()
		query_random = collection_ref.where("rand",">=",rand_value).order_by("rand").limit(nques)
		docs_newest = query_random.stream()
		result = []
		for doc in docs_newest:
			result.append(getQuestionFromId(doc.to_dict()['question_id']))
		
		if len(result) < nques:
			query_fallback = collection_ref.where("rand", "<", rand_value).order_by("rand").limit(nques - len(result))
			docs_fallback = list(query_fallback.stream())
			for doc in docs_fallback:
				result.append(getQuestionFromId(doc.to_dict()['question_id']))
		return result
	
	except Exception as e:
		logger.error(e)
		return []
	
def getQuestionFromId(id: str):
	try:
		doc_ref = db.collection('questions').document(id)
		doc = doc_ref.get()
		return doc.to_dict()
	except Exception as e:
		logger.error(e)
		return {}
	
def saveSessionSummary(session : TutorSession):
	try:
		user_ref = db.collection('session_summary').document(session.user_id)
		session_ref = user_ref.collection('sessions').document(session.session_id)
		summary_data = session.to_dict()
		if 'messages' in summary_data:
			del summary_data['messages']
		session_ref.set(summary_data)
		logger.info(f"Successfully saved session summary for user {session.user_id}, session {session.session_id}")
		return True
	except Exception as e:
		logger.error(e)
		return False

def _getUserSessions(user_id: str):
	try:
		# Get reference to user's sessions collection
		sessions_ref = db.collection('session_summary').document(user_id).collection('sessions')

		sessions = sessions_ref.stream()

		sessions_list = []
		for session in sessions:
			session_data = session.to_dict()
			sessions_list.append(session_data)
			
		logger.info(f"Successfully fetched {len(sessions_list)} sessions for user {user_id}")
		return sessions_list
		
	except Exception as e:
		logger.error(f"Error fetching sessions for user {user_id}: {str(e)}")
		return []

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