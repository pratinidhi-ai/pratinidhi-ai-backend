"""
Analytics API Routes
Handles all analytics-related endpoints for student performance tracking
"""

from flask import Blueprint, jsonify, request
import logging
import threading
import uuid
from typing import Dict, Any

from helper.middleware import authenticate_request
from database.analytics_db import get_analytics_db
from database.user_db import get_user_db
from models.analytics_schema import QuizSubmission, TagDetail

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__)

# Complete taxonomy of all available tags organized by subject and sub_category
# This ensures we consider tags that haven't been attempted yet
SUBJECT_TAG_TAXONOMY = {
    "math": {
        "algebra": [
            "single-variable-linear-equations",
            "linear-inequalities",
            "slope-intercept",
            "graphing-linear-equations",
            "parallel-perpendicular-lines",
            "systems-of-equations",
            "systems-of-inequalities",
            "linear-word-problems",
            "system-word-problems",
            "literal-equations",
            "inequality-word-problems",
            "mixture-problems",
            "distance-rate-time",
            "direct-variation",
            "age-problems"
        ],
        "advanced-math": [
            "absolute-value-equations",
            "absolute-value-inequalities",
            "quadratic-equations",
            "factoring-polynomials",
            "expanding-polynomials",
            "rational-expressions",
            "rational-equations",
            "radical-equations",
            "radical-simplification",
            "exponent-properties",
            "exponential-equations",
            "exponential-models",
            "function-notation",
            "function-composition",
            "nonlinear-systems"
        ],
        "problem-solving-and-data-analysis": [
            "ratio-proportion",
            "unit-conversion",
            "percentage-calculation",
            "mean-median",
            "variability",
            "data-distributions",
            "scatterplots",
            "best-fit-line",
            "probability",
            "conditional-probability",
            "two-way-tables",
            "sampling-methods",
            "experimental-design",
            "margin-of-error",
            "statistical-inference"
        ],
        "geometry-and-trigonometry": [
            "area-of-polygons",
            "perimeter",
            "angle-relationships",
            "triangle-angles",
            "similar-triangles",
            "right-triangle-trigonometry",
            "volume-of-solids",
            "distance-and-midpoint",
            "pythagorean-theorem",
            "special-right-triangles",
            "polygon-angles",
            "circle-measurements",
            "circle-angles",
            "circle-equations",
            "surface-area"
        ]
    },
    "reading-and-writing": {
        "craft-and-structure": [
            "word-in-context",
            "phrase-in-context",
            "figurative-language",
            "word-choice-effect",
            "text-structure",
            "main-purpose",
            "author-tone",
            "author-attitude",
            "point-of-view",
            "sentence-function",
            "author-technique",
            "argument-structure",
            "cross-text-comparison",
            "cross-text-synthesis",
            "intended-audience"
        ],
        "information-and-ideas": [
            "main-idea",
            "supporting-detail",
            "inference",
            "evidence-support",
            "graph-interpretation",
            "cause-and-effect",
            "compare-and-contrast",
            "passage-completion",
            "draw-conclusion",
            "author-stance",
            "hypothetical-application",
            "identify-claim",
            "paragraph-main-idea",
            "passage-title",
            "not-in-passage"
        ],
        "standard-english-conventions": [
            "subject-verb-agreement",
            "verb-tense",
            "pronoun-antecedent",
            "pronoun-case",
            "parallel-structure",
            "misplaced-modifier",
            "faulty-comparison",
            "comma-usage",
            "semicolon-colon-usage",
            "apostrophe-usage",
            "sentence-fragment",
            "run-on-sentence",
            "idiomatic-usage",
            "diction-errors",
            "adjective-vs-adverb"
        ],
        "expression-of-ideas": [
            "conciseness",
            "clarity",
            "precise-wording",
            "tone-consistency",
            "relevance",
            "supporting-evidence",
            "introduction-focus",
            "conclusion-summary",
            "logical-flow",
            "transitions",
            "sentence-combination",
            "paragraph-organization",
            "integrating-information",
            "active-voice",
            "formal-tone"
        ]
    }
}


