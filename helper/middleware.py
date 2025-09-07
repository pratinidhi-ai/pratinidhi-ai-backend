from functools import wraps
from flask import request , jsonify
from firebase_admin import auth

def authenticate_request(f) :
	@wraps(f)
	def decorated_check_function(*args, **kwargs):
		auth_header = request.headers.get("Authorization", None)
		if not auth_header or not auth_header.startswith("Bearer "):
			return jsonify({"error": "Missing or invalid token"}), 401
		id_token = auth_header.split(" ")[1]
		try:
			decoded_token = auth.verify_id_token(id_token=id_token)
			request.user = decoded_token #new field to keep track of uid etc.
		except Exception as e:
			print(e) #add logging later
			return jsonify({"error":"Invalid Token"})
		return f(*args, **kwargs)
	return decorated_check_function
			 