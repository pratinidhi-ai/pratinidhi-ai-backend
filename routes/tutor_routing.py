from flask import Blueprint , request , jsonify
import uuid , time
from collections import defaultdict
import logging
from models.tutor_session_schema import TutorSession
from helper.ai_api import *

sessions = {}
logger = logging.getLogger(__name__)
tutor_bp = Blueprint('tutor' , __name__ , url_prefix='/tutor')

@tutor_bp.route('/start-session' , methods = ['POST'])
def start_session():
	try:
		data = request.json
		session_id = str(uuid.uuid4())
		session = TutorSession(
			user_id=data["user_id"],
			personality=data["personality"],
			language=data["language"]
		)
		sessions[session_id] = session
		return jsonify({"session_id": session_id}), 200
	except Exception as e:
		logger.error(e)
		return jsonify({"_error" : "Can't Create Session"}) , 500
	
@tutor_bp.route('/<session_id>/message', methods=['POST'])
def session_message(session_id):
	data = request.json
	session = sessions.get(session_id)
	if not session or not session.is_active:
		return jsonify({"error": "Session not found or ended"}), 404
	session.messages.append({"role": "user", "content": data["message"]})
	session.messages = session.messages[-20:]
	ai_response = call_openai_api(session)
	session.messages.append(ai_response)
	session.messages.append({"role": "ai_tutor", "content": ai_response})
	session.length += 2
	if session.length >= 100:
		session.is_active = False
		session.ended_at = time.time()
		session.summary =  generate_summary(session.messages)
		# now store to DB
	return jsonify({"ai_response": ai_response, "session_active" : session.is_active})


