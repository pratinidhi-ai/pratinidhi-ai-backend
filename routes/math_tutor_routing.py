"""
Math Tutor Routing Module
This module handles API endpoints for the math tutor feature.
"""
from flask import Blueprint, request, jsonify
import logging
from helper.middleware import authenticate_request
from math_tutor.math_tutor_response import generate_math_tutor_response, review_student_solution
from math_tutor.math_ai_video_generator import generate_math_ai_video
from math_tutor.process_video import process_knolify_video

logger = logging.getLogger(__name__)
math_tutor_bp = Blueprint('math_tutor', __name__)


@math_tutor_bp.route('/solve', methods=['POST'])
@authenticate_request
def solve_math_problem():
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
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract inputs - text problem and/or image
        math_problem = data.get("problem")
        image_data = data.get("image")
        
        # Validate that at least one input type is provided
        if not math_problem and not image_data:
            return jsonify({
                "error": "At least one of 'problem' (text) or 'image' (base64) is required"
            }), 400
        
        # Extract optional parameters with defaults
        max_tokens = data.get("max_tokens", 4000)
        temperature = data.get("temperature", 0.3)
        
        # Determine input type for response
        if image_data and math_problem:
            input_type = "image+text"
        elif image_data:
            input_type = "image"
        else:
            input_type = "text"
        
        logger.info(f"Solving math problem from {input_type} input")
        
        # Generate solution (function handles text, image, or both)
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


@math_tutor_bp.route('/find-issues-in-solution', methods=['POST'])
@authenticate_request
def find_issues_in_solution():
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
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract problem inputs
        problem_text = data.get("problem")
        problem_image = data.get("problem_image")
        
        # Extract solution inputs
        solution_text = data.get("solution")
        solution_image = data.get("solution_image")
        
        # Validate that at least one problem input is provided
        if not problem_text and not problem_image:
            return jsonify({
                "error": "At least one of 'problem' (text) or 'problem_image' (base64) is required"
            }), 400
        
        # Validate that at least one solution input is provided
        if not solution_text and not solution_image:
            return jsonify({
                "error": "At least one of 'solution' (text) or 'solution_image' (base64) is required"
            }), 400
        
        # Extract optional parameters
        max_tokens = data.get("max_tokens", 4000)
        temperature = data.get("temperature", 0.3)
        
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
        
        # Review the solution
        feedback = review_student_solution(
            problem_text=problem_text,
            problem_image=problem_image,
            solution_text=solution_text,
            solution_image=solution_image,
            max_tokens=max_tokens,
            temperature=temperature
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
        
        return jsonify(response_data), 200
        
    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        return jsonify({
            "error": "Validation error",
            "details": str(ve)
        }), 400
        
    except Exception as e:
        logger.error(f"Error reviewing solution: {str(e)}")
        return jsonify({
            "error": "Failed to review solution",
            "details": str(e)
        }), 500
