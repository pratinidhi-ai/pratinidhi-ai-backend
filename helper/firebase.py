import firebase_admin
from firebase_admin import credentials , firestore
import os

dir = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(dir,'..','dev-private-keys.json')
cred = credentials.Certificate(key_path)

firebase_admin.initialize_app(cred)

db = firestore.client()

def getUsers() -> list:
	users_collection = db.collection('users').where('active', '==', True)
	docs = users_collection.stream()
	users_list = []
	for doc in docs:
		users_list.append(doc.to_dict())
	return users_list
