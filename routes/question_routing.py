"""
Question Bank API Routes
Handles all question bank related endpoints
"""

from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any
from database.firebase_client import get_question_db_client
from helper.middleware import authenticate_request
import random

logger = logging.getLogger(__name__)

question_bp = Blueprint('question', __name__)


@question_bp.route('/metadata', methods=['GET'])
@authenticate_request
def get_metadata():
    """
    Get all question bank metadata
    Returns all documents from 'question_bank' collection with their statistics
    
    Response format:
    {
        "subject|subcategory": {
            "subject": "math",
            "sub_category": "algebra",
            "total_questions": 1948,
            "difficulty_distribution": {1: 436, 2: 401, ...},
            "theme_distribution": {"Harry Potter": 331, ...},
            "created_at": "2025-10-27T04:39:32.753918+00:00",
            "updated_at": "2025-10-30T03:59:34.952684+00:00"
        },
        ...
    }
    """
    try:
        db = get_question_db_client()
        
        if db is None:
            logger.error("Firestore client is not initialized")
            return jsonify({
                'error': 'Database connection failed',
                'message': 'Unable to connect to question bank database'
            }), 500
        
        # Fetch all documents from question_bank collection
        docs = db.collection('question_bank').stream()
        
        metadata = {}
        doc_count = 0
        
        for doc in docs:
            doc_id = doc.id
            doc_data = doc.to_dict()
            
            if doc_data:
                # Convert datetime objects to ISO format strings for JSON serialization
                if 'created_at' in doc_data and hasattr(doc_data['created_at'], 'isoformat'):
                    doc_data['created_at'] = doc_data['created_at'].isoformat()
                if 'updated_at' in doc_data and hasattr(doc_data['updated_at'], 'isoformat'):
                    doc_data['updated_at'] = doc_data['updated_at'].isoformat()
                
                metadata[doc_id] = doc_data
                doc_count += 1
        
        logger.info(f"Retrieved metadata for {doc_count} question bank categories")
        
        return jsonify({
            'success': True,
            'metadata': metadata,
            'total_categories': doc_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching question bank metadata: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch metadata',
            'message': str(e)
        }), 500


@question_bp.route('/fetch-quiz', methods=['POST'])
@authenticate_request
def fetch_quiz():
    """
    Fetch quiz questions based on criteria
    
    Request Body (JSON):
    {
        "subject_name": "math",                    # Required
        "sub_category": "algebra",                 # Required
        "selected_difficulty_level": 3,            # Required (1-5)
        "number_of_questions": 10,                 # Required
        "theme": "Harry Potter"                    # Optional
    }
    
    Response:
    {
        "success": true,
        "questions": [array of question objects],
        "count": 10,
        "filters": {applied filters}
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body must be JSON'
            }), 400
        
        # Validate required parameters
        required_params = ['subject_name', 'sub_category', 'selected_difficulty_level', 'number_of_questions']
        missing_params = [param for param in required_params if param not in data]
        
        if missing_params:
            return jsonify({
                'error': 'Missing required parameters',
                'missing': missing_params
            }), 400
        
        # Extract parameters
        subject_name = data['subject_name']
        sub_category = data['sub_category']
        difficulty_level = data['selected_difficulty_level']
        num_questions = data['number_of_questions']
        theme = data.get('theme')  # Optional
        
        # Validate number_of_questions
        try:
            num_questions = int(num_questions)
            if num_questions <= 0:
                raise ValueError("Must be positive")
        except (ValueError, TypeError):
            return jsonify({
                'error': 'Invalid number_of_questions',
                'message': 'Must be a positive integer'
            }), 400
        
        # Validate difficulty_level
        try:
            difficulty_level = int(difficulty_level)
            if difficulty_level not in [1, 2, 3, 4, 5]:
                raise ValueError("Must be between 1 and 5")
        except (ValueError, TypeError):
            return jsonify({
                'error': 'Invalid difficulty level',
                'message': 'Must be an integer between 1 and 5'
            }), 400
        
        # Get database client
        db = get_question_db_client()
        
        if db is None:
            logger.error("Firestore client is not initialized")
            return jsonify({
                'error': 'Database connection failed',
                'message': 'Unable to connect to question bank database'
            }), 500
        
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
        
        # Fetch questions using random_value for randomization
        # Use a two-pass approach to ensure we get enough questions
        rand_value = random.random()
        
        # First pass: Get questions with random_value >= rand_value
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
                # Convert datetime fields
                if 'created_at' in question_data and hasattr(question_data['created_at'], 'isoformat'):
                    question_data['created_at'] = question_data['created_at'].isoformat()
                if 'updated_at' in question_data and hasattr(question_data['updated_at'], 'isoformat'):
                    question_data['updated_at'] = question_data['updated_at'].isoformat()
                questions.append(question_data)
        
        # Second pass: If we need more questions, fetch with random_value < rand_value
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
                    # Convert datetime fields
                    if 'created_at' in question_data and hasattr(question_data['created_at'], 'isoformat'):
                        question_data['created_at'] = question_data['created_at'].isoformat()
                    if 'updated_at' in question_data and hasattr(question_data['updated_at'], 'isoformat'):
                        question_data['updated_at'] = question_data['updated_at'].isoformat()
                    questions.append(question_data)
        
        # Shuffle the results for additional randomness
        random.shuffle(questions)
        
        # Prepare response
        filters_applied = {
            'subject_name': subject_name,
            'sub_category': sub_category,
            'difficulty_level': difficulty_level,
            'requested_count': num_questions
        }
        
        if theme:
            filters_applied['theme'] = theme
        
        logger.info(f"Fetched {len(questions)} questions for {subject_name}|{sub_category} (difficulty: {difficulty_level})")
        
        if len(questions) == 0:
            return jsonify({
                'success': False,
                'message': 'No questions found matching the criteria',
                'questions': [],
                'count': 0,
                'filters': filters_applied
            }), 404
        
        return jsonify({
            'success': True,
            'questions': questions,
            'count': len(questions),
            'filters': filters_applied
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching quiz questions: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to fetch questions',
            'message': str(e)
        }), 500
