import time

class TutorSession:
    def __init__(self, user_id, personality, language):
        self.user_id = user_id
        self.personality = personality
        self.language = language
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
            "messages": self.messages,
            "length": self.length,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "summary": self.summary,
            "ended_at": self.ended_at
        }