def process_quiz_submission_background(submission_data: dict, request_id: str):
    """
    Background task to process quiz submission and store analytics
    This runs asynchronously after sending immediate response to user
    
    Args:
        submission_data: The validated quiz submission data
        request_id: Unique ID for tracking this submission
    """
    try:
        logger.info(f"[{request_id}] Starting background processing for student {submission_data['student_id']}")
        
        # Convert tag_wise_details to TagDetail objects with score calculation
        tag_details = []
        difficulty_level = submission_data['difficulty_level']
        
        for tag_data in submission_data['tag_wise_details']:
            # Calculate score and total_possible_score for this tag
            total_questions = tag_data['total_questions']
            correct_answers = tag_data['correct_answers']
            
            # Score = correct_answers * difficulty_level
            score = correct_answers * difficulty_level
            total_possible_score = total_questions * difficulty_level
            
            tag_detail = TagDetail(
                tag=tag_data['tag'],
                total_questions=total_questions,
                correct_answers=correct_answers,
                score=score,
                total_possible_score=total_possible_score
            )
            tag_details.append(tag_detail)
        
        # Create QuizSubmission object
        submission = QuizSubmission(
            student_id=submission_data['student_id'],
            time_spent=submission_data['time_spent'],
            number_of_questions=submission_data['number_of_questions'],
            number_of_correct_answers=submission_data['number_of_correct_answers'],
            subject=submission_data['subject'],
            sub_category=submission_data['sub_category'],
            difficulty_level=difficulty_level,
            tag_wise_details=tag_details,
            correct_question_ids=submission_data['correct_question_ids'],
            incorrect_question_ids=submission_data['incorrect_question_ids']
        )
        
        # Submit to analytics database
        analytics_db = get_analytics_db()
        success, session_id = analytics_db.submit_quiz_analytics(submission)
        
        if success:
            logger.info(f"[{request_id}] Successfully processed quiz analytics for student {submission_data['student_id']}, session {session_id}")
        else:
            logger.error(f"[{request_id}] Failed to submit analytics for student {submission_data['student_id']}")
            
    except Exception as e:
        logger.error(f"[{request_id}] Error in background processing: {str(e)}")
        import traceback
        traceback.print_exc()


