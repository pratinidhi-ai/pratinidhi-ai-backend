from fastapi import  HTTPException, status
from typing import Dict, Any
from database.user_db import getUserbyId, get_user_db
import logging

logger = logging.getLogger(__name__)

def validate_user_id(user_id: str) -> None:
    """Validate user_id and raise HTTPException if invalid"""
    if not user_id:
        logger.error("Invalid user ID: empty or None")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'error': 'Invalid user ID',
                'message': 'User ID is required and cannot be empty'
            }
        )
        
def get_user(user_id: str) -> dict:
    """Validate user existence and raise HTTPException if not found"""
    user_data = getUserbyId(user_id=user_id)
    if user_data is None:
        logger.error(f"User not found with ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                'error': 'User not found',
                'message': f'No user found with ID: {user_id}'
            }
        )
    return user_data
        
def update_user(user_id: str, update_data: Dict[str, Any], error_message: str) -> None:
    """Update user in database or raise HTTPException if update fails"""
    user_db = get_user_db()
    is_updated = user_db.update_user(user_id=user_id, update_data=update_data)
    if not is_updated:
        logger.error(f"Failed to update user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Update failed',
                'message': error_message
            }
        )
        
def save_last_predictor_score(user_id: str, math_score: int, rw_score:int , total_score: int) -> None:
    """Save the last predictor score for a user"""
    try:
        user_db = get_user_db()
        
        update_data = {
            'predicted_score': {
                'math_score': math_score,
                'rw_score': rw_score,
                'total_score': total_score,
                'is_synced': True
            }
        }
        user_db.update_user(user_id=user_id, update_data=update_data)
        logger.info(f"Saved last predictor scores for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error saving last predictor scores for user {user_id}: {str(e)}")
