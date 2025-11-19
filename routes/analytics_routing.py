"""
Analytics API Routes
Handles all analytics-related endpoints for student performance tracking
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
import uuid

from helper.middleware import authenticate_request
from database.analytics_db import get_analytics_db
from database.user_db import get_user_db
from models.analytics_schema import QuizSubmission, TagDetail
from database.leaderboard_db import get_leaderboard_db
from models.leaderboard_schema import LeaderboardEntity, PerformanceMetric, Region
from routes.leaderboard_routing import update_leaderboard_db

logger = logging.getLogger(__name__)

analytics_router = APIRouter(prefix="/api/analytics", tags=["analytics"])

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

# Pydantic models for request/response
class TagWiseDetail(BaseModel):
    tag: str
    total_questions: int
    correct_answers: int
    score: Optional[int] = None
    total_possible_score: Optional[int] = None

class QuizSubmitRequest(BaseModel):
    student_id: str
    time_spent: int = Field(..., description="Time spent in seconds")
    number_of_questions: int
    number_of_correct_answers: int
    subject: str
    sub_category: str
    difficulty_level: int = Field(..., ge=1, le=5)
    tag_wise_details: List[TagWiseDetail]
    correct_question_ids: List[str]
    incorrect_question_ids: List[str]

class PerformanceRequest(BaseModel):
    user_id: str
    subject: str
    sub_category: Optional[str] = None  # Make it optional since some endpoints don't need it

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
        logger.info(f"[{request_id}] Submission data: {submission_data}")
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
            
            # Update daily progress stats (IST timezone aware)
            daily_progress_success = analytics_db.update_daily_progress(submission_data['student_id'], submission)
            if daily_progress_success:
                logger.info(f"[{request_id}] Successfully updated daily progress for student {submission_data['student_id']}")
            else:
                logger.warning(f"[{request_id}] Failed to update daily progress for student {submission_data['student_id']}")
        else:
            logger.error(f"[{request_id}] Failed to submit analytics for student {submission_data['student_id']}")
            
        # Update leaderboard metrics
        update_leaderboard_db(submission_data, request_id)
    except Exception as e:
        logger.error(f"[{request_id}] Error in background processing: {str(e)}")
        import traceback
        traceback.print_exc()


@analytics_router.post('/submit-quiz', status_code=202)
def submit_quiz(
    data: QuizSubmitRequest,
    background_tasks: BackgroundTasks,
    user=Depends(authenticate_request)
):
    """
    Submit quiz results and update analytics (ASYNC)
    
    This endpoint accepts the quiz data, validates it, and immediately returns a response
    with a request_id. The actual processing and storage happens asynchronously in the background.
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(data.student_id):
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {data.student_id} does not exist"
            )
        
        # Quick calculation for immediate feedback (estimated)
        estimated_score = 0
        estimated_total_possible = 0
        
        for tag_data in data.tag_wise_details:
            correct = tag_data.correct_answers
            total = tag_data.total_questions
            estimated_score += correct * data.difficulty_level
            estimated_total_possible += total * data.difficulty_level
        
        estimated_accuracy = round((data.number_of_correct_answers / data.number_of_questions * 100), 2) if data.number_of_questions > 0 else 0
        
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())
        
        # Add background task
        background_tasks.add_task(
            process_quiz_submission_background,
            data.dict(),
            request_id
        )
        
        logger.info(f"[{request_id}] Quiz submission accepted for student {data.student_id}, processing in background")
        
        # Return immediate response
        return {
            'success': True,
            'message': 'Quiz submission received and is being processed',
            'request_id': request_id,
            'estimated_score': estimated_score,
            'estimated_total_possible_score': estimated_total_possible,
            'estimated_accuracy': estimated_accuracy,
            'subject': data.subject,
            'sub_category': data.sub_category,
            'difficulty_level': data.difficulty_level
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting quiz submission: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get('/performance-summary/{student_id}')
def get_performance_summary(
    student_id: str,
    subject: Optional[str] = Query(None),
    sub_category: Optional[str] = Query(None),
    user=Depends(authenticate_request)
):
    """
    Get overall performance summary for a student
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(student_id):
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {student_id} does not exist"
            )
        
        # Get performance summary
        analytics_db = get_analytics_db()
        summary = analytics_db.get_performance_summary(student_id)
        
        if not summary:
            return {
                'success': True,
                'message': 'No analytics data found for this student',
                'summary': None
            }
        
        # Filter if subject/sub_category specified
        if subject:
            subjects_data = summary.get('subjects', {})
            if subject in subjects_data:
                filtered_subject = subjects_data[subject]
                
                if sub_category:
                    sub_cats = filtered_subject.get('sub_categories', {})
                    if sub_category in sub_cats:
                        summary = {
                            'student_id': summary['student_id'],
                            'subject': subject,
                            'sub_category': sub_category,
                            'data': sub_cats[sub_category]
                        }
                    else:
                        raise HTTPException(
                            status_code=404,
                            detail=f'No data found for sub_category: {sub_category}'
                        )
                else:
                    summary = {
                        'student_id': summary['student_id'],
                        'subject': subject,
                        'data': filtered_subject
                    }
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f'No data found for subject: {subject}'
                )
        
        return {
            'success': True,
            'summary': summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance summary for {student_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get('/activity-logs/{student_id}')
def get_activity_logs(
    student_id: str,
    limit: int = Query(50, le=100),
    user=Depends(authenticate_request)
):
    """
    Get activity logs (quiz history) for a student
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(student_id):
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {student_id} does not exist"
            )
        
        # Get activity logs
        analytics_db = get_analytics_db()
        logs = analytics_db.get_activity_logs(student_id, limit=limit)
        
        return {
            'success': True,
            'logs': logs,
            'count': len(logs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting activity logs for {student_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get('/correct-questions/{student_id}')
def get_correct_questions(
    student_id: str,
    subject: Optional[str] = Query(None),
    sub_category: Optional[str] = Query(None),
    user=Depends(authenticate_request)
):
    """
    Get list of correctly answered question IDs for a student
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(student_id):
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {student_id} does not exist"
            )
        
        # Get correct questions
        analytics_db = get_analytics_db()
        correct_questions = analytics_db.get_correct_questions(
            student_id, 
            subject=subject, 
            sub_category=sub_category
        )
        
        return {
            'success': True,
            'correct_questions': correct_questions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting correct questions for {student_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get('/incorrect-questions/{student_id}')
def get_incorrect_questions(
    student_id: str,
    subject: Optional[str] = Query(None),
    sub_category: Optional[str] = Query(None),
    user=Depends(authenticate_request)
):
    """
    Get list of incorrectly answered question IDs for a student
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(student_id):
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {student_id} does not exist"
            )
        
        # Get incorrect questions
        analytics_db = get_analytics_db()
        incorrect_questions = analytics_db.get_incorrect_questions(
            student_id,
            subject=subject,
            sub_category=sub_category
        )
        
        return {
            'success': True,
            'incorrect_questions': incorrect_questions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting incorrect questions for {student_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get('/stats/{student_id}')
def get_quick_stats(
    student_id: str,
    user=Depends(authenticate_request)
):
    """
    Get quick stats overview for a student
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(student_id):
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {student_id} does not exist"
            )
        
        # Get performance summary
        analytics_db = get_analytics_db()
        summary = analytics_db.get_performance_summary(student_id)
        
        if not summary:
            return {
                'success': True,
                'message': 'No analytics data found for this student',
                'stats': None
            }
        
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
        
        return {
            'success': True,
            'stats': stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quick stats for {student_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post('/get-my-strength')
def get_my_strength(
    data: PerformanceRequest,
    user=Depends(authenticate_request)
):
    """
    Get the user's strongest tag in a subject
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(data.user_id):
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {data.user_id} does not exist"
            )
        
        # Get performance summary
        analytics_db = get_analytics_db()
        summary = analytics_db.get_performance_summary(data.user_id)
        
        if not summary or 'subjects' not in summary:
            return {
                'success': True,
                'strength': ""
            }
        
        # Check if subject exists
        subjects_data = summary.get('subjects', {})
        if data.subject not in subjects_data:
            return {
                'success': True,
                'strength': ""
            }
        
        subject_data = subjects_data[data.subject]
        sub_categories = subject_data.get('sub_categories', {})
        
        if not sub_categories:
            return {
                'success': True,
                'strength': ""
            }
        
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
            return {
                'success': True,
                'strength': ""
            }
        
        # Return the strongest tag
        return {
            'success': True,
            'strength': {
                'subject': data.subject,
                'sub_category': best_sub_category,
                'tag': best_tag,
                'total_score': best_tag_data.get('total_score', 0),
                'score_percentage': best_tag_data.get('score_percentage', 0),
                'total_questions_attempted': best_tag_data.get('total_questions_attempted', 0),
                'accuracy': best_tag_data.get('accuracy', 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strength for user: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post('/get-my-weakness')
def get_my_weakness(
    data: PerformanceRequest,
    user=Depends(authenticate_request)
):
    """
    Get the user's weakest tag in a subject
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(data.user_id):
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {data.user_id} does not exist"
            )
        
        # Get performance summary
        analytics_db = get_analytics_db()
        summary = analytics_db.get_performance_summary(data.user_id)
        
        if not summary or 'subjects' not in summary:
            return {
                'success': True,
                'weakness': ""
            }
        
        # Check if subject exists
        subjects_data = summary.get('subjects', {})
        if data.subject not in subjects_data:
            return {
                'success': True,
                'weakness': ""
            }
        
        subject_data = subjects_data[data.subject]
        sub_categories = subject_data.get('sub_categories', {})
        
        if not sub_categories:
            return {
                'success': True,
                'weakness': ""
            }
        
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
            return {
                'success': True,
                'weakness': ""
            }
        
        # Return the weakest tag
        return {
            'success': True,
            'weakness': {
                'subject': data.subject,
                'sub_category': worst_sub_category,
                'tag': worst_tag,
                'total_score': worst_tag_data.get('total_score', 0),
                'score_percentage': worst_tag_data.get('score_percentage', 0),
                'total_questions_attempted': worst_tag_data.get('total_questions_attempted', 0),
                'accuracy': worst_tag_data.get('accuracy', 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting weakness for user: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post('/get-my-least-attempted')
def get_my_least_attempted(
    data: PerformanceRequest,
    user=Depends(authenticate_request)
):
    """
    Get the tag with least number of questions attempted by the user in a subject
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(data.user_id):
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {data.user_id} does not exist"
            )
        
        # Verify subject is valid
        if data.subject not in SUBJECT_TAG_TAXONOMY:
            raise HTTPException(
                status_code=400,
                detail=f"Subject '{data.subject}' is not valid. Must be one of: {list(SUBJECT_TAG_TAXONOMY.keys())}"
            )
        
        # Get performance summary
        analytics_db = get_analytics_db()
        summary = analytics_db.get_performance_summary(data.user_id)
        
        # Build a map of attempted tags with their data
        attempted_tags = {}
        if summary and 'subjects' in summary:
            subjects_data = summary.get('subjects', {})
            if data.subject in subjects_data:
                subject_data = subjects_data[data.subject]
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
        for sub_cat_name, tag_list in SUBJECT_TAG_TAXONOMY[data.subject].items():
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
        return {
            'success': True,
            'least_attempted': {
                'subject': data.subject,
                'sub_category': least_attempted_sub_category,
                'tag': least_attempted_tag,
                'total_score': least_attempted_tag_data.get('total_score', 0),
                'score_percentage': least_attempted_tag_data.get('score_percentage', 0),
                'total_questions_attempted': least_attempted_tag_data.get('total_questions_attempted', 0),
                'accuracy': least_attempted_tag_data.get('accuracy', 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting least attempted for user: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get('/daily-progress/{student_id}')
def get_daily_progress(
    student_id: str,
    user=Depends(authenticate_request)
):
    """
    Get daily progress statistics for a student (IST timezone)
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(student_id):
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {student_id} does not exist"
            )
        
        # Get daily progress
        analytics_db = get_analytics_db()
        daily_progress = analytics_db.get_daily_progress(student_id)
        
        if not daily_progress:
            # Return empty structure if no data found
            return {
                'success': True,
                'message': 'No daily progress data found for this student',
                'daily_progress': {
                    'today': {
                        'date': None,
                        'total_time_spent': 0,
                        'total_quizzes': 0,
                        'total_questions': 0,
                        'total_correct': 0,
                        'accuracy': 0,
                        'hot_topic': None,
                        'hot_topic_count': 0,
                        'tags': {}
                    },
                    'yesterday': {},
                    'streak': 0,
                    'last_activity_date': None
                }
            }
        
        return {
            'success': True,
            'daily_progress': daily_progress
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting daily progress for {student_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post('/get-my-performance-analytics')
def get_my_performance_analytics(
    data: PerformanceRequest,
    user=Depends(authenticate_request)
):
    """
    Get comprehensive performance analytics for a user in a subject
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(data.user_id):
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {data.user_id} does not exist"
            )
        
        # Verify subject is valid
        if data.subject not in SUBJECT_TAG_TAXONOMY:
            raise HTTPException(
                status_code=400,
                detail=f"Subject '{data.subject}' is not valid. Must be one of: {list(SUBJECT_TAG_TAXONOMY.keys())}"
            )
        
        # Get performance summary once for all calculations
        analytics_db = get_analytics_db()
        summary = analytics_db.get_performance_summary(data.user_id)
        
        # Initialize response structure
        analytics_response = {
            'subject': data.subject,
            'strength': "",
            'weakness': "",
            'least_attempted': ""
        }
        
        # Check if we have any data
        if not summary or 'subjects' not in summary:
            return {
                'success': True,
                'analytics': analytics_response
            }
        
        subjects_data = summary.get('subjects', {})
        if data.subject not in subjects_data:
            return {
                'success': True,
                'analytics': analytics_response
            }
        
        subject_data = subjects_data[data.subject]
        sub_categories = subject_data.get('sub_categories', {})
        
        # Calculate Strength (highest combined score)
        if sub_categories:
            best_tag = None
            best_score = -1
            best_sub_category = None
            best_tag_data = {}
            
            for sub_cat_name, sub_cat_data in sub_categories.items():
                tags = sub_cat_data.get('tags', {})
                
                for tag_name, tag_data in tags.items():
                    total_score = tag_data.get('total_score', 0)
                    score_percentage = tag_data.get('score_percentage', 0)
                    
                    if total_score == 0 and score_percentage == 0:
                        continue
                    
                    normalized_total_score = min(total_score, 100)
                    combined_score = (score_percentage * 0.7) + (normalized_total_score * 0.3)
                    
                    if combined_score > best_score:
                        best_score = combined_score
                        best_tag = tag_name
                        best_sub_category = sub_cat_name
                        best_tag_data = tag_data
            
            if best_tag is not None and best_tag_data:
                analytics_response['strength'] = {
                    'sub_category': best_sub_category,
                    'tag': best_tag,
                    'total_score': best_tag_data.get('total_score', 0),
                    'score_percentage': best_tag_data.get('score_percentage', 0),
                    'total_questions_attempted': best_tag_data.get('total_questions_attempted', 0),
                    'accuracy': best_tag_data.get('accuracy', 0)
                }
        
        # Calculate Weakness (lowest combined score)
        if sub_categories:
            worst_tag = None
            worst_score = float('inf')
            worst_sub_category = None
            worst_tag_data = {}
            
            for sub_cat_name, sub_cat_data in sub_categories.items():
                tags = sub_cat_data.get('tags', {})
                
                for tag_name, tag_data in tags.items():
                    total_score = tag_data.get('total_score', 0)
                    score_percentage = tag_data.get('score_percentage', 0)
                    
                    if total_score == 0 and score_percentage == 0:
                        continue
                    
                    normalized_total_score = min(total_score, 100)
                    combined_score = (score_percentage * 0.7) + (normalized_total_score * 0.3)
                    
                    if combined_score < worst_score:
                        worst_score = combined_score
                        worst_tag = tag_name
                        worst_sub_category = sub_cat_name
                        worst_tag_data = tag_data
            
            if worst_tag is not None and worst_tag_data:
                analytics_response['weakness'] = {
                    'sub_category': worst_sub_category,
                    'tag': worst_tag,
                    'total_score': worst_tag_data.get('total_score', 0),
                    'score_percentage': worst_tag_data.get('score_percentage', 0),
                    'total_questions_attempted': worst_tag_data.get('total_questions_attempted', 0),
                    'accuracy': worst_tag_data.get('accuracy', 0)
                }
        
        # Calculate Least Attempted (considers all tags from taxonomy)
        attempted_tags = {}
        if sub_categories:
            for sub_cat_name, sub_cat_data in sub_categories.items():
                tags = sub_cat_data.get('tags', {})
                for tag_name, tag_data in tags.items():
                    attempted_tags[f"{sub_cat_name}|{tag_name}"] = tag_data
        
        least_attempted_tag = None
        least_attempts = float('inf')
        least_attempted_sub_category = None
        least_attempted_tag_data = {
            'total_score': 0,
            'score_percentage': 0,
            'total_questions_attempted': 0,
            'accuracy': 0
        }
        
        for sub_cat_name, tag_list in SUBJECT_TAG_TAXONOMY[data.subject].items():
            for tag_name in tag_list:
                tag_key = f"{sub_cat_name}|{tag_name}"
                
                if tag_key in attempted_tags:
                    tag_data = attempted_tags[tag_key]
                    total_questions = tag_data.get('total_questions_attempted', 0)
                else:
                    total_questions = 0
                    tag_data = {
                        'total_score': 0,
                        'score_percentage': 0,
                        'total_questions_attempted': 0,
                        'accuracy': 0
                    }
                
                if total_questions < least_attempts:
                    least_attempts = total_questions
                    least_attempted_tag = tag_name
                    least_attempted_sub_category = sub_cat_name
                    least_attempted_tag_data = tag_data
        
        if least_attempted_tag is not None:
            analytics_response['least_attempted'] = {
                'sub_category': least_attempted_sub_category,
                'tag': least_attempted_tag,
                'total_score': least_attempted_tag_data.get('total_score', 0),
                'score_percentage': least_attempted_tag_data.get('score_percentage', 0),
                'total_questions_attempted': least_attempted_tag_data.get('total_questions_attempted', 0),
                'accuracy': least_attempted_tag_data.get('accuracy', 0)
            }
        
        return {
            'success': True,
            'analytics': analytics_response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance analytics for user: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get('/last-15-math-questions/{student_id}')
def get_last_15_math_questions(
    student_id: str,
    user=Depends(authenticate_request)
):
    """
    Get the last 15 math questions attempted by a student
    """
    try:
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(student_id):
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {student_id} does not exist"
            )
        
        # Get last 15 math questions
        analytics_db = get_analytics_db()
        last_15_data = analytics_db.get_last_15_math_questions(student_id)
        
        if not last_15_data:
            # Return empty structure if no data found
            return {
                'success': True,
                'message': 'No math questions found for this student',
                'data': {
                    'student_id': student_id,
                    'questions': [],
                    'count': 0,
                    'last_updated': None
                }
            }
        
        # Get questions and format them
        questions = last_15_data.get('questions', [])
        
        # Format each question with proper structure
        formatted_questions = []
        for q in questions:
            formatted_q = {
                'question_id': q.get('question_id'),
                'question_text': q.get('question_text', ''),
                'options': {
                    'A': q.get('option_a', ''),
                    'B': q.get('option_b', ''),
                    'C': q.get('option_c', ''),
                    'D': q.get('option_d', '')
                },
                'correct_answer': q.get('correct_answer', ''),
                'is_answered_correctly': q.get('is_answered_correctly', False),
                'difficulty_level': q.get('difficulty_level'),
                'tags': q.get('tags', []),
                'sub_category': q.get('sub_category'),
                'timestamp': q.get('timestamp')
            }
            formatted_questions.append(formatted_q)
        
        return {
            'success': True,
            'data': {
                'student_id': last_15_data.get('student_id', student_id),
                'questions': formatted_questions,
                'count': len(formatted_questions),
                'last_updated': last_15_data.get('last_updated')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting last 15 math questions for {student_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post('/get-my-comprehensive-performance-analytics')
def get_my_comprehensive_performance_analytics(
    data: PerformanceRequest,
    user=Depends(authenticate_request)
):
    """
    Get comprehensive performance analytics for a user in a specific sub_category
    Categorizes all tags in the sub_category into three buckets: strength, weakness, and unexplored
    
    Categorization Logic:
    - Unexplored: Tags where user has not solved any question OR attempted questions < 50% of mean
    - Strength: Tags with accuracy >= 75% AND not in unexplored
    - Weakness: Tags with accuracy < 75% AND not in unexplored
    """
    try:
        # Validate required fields
        if not data.sub_category:
            raise HTTPException(
                status_code=400,
                detail="sub_category is required"
            )
        
        # Verify user exists
        user_db = get_user_db()
        if not user_db.user_exists(data.user_id):
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {data.user_id} does not exist"
            )
        
        # Verify subject is valid
        if data.subject not in SUBJECT_TAG_TAXONOMY:
            raise HTTPException(
                status_code=400,
                detail=f"Subject '{data.subject}' is not valid. Must be one of: {list(SUBJECT_TAG_TAXONOMY.keys())}"
            )
        
        # Verify sub_category is valid for the subject
        if data.sub_category not in SUBJECT_TAG_TAXONOMY[data.subject]:
            raise HTTPException(
                status_code=400,
                detail=f"Sub-category '{data.sub_category}' is not valid for subject '{data.subject}'. Must be one of: {list(SUBJECT_TAG_TAXONOMY[data.subject].keys())}"
            )
        
        # Get all tags for this sub_category from taxonomy
        all_tags = SUBJECT_TAG_TAXONOMY[data.subject][data.sub_category]
        total_tags = len(all_tags)
        
        # Get performance summary
        analytics_db = get_analytics_db()
        summary = analytics_db.get_performance_summary(data.user_id)
        
        # Build a map of tag data from user's performance
        tag_data_map = {}
        if summary and 'subjects' in summary:
            subjects_data = summary.get('subjects', {})
            if data.subject in subjects_data:
                subject_data = subjects_data[data.subject]
                sub_categories = subject_data.get('sub_categories', {})
                if data.sub_category in sub_categories:
                    sub_cat_data = sub_categories[data.sub_category]
                    tags = sub_cat_data.get('tags', {})
                    tag_data_map = tags
        
        # Calculate mean questions attempted across all tags
        total_questions_attempted = 0
        attempted_count = 0
        
        for tag_name in all_tags:
            if tag_name in tag_data_map:
                questions_attempted = tag_data_map[tag_name].get('total_questions_attempted', 0)
                total_questions_attempted += questions_attempted
                if questions_attempted > 0:
                    attempted_count += 1
        
        # Calculate mean (only from tags that have been attempted)
        mean_questions_attempted = total_questions_attempted / attempted_count if attempted_count > 0 else 0
        unexplored_threshold = mean_questions_attempted * 0.5
        
        # Initialize buckets
        strength = []
        weakness = []
        unexplored = []
        
        # Categorize each tag
        for tag_name in all_tags:
            # Get tag data or create default
            if tag_name in tag_data_map:
                tag_data = tag_data_map[tag_name]
                total_questions = tag_data.get('total_questions_attempted', 0)
                accuracy = tag_data.get('accuracy', 0)
                
                tag_info = {
                    'tag': tag_name,
                    'total_score': tag_data.get('total_score', 0),
                    'score_percentage': tag_data.get('score_percentage', 0),
                    'total_questions_attempted': total_questions,
                    'accuracy': accuracy
                }
            else:
                # Tag has never been attempted
                total_questions = 0
                accuracy = 0
                
                tag_info = {
                    'tag': tag_name,
                    'total_score': 0,
                    'score_percentage': 0,
                    'total_questions_attempted': 0,
                    'accuracy': 0
                }
            
            # Categorization logic
            # Unexplored: no questions OR questions < 50% of mean
            if total_questions == 0 or total_questions < unexplored_threshold:
                unexplored.append(tag_info)
            # Strength: accuracy >= 75%
            elif accuracy >= 75:
                strength.append(tag_info)
            # Weakness: accuracy < 75%
            else:
                weakness.append(tag_info)
        
        # Sort each bucket for better presentation
        # Strength: sorted by accuracy descending
        strength.sort(key=lambda x: x['accuracy'], reverse=True)
        # Weakness: sorted by accuracy ascending (worst first)
        weakness.sort(key=lambda x: x['accuracy'])
        # Unexplored: sorted by questions attempted ascending (least attempted first)
        unexplored.sort(key=lambda x: x['total_questions_attempted'])
        
        return {
            'success': True,
            'analytics': {
                'subject': data.subject,
                'sub_category': data.sub_category,
                'total_tags': total_tags,
                'mean_questions_attempted': round(mean_questions_attempted, 2),
                'unexplored_threshold': round(unexplored_threshold, 2),
                'strength': strength,
                'weakness': weakness,
                'unexplored': unexplored,
                'summary': {
                    'strength_count': len(strength),
                    'weakness_count': len(weakness),
                    'unexplored_count': len(unexplored)
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comprehensive performance analytics for user: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
