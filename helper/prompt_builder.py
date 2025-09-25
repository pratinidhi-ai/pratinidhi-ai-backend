class SystemPromptBuilder:
    def __init__(self, personality, purpose, intro, interests, language, guardrails):
        self.personality = personality
        self.purpose = purpose
        self.intro = intro
        self.interests = interests
        self.language = language
        self.guardrails = guardrails

    def build(self, user_stats=None):
        prompt = f"""
You are an AI tutor with the personality of {self.personality}.
Purpose: {self.purpose}
How to start: {self.intro}
User interests: {self.interests}
Preferred language: {self.language}
Guardrails: {self.guardrails}
"""
        if user_stats:
            prompt += f"\nUser stats: {user_stats}\n"
        return prompt.strip()