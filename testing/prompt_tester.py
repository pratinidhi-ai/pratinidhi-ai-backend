#!/usr/bin/env python3
"""
Quick Prompt Tester

This tool allows you to quickly test and validate system prompts without starting a full chat session.
Perfect for testing prompt changes and seeing the output immediately.
"""

import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helper.prompt_builder import PromptBuilder


class PromptTester:
    def __init__(self):
        self.builder = PromptBuilder()
    
    def test_all_personalities(self):
        """Test prompt generation for all personalities."""
        print("🎭 TESTING ALL PERSONALITIES")
        print("=" * 50)
        
        personalities = self.builder.get_available_personalities()
        
        for personality in personalities:
            print(f"\n--- {personality.upper()} ---")
            info = self.builder.get_personality_info(personality)
            print(f"Name: {info.get('name', 'Unknown')}")
            print(f"Description: {info.get('description', 'No description')}")
            
            # Generate a basic prompt
            prompt = self.builder.build_system_prompt(personality=personality)
            print(f"Prompt length: {len(prompt)} characters")
            print(f"Preview: {prompt[:200]}...")
            print()
    
    def test_personality_with_details(self, personality: str):
        """Test a specific personality with various parameters."""
        print(f"🎯 DETAILED TEST FOR: {personality}")
        print("=" * 50)
        
        # Test basic prompt
        print("\n1. Basic Prompt:")
        basic_prompt = self.builder.build_system_prompt(personality=personality)
        print(f"Length: {len(basic_prompt)} characters")
        print(basic_prompt)
        
        # Test with subject
        print("\n" + "="*50)
        print("2. With Subject (Mathematics):")
        subject_prompt = self.builder.build_system_prompt(
            personality=personality, 
            subject="Mathematics"
        )
        print(f"Length: {len(subject_prompt)} characters")
        print(subject_prompt)
        
        # Test with full parameters
        print("\n" + "="*50)
        print("3. Full Configuration:")
        full_prompt = self.builder.build_system_prompt(
            personality=personality,
            subject="Physics",
            level="high_school",
            exam="AP Physics",
            interests=["basketball", "video games"],
            goals=["improve grades", "understand concepts"]
        )
        print(f"Length: {len(full_prompt)} characters")
        print(full_prompt)
        
        # Test with lecture notes
        print("\n" + "="*50)
        print("4. With Lecture Notes:")
        lecture_notes = """Chapter 1: Introduction to Motion
- Position and displacement
- Velocity and acceleration  
- Graphing motion"""
        
        lecture_prompt = self.builder.build_system_prompt(
            personality=personality,
            subject="Physics", 
            level="high_school",
            lecture_notes=lecture_notes
        )
        print(f"Length: {len(lecture_prompt)} characters")
        print(lecture_prompt)
    
    def interactive_prompt_builder(self):
        """Interactive prompt building interface."""
        print("🛠️  INTERACTIVE PROMPT BUILDER")
        print("=" * 40)
        
        # Get personality
        personalities = self.builder.get_available_personalities()
        print(f"\nAvailable personalities:")
        for i, p in enumerate(personalities, 1):
            info = self.builder.get_personality_info(p)
            print(f"  {i}. {p} - {info.get('name', 'Unknown')}")
        
        try:
            choice = int(input(f"\nChoose personality (1-{len(personalities)}): ")) - 1
            personality = personalities[choice]
        except (ValueError, IndexError):
            print("Invalid choice. Using albert_einstein as default.")
            personality = "albert_einstein"
        
        # Get other parameters
        subject = input("Subject (optional): ").strip() or None
        level = input("Level (elementary/middle_school/high_school/college/graduate/professional): ").strip() or None
        exam = input("Exam (optional): ").strip() or None
        
        interests_input = input("Interests (comma-separated): ").strip()
        interests = [i.strip() for i in interests_input.split(",")] if interests_input else None
        
        goals_input = input("Goals (comma-separated): ").strip()  
        goals = [g.strip() for g in goals_input.split(",")] if goals_input else None
        
        # Generate and display prompt
        prompt = self.builder.build_system_prompt(
            personality=personality,
            subject=subject,
            level=level,
            exam=exam,
            interests=interests,
            goals=goals
        )
        
        print("\n" + "="*60)
        print("GENERATED SYSTEM PROMPT")
        print("="*60)
        print(prompt)
        print("="*60)
        print(f"Length: {len(prompt)} characters")
        
        # Save option
        save = input("\nSave to file? (y/n): ").strip().lower()
        if save == 'y':
            filename = f"prompt_{personality}_{len(prompt)}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(prompt)
            print(f"Saved to {filename}")
    
    def compare_personalities(self, subject: str = "Mathematics"):
        """Compare how different personalities handle the same subject."""
        print(f"⚖️  PERSONALITY COMPARISON - {subject}")
        print("=" * 60)
        
        personalities = self.builder.get_available_personalities()[:4]  # Test first 4
        
        for personality in personalities:
            prompt = self.builder.build_system_prompt(
                personality=personality,
                subject=subject,
                level="high_school"
            )
            
            info = self.builder.get_personality_info(personality)
            print(f"\n{info.get('name', personality)} ({personality}):")
            print("-" * 40)
            
            # Extract personality section
            lines = prompt.split('\n')
            personality_started = False
            for line in lines:
                if "embody the personality" in line.lower():
                    personality_started = True
                elif personality_started and line.strip() == "":
                    break
                
                if personality_started:
                    print(line)
    
    def run_menu(self):
        """Main menu interface."""
        while True:
            print("\n" + "="*50)
            print("🧪 AI TUTOR PROMPT TESTER")
            print("="*50)
            print("1. Test all personalities (quick overview)")
            print("2. Test specific personality (detailed)")
            print("3. Interactive prompt builder")
            print("4. Compare personalities")
            print("5. Exit")
            
            try:
                choice = input("\nChoose option (1-5): ").strip()
                
                if choice == "1":
                    self.test_all_personalities()
                
                elif choice == "2":
                    personalities = self.builder.get_available_personalities()
                    print("\nAvailable personalities:")
                    for p in personalities:
                        print(f"  - {p}")
                    
                    personality = input("\nEnter personality name: ").strip()
                    if personality in personalities:
                        self.test_personality_with_details(personality)
                    else:
                        print("Invalid personality name!")
                
                elif choice == "3":
                    self.interactive_prompt_builder()
                
                elif choice == "4":
                    subject = input("Enter subject for comparison (default: Mathematics): ").strip()
                    if not subject:
                        subject = "Mathematics"
                    self.compare_personalities(subject)
                
                elif choice == "5":
                    print("\n👋 Goodbye!")
                    break
                
                else:
                    print("Invalid choice! Please choose 1-5.")
            
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break


def main():
    """Entry point for the prompt tester."""
    if len(sys.argv) > 1:
        # Command line usage
        tester = PromptTester()
        command = sys.argv[1]
        
        if command == "all":
            tester.test_all_personalities()
        elif command == "compare":
            subject = sys.argv[2] if len(sys.argv) > 2 else "Mathematics"
            tester.compare_personalities(subject)
        else:
            tester.test_personality_with_details(command)
    else:
        # Interactive menu
        tester = PromptTester()
        tester.run_menu()


if __name__ == "__main__":
    main()