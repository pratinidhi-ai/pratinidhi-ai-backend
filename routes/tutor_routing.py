from flask import Blueprint , request , jsonify
import uuid , time
from collections import defaultdict
import logging
from models.tutor_session_schema import TutorSession
from helper.ai_api import *
from helper.middleware import authenticate_request
from helper.firebase import saveSessionSummary , _getUserSessions
sessions = {}
logger = logging.getLogger(__name__)
tutor_bp = Blueprint('tutor' , __name__ , url_prefix='/tutor')

@tutor_bp.route('/start-session' , methods = ['POST'])
@authenticate_request
def start_session():
	try:
		data = request.json
		session_id = str(uuid.uuid4())
		session = TutorSession(
			user_id=data["user_id"],
			personality=data["personality"],
			language=data["language"],
			session_id = session_id
		)
		sessions[session_id] = session
		return jsonify({"session_id": session_id}), 200
	except Exception as e:
		logger.error(e)
		return jsonify({"_error" : "Can't Create Session"}) , 500
	
@tutor_bp.route('/<session_id>/message', methods=['POST'])
@authenticate_request
def session_message(session_id):
    data = request.json
    session = sessions.get(session_id)
    if not session or not session.is_active:
        return jsonify({"error": "Session not found or ended"}), 404
    

    session.messages.append({"role": "user", "content": data["message"]})
    session.messages = session.messages[-20:]  # Keep last 20 messages
    
    # Get AI response
    ai_response = call_openai_api(session)
    
    session.messages.append({"role": "assistant", "content": ai_response})
    session.length += 2
    
    if session.length >= 100:
        session.is_active = False
        session.ended_at = time.time()
        session.summary = generate_summary(session.messages)
        saveSessionSummary(session=session)
        del sessions[session_id]
    
    return jsonify({"ai_response": ai_response, "session_active": session.is_active})



@tutor_bp.route('/<session_id>/end', methods=['POST'])
@authenticate_request
def end_session(session_id):
	try:
		session = sessions.get(session_id)
		if not session:
			return jsonify({"error": "Session not found"}), 404
		
		if not session.is_active:
			return jsonify({"error": "Session already ended"}), 400
		
		session.is_active = False
		session.ended_at = time.time()
		session.summary = generate_summary(session.messages)
		
		response_data = {
			"success": True,
			"summary": session.summary,
			"total_messages": session.length
		}
		if not saveSessionSummary(session=session):
			logger.warning("Error in storing user session summary.")
		del sessions[session_id]
		return jsonify(response_data), 200
		
	except Exception as e:
		logger.error(f"Error ending session {session_id}: {str(e)}")
		return jsonify({"error": "Failed to end session"}), 500

@tutor_bp.route('/<user_id>' , methods = ['GET'])
@authenticate_request
def getUserSessions(user_id):
    try:
        sessions_list = _getUserSessions(user_id)
        
        if not sessions_list:
            return jsonify({
                "message": "No sessions found",
                "sessions": []
            }), 200
            
        return jsonify({
            "message": "Sessions retrieved successfully",
            "sessions": sessions_list
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching sessions for user {user_id}: {str(e)}")
        return jsonify({
            "error": "Failed to fetch user sessions"
        }), 500
