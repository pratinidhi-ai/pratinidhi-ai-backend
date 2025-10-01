import time

class TutorSession:
    def __init__(self, user_id, personality, language, session_id, subject=None, 
                 level=None, exam=None, interests=None, goals=None, 
                 lecture_notes=None, lecture_subject=None, lecture_chapter=None, 
                 session_system_prompt=None):
        self.user_id = user_id
        self.personality = personality
        self.language = language
        self.session_id = session_id
        self.subject = subject
        self.level = level
        self.exam = exam
        self.interests = interests or []
        self.goals = goals or []
        self.lecture_notes = lecture_notes
        self.lecture_subject = lecture_subject  # For structured lecture notes (e.g., 'SAT')
        self.lecture_chapter = lecture_chapter  # For structured lecture notes (e.g., 'Chapter 1')
        self.session_system_prompt = session_system_prompt
        self.messages = []
        self.length = 0
        self.is_active = True
        self.created_at = time.time()
        self.summary = None
        self.ended_at = None

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "personality": self.personality,
            "language": self.language,
            "session_id": self.session_id,
            "subject": self.subject,
            "level": self.level,
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
            "created_at": self.created_at,
            "summary": self.summary,
            "ended_at": self.ended_at
        }