@analytics_bp.route('/submit-quiz', methods=['POST'])
@authenticate_request
def submit_quiz():
    """
    Submit quiz results and update analytics (ASYNC)
    
    This endpoint accepts the quiz data, validates it, and immediately returns a response
    with a request_id. The actual processing and storage happens asynchronously in the background.
    
    Request Body (JSON):
    {
        "student_id": "string",
        "time_spent": integer (seconds),
        "number_of_questions": integer,
        "number_of_correct_answers": integer,
        "subject": "string" (e.g., "math", "reading-and-writing"),
        "sub_category": "string" (e.g., "algebra", "craft-and-structure"),
        "difficulty_level": integer (1-5),
        "tag_wise_details": [
            {
                "tag": "string",
                "total_questions": integer,
                "correct_answers": integer,
                "score": integer (optional, will be calculated),
                "total_possible_score": integer (optional, will be calculated)
            }
        ],
        "correct_question_ids": ["string"],
        "incorrect_question_ids": ["string"]
    }
    
    Response:
    {
        "success": true,
        "message": "Quiz submission received and is being processed",
        "request_id": "uuid-string",
        "estimated_score": integer,
        "estimated_accuracy": float
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body must be JSON'
            }), 400
        
        # Validate required fields
        required_fields = [
            'student_id', 'time_spent', 'number_of_questions',
            'number_of_correct_answers', 'subject', 'sub_category',
            'difficulty_level', 'tag_wise_details',
            'correct_question_ids', 'incorrect_question_ids'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing': missing_fields
            }), 400
        
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(data['student_id']):
            return jsonify({
                'error': 'User not found',
                'message': f"Student with ID {data['student_id']} does not exist"
            }), 404
        
        # Basic validation of data structure
        try:
            difficulty_level = data['difficulty_level']
            
            # Quick calculation for immediate feedback (estimated)
            estimated_score = 0
            estimated_total_possible = 0
            
            for tag_data in data['tag_wise_details']:
                if 'tag' not in tag_data or 'total_questions' not in tag_data or 'correct_answers' not in tag_data:
                    return jsonify({
                        'error': 'Invalid tag_wise_details',
                        'message': 'Each tag detail must have tag, total_questions, and correct_answers'
                    }), 400
                
                correct = tag_data['correct_answers']
                total = tag_data['total_questions']
                estimated_score += correct * difficulty_level
                estimated_total_possible += total * difficulty_level
            
            estimated_accuracy = round((data['number_of_correct_answers'] / data['number_of_questions'] * 100), 2) if data['number_of_questions'] > 0 else 0
            
        except (ValueError, KeyError, TypeError) as ve:
            return jsonify({
                'error': 'Invalid data',
                'message': str(ve)
            }), 400
        
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())
        
        # Start background processing in a separate thread
        background_thread = threading.Thread(
            target=process_quiz_submission_background,
            args=(data, request_id),
            daemon=True  # Daemon thread won't prevent app shutdown
        )
        background_thread.start()
        
        logger.info(f"[{request_id}] Quiz submission accepted for student {data['student_id']}, processing in background")
        
        # Return immediate response
        return jsonify({
            'success': True,
            'message': 'Quiz submission received and is being processed',
            'request_id': request_id,
            'estimated_score': estimated_score,
            'estimated_total_possible_score': estimated_total_possible,
            'estimated_accuracy': estimated_accuracy,
            'subject': data['subject'],
            'sub_category': data['sub_category'],
            'difficulty_level': data['difficulty_level']
        }), 202  # 202 Accepted - indicates async processing
        
    except Exception as e:
        logger.error(f"Error accepting quiz submission: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to accept quiz submission',
            'message': str(e)
        }), 500


@analytics_bp.route('/performance-summary/<student_id>', methods=['GET'])
@authenticate_request
def get_performance_summary(student_id: str):
    """
    Get overall performance summary for a student
    
    URL Parameters:
        student_id: The student's user ID
    
    Query Parameters:
        subject: Optional - filter by subject
        sub_category: Optional - filter by sub_category (requires subject)
    
    Response:
    {
        "success": true,
        "summary": {performance data with hierarchical structure}
    }
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(student_id):
            return jsonify({
                'error': 'User not found',
                'message': f"Student with ID {student_id} does not exist"
            }), 404
        
        # Get performance summary
        analytics_db = get_analytics_db()
        summary = analytics_db.get_performance_summary(student_id)
        
        if not summary:
            return jsonify({
                'success': True,
                'message': 'No analytics data found for this student',
                'summary': None
            }), 200
        
        # Filter if subject/sub_category specified
        subject_filter = request.args.get('subject')
        sub_category_filter = request.args.get('sub_category')
        
        if subject_filter:
            subjects_data = summary.get('subjects', {})
            if subject_filter in subjects_data:
                filtered_subject = subjects_data[subject_filter]
                
                if sub_category_filter:
                    sub_cats = filtered_subject.get('sub_categories', {})
                    if sub_category_filter in sub_cats:
                        summary = {
                            'student_id': summary['student_id'],
                            'subject': subject_filter,
                            'sub_category': sub_category_filter,
                            'data': sub_cats[sub_category_filter]
                        }
                    else:
                        return jsonify({
                            'success': False,
                            'message': f'No data found for sub_category: {sub_category_filter}'
                        }), 404
                else:
                    summary = {
                        'student_id': summary['student_id'],
                        'subject': subject_filter,
                        'data': filtered_subject
                    }
            else:
                return jsonify({
                    'success': False,
                    'message': f'No data found for subject: {subject_filter}'
                }), 404
        
        return jsonify({
            'success': True,
            'summary': summary
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting performance summary for {student_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to get performance summary',
            'message': str(e)
        }), 500


@analytics_bp.route('/activity-logs/<student_id>', methods=['GET'])
@authenticate_request
def get_activity_logs(student_id: str):
    """
    Get activity logs (quiz history) for a student
    
    URL Parameters:
        student_id: The student's user ID
    
    Query Parameters:
        limit: Optional - maximum number of logs to return (default 50, max 100)
    
    Response:
    {
        "success": true,
        "logs": [array of quiz sessions],
        "count": integer
    }
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(student_id):
            return jsonify({
                'error': 'User not found',
                'message': f"Student with ID {student_id} does not exist"
            }), 404
        
        # Get limit parameter
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 100)  # Cap at 100
        
        # Get activity logs
        analytics_db = get_analytics_db()
        logs = analytics_db.get_activity_logs(student_id, limit=limit)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting activity logs for {student_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to get activity logs',
            'message': str(e)
        }), 500


@analytics_bp.route('/correct-questions/<student_id>', methods=['GET'])
@authenticate_request
def get_correct_questions(student_id: str):
    """
    Get list of correctly answered question IDs for a student
    
    URL Parameters:
        student_id: The student's user ID
    
    Query Parameters:
        subject: Optional - filter by subject
        sub_category: Optional - filter by sub_category (requires subject)
    
    Response:
    {
        "success": true,
        "correct_questions": {
            "subject|sub_category": ["question_id1", "question_id2", ...]
        }
    }
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(student_id):
            return jsonify({
                'error': 'User not found',
                'message': f"Student with ID {student_id} does not exist"
            }), 404
        
        # Get filters
        subject = request.args.get('subject')
        sub_category = request.args.get('sub_category')
        
        # Get correct questions
        analytics_db = get_analytics_db()
        correct_questions = analytics_db.get_correct_questions(
            student_id, 
            subject=subject, 
            sub_category=sub_category
        )
        
        return jsonify({
            'success': True,
            'correct_questions': correct_questions
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting correct questions for {student_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to get correct questions',
            'message': str(e)
        }), 500


@analytics_bp.route('/incorrect-questions/<student_id>', methods=['GET'])
@authenticate_request
def get_incorrect_questions(student_id: str):
    """
    Get list of incorrectly answered question IDs for a student
    
    URL Parameters:
        student_id: The student's user ID
    
    Query Parameters:
        subject: Optional - filter by subject
        sub_category: Optional - filter by sub_category (requires subject)
    
    Response:
    {
        "success": true,
        "incorrect_questions": {
            "subject|sub_category": ["question_id1", "question_id2", ...]
        }
    }
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(student_id):
            return jsonify({
                'error': 'User not found',
                'message': f"Student with ID {student_id} does not exist"
            }), 404
        
        # Get filters
        subject = request.args.get('subject')
        sub_category = request.args.get('sub_category')
        
        # Get incorrect questions
        analytics_db = get_analytics_db()
        incorrect_questions = analytics_db.get_incorrect_questions(
            student_id,
            subject=subject,
            sub_category=sub_category
        )
        
        return jsonify({
            'success': True,
            'incorrect_questions': incorrect_questions
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting incorrect questions for {student_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to get incorrect questions',
            'message': str(e)
        }), 500


@analytics_bp.route('/stats/<student_id>', methods=['GET'])
@authenticate_request
def get_quick_stats(student_id: str):
    """
    Get quick stats overview for a student
    
    URL Parameters:
        student_id: The student's user ID
    
    Response:
    {
        "success": true,
        "stats": {
            "total_quizzes": integer,
            "total_time_spent_hours": float,
            "overall_accuracy": float,
            "subjects": {
                "subject_name": {
                    "accuracy": float,
                    "quizzes_taken": integer
                }
            }
        }
    }
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(student_id):
            return jsonify({
                'error': 'User not found',
                'message': f"Student with ID {student_id} does not exist"
            }), 404
        
        # Get performance summary
        analytics_db = get_analytics_db()
        summary = analytics_db.get_performance_summary(student_id)
        
        if not summary:
            return jsonify({
                'success': True,
                'message': 'No analytics data found for this student',
                'stats': None
            }), 200
        
        # Calculate quick stats
        stats = {
            'total_quizzes': summary.get('total_quizzes', 0),
            'total_time_spent_hours': round(summary.get('total_time_spent', 0) / 3600, 2),
            'subjects': {}
        }
        
        # Calculate overall accuracy
        total_correct = 0
        total_attempted = 0
        
        subjects_data = summary.get('subjects', {})
        for subject_name, subject_data in subjects_data.items():
            correct = subject_data.get('total_correct_answers', 0)
            attempted = subject_data.get('total_questions_attempted', 0)
            
            total_correct += correct
            total_attempted += attempted
            
            stats['subjects'][subject_name] = {
                'accuracy': round((correct / attempted * 100), 2) if attempted > 0 else 0,
                'quizzes_taken': subject_data.get('quiz_count', 0),
                'score_percentage': round(
                    (subject_data.get('total_score', 0) / subject_data.get('total_possible_score', 1) * 100), 2
                ) if subject_data.get('total_possible_score', 0) > 0 else 0
            }
        
        stats['overall_accuracy'] = round((total_correct / total_attempted * 100), 2) if total_attempted > 0 else 0
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting quick stats for {student_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to get quick stats',
            'message': str(e)
        }), 500


@analytics_bp.route('/get-my-strength', methods=['POST'])
@authenticate_request
def get_my_strength():
    """
    Get the user's strongest tag in a subject
    
    Request Body (JSON):
    {
        "user_id": "string",
        "subject": "string" (e.g., "math", "reading-and-writing")
    }
    
    Response:
    {
        "success": true,
        "strength": {
            "subject": "math",
            "sub_category": "algebra",
            "tag": "linear-equations",
            "total_score": 120,
            "score_percentage": 95.5,
            "total_questions_attempted": 25,
            "accuracy": 96.0
        }
    }
    
    Returns empty string if no data available
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body must be JSON'
            }), 400
        
        # Validate required fields
        user_id = data.get('user_id')
        subject = data.get('subject')
        
        if not user_id or not subject:
            return jsonify({
                'error': 'Missing required fields',
                'message': 'user_id and subject are required'
            }), 400
        
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(user_id):
            return jsonify({
                'error': 'User not found',
                'message': f"Student with ID {user_id} does not exist"
            }), 404
        
        # Get performance summary
        analytics_db = get_analytics_db()
        summary = analytics_db.get_performance_summary(user_id)
        
        if not summary or 'subjects' not in summary:
            return jsonify({
                'success': True,
                'strength': ""
            }), 200
        
        # Check if subject exists
        subjects_data = summary.get('subjects', {})
        if subject not in subjects_data:
            return jsonify({
                'success': True,
                'strength': ""
            }), 200
        
        subject_data = subjects_data[subject]
        sub_categories = subject_data.get('sub_categories', {})
        
        if not sub_categories:
            return jsonify({
                'success': True,
                'strength': ""
            }), 200
        
        # Find the strongest tag
        best_tag = None
        best_score = -1
        best_sub_category = None
        
        for sub_cat_name, sub_cat_data in sub_categories.items():
            tags = sub_cat_data.get('tags', {})
            
            for tag_name, tag_data in tags.items():
                total_score = tag_data.get('total_score', 0)
                score_percentage = tag_data.get('score_percentage', 0)
                total_questions = tag_data.get('total_questions_attempted', 0)
                
                # Skip if no data
                if total_score == 0 and score_percentage == 0:
                    continue
                
                # Calculate combined score: weight both total_score and score_percentage
                # Higher total_score shows more practice, higher percentage shows mastery
                # Formula: (score_percentage * 0.7) + (min(total_score, 100) * 0.3)
                # This balances percentage mastery with volume of correct answers
                normalized_total_score = min(total_score, 100)  # Cap at 100 to prevent domination
                combined_score = (score_percentage * 0.7) + (normalized_total_score * 0.3)
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_tag = tag_name
                    best_sub_category = sub_cat_name
                    best_tag_data = tag_data
        
        # If no tag found (all zeros)
        if best_tag is None:
            return jsonify({
                'success': True,
                'strength': ""
            }), 200
        
        # Return the strongest tag
        return jsonify({
            'success': True,
            'strength': {
                'subject': subject,
                'sub_category': best_sub_category,
                'tag': best_tag,
                'total_score': best_tag_data.get('total_score', 0),
                'score_percentage': best_tag_data.get('score_percentage', 0),
                'total_questions_attempted': best_tag_data.get('total_questions_attempted', 0),
                'accuracy': best_tag_data.get('accuracy', 0)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting strength for user: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to get strength',
            'message': str(e)
        }), 500


@analytics_bp.route('/get-my-weakness', methods=['POST'])
@authenticate_request
def get_my_weakness():
    """
    Get the user's weakest tag in a subject
    
    Request Body (JSON):
    {
        "user_id": "string",
        "subject": "string" (e.g., "math", "reading-and-writing")
    }
    
    Response:
    {
        "success": true,
        "weakness": {
            "subject": "math",
            "sub_category": "algebra",
            "tag": "systems-of-equations",
            "total_score": 30,
            "score_percentage": 45.5,
            "total_questions_attempted": 20,
            "accuracy": 50.0
        }
    }
    
    Returns empty string if no data available
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body must be JSON'
            }), 400
        
        # Validate required fields
        user_id = data.get('user_id')
        subject = data.get('subject')
        
        if not user_id or not subject:
            return jsonify({
                'error': 'Missing required fields',
                'message': 'user_id and subject are required'
            }), 400
        
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(user_id):
            return jsonify({
                'error': 'User not found',
                'message': f"Student with ID {user_id} does not exist"
            }), 404
        
        # Get performance summary
        analytics_db = get_analytics_db()
        summary = analytics_db.get_performance_summary(user_id)
        
        if not summary or 'subjects' not in summary:
            return jsonify({
                'success': True,
                'weakness': ""
            }), 200
        
        # Check if subject exists
        subjects_data = summary.get('subjects', {})
        if subject not in subjects_data:
            return jsonify({
                'success': True,
                'weakness': ""
            }), 200
        
        subject_data = subjects_data[subject]
        sub_categories = subject_data.get('sub_categories', {})
        
        if not sub_categories:
            return jsonify({
                'success': True,
                'weakness': ""
            }), 200
        
        # Find the weakest tag
        worst_tag = None
        worst_score = float('inf')
        worst_sub_category = None
        
        for sub_cat_name, sub_cat_data in sub_categories.items():
            tags = sub_cat_data.get('tags', {})
            
            for tag_name, tag_data in tags.items():
                total_score = tag_data.get('total_score', 0)
                score_percentage = tag_data.get('score_percentage', 0)
                total_questions = tag_data.get('total_questions_attempted', 0)
                
                # Skip if no data
                if total_score == 0 and score_percentage == 0:
                    continue
                
                # Calculate combined score: weight both total_score and score_percentage
                # Lower score_percentage shows weakness, but we also consider volume
                # Formula: (score_percentage * 0.7) + (min(total_score, 100) * 0.3)
                normalized_total_score = min(total_score, 100)
                combined_score = (score_percentage * 0.7) + (normalized_total_score * 0.3)
                
                if combined_score < worst_score:
                    worst_score = combined_score
                    worst_tag = tag_name
                    worst_sub_category = sub_cat_name
                    worst_tag_data = tag_data
        
        # If no tag found (all zeros)
        if worst_tag is None:
            return jsonify({
                'success': True,
                'weakness': ""
            }), 200
        
        # Return the weakest tag
        return jsonify({
            'success': True,
            'weakness': {
                'subject': subject,
                'sub_category': worst_sub_category,
                'tag': worst_tag,
                'total_score': worst_tag_data.get('total_score', 0),
                'score_percentage': worst_tag_data.get('score_percentage', 0),
                'total_questions_attempted': worst_tag_data.get('total_questions_attempted', 0),
                'accuracy': worst_tag_data.get('accuracy', 0)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting weakness for user: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to get weakness',
            'message': str(e)
        }), 500


@analytics_bp.route('/get-my-least-attempted', methods=['POST'])
@authenticate_request
def get_my_least_attempted():
    """
    Get the tag with least number of questions attempted by the user in a subject
    Considers ALL tags from the taxonomy, including tags with zero attempts
    
    Request Body (JSON):
    {
        "user_id": "string",
        "subject": "string" (e.g., "math", "reading-and-writing")
    }
    
    Response:
    {
        "success": true,
        "least_attempted": {
            "subject": "math",
            "sub_category": "algebra",
            "tag": "mixture-problems",
            "total_score": 0,
            "score_percentage": 0,
            "total_questions_attempted": 0,
            "accuracy": 0
        }
    }
    
    Returns empty string if subject is invalid
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body must be JSON'
            }), 400
        
        # Validate required fields
        user_id = data.get('user_id')
        subject = data.get('subject')
        
        if not user_id or not subject:
            return jsonify({
                'error': 'Missing required fields',
                'message': 'user_id and subject are required'
            }), 400
        
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(user_id):
            return jsonify({
                'error': 'User not found',
                'message': f"Student with ID {user_id} does not exist"
            }), 404
        
        # Verify subject is valid
        if subject not in SUBJECT_TAG_TAXONOMY:
            return jsonify({
                'error': 'Invalid subject',
                'message': f"Subject '{subject}' is not valid. Must be one of: {list(SUBJECT_TAG_TAXONOMY.keys())}"
            }), 400
        
        # Get performance summary
        analytics_db = get_analytics_db()
        summary = analytics_db.get_performance_summary(user_id)
        
        # Build a map of attempted tags with their data
        attempted_tags = {}
        if summary and 'subjects' in summary:
            subjects_data = summary.get('subjects', {})
            if subject in subjects_data:
                subject_data = subjects_data[subject]
                sub_categories = subject_data.get('sub_categories', {})
                
                for sub_cat_name, sub_cat_data in sub_categories.items():
                    tags = sub_cat_data.get('tags', {})
                    for tag_name, tag_data in tags.items():
                        attempted_tags[f"{sub_cat_name}|{tag_name}"] = tag_data
        
        # Now check ALL tags from taxonomy and find the least attempted
        least_attempted_tag = None
        least_attempts = float('inf')
        least_attempted_sub_category = None
        least_attempted_tag_data = {
            'total_score': 0,
            'score_percentage': 0,
            'total_questions_attempted': 0,
            'accuracy': 0
        }
        
        # Iterate through all tags in the taxonomy for this subject
        for sub_cat_name, tag_list in SUBJECT_TAG_TAXONOMY[subject].items():
            for tag_name in tag_list:
                tag_key = f"{sub_cat_name}|{tag_name}"
                
                # Get attempt count (0 if not attempted)
                if tag_key in attempted_tags:
                    tag_data = attempted_tags[tag_key]
                    total_questions = tag_data.get('total_questions_attempted', 0)
                else:
                    # Tag has never been attempted
                    total_questions = 0
                    tag_data = {
                        'total_score': 0,
                        'score_percentage': 0,
                        'total_questions_attempted': 0,
                        'accuracy': 0
                    }
                
                # Find tag with minimum attempts
                if total_questions < least_attempts:
                    least_attempts = total_questions
                    least_attempted_tag = tag_name
                    least_attempted_sub_category = sub_cat_name
                    least_attempted_tag_data = tag_data
        
        # Return the least attempted tag
        return jsonify({
            'success': True,
            'least_attempted': {
                'subject': subject,
                'sub_category': least_attempted_sub_category,
                'tag': least_attempted_tag,
                'total_score': least_attempted_tag_data.get('total_score', 0),
                'score_percentage': least_attempted_tag_data.get('score_percentage', 0),
                'total_questions_attempted': least_attempted_tag_data.get('total_questions_attempted', 0),
                'accuracy': least_attempted_tag_data.get('accuracy', 0)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting least attempted for user: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to get least attempted',
            'message': str(e)
        }), 500
