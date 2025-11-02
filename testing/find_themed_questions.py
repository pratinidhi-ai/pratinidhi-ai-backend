"""
Find questions with actual theme values
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.firebase_client import get_question_db_client

def find_themed_questions():
    print("Searching for questions with theme values...")
    
    db = get_question_db_client()
    
    # Check the metadata first to see what themes exist
    doc_path = "math|algebra"
    doc_ref = db.collection('question_bank').document(doc_path)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        theme_dist = data.get('theme_distribution', {})
        print(f"\nTheme distribution from metadata:")
        for theme, count in theme_dist.items():
            print(f"  '{theme}': {count} questions")
    
    print("\n" + "="*50)
    print("Searching for actual themed questions...\n")
    
    # Get more questions to find ones with themes
    questions_ref = (db.collection('question_bank')
                    .document(doc_path)
                    .collection('difficulty_levels')
                    .document('3')
                    .collection('questions'))
    
    # Get first 20 questions to find ones with themes
    questions = list(questions_ref.limit(20).stream())
    
    themed_count = 0
    for doc in questions:
        data = doc.to_dict()
        theme_value = data.get('theme', '')
        
        if theme_value and theme_value.strip():  # If theme has a value
            themed_count += 1
            print(f"Question ID: {doc.id}")
            print(f"  Theme: '{theme_value}'")
            print(f"  Question (first 100 chars): {data.get('question_text', '')[:100]}")
            print()
            
            if themed_count >= 3:  # Show first 3 themed questions
                break
    
    if themed_count == 0:
        print("❌ No questions with theme values found in first 20 questions")
        print("\nLet's check if theme field name is different...")
        
        # Check first question for any field that might contain theme
        if questions:
            first_q = questions[0].to_dict()
            print("\nAll fields in first question:")
            for key, value in first_q.items():
                if isinstance(value, str) and value.strip():
                    print(f"  {key}: {value[:50]}...")

if __name__ == "__main__":
    find_themed_questions()
