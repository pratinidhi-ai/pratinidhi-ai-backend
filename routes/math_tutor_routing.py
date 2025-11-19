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
from math_tutor.math_tutor_response import generate_math_tutor_response
from math_tutor.math_ai_video_generator import generate_math_ai_video
from math_tutor.process_video import process_knolify_video

logger = logging.getLogger(__name__)

math_tutor_router = APIRouter(prefix="/api/math-tutor", tags=["math-tutor"])


# Pydantic models for request/response
class MathProblemRequest(BaseModel):
    problem: str = Field(..., description="The math problem to solve")
    max_tokens: Optional[int] = Field(4000, description="Maximum tokens for solution")
    temperature: Optional[float] = Field(0.3, description="Temperature for AI response")


class MathProblemWithVideoRequest(BaseModel):
    problem: str = Field(..., description="The math problem to solve")
    max_tokens: Optional[int] = Field(4000, description="Maximum tokens for solution")
    temperature: Optional[float] = Field(0.3, description="Temperature for AI response")
    generate_video: Optional[bool] = Field(True, description="Whether to generate video explanation")
    remove_watermark: Optional[bool] = Field(False, description="Whether to remove watermark from video")


@math_tutor_router.post('/solve')
async def solve_math_problem(
    data: MathProblemRequest,
    user=Depends(authenticate_request)
):
    """
    Solve a math problem with step-by-step solution.
    
    Returns:
        JSON response with step-by-step solution in LaTeX format
    """
    try:
        logger.info(f"Solving math problem")
        
        # Generate solution (run in thread pool to avoid blocking)
        solution = await asyncio.to_thread(
            generate_math_tutor_response,
            math_problem=data.problem,
            max_tokens=data.max_tokens,
            temperature=data.temperature
        )
        
        return {
            "success": True,
            "problem": data.problem,
            "solution": solution
        }
        
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
        logger.info(f"Solving math problem with video generation: {data.generate_video}")
        
        # Generate solution (run in thread pool to avoid blocking)
        solution = await asyncio.to_thread(
            generate_math_tutor_response,
            math_problem=data.problem,
            max_tokens=data.max_tokens,
            temperature=data.temperature
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
        
        return response_data
        
    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(ve)}")
        
    except Exception as e:
        logger.error(f"Error solving math problem: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to solve math problem: {str(e)}")
