"""
THis file contains utility functions for generative AI tasks.
All functions here should be independent of any specific LLM provider.
"""
import os
from ai_utils.all_llm_model_methods import generate_anthropic_response, generate_openai_response, generate_gemini_response, generate_deepseek_response


def generate_gpt_response_from_message(messages, llm=None, model="", max_tokens=8000, temperature=0.3,
                                       response_format=None):
    """
    Routes to the appropriate LLM function based on agent_llm and agent_ai_model from agent data.
    :param messages: Input messages.
    :param llm: LLM provider from agent data (e.g., 'anthropic', 'openai').
    :param model: Specific model from agent data (e.g., 'claude-3-haiku-20240307').
    :param max_tokens: Maximum tokens for the response.
    :param temperature: Controls randomness.
    :param response_format: Optional response format (e.g., 'json', 'text').
    :return: Generated text response.
    """
    # Use defaults if agent data doesn’t provide values
    print("Generating response using LLM...", llm, model)

    # Route to the cast-specific function in llm_functions.py
    if llm == "anthropic":
        return generate_anthropic_response(messages, model, max_tokens, temperature)
    elif llm == "gemini":
        return generate_gemini_response(messages, model, max_tokens, temperature )
    elif llm == "deepseek":
        return generate_deepseek_response(messages, model, max_tokens, temperature, response_format=response_format )
    else:
        print(f"LLM {llm} not recognized. Defaulting to OpenAI.")
        return generate_openai_response(messages, model, max_tokens, temperature, response_format=response_format)