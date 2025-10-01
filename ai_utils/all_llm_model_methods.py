"""
All LLM model methods are defined in this file.
"""

from anthropic import Anthropic
import openai
from openai import OpenAI
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI API key
openai.api_type = os.getenv('OPENAI_API_TYPE')
openai.api_key = os.getenv("OPENAI_API_KEY")

claude_available_models = ["claude-3-opus-20240229", "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022", "claude-opus-4-1-20250805"]
openai_available_models = ["gpt-4o-mini", "o4-mini", "gpt-4o", "gpt-5"]
gemini_available_models = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-2.5-pro-preview-06-05"]
deepseek_available_models = ["deepseek-chat", "deepseek-reasoner"]



def generate_anthropic_response(messages, model="claude-3-haiku-20240307", max_tokens=1000, temperature=0.7):
    """Generate a response using Anthropic's Claude models."""
    print(f"Generating response using Anthropic model: {model}")
    if model not in claude_available_models:
        model=claude_available_models[0]  # Default to the first available model
        print(f"Model not in available list, defaulting to: {model}")
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        anthropic_messages = []
        system_message = ""
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        response = client.messages.create(
            model=model,
            messages=anthropic_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message
        )
        # Concatenate all text blocks from the response content
        if hasattr(response, "content"):
            if isinstance(response.content, str):
                return response.content
            elif isinstance(response.content, list):
                return "".join(
                    getattr(block, "text", str(block))
                    for block in response.content
                )
        raise Exception("Unexpected response format from Anthropic API")
    except Exception as e:
        raise Exception(f"Error generating Anthropic response: {e}")

def generate_openai_response(messages, model, max_tokens=350, temperature=0.7, response_format=None):
    """Generate a response using OpenAI models."""
    if response_format is None:
        response_format = {"type": "text"}
    if not model or model not in openai_available_models:
        model = openai_available_models[0]  # Default to the first available model
    print("Generating response using GPT model: ", model)
    try:
        completion = openai.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format=response_format # pyright: ignore[reportArgumentType]
        )

        return completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error generating GPT response: {e}")

def generate_deepseek_response(messages, model="deepseek-chat", max_tokens=350, temperature=0.7, response_format=None):
    """Generate a response using DeepSeek API."""
    print(f"Generating response using DeepSeek model: {model}")

    # Initialize DeepSeek client with custom base URL and API key
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),  #  DeepSeek API key
        base_url="https://api.deepseek.com"  # DeepSeek's API endpoint
    )

    # Fallback to default model if the specified model isn’t available
    if model not in deepseek_available_models:
        model = deepseek_available_models[0]
        print(f"Model not in available list, defaulting to: {model}")

    try:
        # Call DeepSeek API using the OpenAI client
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format=response_format # pyright: ignore[reportArgumentType]
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error generating DeepSeek response: {e}")

def generate_gemini_response(messages, model, max_tokens=1000, temperature=0.7):
    """Generate a response using Google's Gemini models."""
    print(f"Generating response using Gemini model: {model}")
    if model not in gemini_available_models:
        model=gemini_available_models[0]
        print(f"Model not in available list, defaulting to: {model}")

    genai.configure(api_key=os.getenv("GEMINI_API_KEY") ) # pyright: ignore[reportPrivateImportUsage]
    model_instance = genai.GenerativeModel(model) # pyright: ignore[reportPrivateImportUsage]
    try:
        contents = []
        combined_user_content = ""
        for message in messages:
            if message["role"] == "system":
                combined_user_content += message["content"] + "\n\n"
            elif message["role"] == "user":
                if not contents:
                    combined_user_content += message["content"]
                    contents.append({"role": "user", "parts": [combined_user_content]})
                else:
                    contents.append({"role": "user", "parts": [message["content"]]})
            elif message["role"] == "assistant":
                contents.append({"role": "assistant", "parts": [message["content"]]})
        response = model_instance.generate_content(
            contents,
            generation_config=genai.GenerationConfig( # pyright: ignore[reportPrivateImportUsage]
                max_output_tokens=max_tokens,
                temperature=temperature
            )
        )
        return response.text
    except Exception as e:
        raise Exception(f"Error generating Gemini response: {e}")