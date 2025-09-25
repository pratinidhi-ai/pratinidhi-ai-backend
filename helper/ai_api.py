from prompt_builder import SystemPromptBuilder
from models.tutor_session_schema import TutorSession

def call_openai_api(session : TutorSession):
    # Compose system prompt from session info
    # Call OpenAI API and return response
    builder = SystemPromptBuilder(
        personality=session.personality,
        purpose="Help the user learn in a fun and engaging way.",
        intro="Greet the student warmly and make them comfortable.",
        interests="Math, Science, Coding",  # You can fetch from user profile
        language= session.language,
        guardrails="Never say anything inappropriate. Be safe for kids."
    )
    
    return "AI response here"

def generate_summary(messages):
    # Optionally call OpenAI API to summarize
    return "Session summary here"