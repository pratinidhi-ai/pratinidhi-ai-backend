import redis
import pickle
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
USE_SSL = '.cache.amazonaws.com' in REDIS_HOST

class RedisSessionManager:
    def __init__(self, session_expiry_seconds=86400):
        self.session_expiry = session_expiry_seconds
        connection_kwargs = {
            'host': REDIS_HOST,
            'port': REDIS_PORT,
            'db': REDIS_DB,
            'decode_responses': False,
            'socket_timeout': 5,  
            'socket_connect_timeout': 5,  
            'socket_keepalive': True,
            'retry_on_timeout': True,  
            'max_connections': 10,
            'health_check_interval': 15
        }

        if USE_SSL:
            self.redis_client = redis.Redis(
                connection_pool=redis.ConnectionPool(
                    connection_class=redis.SSLConnection,
                    ssl_cert_reqs='none',
                    **connection_kwargs
                )
            )
        else:
            self.redis_client = redis.Redis(**connection_kwargs)
        
        try:
            self.redis_client.ping()
            logger.info(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")

    
    def _test_connection(self):
        """Test if Redis is actually reachable"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            return False

    def save_session(self, session_id, session):
        try:
            if not self._test_connection():
                logger.error("Redis not reachable before save")
                return False
                
            pickled_session = pickle.dumps(session)
            self.redis_client.set(session_id, pickled_session, ex=self.session_expiry)
            logger.info(f"Session saved with ID: {session_id}")
            return True
        except redis.TimeoutError as e:
            logger.error(f"Redis timeout saving session {session_id}: {e}")
            return False
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error saving session {session_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to save session {session_id} to Redis: {e}")
            return False
    
    def get_session(self, session_id):
        try:
            if not self._test_connection():
                logger.error("Redis not reachable before get")
                return None
                
            pickled_session = self.redis_client.get(session_id)
            if not pickled_session:
                logger.warning(f"Session not found with ID: {session_id}")
                return None
            session_object = pickle.loads(pickled_session)
            logger.info(f"Session retrieved with ID: {session_id}")
            return session_object
        except redis.TimeoutError as e:
            logger.error(f"Redis timeout getting session {session_id}: {e}")
            return None
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error getting session {session_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id} from Redis: {e}")
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