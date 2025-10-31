"""
Quick test for question bank database structure
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.firebase_client import get_question_db_client

def quick_test():
    print("Testing question bank structure...")
    
    db = get_question_db_client()
    
    # Test 1: Get a specific category document
    doc_path = "math|algebra"
    doc_ref = db.collection('question_bank').document(doc_path)
    doc = doc_ref.get()
    
    if doc.exists:
        print(f"✅ Document '{doc_path}' exists")
        data = doc.to_dict()
        print(f"   Total questions: {data.get('total_questions')}")
    
    # Test 2: Check if difficulty_levels subcollection exists
    difficulty_ref = doc_ref.collection('difficulty_levels')
    difficulty_docs = list(difficulty_ref.limit(1).stream())
    
    if difficulty_docs:
        print(f"✅ Difficulty levels subcollection exists")
        print(f"   First difficulty doc ID: {difficulty_docs[0].id}")
    
    # Test 3: Check if questions subcollection exists
    questions_ref = doc_ref.collection('difficulty_levels').document('3').collection('questions')
    questions = list(questions_ref.limit(2).stream())
    
    if questions:
        print(f"✅ Questions subcollection exists")
        print(f"   Found {len(questions)} sample questions")
        first_q = questions[0].to_dict()
        print(f"   First question fields: {list(first_q.keys())[:5]}")
    else:
        print("❌ No questions found in subcollection")
    
    print("\nTest complete!")

if __name__ == "__main__":
    quick_test()
