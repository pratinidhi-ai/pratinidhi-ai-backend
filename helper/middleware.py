from functools import wraps
from flask import request , jsonify , current_app
from firebase_admin import auth
import logging

logger = logging.getLogger(__name__)

def authenticate_request(f) :
	@wraps(f)
	def decorated_check_function(*args, **kwargs):
		auth_header = request.headers.get("Authorization", None)
		if not auth_header or not auth_header.startswith("Bearer "):
			return jsonify({"error": "Missing or invalid token"}), 401
		id_token = auth_header.split(" ")[1]
		print(id_token)
		try:
			# The decoded token contains user info like UID, email, etc.
			decoded_token = auth.verify_id_token(id_token)
			
			# 4. Attach user data to the request object for use in the route
			request.user = decoded_token

		except auth.InvalidIdTokenError as e:
			# Token is invalid, malformed, or has an incorrect signature.
			current_app.logger.error(f"Invalid ID token: {e}")
			return jsonify({"error": "The provided token is invalid"}), 401
		
		except auth.ExpiredIdTokenError as e:
			current_app.logger.warning(f"Expired ID token: {e}")
			return jsonify({"error": "The provided token has expired"}), 401
		
		except Exception as e:

			current_app.logger.error(f"An unexpected error occurred during token verification: {e}")
			return jsonify({"error": "An unexpected error occurred"}), 500

		return f(*args, **kwargs)
	return decorated_check_function
			 