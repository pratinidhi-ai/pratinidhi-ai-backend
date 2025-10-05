import redis
import pickle
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT',6379))
REDIS_DB = int(os.getenv('REDIS_DB',0))
USE_SSL = REDIS_HOST!= 'localhost'

class RedisSessionManager:
	def __init__(self, session_expiry_seconds=86400):
		try:
			self.redis_client = redis.Redis(
				host=REDIS_HOST,
				db=REDIS_DB,
				port=REDIS_PORT,
				decode_responses=False,
				ssl= USE_SSL
			)
			self.redis_client.ping()
			logger.info("Successfully connected to Redis.")
		except redis.exceptions.ConnectionError as e:
			logger.error(f"Couldn't Connect to redis : {e}")
			raise e
		self.session_expiry = session_expiry_seconds
	
	def save_session(self, session_id, session):
		try:
			pickled_session = pickle.dumps(session)
			self.redis_client.set(session_id, pickled_session, ex=self.session_expiry)
			logger.debug(f"Session saved with ID: {session_id}")
			return True
		except Exception as e:
			logger.error(f"Failed to save session {session_id} to Redis: {e}")
			return False
	
	def get_session(self, session_id):
		try:
			pickled_session = self.redis_client.get(session_id)
			if not pickled_session:
				logger.warning(f"Session not found with ID: {session_id}")
				return None
			session_object = pickle.loads(pickled_session)
			return session_object
		except Exception as e:
			logger.error(f"Failed to get or deserialize session {session_id} from Redis {e}")
			return None
		
	def delete_session(self, session_id):
		try:
			self.redis_client.delete(session_id)
			logger.info(f"Session deleted with ID: {session_id}")
			return True
		except Exception as e:
			logger.error(f"Failed to delete session {session_id} from Redis: {e}")
			return False
		
redis_session_manager = RedisSessionManager()