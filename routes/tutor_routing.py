from flask import Blueprint , request , jsonify
import uuid , time
from collections import defaultdict
import logging
from models.tutor_session_schema import TutorSession
from ai.ai_api import *
from helper.middleware import authenticate_request
from helper.firebase import saveSessionSummary, _getUserSessions, userStartSession
from database.session_db import saveSessionSummary, _getUserSessions
from helper.prompt_builder import PromptBuilder
from helper.redis_sessions import redis_session_manager ,REDIS_HOST, REDIS_PORT


sessions = {}
logger = logging.getLogger(__name__)
tutor_bp = Blueprint('tutor' , __name__ , url_prefix='/tutor')

@tutor_bp.route('/start-session' , methods = ['POST'])
@authenticate_request
def start_session():
	try:
		data = request.json
		if not data:
			return jsonify({"error": "No JSON data provided"}), 400
			
		session_id = str(uuid.uuid4())
		
		# Extract session parameters
		user_id = data.get("user_id")
		if not user_id:
			return jsonify({"error": "user_id is required"}), 400

		if not userStartSession(user_id=user_id):
			return jsonify({"error": "You Have Used up the quota of allotted sessions"}) ,403

		personality = data.get("personality", "albert_einstein")  # Default personality
		language = data.get("language", "english")
		subject = data.get("subject")
		level = data.get("level")
		exam = data.get("exam")
		interests = data.get("interests", [])
		goals = data.get("goals", [])
		lecture_notes = data.get("lecture_notes")
		lecture_subject = data.get("lecture_subject")  # e.g., "SAT"
		lecture_chapter = data.get("lecture_chapter")  # e.g., "Chapter 1"
		
		# Build system prompt
		prompt_builder = PromptBuilder()
		system_prompt = prompt_builder.build_system_prompt(
			personality=personality,
			subject=subject,
			level=level,
			exam=exam,
			interests=interests,
			goals=goals,
			lecture_notes=lecture_notes,
			lecture_subject=lecture_subject,
			lecture_chapter=lecture_chapter
		)
		
		# Create session with all parameters
		session = TutorSession(
			user_id=user_id,
			personality=personality,
			language=language,
			session_id=session_id,
			subject=subject,
			level=level,
			exam=exam,
			interests=interests,
			goals=goals,
			lecture_notes=lecture_notes,
			lecture_subject=lecture_subject,
			lecture_chapter=lecture_chapter,
			session_system_prompt=system_prompt
		)
		redis_session_manager.save_session(session_id, session)
		# sessions[session_id] = session
		return jsonify({
			"session_id": session_id,
			"system_prompt": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt
		}), 200
	except Exception as e:
		logger.error(f"Error creating session: {str(e)}")
		return jsonify({"error": "Can't Create Session", "details": str(e)}), 500
	

@tutor_bp.route('/<session_id>/message', methods=['POST'])
@authenticate_request
def session_message(session_id):
	try:
		data = request.json
		if not data:
			return jsonify({"error": "No JSON data provided"}), 400
		
		logger.info(f"Step 1: Getting session {session_id}")
		session = redis_session_manager.get_session(session_id)
		
		if not session or not session.is_active:
			return jsonify({"error": "Session not found or ended"}), 404
		
		user_message = data.get("message")
		if not user_message:
			return jsonify({"error": "Message content is required"}), 400

		use_rag = data.get("use_rag", False)
		
		session.messages.append({"role": "user", "content": user_message})
		session.messages = session.messages[-20:]
		
		logger.info("Step 2: Calling OpenAI API")
		try:
			ai_response = call_openai_api(session, use_rag)
			logger.info(f"OpenAI API call successful, response length: {len(ai_response)}")
		except Exception as openai_error:
			logger.exception(f"OpenAI API call failed: {str(openai_error)}")
			return jsonify({
				"error": "OpenAI API call failed",
				"details": str(openai_error),
				"error_type": type(openai_error).__name__
			}), 500
		
		session.messages.append({"role": "assistant", "content": ai_response})
		session.length += 2
		
		if session.length >= 100:
			session.is_active = False
			session.ended_at = time.time()
			session.summary = generate_summary(session.messages)
			saveSessionSummary(session=session)
			redis_session_manager.delete_session(session_id)
		else:
			redis_session_manager.save_session(session_id, session)

		return jsonify({
			"ai_response": ai_response, 
			"session_active": session.is_active,
			"message_count": session.length
		})
		
	except Exception as e:
		logger.exception(f"Error in session message {session_id}")
		return jsonify({"error": "Failed to process message", "details": str(e)}), 500


@tutor_bp.route('/<session_id>/end', methods=['POST'])
@authenticate_request
def end_session(session_id):
	try:
		session = redis_session_manager.get_session(session_id)
		# session = sessions.get(session_id)
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
		# del sessions[session_id]
		redis_session_manager.delete_session(session_id)
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

import time

@tutor_bp.route('/redis-health', methods=['GET'])
def redis_health():
    try:
        start_time = time.time()
        result = redis_session_manager.redis_client.ping()
        latency = (time.time() - start_time) * 1000
        
        return jsonify({
            "status": "healthy",
            "redis_host": REDIS_HOST,
            "redis_port": REDIS_PORT,
            "latency_ms": round(latency, 2),
            "ping_result": result
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__,
            "redis_host": REDIS_HOST,
            "redis_port": REDIS_PORT
        }), 500