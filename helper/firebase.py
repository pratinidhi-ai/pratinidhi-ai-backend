import firebase_admin
from firebase_admin import credentials , firestore , auth
import os
import logging


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