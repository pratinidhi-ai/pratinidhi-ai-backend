"""
Math Tutor Routing Module
This module handles API endpoints for the math tutor feature.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import asyncio
from helper.middleware import authenticate_request
from math_tutor.math_tutor_response import generate_math_tutor_response, review_student_solution
from math_tutor.math_ai_video_generator import generate_math_ai_video
from math_tutor.process_video import process_knolify_video
from database.user_db import getUserbyId, record_trial_activity
from models.users_schema import User, TRIAL_MATH_SOLVER_LIMIT

logger = logging.getLogger(__name__)

math_tutor_router = APIRouter(prefix="/api/math_tutor", tags=["math_tutor"])


def _check_math_solver_trial_limit(user: dict) -> Optional[str]:
    """
    Raise 403 if the authenticated user is on trial and has used up their
    trial Math Solver attempts. Returns the user's uid for trial-usage
    recording after a successful solve (None if uid can't be resolved).
    """
    uid = user.get('uid')
    if not uid:
        return uid
    user_data = getUserbyId(uid)
    if user_data:
        user_obj = User.from_dict(user_data)
        if user_obj.is_on_trial() and user_obj.trial_math_solver_completed >= TRIAL_MATH_SOLVER_LIMIT:
            raise HTTPException(
                status_code=403,
                detail={
                    'error': 'Trial limit reached',
                    'message': 'You have used your trial Math Solver attempts. Upgrade to continue.'
                }
            )
    return uid


# Pydantic models for request/response
class MathProblemRequest(BaseModel):
    problem: Optional[str] = Field(None, description="The math problem to solve (text)")
    image: Optional[str] = Field(None, description="Base64 encoded image or data URI")
    max_tokens: Optional[int] = Field(4000, description="Maximum tokens for solution")
    temperature: Optional[float] = Field(0.3, description="Temperature for AI response")


class MathProblemWithVideoRequest(BaseModel):
    problem: str = Field(..., description="The math problem to solve")
    max_tokens: Optional[int] = Field(4000, description="Maximum tokens for solution")
    temperature: Optional[float] = Field(0.3, description="Temperature for AI response")
    generate_video: Optional[bool] = Field(True, description="Whether to generate video explanation")
    remove_watermark: Optional[bool] = Field(False, description="Whether to remove watermark from video")


class ReviewSolutionRequest(BaseModel):
    problem: Optional[str] = Field(None, description="The math problem text")
    problem_image: Optional[str] = Field(None, description="Base64 encoded image of the problem")
    solution: Optional[str] = Field(None, description="The student's solution text")
    solution_image: Optional[str] = Field(None, description="Base64 encoded image of the solution")
    max_tokens: Optional[int] = Field(4000, description="Maximum tokens for feedback")
    temperature: Optional[float] = Field(0.3, description="Temperature for AI response")


@math_tutor_router.post('/solve')
async def solve_math_problem(
    data: MathProblemRequest,
    user=Depends(authenticate_request)
):
    """
    Solve a math problem with step-by-step solution.
    Supports text, image, or both combined (text provides additional context with image).
    
    Expected JSON body (for text only):
    {
        "problem": "Solve for x: 2x + 5 = 15",
        "max_tokens": 4000 (optional),
        "temperature": 0.3 (optional)
    }
    
    Expected JSON body (for image only):
    {
        "image": "base64_encoded_image_or_data_uri",
        "max_tokens": 4000 (optional),
        "temperature": 0.3 (optional)
    }
    
    Expected JSON body (for image + text):
    {
        "image": "base64_encoded_image_or_data_uri",
        "problem": "Additional context or clarification",
        "max_tokens": 4000 (optional),
        "temperature": 0.3 (optional)
    }
    
    Returns:
        JSON response with step-by-step solution in LaTeX format
    """
    try:
        uid = _check_math_solver_trial_limit(user)

        # Extract inputs - either text problem or image
        math_problem = data.problem
        image_data = data.image

        # Validate that at least one input type is provided
        if not math_problem and not image_data:
            raise HTTPException(
                status_code=400,
                detail="Either 'problem' (text) or 'image' (base64) field is required"
            )
        
        if math_problem and image_data:
            raise HTTPException(
                status_code=400,
                detail="Provide either 'problem' OR 'image', not both"
            )
        
        # Determine input type for response
        if image_data and math_problem:
            input_type = "image+text"
        elif image_data:
            input_type = "image"
        else:
            input_type = "text"
        
        logger.info(f"Solving math problem from {input_type} input")
        
        # Generate solution (function handles both text and image)
        solution = await asyncio.to_thread(
            generate_math_tutor_response,
            math_problem=math_problem,
            image_data=image_data,
            max_tokens=data.max_tokens or 4000,
            temperature=data.temperature or 0.3
        )
        
        response_data = {
            "success": True,
            "solution": solution,
            "input_type": input_type
        }

        # Include the problem text in response if provided
        if math_problem:
            response_data["problem"] = math_problem

        if uid:
            record_trial_activity(uid, 'math_solver')

        return response_data
        
    except HTTPException:
        raise

    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(ve)}")

    except Exception as e:
        logger.error(f"Error solving math problem: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to solve math problem: {str(e)}")


@math_tutor_router.get('/health')
def health_check():
    """
    Health check endpoint for the math tutor service.
    """
    return {
        "status": "healthy",
        "service": "math-tutor"
    }


@math_tutor_router.post('/solve-with-video')
async def solve_math_problem_with_video(
    data: MathProblemWithVideoRequest,
    user=Depends(authenticate_request)
):
    """
    Solve a math problem with step-by-step solution AND generate an AI video explanation.
    
    Returns:
        JSON response with solution and video links
    """
    try:
        uid = _check_math_solver_trial_limit(user)

        logger.info(f"Solving math problem with video generation: {data.generate_video}")

        # Generate solution (run in thread pool to avoid blocking)
        solution = await asyncio.to_thread(
            generate_math_tutor_response,
            math_problem=data.problem,
            max_tokens=data.max_tokens or 4000,
            temperature=data.temperature or 0.3
        )
        
        response_data = {
            "success": True,
            "problem": data.problem,
            "solution": solution
        }
        
        # Generate video if requested
        if data.generate_video:
            try:
                logger.info("Generating AI video explanation...")
                video_result = await asyncio.to_thread(
                    generate_math_ai_video,
                    math_problem=data.problem
                )
                
                video_link = video_result.get("video_link")
                vtt_file = video_result.get("vtt_file")
                
                # Process video to remove watermark if requested
                if data.remove_watermark and video_link:
                    try:
                        logger.info("Removing watermark from video...")
                        processed_video_path = await asyncio.to_thread(
                            process_knolify_video,
                            video_link
                        )
                        
                        # TODO: Upload processed video to your own storage
                        # For now, return the local path
                        response_data["video"] = {
                            "video_link": video_link,  # Original video
                            "processed_video_path": processed_video_path,  # Local processed video
                            "vtt_file": vtt_file,
                            "status": video_result.get("status"),
                            "watermark_removed": True
                        }
                        logger.info("Watermark removed successfully")
                    except Exception as watermark_error:
                        logger.error(f"Watermark removal failed: {str(watermark_error)}")
                        response_data["video"] = {
                            "video_link": video_link,
                            "vtt_file": vtt_file,
                            "status": video_result.get("status"),
                            "watermark_removed": False,
                            "watermark_error": str(watermark_error)
                        }
                else:
                    response_data["video"] = {
                        "video_link": video_link,
                        "vtt_file": vtt_file,
                        "status": video_result.get("status")
                    }
                
                logger.info("Video generated successfully")
                
            except Exception as video_error:
                logger.error(f"Video generation failed: {str(video_error)}")
                response_data["video"] = {
                    "status": "failed",
                    "error": str(video_error)
                }

        if uid:
            record_trial_activity(uid, 'math_solver')

        return response_data

    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(ve)}")

    except Exception as e:
        logger.error(f"Error solving math problem: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to solve math problem: {str(e)}")


@math_tutor_router.post('/find-issues-in-solution')
async def find_issues_in_solution(
    data: ReviewSolutionRequest,
    user=Depends(authenticate_request)
):
    """
    Review a student's solution and identify mistakes.
    Supports text, image, or both combined for problem and solution.
    Text can provide additional context when used with images.
    
    Expected JSON body examples:
    
    1. Text problem + Text solution:
    {
        "problem": "Solve for x: 2x + 5 = 15",
        "solution": "2x + 5 = 15\\n2x = 10\\nx = 10",
        "max_tokens": 4000 (optional),
        "temperature": 0.3 (optional)
    }
    
    2. Image problem + Text solution:
    {
        "problem_image": "base64_encoded_image",
        "solution": "Step 1: ...",
        "max_tokens": 4000 (optional)
    }
    
    3. Text problem + Image solution:
    {
        "problem": "Solve for x: 2x + 5 = 15",
        "solution_image": "base64_encoded_image",
        "max_tokens": 4000 (optional)
    }
    
    4. Image problem + Image solution:
    {
        "problem_image": "base64_encoded_image",
        "solution_image": "base64_encoded_image",
        "max_tokens": 4000 (optional)
    }
    
    5. Image problem with text context + Image solution with notes:
    {
        "problem_image": "base64_encoded_image",
        "problem": "Additional context about the problem",
        "solution_image": "base64_encoded_image",
        "solution": "My notes about my solution",
        "max_tokens": 4000 (optional)
    }
    
    Returns:
        JSON response with detailed feedback on mistakes and corrections
    """
    try:
        # Extract problem inputs
        problem_text = data.problem
        problem_image = data.problem_image
        
        # Extract solution inputs
        solution_text = data.solution
        solution_image = data.solution_image
        
        # Validate that at least one problem input is provided
        if not problem_text and not problem_image:
            raise HTTPException(
                status_code=400,
                detail="At least one of 'problem' (text) or 'problem_image' (base64) is required"
            )
        
        # Validate that at least one solution input is provided
        if not solution_text and not solution_image:
            raise HTTPException(
                status_code=400,
                detail="At least one of 'solution' (text) or 'solution_image' (base64) is required"
            )
        
        # Determine input types for logging and response
        if problem_image and problem_text:
            problem_type = "image+text"
        elif problem_image:
            problem_type = "image"
        else:
            problem_type = "text"
        
        if solution_image and solution_text:
            solution_type = "image+text"
        elif solution_image:
            solution_type = "image"
        else:
            solution_type = "text"
        
        logger.info(f"Reviewing solution - Problem: {problem_type}, Solution: {solution_type}")
        
        # Review the solution (run in thread pool to avoid blocking)
        feedback = await asyncio.to_thread(
            review_student_solution,
            problem_text=problem_text,
            problem_image=problem_image,
            solution_text=solution_text,
            solution_image=solution_image,
            max_tokens=data.max_tokens or 4000,
            temperature=data.temperature or 0.3
        )
        
        response_data = {
            "success": True,
            "feedback": feedback,
            "input_types": {
                "problem": problem_type,
                "solution": solution_type
            }
        }
        
        # Include original texts in response if provided
        if problem_text:
            response_data["problem"] = problem_text
        if solution_text:
            response_data["solution"] = solution_text
        
        return response_data
        
    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(ve)}")
        
    except Exception as e:
        logger.error(f"Error reviewing solution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to review solution: {str(e)}")
