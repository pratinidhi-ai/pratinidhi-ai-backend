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
    Supports both text input and image input (via vision-capable LLM).
    
    Args:
        math_problem (str, optional): The math problem text to solve
        image_data (str, optional): Base64 encoded image of the math problem
        max_tokens (int): Maximum tokens for the response (default: 4000)
        temperature (float): Temperature for response generation (default: 0.3)
    
    Returns:
        str: The step-by-step solution in LaTeX format
        
    Raises:
        ValueError: If neither math_problem nor image_data is provided, or both are provided
        Exception: If LLM call fails
    """
    # Validate inputs
    if not math_problem and not image_data:
        raise ValueError("Either math_problem (text) or image_data (base64 image) must be provided")
    
    if math_problem and image_data:
        raise ValueError("Provide either math_problem (text) OR image_data (image), not both")
    
    # Handle text-based problem
    if math_problem:
        if not math_problem.strip():
            raise ValueError("Math problem cannot be empty")
        
        messages = [
            {"role": "system", "content": MATH_TUTOR_SYSTEM_PROMPT},
            {"role": "user", "content": math_problem}
        ]
        logger.info(f"Generating math solution from text using {MATH_TUTOR_LLM}/{MATH_TUTOR_MODEL}")
    
    # Handle image-based problem
    else:
        # Validate and format image data
        formatted_image = _validate_base64_image(image_data)
        
        messages = [
            {"role": "system", "content": MATH_TUTOR_VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please solve this math problem shown in the image. Provide a step-by-step solution in LaTeX format."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": formatted_image
                        }
                    }
                ]
            }
        ]
        logger.info(f"Generating math solution from image using {MATH_TUTOR_LLM}/{MATH_TUTOR_MODEL}")
    
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