"""
Test script for new Question Bank APIs
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_get_metadata():
    """Test the get_metadata API endpoint logic"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Get Metadata")
    logger.info("="*60)
    
    from database.firebase_client import get_question_db_client
    
    try:
        db = get_question_db_client()
        
        if db is None:
            logger.error("❌ Failed to initialize Firestore client")
            return False
        
        # Fetch all documents from question_bank collection
        docs = db.collection('question_bank').stream()
        
        metadata = {}
        doc_count = 0
        
        for doc in docs:
            doc_id = doc.id
            doc_data = doc.to_dict()
            
            if doc_data:
                # Convert datetime objects to ISO format strings
                if 'created_at' in doc_data and hasattr(doc_data['created_at'], 'isoformat'):
                    doc_data['created_at'] = doc_data['created_at'].isoformat()
                if 'updated_at' in doc_data and hasattr(doc_data['updated_at'], 'isoformat'):
                    doc_data['updated_at'] = doc_data['updated_at'].isoformat()
                
                metadata[doc_id] = doc_data
                doc_count += 1
        
        logger.info(f"✅ Retrieved metadata for {doc_count} categories")
        logger.info(f"Categories: {list(metadata.keys())}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_fetch_quiz():
    """Test the fetch_quiz API endpoint logic"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Fetch Quiz")
    logger.info("="*60)
    
    from database.firebase_client import get_question_db_client
    import random
    
    # Test parameters
    subject_name = "math"
    sub_category = "algebra"
    difficulty_level = 3
    num_questions = 5
    theme = None  # Test without theme first
    
    logger.info(f"Parameters:")
    logger.info(f"  - Subject: {subject_name}")
    logger.info(f"  - Sub Category: {sub_category}")
    logger.info(f"  - Difficulty: {difficulty_level}")
    logger.info(f"  - Number of Questions: {num_questions}")
    logger.info(f"  - Theme: {theme or 'None'}")
    
    try:
        db = get_question_db_client()
        
        if db is None:
            logger.error("❌ Failed to initialize Firestore client")
            return False
        
        # Build the query path
        doc_path = f"{subject_name}|{sub_category}"
        
        # Build the collection reference
        questions_ref = (db.collection('question_bank')
                        .document(doc_path)
                        .collection('difficulty_levels')
                        .document(str(difficulty_level))
                        .collection('questions'))
        
        # Apply theme filter if provided
        if theme:
            questions_ref = questions_ref.where('question_theme', '==', theme)
        
        # Fetch questions using random_value
        rand_value = random.random()
        logger.info(f"Random value for selection: {rand_value:.4f}")
        
        # First pass
        query_first = (questions_ref
                      .where('random_value', '>=', rand_value)
                      .order_by('random_value')
                      .limit(num_questions))
        
        docs_first = list(query_first.stream())
        questions = []
        
        for doc in docs_first:
            question_data = doc.to_dict()
            if question_data:
                question_data['id'] = doc.id
                questions.append(question_data)
        
        # Second pass if needed
        if len(questions) < num_questions:
            remaining = num_questions - len(questions)
            query_second = (questions_ref
                           .where('random_value', '<', rand_value)
                           .order_by('random_value')
                           .limit(remaining))
            
            docs_second = list(query_second.stream())
            
            for doc in docs_second:
                question_data = doc.to_dict()
                if question_data:
                    question_data['id'] = doc.id
                    questions.append(question_data)
        
        # Shuffle for additional randomness
        random.shuffle(questions)
        
        logger.info(f"\n✅ Fetched {len(questions)} questions")
        
        if questions:
            logger.info(f"\nFirst question sample:")
            first_q = questions[0]
            logger.info(f"  - ID: {first_q.get('id', 'N/A')[:20]}...")
            logger.info(f"  - Type: {first_q.get('question_type', 'N/A')}")
            logger.info(f"  - Theme: {first_q.get('question_theme', 'N/A')}")
            logger.info(f"  - Standard: {first_q.get('question_standard', 'N/A')}")
            logger.info(f"  - Random Value: {first_q.get('random_value', 'N/A')}")
            
            # Check if question has required fields
            logger.info(f"\nQuestion fields: {list(first_q.keys())[:10]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_fetch_quiz_with_theme():
    """Test the fetch_quiz API with theme filter"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Fetch Quiz with Theme")
    logger.info("="*60)
    
    from database.firebase_client import get_question_db_client
    import random
    
    # Test parameters with theme
    subject_name = "math"
    sub_category = "algebra"
    difficulty_level = 2
    num_questions = 3
    theme = "Harry Potter"  # Use a theme from the metadata
    
    logger.info(f"Parameters:")
    logger.info(f"  - Subject: {subject_name}")
    logger.info(f"  - Sub Category: {sub_category}")
    logger.info(f"  - Difficulty: {difficulty_level}")
    logger.info(f"  - Number of Questions: {num_questions}")
    logger.info(f"  - Theme: {theme}")
    
    try:
        db = get_question_db_client()
        
        if db is None:
            logger.error("❌ Failed to initialize Firestore client")
            return False
        
        # Build the query path
        doc_path = f"{subject_name}|{sub_category}"
        
        # Build the collection reference with theme filter
        questions_ref = (db.collection('question_bank')
                        .document(doc_path)
                        .collection('difficulty_levels')
                        .document(str(difficulty_level))
                        .collection('questions')
                        .where('question_theme', '==', theme))
        
        # Fetch questions
        rand_value = random.random()
        
        query_first = (questions_ref
                      .where('random_value', '>=', rand_value)
                      .order_by('random_value')
                      .limit(num_questions))
        
        docs_first = list(query_first.stream())
        questions = []
        
        for doc in docs_first:
            question_data = doc.to_dict()
            if question_data:
                question_data['id'] = doc.id
                questions.append(question_data)
        
        if len(questions) < num_questions:
            remaining = num_questions - len(questions)
            query_second = (questions_ref
                           .where('random_value', '<', rand_value)
                           .order_by('random_value')
                           .limit(remaining))
            
            docs_second = list(query_second.stream())
            
            for doc in docs_second:
                question_data = doc.to_dict()
                if question_data:
                    question_data['id'] = doc.id
                    questions.append(question_data)
        
        random.shuffle(questions)
        
        logger.info(f"\n✅ Fetched {len(questions)} questions with theme '{theme}'")
        
        if questions:
            logger.info(f"\nVerifying theme in all questions:")
            for i, q in enumerate(questions, 1):
                q_theme = q.get('question_theme', 'N/A')
                logger.info(f"  Question {i}: Theme = {q_theme}")
                if q_theme != theme:
                    logger.warning(f"    ⚠️  Theme mismatch!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("QUESTION BANK API TESTS")
    logger.info("="*60)
    
    results = []
    
    # Run all tests
    results.append(("Get Metadata", test_get_metadata()))
    results.append(("Fetch Quiz (No Theme)", test_fetch_quiz()))
    results.append(("Fetch Quiz (With Theme)", test_fetch_quiz_with_theme()))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        logger.info("\n🎉 All tests passed!")
    else:
        logger.info("\n⚠️  Some tests failed. Please review the errors above.")
