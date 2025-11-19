"""
Math Tutor Response Module
This module provides functionality to generate step-by-step solutions for math problems using LLM.
"""
import logging
import base64
import re
from ai_utils.gen_ai_functions import generate_gpt_response_from_message

logger = logging.getLogger(__name__)

MATH_TUTOR_LLM = "openai"
MATH_TUTOR_MODEL = "gpt-4o"

MATH_TUTOR_SYSTEM_PROMPT = (
    "As a math specialist, your task is to provide step-by-step solutions in latex for a given math question. "
    "Please answer the question step by step. Please be CAREFUL and think twice about calculations. "
    "You'd better make sure the calculation is correct. Please keep it short and concise."
)

MATH_TUTOR_VISION_SYSTEM_PROMPT = (
    "As a math specialist, analyze the math problem shown in the image and provide a step-by-step solution in LaTeX format. "
    "First, identify and transcribe the problem clearly. Then solve it step by step. "
    "Please be CAREFUL and think twice about calculations. Please keep it short and concise."
    "If the provided text is not a math problem, respond with 'The provided input is not a math problem.'"
)

SOLUTION_REVIEW_SYSTEM_PROMPT = (
    "As a math specialist and tutor, your task is to review a student's solution to a math problem and provide a step-by-step solution in LaTeX format."
    "Carefully analyze their work and identify any mistakes, misconceptions, or errors. "
    "For each mistake found: "
    "1. Point out exactly where the error occurred "
    "2. Explain why it's incorrect "
    "3. Show the correct approach from that point onwards "
    "If the solution is correct, acknowledge it and provide positive feedback. "
    "Format your response in LaTeX. Be constructive and educational in your feedback."
    "If the provided text is not a math problem, respond with 'The provided input is not a math problem.'"
)


def _validate_base64_image(image_data):
    """Validate base64 image data.
    
    Args:
        image_data (str): Base64 encoded image with or without data URI prefix
    
    Returns:
        str: Properly formatted data URI for the image
        
    Raises:
        ValueError: If image data is invalid
    """
    if not image_data or not image_data.strip():
        raise ValueError("Image data cannot be empty")
    
    # If already has data URI prefix, validate it
    if image_data.startswith('data:image/'):
        # Check if it has the proper format
        if ';base64,' not in image_data:
            raise ValueError("Invalid data URI format. Expected 'data:image/<type>;base64,<data>'")
        return image_data
    
    # Try to decode to validate it's proper base64
    try:
        base64.b64decode(image_data, validate=True)
    except Exception as e:
        raise ValueError(f"Invalid base64 encoding: {str(e)}")
    
    # Add data URI prefix (default to jpeg)
    return f"data:image/jpeg;base64,{image_data}"


def generate_math_tutor_response(math_problem=None, image_data=None, max_tokens=4000, temperature=0.3):
    """
    Generate a step-by-step solution for a given math problem using an LLM.
    Supports text input, image input, or both combined (via vision-capable LLM).
    
    Args:
        math_problem (str, optional): The math problem text (can be used alone or with image for additional context)
        image_data (str, optional): Base64 encoded image of the math problem (can be used alone or with text)
        max_tokens (int): Maximum tokens for the response (default: 4000)
        temperature (float): Temperature for response generation (default: 0.3)
    
    Returns:
        str: The step-by-step solution in LaTeX format
        
    Raises:
        ValueError: If neither math_problem nor image_data is provided
        Exception: If LLM call fails
    """
    # Validate inputs - at least one must be provided
    if not math_problem and not image_data:
        raise ValueError("At least one of math_problem (text) or image_data (base64 image) must be provided")
    
    # Handle text-only problem
    if math_problem and not image_data:
        if not math_problem.strip():
            raise ValueError("Math problem cannot be empty")
        
        messages = [
            {"role": "system", "content": MATH_TUTOR_SYSTEM_PROMPT},
            {"role": "user", "content": math_problem}
        ]
        logger.info(f"Generating math solution from text using {MATH_TUTOR_LLM}/{MATH_TUTOR_MODEL}")
    
    # Handle image-only or image+text problem
    else:
        # Validate and format image data
        formatted_image = _validate_base64_image(image_data)
        
        # Build content with image
        content_parts = []
        
        # Add image first
        content_parts.append({
            "type": "image_url",
            "image_url": {
                "url": formatted_image
            }
        })
        
        # Add text instruction with optional additional context
        if math_problem and math_problem.strip():
            text_content = f"Please solve this math problem shown in the image. Additional context: {math_problem}\n\nProvide a step-by-step solution in LaTeX format."
            logger.info(f"Generating math solution from image+text using {MATH_TUTOR_LLM}/{MATH_TUTOR_MODEL}")
        else:
            text_content = "Please solve this math problem shown in the image. Provide a step-by-step solution in LaTeX format."
            logger.info(f"Generating math solution from image using {MATH_TUTOR_LLM}/{MATH_TUTOR_MODEL}")
        
        content_parts.append({
            "type": "text",
            "text": text_content
        })
        
        messages = [
            {"role": "system", "content": MATH_TUTOR_VISION_SYSTEM_PROMPT},
            {"role": "user", "content": content_parts}
        ]
    
    try:
        response = generate_gpt_response_from_message(
            messages=messages,
            llm=MATH_TUTOR_LLM,
            model=MATH_TUTOR_MODEL,
            max_tokens=max_tokens,
            temperature=temperature
        )
        logger.info("Math solution generated successfully")
        return response
    except Exception as e:
        logger.error(f"Error generating math solution: {str(e)}")
        raise Exception(f"Failed to generate math solution: {str(e)}")


