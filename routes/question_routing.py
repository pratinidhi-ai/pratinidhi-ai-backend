"""
Question Bank API Routes
Handles all question bank related endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
import logging
from database.firebase_client import get_question_db_client
from helper.middleware import authenticate_request
import random
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

question_router = APIRouter(prefix="/api/questions", tags=["questions"])


# Helper function to fetch questions for SAT predictor quiz
def _fetch_questions_by_criteria(
    db, 
    subject_name: str, 
    sub_category: str, 
    difficulty_level: int, 
    num_questions: int
) -> List[Dict[str, Any]]:
    """
    Helper function to fetch questions based on specific criteria.
    Used internally for SAT predictor quiz composition.
    
    Args:
        db: Firestore database client
        subject_name: Subject (e.g., 'math', 'reading-and-writing')
        sub_category: Subcategory (e.g., 'algebra', 'craft-and-structure')
        difficulty_level: Difficulty level (1-5)
        num_questions: Number of questions to fetch
    
    Returns:
        List of question dictionaries
    """
    try:
        # Build the query path
        doc_path = f"{subject_name}|{sub_category}"
        
        # Build the collection reference
        questions_ref = (db.collection('question_bank')
                        .document(doc_path)
                        .collection('difficulty_levels')
                        .document(str(difficulty_level))
                        .collection('questions'))
        
        # Fetch questions using random_value for randomization
        rand_value = random.random()
        
        # Fields to exclude from response
        excluded_fields = [
            'question_exam', 'math_validation_result', 'validation_results',
            'created_at', 'random_value', 'updated_at', 'is_correct',
            'question_standard', 'llm_model_used'
        ]
        
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
                # Remove unnecessary fields
                for field in excluded_fields:
                    question_data.pop(field, None)
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
                    # Remove unnecessary fields
                    for field in excluded_fields:
                        question_data.pop(field, None)
                    questions.append(question_data)
        
        logger.info(f"Fetched {len(questions)}/{num_questions} questions for {subject_name}|{sub_category} (difficulty: {difficulty_level})")
        return questions
        
    except Exception as e:
        logger.error(f"Error fetching questions for {subject_name}|{sub_category}: {str(e)}")
        return []


# Pydantic models for request validation
class FetchQuizRequest(BaseModel):
    subject_name: str
    sub_category: str
    selected_difficulty_level: int = Field(..., ge=1, le=5)
    number_of_questions: int = Field(..., gt=0)
    theme: Optional[str] = None
    tags: Optional[List[str]] = Field(None, max_items=10)
    tag: Optional[str] = None
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None and not isinstance(v, list):
            raise ValueError('tags must be an array')
        return v


class ReportQuestionRequest(BaseModel):
    user_id: str
    question_id: str
    subject_name: str
    sub_category: str
    difficulty_level: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=1)
    
    @validator('comment')
    def validate_comment(cls, v):
        if not v or not v.strip():
            raise ValueError('Comment cannot be empty')
        return v.strip()


@question_router.get('/metadata')
def get_metadata(user: dict = Depends(authenticate_request)):
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'error': 'Database connection failed',
                    'message': 'Unable to connect to question bank database'
                }
            )
        
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
        
        return {
            'success': True,
            'metadata': metadata,
            'total_categories': doc_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching question bank metadata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Failed to fetch metadata',
                'message': str(e)
            }
        )


@question_router.post('/fetch-quiz')
def fetch_quiz(
    request_data: FetchQuizRequest,
    user: dict = Depends(authenticate_request)
):
    """
    Fetch quiz questions based on criteria
    
    Request Body (JSON):
    {
        "subject_name": "math",                    # Required
        "sub_category": "algebra",                 # Required
        "selected_difficulty_level": 3,            # Required (1-5)
        "number_of_questions": 10,                 # Required
        "theme": "Harry Potter",                   # Optional
        "tags": ["tag1", "tag2"]                   # Optional - array of tags (max 10)
        # OR
        "tag": "single_tag"                        # Optional - single tag
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
        # Extract parameters from validated model
        subject_name = request_data.subject_name
        sub_category = request_data.sub_category
        difficulty_level = request_data.selected_difficulty_level
        num_questions = request_data.number_of_questions
        theme = request_data.theme
        tags = request_data.tags
        tag = request_data.tag
        
        # Get database client
        db = get_question_db_client()
        
        if db is None:
            logger.error("Firestore client is not initialized")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'error': 'Database connection failed',
                    'message': 'Unable to connect to question bank database'
                }
            )
        
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
            questions_ref = questions_ref.where('theme', '==', theme)
        
        # Apply tag filters if provided
        if tags:
            # Use array-contains-any to match ANY of the provided tags
            questions_ref = questions_ref.where('tags', 'array_contains_any', tags)
        elif tag:
            # Single tag filter using array-contains
            questions_ref = questions_ref.where('tags', 'array_contains', tag)

        # Fetch questions using random_value for randomization
        rand_value = random.random()
        
        # Fields to exclude from response
        excluded_fields = [
            'question_exam', 'math_validation_result', 'validation_results',
            'created_at', 'random_value', 'updated_at', 'is_correct',
            'question_standard', 'llm_model_used'
        ]
        
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
                # Remove unnecessary fields
                for field in excluded_fields:
                    question_data.pop(field, None)
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
                    # Remove unnecessary fields
                    for field in excluded_fields:
                        question_data.pop(field, None)
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
        
        if tags:
            filters_applied['tags'] = tags
        elif tag:
            filters_applied['tag'] = tag
        
        logger.info(f"Fetched {len(questions)} questions for {subject_name}|{sub_category} (difficulty: {difficulty_level})")
        
        if len(questions) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    'success': False,
                    'message': 'No questions found matching the criteria',
                    'questions': [],
                    'count': 0,
                    'filters': filters_applied
                }
            )
        
        return {
            'success': True,
            'questions': questions,
            'count': len(questions),
            'filters': filters_applied
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quiz questions: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Failed to fetch questions',
                'message': str(e)
            }
        )


