from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid, time
from collections import defaultdict
import logging
from models.tutor_session_schema import TutorSession
from ai.ai_api import *
from helper.middleware import authenticate_request
from database.user_db import userStartSession
from database.session_db import saveSessionSummary, _getUserSessions
from helper.prompt_builder import PromptBuilder
from helper.redis_sessions import get_redis_session_manager, REDIS_HOST, REDIS_PORT

logger = logging.getLogger(__name__)
tutor_router = APIRouter(prefix="/api/tutor", tags=["tutor"])


# Pydantic models for request validation
class StartSessionRequest(BaseModel):
    user_id: str
    personality: str = Field(default="albert_einstein")
    language: str = Field(default="english")
    subject: Optional[str] = None
    exam: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    lecture_notes: Optional[str] = None
    lecture_subject: Optional[str] = None
    lecture_chapter: Optional[str] = None


class SessionMessageRequest(BaseModel):
    message: str
    use_rag: bool = Field(default=False)


@tutor_router.post('/start-session', status_code=status.HTTP_200_OK)
async def start_session(request_data: StartSessionRequest, user: dict = Depends(authenticate_request)):
    try:
        user_id = request_data.user_id
        
        if not await userStartSession(user_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "You Have Used up the quota of allotted sessions"}
            )

        session_id = str(uuid.uuid4())
        
        # Build system prompt
        prompt_builder = PromptBuilder()
        system_prompt = prompt_builder.build_system_prompt(
            personality=request_data.personality,
            subject=request_data.subject,
            exam=request_data.exam,
            interests=request_data.interests,
            goals=request_data.goals,
            lecture_notes=request_data.lecture_notes,
            lecture_subject=request_data.lecture_subject,
            lecture_chapter=request_data.lecture_chapter
        )
        
        # Create session with all parameters
        session = TutorSession(
            user_id=user_id,
            personality=request_data.personality,
            language=request_data.language,
            session_id=session_id,
            subject=request_data.subject,
            exam=request_data.exam,
            interests=request_data.interests,
            goals=request_data.goals,
            lecture_notes=request_data.lecture_notes,
            lecture_subject=request_data.lecture_subject,
            lecture_chapter=request_data.lecture_chapter,
            session_system_prompt=system_prompt
        )
        await get_redis_session_manager().save_session(session_id, session)
        
        return {
            "session_id": session_id,
            "system_prompt": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Can't Create Session", "details": str(e)}
        )


@tutor_router.post('/{session_id}/message', status_code=status.HTTP_200_OK)
async def session_message(
    session_id: str,
    request_data: SessionMessageRequest,
    user: dict = Depends(authenticate_request)
):
    try:
        logger.info(f"Step 1: Getting session {session_id}")
        session = await get_redis_session_manager().get_session(session_id)
        
        if not session or not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Session not found or ended"}
            )
        
        user_message = request_data.message
        use_rag = request_data.use_rag
        
        session.messages.append({"role": "user", "content": user_message})
        session.messages = session.messages[-20:]
        
        logger.info("Step 2: Calling OpenAI API")
        try:
            ai_response = await call_openai_api(session, use_rag)
            logger.info(f"OpenAI API call successful, response length: {len(ai_response)}")
        except Exception as openai_error:
            logger.exception(f"OpenAI API call failed: {str(openai_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "OpenAI API call failed",
                    "details": str(openai_error),
                    "error_type": type(openai_error).__name__
                }
            )
        
        session.messages.append({"role": "assistant", "content": ai_response})
        session.length += 2
        
        if session.length >= 100:
            session.is_active = False
            session.ended_at = time.time()
            session.summary = await generate_summary(session.messages)
            await saveSessionSummary(session=session)
            await get_redis_session_manager().delete_session(session_id)
        else:
            await get_redis_session_manager().save_session(session_id, session)

        return {
            "ai_response": ai_response, 
            "session_active": session.is_active,
            "message_count": session.length
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in session message {session_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to process message", "details": str(e)}
        )


@tutor_router.post('/{session_id}/end', status_code=status.HTTP_200_OK)
async def end_session(session_id: str, user: dict = Depends(authenticate_request)):
    try:
        session = await get_redis_session_manager().get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Session not found"}
            )
        
        if not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Session already ended"}
            )
        
        session.is_active = False
        session.ended_at = time.time()
        session.summary = await generate_summary(session.messages)
        
        response_data = {
            "success": True,
            "summary": session.summary,
            "total_messages": session.length
        }
        if not await saveSessionSummary(session=session):
            logger.warning("Error in storing user session summary.")
        
        await get_redis_session_manager().delete_session(session_id)
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to end session"}
        )


@tutor_router.get('/{user_id}', status_code=status.HTTP_200_OK)
async def get_user_sessions(user_id: str, user: dict = Depends(authenticate_request)):
    try:
        sessions_list = await _getUserSessions(user_id)
        
        return {
            "message": "Sessions retrieved successfully" if sessions_list else "No sessions found",
            "sessions": sessions_list or []
        }
        
    except Exception as e:
        logger.error(f"Error fetching sessions for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to fetch user sessions"}
        )


@tutor_router.get('/redis-health', status_code=status.HTTP_200_OK)
async def redis_health():
    try:
        start_time = time.time()
        result = await get_redis_session_manager().redis_client.ping()
        latency = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "redis_host": REDIS_HOST,
            "redis_port": REDIS_PORT,
            "latency_ms": round(latency, 2),
            "ping_result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__,
                "redis_host": REDIS_HOST,
                "redis_port": REDIS_PORT
            }
        )