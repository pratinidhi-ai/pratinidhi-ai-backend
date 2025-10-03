import json
import os
from typing import Dict, List, Optional

class PromptBuilder:
    def __init__(self, personalities_config_path: Optional[str] = None, lecture_notes_config_path: Optional[str] = None):
        """Initialize the PromptBuilder with personality and lecture notes configurations."""
        if personalities_config_path is None:
            # Default path relative to the project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            personalities_config_path = os.path.join(project_root, 'config', 'personalities.json')
        
        if lecture_notes_config_path is None:
            # Default path for lecture notes
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            lecture_notes_config_path = os.path.join(project_root, 'config', 'lecture_notes.json')
        
        self.personalities_config_path = personalities_config_path
        self.lecture_notes_config_path = lecture_notes_config_path
        self.personalities = self._load_personalities()
        self.lecture_notes_db = self._load_lecture_notes()
    
    def _load_personalities(self) -> Dict:
        """Load personality configurations from JSON file."""
        try:
            with open(self.personalities_config_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Warning: Personalities config file not found at {self.personalities_config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing personalities config: {e}")
            return {}
    
    def _load_lecture_notes(self) -> Dict:
        """Load lecture notes configurations from JSON file."""
        try:
            with open(self.lecture_notes_config_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Warning: Lecture notes config file not found at {self.lecture_notes_config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing lecture notes config: {e}")
            return {}
    
    def _get_fixed_prompt_parts(self) -> str:
        """Get the fixed parts of the AI tutor prompt."""
        fixed_parts = [
            "You are an AI tutor who is friendly, patient, and knowledgeable. You explain concepts in simple, clear terms that are easy to understand.",
            "You use examples and analogies from the student's interests (such as sports, music, movies, games, etc.) to explain complex concepts and make them relatable.",
            "You try to make learning fun and engaging by using interactive methods, storytelling, and creative explanations.",
            "You encourage the student to ask questions, think critically, and explore topics deeply. You celebrate their curiosity and progress."
        ]
        return "\n\n".join(fixed_parts)
    
    def _get_subject_section(self, subject: Optional[str]) -> str:
        """Build the subject expertise section of the prompt."""
        if not subject:
            return "You are a versatile tutor capable of helping with various subjects."
        
        return f"You are a subject matter expert in {subject}, capable of explaining concepts from basic fundamentals to advanced levels. You have deep knowledge of the curriculum, common misconceptions, and effective teaching strategies for this subject."
    
    def _get_student_level_section(self, level: Optional[str]) -> str:
        """Build the student level section of the prompt."""
        if not level:
            return ""
        
        level_descriptions = {
            "elementary": "elementary school level, so use very simple language and basic concepts",
            "middle_school": "middle school level, so use clear explanations with some complexity",
            "high_school": "high school level, so you can use more advanced concepts and terminology",
            "college": "college level, so you can engage with sophisticated ideas and complex reasoning",
            "graduate": "graduate level, so you can discuss advanced theories and research-level concepts",
            "professional": "professional level, so focus on practical applications and industry-relevant knowledge"
        }
        
        description = level_descriptions.get(level.lower(), f"{level} level")
        return f"The student is currently at {description}. Adjust your explanations and examples accordingly."
    
    def _get_exam_section(self, exam: Optional[str]) -> str:
        """Build the exam preparation section of the prompt."""
        if not exam:
            return ""
        
        return f"The student is preparing for {exam}. Focus your teaching on concepts, question types, and strategies that will help them succeed in this specific exam. Provide practice questions and test-taking tips when relevant."
    
    def _get_interests_section(self, interests: Optional[List[str]]) -> str:
        """Build the student interests section of the prompt."""
        if not interests or len(interests) == 0:
            return ""
        
        interests_str = ", ".join(interests)
        return f"The student has shown interest in: {interests_str}. Use examples, analogies, and references from these areas to make your explanations more relatable and engaging."
    
    def _get_goals_section(self, goals: Optional[List[str]]) -> str:
        """Build the student goals section of the prompt."""
        if not goals or len(goals) == 0:
            return ""
        
        goals_str = ", ".join(goals)
        return f"The student's learning goals include: {goals_str}. Keep these objectives in mind and help them work towards achieving these goals through your teaching."
    
    def _get_personality_section(self, personality: str) -> str:
        """Build the personality section based on the selected character."""
        if personality not in self.personalities:
            return "Maintain a professional, encouraging, and supportive teaching style."
        
        personality_data = self.personalities[personality]
        name = personality_data.get('name', personality)
        description = personality_data.get('description', '')
        traits = personality_data.get('traits', [])
        catchphrases = personality_data.get('catchphrases', [])
        
        personality_section = f"You embody the personality of {name} - {description}."
        
        if traits:
            traits_str = "\n".join([f"- {trait}" for trait in traits])
            personality_section += f"\n\nYour teaching style reflects these characteristics:\n{traits_str}"
        
        if catchphrases:
            phrases_str = "\n".join([f'- "{phrase}"' for phrase in catchphrases])
            personality_section += f"\n\nYou may occasionally use phrases like:\n{phrases_str}"
        
        personality_section += f"\n\nStay true to {name}'s character while being an effective and supportive tutor."
        
        return personality_section
    
    def get_available_subjects(self) -> List[str]:
        """Get a list of available subjects from lecture notes database."""
        return list(self.lecture_notes_db.keys())
    
    def get_subject_chapters(self, subject: str) -> List[str]:
        """Get available chapters for a specific subject."""
        if subject not in self.lecture_notes_db:
            return []
        
        subject_data = self.lecture_notes_db[subject]
        if 'chapters' in subject_data:
            return list(subject_data['chapters'].keys())
        return []
    
    def get_chapter_content(self, subject: str, chapter: str) -> Optional[Dict]:
        """Get the content for a specific chapter."""
        if subject not in self.lecture_notes_db:
            return None
        
        subject_data = self.lecture_notes_db[subject]
        if 'chapters' in subject_data and chapter in subject_data['chapters']:
            return subject_data['chapters'][chapter]
        return None
    
    def format_chapter_for_prompt(self, subject: str, chapter: str) -> str:
        """Format a chapter's content for use in system prompt."""
        chapter_content = self.get_chapter_content(subject, chapter)
        if not chapter_content:
            return ""
        
        formatted_content = f"""CHAPTER: {chapter_content.get('title', chapter)}

DETAILED NOTES:
{chapter_content.get('notes', 'No detailed notes available.')}

CHAPTER SUMMARY:
{chapter_content.get('summary', 'No summary available.')}

KEY INSIGHTS:"""
        
        key_insights = chapter_content.get('key_insights', [])
        if key_insights:
            for i, insight in enumerate(key_insights, 1):
                formatted_content += f"\n{i}. {insight}"
        else:
            formatted_content += "\nNo key insights available."
        
        return formatted_content
    
    def _get_lecture_notes_section(self, lecture_notes: Optional[str] = None, subject: Optional[str] = None, chapter: Optional[str] = None) -> str:
        """Build the lecture notes section of the prompt."""
        # Handle structured lecture notes from database
        if subject and chapter:
            formatted_content = self.format_chapter_for_prompt(subject, chapter)
            if formatted_content:
                lecture_notes = formatted_content
        
        # Handle raw lecture notes string
        if not lecture_notes:
            return ""
        
        return f"""IMPORTANT: You have been provided with specific lecture notes for this session. You must follow these guidelines strictly:

1. Use ONLY the content from these lecture notes to explain concepts to the student
2. Do not go beyond the topics covered in the provided notes
3. If the student asks about topics not covered in the notes, politely decline and say: "That's an excellent question, but it's not covered in today's material. We can discuss that in a future session, or you can create an additional session specifically for that topic."
4. Use the notes to create quizzes and practice questions for the student
5. Ensure all explanations are based on the provided material

LECTURE NOTES:
{lecture_notes}

Remember to stick strictly to this content."""
    
    def _get_lecture_plan_section(self, lecture_notes: Optional[str]) -> str:
        """Build the lecture plan section when lecture notes are provided."""
        if not lecture_notes:
            return ""
        
        return """LECTURE PLAN: When teaching from the provided lecture notes, follow this structured approach:

1. **Point-by-Point Teaching**: Go through each main point/concept in the chapter systematically
2. **Check Understanding**: After explaining each point, ask if the student has any questions about that specific concept
3. **Quick Assessment**: Ask 1-2 targeted questions to test the student's understanding of each point before moving on
4. **Overall Q&A**: After covering all points, ask if the student has any general questions about the chapter
5. **Comprehensive Quiz**: Create a 5-question quiz covering the entire chapter to test overall understanding
6. **Detailed Explanations**: Provide thorough explanations for each quiz question, including why wrong answers are incorrect
7. **Session Summary**: At the end, provide:
   - A summary of the chapter covered
   - A list of important points to remember
   - Feedback on the student's quiz performance
   - Suggestions for improvement

Follow this structure to ensure comprehensive learning and assessment."""
    
    def build_system_prompt(self, personality: str, subject: Optional[str] = None, 
                          level: Optional[str] = None, exam: Optional[str] = None,
                          interests: Optional[List[str]] = None, goals: Optional[List[str]] = None,
                          lecture_notes: Optional[str] = None, 
                          lecture_subject: Optional[str] = None, lecture_chapter: Optional[str] = None) -> str:
        """Build the complete system prompt for the AI tutor.
        
        Args:
            personality: The tutor personality to use
            subject: The subject being taught
            level: Student's education level
            exam: Exam being prepared for
            interests: Student's interests
            goals: Student's learning goals
            lecture_notes: Raw lecture notes string (legacy support)
            lecture_subject: Subject from structured lecture database (e.g., 'SAT')
            lecture_chapter: Chapter from structured lecture database (e.g., 'Chapter 1')
        """
        
        sections = []
        
        # Fixed parts
        sections.append(self._get_fixed_prompt_parts())
        
        # Dynamic parts
        subject_section = self._get_subject_section(subject)
        if subject_section:
            sections.append(subject_section)
        
        level_section = self._get_student_level_section(level)
        if level_section:
            sections.append(level_section)
        
        exam_section = self._get_exam_section(exam)
        if exam_section:
            sections.append(exam_section)
        
        interests_section = self._get_interests_section(interests)
        if interests_section:
            sections.append(interests_section)
        
        goals_section = self._get_goals_section(goals)
        if goals_section:
            sections.append(goals_section)
        
        # Personality section
        personality_section = self._get_personality_section(personality)
        if personality_section:
            sections.append(personality_section)
        
        # Lecture notes (structured or raw)
        lecture_notes_section = self._get_lecture_notes_section(
            lecture_notes=lecture_notes, 
            subject=lecture_subject, 
            chapter=lecture_chapter
        )
        if lecture_notes_section:
            sections.append(lecture_notes_section)
        
        # Lecture plan (if any lecture notes are provided)
        has_lecture_content = (lecture_notes or (lecture_subject and lecture_chapter))
        lecture_plan_section = self._get_lecture_plan_section(lecture_notes if lecture_notes else has_lecture_content)
        if lecture_plan_section:
            sections.append(lecture_plan_section)
        
        # Join all sections
        complete_prompt = "\n\n".join(sections)
        
        return complete_prompt
    
    def get_available_personalities(self) -> List[str]:
        """Get a list of available personality keys."""
        return list(self.personalities.keys())
    
    def get_personality_info(self, personality: str) -> Dict:
        """Get detailed information about a specific personality."""
        return self.personalities.get(personality, {})
    
    def get_subject_info(self, subject: str) -> Dict:
        """Get detailed information about a specific subject from lecture database."""
        return self.lecture_notes_db.get(subject, {})


# Legacy class for backward compatibility
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


# Convenience function for easy import
def build_tutor_prompt(personality: str, subject: Optional[str] = None, 
                      level: Optional[str] = None, exam: Optional[str] = None,
                      interests: Optional[List[str]] = None, goals: Optional[List[str]] = None,
                      lecture_notes: Optional[str] = None,
                      lecture_subject: Optional[str] = None, lecture_chapter: Optional[str] = None) -> str:
    """Convenience function to build a tutor prompt without instantiating PromptBuilder."""
    builder = PromptBuilder()
    return builder.build_system_prompt(
        personality=personality,
        subject=subject,
        level=level,
        exam=exam,
        interests=interests,
        goals=goals,
        lecture_notes=lecture_notes,
        lecture_subject=lecture_subject,
        lecture_chapter=lecture_chapter
    )