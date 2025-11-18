from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.firebase_client import get_auth
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def authenticate_request(credentials: HTTPAuthorizationCredentials = Depends(security)):
	"""
	FastAPI dependency for authenticating requests using Firebase ID tokens.
	Usage: Add as a dependency to your route: async def my_route(user = Depends(authenticate_request))
	"""
	id_token = credentials.credentials
	print(id_token)
	
	try:
		# Get Firebase Auth instance
		auth = get_auth()
		# The decoded token contains user info like UID, email, etc.
		decoded_token = auth.verify_id_token(id_token)
		
		# Return the decoded token which can be used in the route
		return decoded_token

	except auth.InvalidIdTokenError as e:
		# Token is invalid, malformed, or has an incorrect signature.
		logger.error(f"Invalid ID token: {e}")
		raise HTTPException(status_code=401, detail="The provided token is invalid")
	
	except auth.ExpiredIdTokenError as e:
		logger.warning(f"Expired ID token: {e}")
		raise HTTPException(status_code=401, detail="The provided token has expired")
	
	except Exception as e:
		logger.error(f"An unexpected error occurred during token verification: {e}")
		raise HTTPException(status_code=500, detail="An unexpected error occurred")
