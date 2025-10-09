#!/usr/bin/env python3
"""
Interactive Terminal Chat Interface for AI Tutor

This tool allows you to test the AI tutor system directly from the terminal.
You can create sessions, chat with different personalities, and test prompt changes in real-time.
"""

import sys
import os
import json
from typing import Dict, List, Optional

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helper.prompt_builder import PromptBuilder
from models.tutor_session_schema import TutorSession
from ai.ai_api import call_openai_api


class TutorChatTester:
    def __init__(self):
        self.builder = PromptBuilder()
        self.session = None
        self.session_count = 0
    
    def display_welcome(self):
        """Display welcome message and instructions."""
        print("=" * 60)
        print("🤖 AI TUTOR TERMINAL CHAT TESTER")
        print("=" * 60)
        print("Test your AI tutor system directly from the terminal!")
        print("\nAvailable commands:")
        print("  /help          - Show this help message")
        print("  /personalities - List available personalities")
        print("  /new           - Create a new tutor session")
        print("  /session       - Show current session info")
        print("  /prompt        - Show current system prompt")
        print("  /quit          - Exit the chat")
        print("\nType any message to chat with your tutor.")
        print("=" * 60)
    
    def display_personalities(self):
        """Display available tutor personalities."""
        personalities = self.builder.get_available_personalities()
        print("\n🎭 AVAILABLE PERSONALITIES:")
        print("-" * 40)
        
        for personality in personalities:
            info = self.builder.get_personality_info(personality)
            name = info.get('name', personality)
            description = info.get('description', 'No description available')
            print(f"  {personality}")
            print(f"    Name: {name}")
            print(f"    Description: {description}")
            print()
    
    def create_session(self):
        """Interactive session creation."""
        print("\n🚀 CREATING NEW TUTOR SESSION")
        print("-" * 35)
        
        # Get personality
        personalities = self.builder.get_available_personalities()
        print(f"\nAvailable personalities: {', '.join(personalities)}")
        personality = input("Choose personality (default: albert_einstein): ").strip()
        if not personality:
            personality = "albert_einstein"
        
        # Get other parameters
        subject = input("Subject (optional): ").strip() or None
        level = input("Education level (elementary/middle_school/high_school/college/graduate/professional): ").strip() or None
        exam = input("Exam preparation (optional): ").strip() or None
        
        # Get interests
        interests_input = input("Student interests (comma-separated, optional): ").strip()
        interests = [i.strip() for i in interests_input.split(",")] if interests_input else []
        
        # Get goals  
        goals_input = input("Learning goals (comma-separated, optional): ").strip()
        goals = [g.strip() for g in goals_input.split(",")] if goals_input else []
        
        # Get lecture notes - offer structured or raw options
        lecture_notes = None
        lecture_subject = None
        lecture_chapter = None
        
        print("\n📚 LECTURE NOTES OPTIONS:")
        print("1. Use structured lecture notes (from database)")
        print("2. Enter raw lecture content")
        print("3. Skip lecture notes")
        
        lecture_choice = input("Choose option (1-3, default: 3): ").strip()
        
        if lecture_choice == "1":
            # Structured lecture notes
            available_subjects = self.builder.get_available_subjects()
            if available_subjects:
                print(f"\nAvailable subjects: {', '.join(available_subjects)}")
                lecture_subject = input("Choose subject: ").strip()
                
                if lecture_subject in available_subjects:
                    chapters = self.builder.get_subject_chapters(lecture_subject)
                    if chapters:
                        print(f"Available chapters: {', '.join(chapters)}")
                        lecture_chapter = input("Choose chapter: ").strip()
                        
                        if lecture_chapter in chapters:
                            # Preview the chapter content
                            chapter_content = self.builder.get_chapter_content(lecture_subject, lecture_chapter)
                            if chapter_content:
                                print(f"\n✅ Selected: {lecture_subject} - {chapter_content.get('title', lecture_chapter)}")
                        else:
                            print("Invalid chapter. Skipping structured notes.")
                            lecture_subject = None
                    else:
                        print("No chapters available for this subject.")
                        lecture_subject = None
                else:
                    print("Invalid subject. Skipping structured notes.")
            else:
                print("No structured lecture notes available.")
        
        elif lecture_choice == "2":
            # Raw lecture notes
            print("\nEnter lecture content (press Enter twice to finish):")
            lecture_lines = []
            while True:
                line = input()
                if line == "" and lecture_lines and lecture_lines[-1] == "":
                    lecture_lines.pop()  # Remove the last empty line
                    break
                lecture_lines.append(line)
            
            lecture_notes = "\n".join(lecture_lines) if lecture_lines else None
        
        # Build system prompt
        system_prompt = self.builder.build_system_prompt(
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
        
        # Create session
        self.session_count += 1
        session_id = f"test_session_{self.session_count}"
        
        self.session = TutorSession(
            user_id="test_user",
            personality=personality,
            language="english",
            session_id=session_id,
            subject=subject,
            level=level,
            exam=exam,
            interests=interests,
            goals=goals,
            lecture_notes=lecture_notes,
            lecture_subject=lecture_subject,
            lecture_chapter=lecture_chapter,
            session_system_prompt=system_prompt
        )
        
        print(f"\n✅ Session created successfully!")
        print(f"Session ID: {session_id}")
        print(f"Personality: {personality}")
        if subject:
            print(f"Subject: {subject}")
        if level:
            print(f"Level: {level}")
        if exam:
            print(f"Exam: {exam}")
        if interests:
            print(f"Interests: {', '.join(interests)}")
        if goals:
            print(f"Goals: {', '.join(goals)}")

        print("System prompt: \n", system_prompt)
        
        print("\n💬 You can now start chatting with your tutor!")
        print("Type your first message or use /prompt to see the system prompt.")
    
    def show_session_info(self):
        """Display current session information."""
        if not self.session:
            print("\n❌ No active session. Use /new to create one.")
            return
        
        print(f"\n📋 CURRENT SESSION INFO")
        print("-" * 30)
        print(f"Session ID: {self.session.session_id}")
        print(f"Personality: {self.session.personality}")
        print(f"Subject: {self.session.subject or 'Not specified'}")
        print(f"Level: {self.session.level or 'Not specified'}")
        print(f"Exam: {self.session.exam or 'Not specified'}")
        print(f"Interests: {', '.join(self.session.interests) if self.session.interests else 'None'}")
        print(f"Goals: {', '.join(self.session.goals) if self.session.goals else 'None'}")
        print(f"Messages: {len(self.session.messages)}")
        print(f"Active: {self.session.is_active}")
        
        # Show lecture notes info
        if self.session.lecture_subject and self.session.lecture_chapter:
            print(f"Structured lecture: {self.session.lecture_subject} - {self.session.lecture_chapter}")
        elif self.session.lecture_notes:
            print(f"Raw lecture notes: Yes ({len(self.session.lecture_notes)} characters)")
        else:
            print("Lecture notes: None")
    
    def show_prompt(self):
        """Display the current system prompt."""
        if not self.session:
            print("\n❌ No active session. Use /new to create one.")
            return
        
        print(f"\n📜 SYSTEM PROMPT")
        print("-" * 20)
        print(self.session.session_system_prompt)
        print("-" * 20)
    
    def send_message(self, message: str):
        """Send a message to the tutor and get response."""
        if not self.session:
            print("\n❌ No active session. Use /new to create one.")
            return
        
        if not self.session.is_active:
            print("\n❌ Session has ended. Use /new to create a new one.")
            return
        
        try:
            # Add user message
            self.session.messages.append({"role": "user", "content": message})
            
            print("\n🤖 Tutor is thinking...")
            
            # Get AI response
            ai_response = call_openai_api(self.session)
            
            # Add AI response
            self.session.messages.append({"role": "assistant", "content": ai_response})
            self.session.length += 2
            
            # Display response
            print(f"\n🎓 Tutor ({self.session.personality}):")
            print(f"{ai_response}")
            
        except Exception as e:
            print(f"\n❌ Error getting AI response: {str(e)}")
            print("Make sure your OpenAI API key is configured correctly.")
    
    def run(self):
        """Main chat loop."""
        self.display_welcome()
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    command = user_input[1:].lower()
                    
                    if command == "help":
                        self.display_welcome()
                    elif command == "personalities":
                        self.display_personalities()
                    elif command == "new":
                        self.create_session()
                    elif command == "session":
                        self.show_session_info()
                    elif command == "prompt":
                        self.show_prompt()
                    elif command in ["quit", "exit", "q"]:
                        print("\n👋 Goodbye! Thanks for testing the AI tutor!")
                        break
                    else:
                        print(f"\n❌ Unknown command: {command}")
                        print("Type /help for available commands.")
                
                else:
                    # Regular message to tutor
                    self.send_message(user_input)
            
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for testing the AI tutor!")
                break
            except EOFError:
                print("\n\n👋 Goodbye! Thanks for testing the AI tutor!")
                break


def main():
    """Entry point for the chat tester."""
    tester = TutorChatTester()
    tester.run()


if __name__ == "__main__":
    main()