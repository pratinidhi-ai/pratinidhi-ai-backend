"""
Leaderboard API Routes
Handles all leaderboard related endpoints
"""

from fastapi import APIRouter, HTTPException, Query
import logging
from typing import Dict, Any

from database.leaderboard_db import get_leaderboard_db
from models.leaderboard_schema import LeaderboardEntity, PerformanceMetric, Region
from helper.middleware import authenticate_request
from database.user_db import get_user_db

router = APIRouter(prefix='/api/leaderboard', tags=['Leaderboard'])
logger = logging.getLogger(__name__)


@router.get('/get_leaderboard_generic/{user_id}')
@authenticate_request
async def get_leaderboard_generic(
    user_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    sort_by: str = Query(default='correct_questions'),
    sort_order: str = Query(default='desc'),
    filter_by: str = Query(default='none')
):
    """
    Get leaderboard entities with filtering and sorting, and accomodate current user 
    If user is not in top N, then remove N-1 and add them at the end of the list.
    
    Query Parameters:
        limit: Maximum number of entries to return (default: 100, max: 500)
        sort_by: Sort by metric - 'rating', 'score', 'correct_questions', 'total_quiz' (default: 'rating')
        sort_order: Sort order - 'desc' or 'asc' (default: 'desc')
        filter_by: Filter scope - 'city', 'state', 'country', 'none' (default: 'none')
    
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
                "filter_by": "city",
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
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'Invalid parameter',
                    'message': 'user_id cannot be empty'
                }
            )
        
        # Validate sort_by
        valid_sort_fields = ['rating', 'score', 'correct_questions', 'total_quiz', 'total_questions']
        if sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'Invalid parameter',
                    'message': f'sort_by must be one of: {", ".join(valid_sort_fields)}'
                }
            )
        
        # Validate sort_order
        if sort_order.lower() not in ['asc', 'desc']:
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'Invalid parameter',
                    'message': 'sort_order must be either "asc" or "desc"'
                }
            )
        
        # Validate filter_by
        valid_filters = ['city', 'state', 'country','none']
        if filter_by.lower() not in valid_filters:
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'Invalid parameter',
                    'message': f'filter_by must be one of: {", ".join(valid_filters)}'
                }
            )
        
        # Get leaderboard from database
        leaderboard_db = get_leaderboard_db()
        user_leaderboard_entity = leaderboard_db.get_leaderboard_entity(user_id=user_id)
        if not user_leaderboard_entity:
            logger.error(f"No leaderboard entity found for user {user_id}")
            raise HTTPException(
                status_code=404,
                detail={
                    'success': False,
                    'message': f'No leaderboard entity found for user {user_id}'
                }
            )
            
        # Determine filter values based on filter_by parameter
        country = None
        state = None
        city = None
        
        if filter_by.lower() == 'city':
            city = user_leaderboard_entity.region.city
        elif filter_by.lower() == 'state':
            state = user_leaderboard_entity.region.state
        elif filter_by.lower() == 'country':
            country = user_leaderboard_entity.region.country   
        
        leaderboard_list = leaderboard_db.get_leaderboard_entity(
            limit=limit, country=country, state=state, city=city,
            sort_by=sort_by, sort_order=sort_order
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

        return {
            'success': True,
            'leaderboard': leaderboard_list,
            'count': len(leaderboard_list),
            'scope': scope,
            'sort': {
                'by': sort_by,
                'order': sort_order
            }
        }
 
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting leaderboard entities: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Failed to get leaderboard',
                'message': str(e)
            }
        )

# TODO: Add route to get leaderboard within the user's friend group
# @router.get('/get_leaderboard_friends/{user_id}')

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
        logger.error(f"[{request_id}] Error creating leaderboard entry for student {user_id}: {str(e)}")
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