@question_router.post('/report-question')
def report_question(
    request_data: ReportQuestionRequest,
    user: dict = Depends(authenticate_request)
):
    """
    Report a question as incorrect or problematic
    
    Request Body (JSON):
    {
        "user_id": "user123",                      # Required - ID of the reporting user
        "question_id": "abc123",                   # Required - ID of the question
        "subject_name": "math",                    # Required
        "sub_category": "algebra",                 # Required
        "difficulty_level": 3,                     # Required (1-5)
        "comment": "The answer is incorrect..."    # Required - User's comment about the issue
    }
    
    Response:
    {
        "success": true,
        "report_id": "generated_report_id",
        "message": "Question report submitted successfully"
    }
    """
    try:
        # Get database client
        db = get_question_db_client()
        
        if db is None:
            logger.error("Firestore client is not initialized")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'error': 'Database connection failed',
                    'message': 'Unable to connect to question bank database'
                }
            )
        
        # Prepare report data
        report_data = {
            'question_id': request_data.question_id,
            'subject_name': request_data.subject_name,
            'sub_category': request_data.sub_category,
            'difficulty_level': request_data.difficulty_level,
            'comment': request_data.comment,
            'reported_by': request_data.user_id,
            'status': 'pending',  # Status: pending, reviewed, resolved
            'bounty_awarded': False,  # Will be set to True when verified and bounty given
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Store the report in question_reports collection
        doc_ref = db.collection('question_reports').add(report_data)
        report_id = doc_ref[1].id
        
        logger.info(f"Question report submitted: {report_id} for question {request_data.question_id} by user {request_data.user_id}")
        
        return {
            'success': True,
            'report_id': report_id,
            'message': 'Question report submitted successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting question report: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Failed to submit question report',
                'message': str(e)
            }
        )


