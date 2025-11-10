"""
Leaderboard API Routes
Handles all leaderboard related endpoints
"""

from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any

from database.leaderboard_db import get_leaderboard_db
from models.leaderboard_schema import LeaderboardEntity, PerformanceMetric, Region
from helper.middleware import authenticate_request
from database.user_db import get_user_db

leaderboard_bp = Blueprint('leaderboard', __name__, url_prefix='/api/leaderboard')
logger = logging.getLogger(__name__)


@leaderboard_bp.route('/get_leaderboard_generic/<user_id>', methods=['GET'])
@authenticate_request
def get_leaderboard_generic(user_id: str):
    """
    Get leaderboard entities with filtering and sorting, and accomodate current user 
    If user is not in top N, then remove N-1 and add them at the end of the list.
    
    Query Parameters:
        limit: Maximum number of entries to return (default: 100, max: 500)
        sort_by: Sort by metric - 'rating', 'score', 'correct_questions', 'total_quiz' (default: 'rating')
        sort_order: Sort order - 'desc' or 'asc' (default: 'desc')
        country: Filter by country (optional)
        state: Filter by state (optional, requires country)
        city: Filter by city (optional, requires state and country)
    
    Response:
        {
            "success": true,
            "leaderboard": [
                {
                    "rank": 1,
                    "user_id": "user_123",
                    "region": {
                        "country": "India",
                        "state": "Maharashtra",
                        "city": "Mumbai"
                    },
                    "performance_metric": {
                        "rating": 1500,
                        "correct_questions": 150,
                        "score": 2500,
                        "total_questions": 200,
                        "total_quiz": 20
                    },
                    "accuracy": 75.0,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-15T10:30:00"
                },
                ...
            ],
            "count": 100,
            "filters": {
                "country": "India",
                "state": "Maharashtra",
                "city": null
            },
            "sort": {
                "by": "correct_questions",
                "order": "desc"
            }
        }
    
    Error Response:
        {
            "error": "Invalid parameter",
            "message": "limit must be between 1 and 500"
        }
    """
    try:
        logger.info(f"Getting leaderboard for user {user_id} with filters and sorting")
        # Validate user_id
        if not user_id or user_id.strip() == '':
            return jsonify({
                'error': 'Invalid parameter',
                'message': 'user_id cannot be empty'
            }), 400
        
        # Get query parameters
        limit = request.args.get('limit', default=100, type=int)
        sort_by = request.args.get('sort_by', default='correct_questions', type=str)
        sort_order = request.args.get('sort_order', default='desc', type=str)
        country = request.args.get('country', default=None, type=str)
        state = request.args.get('state', default=None, type=str)
        city = request.args.get('city', default=None, type=str)
        
        # Validate limit
        if limit <= 0 or limit > 500:
            return jsonify({
                'error': 'Invalid parameter',
                'message': 'limit must be between 1 and 500'
            }), 400
        
        # Validate sort_by
        valid_sort_fields = ['rating', 'score', 'correct_questions', 'total_quiz', 'total_questions']
        if sort_by not in valid_sort_fields:
            return jsonify({
                'error': 'Invalid parameter',
                'message': f'sort_by must be one of: {", ".join(valid_sort_fields)}'
            }), 400
        
        # Validate sort_order
        if sort_order.lower() not in ['asc', 'desc']:
            return jsonify({
                'error': 'Invalid parameter',
                'message': 'sort_order must be either "asc" or "desc"'
            }), 400
        
        
        # Get leaderboard from database
        leaderboard_db = get_leaderboard_db()
        user_leaderboard_entity = leaderboard_db.get_leaderboard_entity(user_id=user_id)
        if not user_leaderboard_entity:
            logger.error(f"No leaderboard entity found for user {user_id}")
            return jsonify({
                'success': False,
                'message': f'No leaderboard entity found for user {user_id}'
            }), 404
            
        # check filter options
        if city and user_leaderboard_entity.region.city.lower() != city.strip().lower():
            logger.error(f"User {user_id} city '{user_leaderboard_entity.region.city}' does not match filter city '{city}'")
            return jsonify({
                'success': False,
                'message': f'User city does not match filter city'
            }), 400
        if state and user_leaderboard_entity.region.state.lower() != state.strip().lower():
            logger.error(f"User {user_id} state '{user_leaderboard_entity.region.state}' does not match filter state '{state}'")
            return jsonify({
                'success': False,
                'message': f'User state does not match filter state'
            }), 400
        if country and user_leaderboard_entity.region.country.lower() != country.strip().lower():
            logger.error(f"User {user_id} country '{user_leaderboard_entity.region.country}' does not match filter country '{country}'")
            return jsonify({
                'success': False,
                'message': f'User country does not match filter country'
            }), 400
            
        
        leaderboard_list = leaderboard_db.get_leaderboard_entity(
            limit=limit, 
            country=country,
            state=state,
            city=city,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        logger.info(f"Leaderboard entries retrieved: {leaderboard_list}")
        

        # Build scope description
        scope_parts = []
        if city:
            scope_parts.append(city)
        if state:
            scope_parts.append(state)
        if country:
            scope_parts.append(country)
        scope = ', '.join(scope_parts) if scope_parts else 'Global'
        
        logger.info(f"Retrieved leaderboard: {len(leaderboard_list)} entries, scope: {scope}, sort: {sort_by} ({sort_order})")
        
        # Add current user in the leaderboard list by rank, if current user is not ranked in top N, 
        # remove the last entry and add current user at the end
        leaderboard_users = {entry.get('user_id', '') for entry in leaderboard_list}
        if user_id not in leaderboard_users:
            leaderboard_list = leaderboard_list[:limit-1]  # Keep only top N-1
            leaderboard_list.append(user_leaderboard_entity)  # Add current user at the end

        return jsonify({
            'success': True,
            'leaderboard': leaderboard_list,
            'count': len(leaderboard_list),
            'scope': scope,
            'filters': {
                'country': country,
                'state': state,
                'city': city
            },
            'sort': {
                'by': sort_by,
                'order': sort_order
            }
        }), 200
 
    except Exception as e:
        logger.error(f"Error getting leaderboard entities: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to get leaderboard',
            'message': str(e)
        }), 500

