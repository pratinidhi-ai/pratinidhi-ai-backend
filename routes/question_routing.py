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

logger = logging.getLogger(__name__)

question_router = APIRouter(prefix="/question", tags=["question"])


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


@question_router.get('/metadata')
async def get_metadata(user: dict = Depends(authenticate_request)):
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
async def fetch_quiz(
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