@question_router.get('/sat_predictor_quiz')
def get_sat_predictor_quiz(user: dict = Depends(authenticate_request)):
    """
    Get SAT Predictor Quiz questions - a curated mix of questions across categories and difficulty levels.
    
    Returns a total of 24 questions:
    - Math: 12 questions (8 difficulty 5, 4 difficulty 1)
      - 3x algebra (diff 5), 1x algebra (diff 1)
      - 3x advanced_math (diff 5), 1x advanced_math (diff 1)
      - 1x problem_solving (diff 5), 1x problem_solving (diff 1)
      - 1x geometry-and-trigonometry (diff 5), 1x geometry-and-trigonometry (diff 1)
    
    - Reading & Writing: 12 questions (8 difficulty 5, 4 difficulty 1)
      - 2x craft-and-structure (diff 5), 1x craft-and-structure (diff 1)
      - 2x expression-of-ideas (diff 5), 1x expression-of-ideas (diff 1)
      - 2x information-and-ideas (diff 5), 1x information-and-ideas (diff 1)
      - 2x standard-english-conventions (diff 5), 1x standard-english-conventions (diff 1)
    
    Response:
    {
        "success": true,
        "questions": [array of 24 question objects],
        "count": 24,
        "composition": {detailed breakdown of questions by category}
    }
    """
    try:
        # Get database client
        db = get_question_db_client()
        
        if db is None:
            logger.error("Firestore client is not initialized")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'error': 'Database connection failed',
                    'message': 'Unable to connect to question bank database'
                }
            )
        
        # Define the composition of the SAT predictor quiz
        quiz_composition = [
            # Math questions
            {"subject": "math", "subcategory": "algebra", "difficulty": 5, "count": 3},
            {"subject": "math", "subcategory": "advanced-math", "difficulty": 5, "count": 3},
            {"subject": "math", "subcategory": "problem-solving-and-data-analysis", "difficulty": 5, "count": 1},
            {"subject": "math", "subcategory": "geometry-and-trigonometry", "difficulty": 5, "count": 1},
            {"subject": "math", "subcategory": "algebra", "difficulty": 1, "count": 1},
            {"subject": "math", "subcategory": "advanced-math", "difficulty": 1, "count": 1},
            {"subject": "math", "subcategory": "problem-solving-and-data-analysis", "difficulty": 1, "count": 1},
            {"subject": "math", "subcategory": "geometry-and-trigonometry", "difficulty": 1, "count": 1},
            
            # Reading and Writing questions
            {"subject": "reading-and-writing", "subcategory": "craft-and-structure", "difficulty": 5, "count": 2},
            {"subject": "reading-and-writing", "subcategory": "expression-of-ideas", "difficulty": 5, "count": 2},
            {"subject": "reading-and-writing", "subcategory": "information-and-ideas", "difficulty": 5, "count": 2},
            {"subject": "reading-and-writing", "subcategory": "standard-english-conventions", "difficulty": 5, "count": 2},
            {"subject": "reading-and-writing", "subcategory": "craft-and-structure", "difficulty": 1, "count": 1},
            {"subject": "reading-and-writing", "subcategory": "expression-of-ideas", "difficulty": 1, "count": 1},
            {"subject": "reading-and-writing", "subcategory": "information-and-ideas", "difficulty": 1, "count": 1},
            {"subject": "reading-and-writing", "subcategory": "standard-english-conventions", "difficulty": 1, "count": 1},
        ]
        
        all_questions = []
        composition_details = []
        
        # Fetch questions for each category
        for spec in quiz_composition:
            questions = _fetch_questions_by_criteria(
                db,
                spec["subject"],
                spec["subcategory"],
                spec["difficulty"],
                spec["count"]
            )
            
            all_questions.extend(questions)
            composition_details.append({
                "subject": spec["subject"],
                "subcategory": spec["subcategory"],
                "difficulty_level": spec["difficulty"],
                "requested": spec["count"],
                "fetched": len(questions)
            })
        
        # Shuffle all questions for randomization
        random.shuffle(all_questions)
        
        logger.info(f"SAT Predictor Quiz: Fetched {len(all_questions)} total questions")
        
        if len(all_questions) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    'success': False,
                    'message': 'No questions found for SAT predictor quiz',
                    'questions': [],
                    'count': 0,
                    'composition': composition_details
                }
            )
        
        return {
            'success': True,
            'questions': all_questions,
            'count': len(all_questions),
            'composition': composition_details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating SAT predictor quiz: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Failed to generate SAT predictor quiz',
                'message': str(e)
            }
        )