def review_student_solution(
    problem_text=None,
    problem_image=None,
    solution_text=None,
    solution_image=None,
    max_tokens=4000,
    temperature=0.3
):
    """
    Review a student's solution to a math problem and identify mistakes.
    Supports text, image, or both combined for problem and solution inputs.
    Text can provide additional context when used with images.
    
    Args:
        problem_text (str, optional): The math problem as text (can be used alone or with image)
        problem_image (str, optional): Base64 encoded image of the problem (can be used alone or with text)
        solution_text (str, optional): The student's solution as text (can be used alone or with image)
        solution_image (str, optional): Base64 encoded image of the solution (can be used alone or with text)
        max_tokens (int): Maximum tokens for the response (default: 4000)
        temperature (float): Temperature for response generation (default: 0.3)
    
    Returns:
        str: Detailed feedback on the solution with identified mistakes and corrections
        
    Raises:
        ValueError: If inputs are invalid
        Exception: If LLM call fails
    """
    # Validate that we have at least one problem input
    if not problem_text and not problem_image:
        raise ValueError("At least one of problem_text or problem_image must be provided")
    
    # Validate that we have at least one solution input
    if not solution_text and not solution_image:
        raise ValueError("At least one of solution_text or solution_image must be provided")
    
    # Build the user message content based on input types
    content_parts = []
    
    # Add problem
    if problem_image:
        formatted_problem_image = _validate_base64_image(problem_image)
        content_parts.append({
            "type": "text",
            "text": "**Problem (shown in image below):**"
        })
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": formatted_problem_image}
        })
        
        # Add additional problem text if provided
        if problem_text and problem_text.strip():
            content_parts.append({
                "type": "text",
                "text": f"\n**Additional context:** {problem_text}\n\n"
            })
        else:
            content_parts.append({
                "type": "text",
                "text": "\n\n"
            })
    else:
        # Text-only problem
        if not problem_text or not problem_text.strip():
            raise ValueError("Problem text cannot be empty")
        content_parts.append({
            "type": "text",
            "text": f"**Problem:**\n{problem_text}\n\n"
        })
    
    # Add solution
    if solution_image:
        formatted_solution_image = _validate_base64_image(solution_image)
        content_parts.append({
            "type": "text",
            "text": "**Student's Solution (shown in image below):**"
        })
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": formatted_solution_image}
        })
        
        # Add additional solution text if provided
        if solution_text and solution_text.strip():
            content_parts.append({
                "type": "text",
                "text": f"\n**Additional notes:** {solution_text}\n\nPlease review this solution and identify any mistakes or errors. If there are mistakes, explain where they went wrong and provide the correct solution from that point onwards."
            })
        else:
            content_parts.append({
                "type": "text",
                "text": "\n\nPlease review this solution and identify any mistakes or errors. If there are mistakes, explain where they went wrong and provide the correct solution from that point onwards."
            })
    else:
        # Text-only solution
        if not solution_text or not solution_text.strip():
            raise ValueError("Solution text cannot be empty")
        content_parts.append({
            "type": "text",
            "text": f"**Student's Solution:**\n{solution_text}\n\nPlease review this solution and identify any mistakes or errors. If there are mistakes, explain where they went wrong and provide the correct solution from that point onwards."
        })
    
    # Prepare messages for LLM
    messages = [
        {"role": "system", "content": SOLUTION_REVIEW_SYSTEM_PROMPT},
        {"role": "user", "content": content_parts}
    ]
    
    input_types = {
        "problem": "image+text" if (problem_image and problem_text) else ("image" if problem_image else "text"),
        "solution": "image+text" if (solution_image and solution_text) else ("image" if solution_image else "text")
    }
    logger.info(f"Reviewing solution - Problem: {input_types['problem']}, Solution: {input_types['solution']}")
    
    try:
        response = generate_gpt_response_from_message(
            messages=messages,
            llm=MATH_TUTOR_LLM,
            model=MATH_TUTOR_MODEL,
            max_tokens=max_tokens,
            temperature=temperature
        )
        logger.info("Solution review generated successfully")
        return response
    except Exception as e:
        logger.error(f"Error reviewing solution: {str(e)}")
        raise Exception(f"Failed to review solution: {str(e)}")