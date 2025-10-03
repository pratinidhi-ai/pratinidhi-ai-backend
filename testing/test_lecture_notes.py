#!/usr/bin/env python3
"""
Quick test script to validate the new structured lecture notes functionality
"""

import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helper.prompt_builder import PromptBuilder


def test_structured_lecture_notes():
    """Test the structured lecture notes functionality."""
    print("🧪 Testing Structured Lecture Notes System")
    print("=" * 50)
    
    # Initialize prompt builder
    builder = PromptBuilder()
    
    # Test 1: Check available subjects
    print("\n1. Available Subjects:")
    subjects = builder.get_available_subjects()
    print(f"   {subjects}")
    
    # Test 2: Check SAT chapters
    if "SAT" in subjects:
        print("\n2. SAT Chapters:")
        chapters = builder.get_subject_chapters("SAT")
        print(f"   {chapters}")
        
        # Test 3: Get specific chapter content
        if chapters:
            first_chapter = chapters[0]
            print(f"\n3. Content for {first_chapter}:")
            content = builder.get_chapter_content("SAT", first_chapter)
            if content:
                print(f"   Title: {content.get('title')}")
                print(f"   Notes: {content.get('notes')[:100]}..." if content.get('notes') else "   Notes: None")
                print(f"   Summary: {content.get('summary')[:100]}..." if content.get('summary') else "   Summary: None")
                print(f"   Key Insights: {len(content.get('key_insights', []))} items")
            
            # Test 4: Generate formatted prompt content
            print(f"\n4. Formatted Content for Prompt:")
            formatted = builder.format_chapter_for_prompt("SAT", first_chapter)
            print(f"   Length: {len(formatted)} characters")
            print(f"   Preview: {formatted[:200]}...")
            
            # Test 5: Generate complete system prompt with structured notes
            print(f"\n5. Complete System Prompt with Structured Notes:")
            system_prompt = builder.build_system_prompt(
                personality="albert_einstein",
                subject="SAT Preparation",
                level="high_school",
                lecture_subject="SAT",
                lecture_chapter=first_chapter
            )
            print(f"   Total Length: {len(system_prompt)} characters")
            print(f"   Contains structured content: {'LECTURE NOTES:' in system_prompt}")
            print(f"   Contains lecture plan: {'LECTURE PLAN:' in system_prompt}")
    
    else:
        print("❌ SAT subject not found in lecture database!")
    
    print("\n✅ Testing completed!")


def test_comparison():
    """Compare structured vs raw lecture notes."""
    print("\n" + "=" * 50)
    print("📊 COMPARING STRUCTURED vs RAW LECTURE NOTES")
    print("=" * 50)
    
    builder = PromptBuilder()
    
    # Test with structured notes
    structured_prompt = builder.build_system_prompt(
        personality="professor_dumbledore",
        subject="SAT Preparation",
        lecture_subject="SAT",
        lecture_chapter="Chapter 1"
    )
    
    # Test with raw notes
    raw_notes = """Chapter 1: SAT Basics
- Test structure: 3 hours, 4 sections
- Scoring: 400-1600 scale
- Reading, Writing, Math sections"""
    
    raw_prompt = builder.build_system_prompt(
        personality="professor_dumbledore", 
        subject="SAT Preparation",
        lecture_notes=raw_notes
    )
    
    print(f"Structured prompt length: {len(structured_prompt)}")
    print(f"Raw notes prompt length: {len(raw_prompt)}")
    print(f"Difference: {abs(len(structured_prompt) - len(raw_prompt))} characters")
    
    # Check for key differences
    structured_has_insights = "key insights" in structured_prompt.lower()
    structured_has_summary = "summary:" in structured_prompt.lower()
    
    print(f"Structured includes key insights: {structured_has_insights}")
    print(f"Structured includes summary: {structured_has_summary}")


if __name__ == "__main__":
    test_structured_lecture_notes()
    test_comparison()