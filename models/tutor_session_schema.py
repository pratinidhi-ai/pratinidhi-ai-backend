import time
from datetime import datetime, timezone

class TutorSession:
	def __init__(self, user_id, personality, language, session_id, subject=None, exam=None, interests=None, goals=None,lecture_notes=None, lecture_subject=None, lecture_chapter=None,session_system_prompt=None):
		self.user_id = user_id
		self.personality = personality
		self.language = language
		self.session_id = session_id
		self.messages = []
		self.length = 0
		self.is_active = True
		self.created_at = datetime.now(timezone.utc).isoformat()  # Store as ISO format string instead of Unix timestamp
		self.summary = None
		self.ended_at = None
		self.subject = subject
		self.exam = exam
		self.interests = interests or []
		self.goals = goals or []
		self.lecture_notes = lecture_notes
		self.lecture_subject = lecture_subject  # For structured lecture notes (e.g., 'SAT')
		self.lecture_chapter = lecture_chapter  # For structured lecture notes (e.g., 'Chapter 1')
		self.session_system_prompt = session_system_prompt

	def to_dict(self):
		return {
			"user_id": self.user_id,
			"personality": self.personality,
			"language": self.language,
			"session_id" : self.session_id,
			"subject": self.subject,
            "exam": self.exam,
            "interests": self.interests,
            "goals": self.goals,
            "lecture_notes": self.lecture_notes,
            "lecture_subject": self.lecture_subject,
            "lecture_chapter": self.lecture_chapter,
			"session_system_prompt": self.session_system_prompt,
			"messages": self.messages,
			"length": self.length,
			"is_active": self.is_active,
			"created_at": self.created_at,  # Already in ISO format
			"summary": self.summary,
			"ended_at": self.ended_at if isinstance(self.ended_at, str) else (datetime.now(timezone.utc).isoformat() if self.ended_at else None)  # Convert to ISO if set
		}