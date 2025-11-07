"""
Math Tutor Response Module
This module provides functionality to generate step-by-step solutions for math problems using LLM.
"""
import logging
from ai_utils.gen_ai_functions import generate_gpt_response_from_message

logger = logging.getLogger(__name__)

MATH_TUTOR_LLM = "openai"
MATH_TUTOR_MODEL = "gpt-4o"

MATH_TUTOR_SYSTEM_PROMPT = (
    "As a math specialist, your task is to provide step-by-step solutions in latex for a given math question. "
    "Please answer the question step by step. Please be CAREFUL and think twice about calculations. "
    "You'd better make sure the calculation is correct. Please keep it short and concise."
)


def generate_math_tutor_response(math_problem, max_tokens=4000, temperature=0.3):
    """
    Generate a step-by-step solution for a given math problem using an LLM.
    
    Args:
        math_problem (str): The math problem to solve
        max_tokens (int): Maximum tokens for the response (default: 4000)
        temperature (float): Temperature for response generation (default: 0.3)
    
    Returns:
        str: The step-by-step solution in LaTeX format
        
    Raises:
        ValueError: If math_problem is empty or None
        Exception: If LLM call fails
    """
    if not math_problem or not math_problem.strip():
        raise ValueError("Math problem cannot be empty")
    
    # Prepare messages for the LLM
    messages = [
        {"role": "system", "content": MATH_TUTOR_SYSTEM_PROMPT},
        {"role": "user", "content": math_problem}
    ]
    
    try:
        logger.info(f"Generating math solution using {MATH_TUTOR_LLM}/{MATH_TUTOR_MODEL}")
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