# TODO: Add route to get leaderboard within the user's friend group
# @leaderboard_bp.route('/get_leaderboard_friends/<user_id>', methods=['GET'])

def fetch_user(user_id: str) -> Dict[str, Any]:
    user_db = get_user_db()
    user_entity = user_db.get_user_by_id(user_id)
    if not user_entity:
        logger.error(f"No user found with ID {user_id}")
        raise Exception(f"No user found with ID {user_id}")
    return user_entity

def add_current_user_metrics(user_id: str, request_id: str) -> Dict[str, Any]:
    # create new leaderboard entry if not exists
        logger.info(f"[{request_id}] No existing leaderboard entry for student {user_id}, creating new entry")
        # fetch user info from user db
        user_entity = fetch_user(user_id)
        region = Region(
            country=user_entity.get('country',''),
            state=user_entity.get('state',''),
            city=user_entity.get('city','')
        )
        
        return LeaderboardEntity(
            username=user_entity.get('name',''),
            user_id=user_id,
            region=region,
            performance_metric=PerformanceMetric()
        )

def update_leaderboard_db(submission_data: dict, request_id: str):
    logger.info(f"[{request_id}] Updating leaderboard for quiz submission by student {submission_data['student_id']}")
    leaderboard_db = get_leaderboard_db()
    user_id = submission_data['student_id'] 
    current_user_metrics = leaderboard_db.get_leaderboard_entity(user_id)
    try:
        if not current_user_metrics:
            current_user_metrics = add_current_user_metrics(user_id, request_id)
    
        if not current_user_metrics.username:
            user_entity = fetch_user(user_id)
            current_user_metrics.username = user_entity.get('name','')
            
    except Exception as e:
        logger.error(f"[{request_id}] Error creating leaderboard entry for student {user_entity}: {str(e)}")
        return
    
    # Update performance metrics
    current_user_metrics.performance_metric.update_from_quiz(
        correct=submission_data.get('number_of_correct_answers', 0),
        total=submission_data.get('number_of_questions', 0),
        points=submission_data.get('number_of_correct_answers', 0) * submission_data.get('difficulty_level', 1)
    )
    
    # Save updated metrics back to DB
    success = leaderboard_db.create_or_update_entity(current_user_metrics)
    if success:
        logger.info(f"[{request_id}] Successfully updated leaderboard for student {user_id}")
    else:
        logger.error(f"[{request_id}] Failed to update leaderboard for student {user_id}")
    return

