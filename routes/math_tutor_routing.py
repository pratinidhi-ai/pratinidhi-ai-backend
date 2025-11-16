"""
Math Tutor Routing Module
This module handles API endpoints for the math tutor feature.
"""
from flask import Blueprint, request, jsonify
import logging
from helper.middleware import authenticate_request
from math_tutor.math_tutor_response import generate_math_tutor_response
from math_tutor.math_ai_video_generator import generate_math_ai_video
from math_tutor.process_video import process_knolify_video

logger = logging.getLogger(__name__)
math_tutor_bp = Blueprint('math_tutor', __name__)


@math_tutor_bp.route('/solve', methods=['POST'])
@authenticate_request
def solve_math_problem():
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
        return jsonify({
            "error": "Validation error",
            "details": str(ve)
        }), 400
        
    except Exception as e:
        logger.error(f"Error solving math problem: {str(e)}")
        return jsonify({
            "error": "Failed to solve math problem",
            "details": str(e)
        }), 500


@math_tutor_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for the math tutor service.
    """
    return jsonify({
        "status": "healthy",
        "service": "math-tutor"
    }), 200


@math_tutor_bp.route('/solve-with-video', methods=['POST'])
@authenticate_request
def solve_math_problem_with_video():
    """
    Solve a math problem with step-by-step solution AND generate an AI video explanation.
    
    Expected JSON body:
    {
        "problem": "Solve for x: 2x + 5 = 15",
        "max_tokens": 4000 (optional),
        "temperature": 0.3 (optional),
        "generate_video": true (optional, default: true)
    }
    
    Returns:
        JSON response with solution and video links
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract math problem
        math_problem = data.get("problem")
        if not math_problem:
            return jsonify({"error": "Problem field is required"}), 400
        
        # Extract optional parameters with defaults
        max_tokens = data.get("max_tokens", 4000)
        temperature = data.get("temperature", 0.3)
        generate_video = data.get("generate_video", True)
        remove_watermark = data.get("remove_watermark", False)  # New parameter
        
        logger.info(f"Solving math problem with video generation: {generate_video}")
        
        # Generate solution
        solution = generate_math_tutor_response(
            math_problem=math_problem,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        response_data = {
            "success": True,
            "problem": math_problem,
            "solution": solution
        }
        
        # Generate video if requested
        if generate_video:
            try:
                logger.info("Generating AI video explanation...")
                video_result = generate_math_ai_video(
                    math_problem=math_problem
                )
                
                video_link = video_result.get("video_link")
                vtt_file = video_result.get("vtt_file")
                
                # Process video to remove watermark if requested
                if remove_watermark and video_link:
                    try:
                        logger.info("Removing watermark from video...")
                        processed_video_path = process_knolify_video(video_link)
                        
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
        
        return jsonify(response_data), 200
        
    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        return jsonify({
            "error": "Validation error",
            "details": str(ve)
        }), 400
        
    except Exception as e:
        logger.error(f"Error solving math problem: {str(e)}")
        return jsonify({
            "error": "Failed to solve math problem",
            "details": str(e)
        }), 500
