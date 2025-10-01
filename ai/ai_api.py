from helper.prompt_builder import SystemPromptBuilder
from models.tutor_session_schema import TutorSession
from dotenv import load_dotenv
from ai.rag_setup import load_vectorstore
from ai_utils.gen_ai_functions import generate_gpt_response_from_message
import os

load_dotenv()


vectorstore = load_vectorstore()
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

def call_openai_api(session : TutorSession , callRag: bool = False):
	# later add something for user stats
	
	user_interests = ["Math", "Science", "Coding", "Space Exploration"] 
	
	builder = SystemPromptBuilder(
		personality=session.personality,
		purpose="Help the user learn in a fun, engaging, and effective way by acting as a personal guide.",
		intro="Greet the student warmly, ask them what they're curious about today, and make them feel comfortable.",
		interests=user_interests,
		language=session.language
	)
	system_prompt = builder.build()
	
	if callRag:
		latest_message = session.messages[-1]["content"] if session.messages else ""
		retrieved_docs = retriever.invoke(latest_message)
		context = "\n\n".join([doc.page_content for doc in retrieved_docs])
		system_prompt += f"\n\nRelevant SAT Book Context:\n{context}"

	messages = [{"role": "system", "content": system_prompt}] + session.messages
	response = generate_gpt_response_from_message(
		messages=messages,
		llm="openai",  
		model="gpt-4o-mini",
		max_tokens=1000,
		temperature=0.7
	)
	
	return response

def generate_summary(messages):
	response = generate_gpt_response_from_message(
		messages=[
			{"role": "system", "content": "Summarize this tutoring session for the student in simple words."},
			{"role": "user", "content": str(messages)}
		],
		llm="openai",
		model="gpt-4o-mini",
		max_tokens=350,
		temperature=0.7
	)
	return response