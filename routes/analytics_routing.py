"""
Analytics API Routes
Handles all analytics-related endpoints for student performance tracking
"""

from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any

from helper.middleware import authenticate_request
from database.analytics_db import get_analytics_db
from database.user_db import get_user_db
from models.analytics_schema import QuizSubmission, TagDetail

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/submit-quiz', methods=['POST'])
@authenticate_request
def submit_quiz():
    """
    Submit quiz results and update analytics
    
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
        "message": "Quiz analytics submitted successfully",
        "session_id": "uuid-string",
        "summary": {calculated metrics}
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
        
        # Convert tag_wise_details to TagDetail objects with score calculation
        tag_details = []
        difficulty_level = data['difficulty_level']
        
        for tag_data in data['tag_wise_details']:
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
        try:
            submission = QuizSubmission(
                student_id=data['student_id'],
                time_spent=data['time_spent'],
                number_of_questions=data['number_of_questions'],
                number_of_correct_answers=data['number_of_correct_answers'],
                subject=data['subject'],
                sub_category=data['sub_category'],
                difficulty_level=difficulty_level,
                tag_wise_details=tag_details,
                correct_question_ids=data['correct_question_ids'],
                incorrect_question_ids=data['incorrect_question_ids']
            )
        except ValueError as ve:
            return jsonify({
                'error': 'Invalid data',
                'message': str(ve)
            }), 400
        
        # Submit to analytics database
        analytics_db = get_analytics_db()
        success, session_id = analytics_db.submit_quiz_analytics(submission)
        
        if not success:
            return jsonify({
                'error': 'Failed to submit analytics',
                'message': 'An error occurred while processing your quiz results'
            }), 500
        
        # Prepare summary response
        summary = {
            'score': submission.calculate_score(),
            'total_possible_score': submission.calculate_total_possible_score(),
            'accuracy': submission.get_accuracy(),
            'time_spent_minutes': round(submission.time_spent / 60, 2),
            'subject': submission.subject,
            'sub_category': submission.sub_category,
            'difficulty_level': submission.difficulty_level
        }
        
        logger.info(f"Quiz analytics submitted successfully for student {data['student_id']}, session {session_id}")
        
        return jsonify({
            'success': True,
            'message': 'Quiz analytics submitted successfully',
            'session_id': session_id,
            'summary': summary
        }), 201
        
    except Exception as e:
        logger.error(f"Error submitting quiz analytics: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to submit quiz analytics',
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
    
    Returns empty string if no data available or all tags have zero attempts
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
                'least_attempted': ""
            }), 200
        
        # Check if subject exists
        subjects_data = summary.get('subjects', {})
        if subject not in subjects_data:
            return jsonify({
                'success': True,
                'least_attempted': ""
            }), 200
        
        subject_data = subjects_data[subject]
        sub_categories = subject_data.get('sub_categories', {})
        
        if not sub_categories:
            return jsonify({
                'success': True,
                'least_attempted': ""
            }), 200
        
        # Find the least attempted tag
        least_attempted_tag = None
        least_attempts = float('inf')
        least_attempted_sub_category = None
        least_attempted_tag_data = None
        
        for sub_cat_name, sub_cat_data in sub_categories.items():
            tags = sub_cat_data.get('tags', {})
            
            for tag_name, tag_data in tags.items():
                total_questions = tag_data.get('total_questions_attempted', 0)
                
                # Find tag with minimum attempts
                if total_questions < least_attempts:
                    least_attempts = total_questions
                    least_attempted_tag = tag_name
                    least_attempted_sub_category = sub_cat_name
                    least_attempted_tag_data = tag_data
        
        # If no tag found or all are at 0
        if least_attempted_tag is None:
            return jsonify({
                'success': True,
                'least_attempted': ""
            }), 200
        
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
