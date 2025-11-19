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
    Supports both text and image inputs.
    
    Expected JSON body (for text):
    {
        "problem": "Solve for x: 2x + 5 = 15",
        "max_tokens": 4000 (optional),
        "temperature": 0.3 (optional)
    }
    
    Expected JSON body (for image):
    {
        "image": "base64_encoded_image_or_data_uri",
        "max_tokens": 4000 (optional),
        "temperature": 0.3 (optional)
    }
    
    Returns:
        JSON response with step-by-step solution in LaTeX format
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract inputs - either text problem or image
        math_problem = data.get("problem")
        image_data = data.get("image")
        
        # Validate that exactly one input type is provided
        if not math_problem and not image_data:
            return jsonify({
                "error": "Either 'problem' (text) or 'image' (base64) field is required"
            }), 400
        
        if math_problem and image_data:
            return jsonify({
                "error": "Provide either 'problem' OR 'image', not both"
            }), 400
        
        # Extract optional parameters with defaults
        max_tokens = data.get("max_tokens", 4000)
        temperature = data.get("temperature", 0.3)
        
        input_type = "text" if math_problem else "image"
        logger.info(f"Solving math problem from {input_type} input")
        
        # Generate solution (function handles both text and image)
        solution = generate_math_tutor_response(
            math_problem=math_problem,
            image_data=image_data,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        response_data = {
            "success": True,
            "solution": solution,
            "input_type": input_type
        }
        
        # Include the problem text in response if provided
        if math_problem:
            response_data["problem"] = math_problem
        
        return jsonify(response_data), 200
        
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
