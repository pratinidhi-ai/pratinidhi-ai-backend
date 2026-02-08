from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from models.users_schema import User
from database.user_db import getUserbyId, createUser, checkUserExists, _update_user_tags_quiz, get_user_db
from database.leaderboard_db import get_leaderboard_db
from models.leaderboard_schema import LeaderboardEntity, PerformanceMetric, Region
import time
from helper.middleware import authenticate_request
from datetime import datetime, timezone
import logging

user_router = APIRouter(prefix="/api/users", tags=["users"])
logger = logging.getLogger(__name__)


@user_router.get('/{user_id}/session-credits', status_code=status.HTTP_200_OK)
def get_session_credits(user_id: str, user: dict = Depends(authenticate_request)):
    """Get the remaining session credits for a user"""
    logger.info(f"Fetching session credits for user: {user_id}")
    try:
        item = getUserbyId(user_id=user_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    'error': 'User not found',
                    'message': 'No user exists with the provided ID'
                }
            )
        
        session_credits = item.get('subscription', {}).get('session_credits', 0)
        
        return {
            'success': True,
            'user_id': user_id,
            'session_credits': session_credits
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session credits for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Failed to fetch session credits',
                'message': str(e)
            }
        )


# Pydantic models for request validation
class CreateUserRequest(BaseModel):
    id: str
    email: str
    name: str
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None


class UpdateTagsRequest(BaseModel):
    user_id: str
    tags: List[str]


class UpdateTaskNumRequest(BaseModel):
    user_id: str
    num_tasks: int = Field(default=16, ge=0)


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    grade: Optional[str] = None
    board: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    num_tasks_per_week: Optional[int] = None


class ReportIssueRequest(BaseModel):
    user_id: str
    issue_title: str
    issue_description: str
    issue_type: str # e.g., 'bug', 'feature_request', 'other'


class UserDeleteRequest(BaseModel):
    user_id: str
    reason: str


def update_predicted_score(user_id: str, math_score: int, rw_score: int, total_score: int) -> None:
    """Update the predicted_score field for a user"""
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
        logger.info(f"Updated predicted_score for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to update predicted_score for user {user_id}: {str(e)}")

@user_router.get('/{user_id}', status_code=status.HTTP_200_OK)
def get_user(user_id: str, user: dict = Depends(authenticate_request)):
    logger.info(f"Fetching user with ID: {user_id}")
    try:
        item = getUserbyId(user_id=user_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    'error': 'User not found',
                    'message': 'No user exists with the provided ID'
                }
            )
        user_obj = User.from_dict(item)
        user_obj.last_login = datetime.now(timezone.utc)
        
        #  If predicted_score is not synced, fetch from SAT predictor history
        if not user_obj.predicted_score or user_obj.predicted_score.is_synced != True:
            from database.analytics_db import get_analytics_db
            analytics_db = get_analytics_db()
            sat_perf_ref = (analytics_db.db.collection('users')
                       .document(user_id)
                       .collection('sat_predictor_performance'))
        
            # Get documents ordered by timestamp, newest first
            docs = list(sat_perf_ref
                .order_by('timestamp', direction='DESCENDING')
                .limit(1)
                .stream())
            
            # If there's no document, set predicted_score to zero
            if len(docs) == 0: 
                logger.info(f"No SAT predictor performance found for user {user_id} to populate predicted_score")
                
                # Set predicted_score on user object
                user_obj.predicted_score.math_score = 0
                user_obj.predicted_score.rw_score = 0
                user_obj.predicted_score.is_synced = True
                
                # Update user in database with zero scores 
                try:
                    update_predicted_score(user_id, 0, 0, 0)
                except Exception as e:
                    logger.error(f"Failed to update user {user_id} with zero predicted_score: {str(e)}")
                
                return {
                    'success': True,
                    'data': user_obj.to_dict()    
                }
              
            data = docs[0].to_dict()
            user_obj.predicted_score.math_score = data.get('math_score', 0)
            user_obj.predicted_score.rw_score = data.get('rw_score', 0)
            user_obj.predicted_score.total_score = data.get('total_sat_score', 0)
            user_obj.predicted_score.is_synced = True
            logger.info(f"Populated predicted_score for user {user_id} from SAT predictor history")
            
            # Update user in database with the new predicted_score
            try:
                update_predicted_score(user_id, data.get('math_score', 0),
                                       data.get('rw_score', 0), data.get('total_sat_score', 0))
            except Exception as e:
                logger.error(f"Failed to update user {user_id} with populated predicted_score: {str(e)}")
        
        return {
            'success': True,
            'data': user_obj.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Internal server error',
                'message': 'Failed to retrieve user'
            }
        )


@user_router.post('/', status_code=status.HTTP_201_CREATED)
def create_user(request_data: CreateUserRequest, user: dict = Depends(authenticate_request)):
    try:
        data = request_data.dict()
        
        # Check if user already exists
        existing_user = getUserbyId(data['id'])
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    'error': 'Conflict',
                    'message': 'User with this ID already exists'
                }
            )
        
        user_obj = User.from_dict(data)
        user_obj.created_at = datetime.now(timezone.utc)
        user_obj.updated_at = datetime.now(timezone.utc)
        
        user_dict = user_obj.to_dict()
        
        success = createUser(user_dict)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'error': 'Internal server error',
                    'message': 'Failed to create user in database'
                }
            )
        
        try: 
            # Add leaderboard entry for new user
            leaderboard_entity = LeaderboardEntity(
                user_id=data['id'],
                username=data.get('name',''),
                region=Region(
                    country=data.get('country', ''),
                    state=data.get('state', ''),
                    city=data.get('city', '')
                ),
                performance_metric=PerformanceMetric()
            )
            leaderboard_db = get_leaderboard_db()
            lb_success = leaderboard_db.create_or_update_entity(leaderboard_entity)
            if not lb_success:
                logger.error(f"Failed to create leaderboard entry for user {data['id']}")
        except Exception as lb_error:
            logger.error(f"Error creating leaderboard entry for user {data['id']}: {str(lb_error)}")
        
        # Initialize tasks for the new user
        try:
            from helper.task_service import initialize_user_tasks
            from database.firebase_client import get_firestore_client
            
            firestore_client = get_firestore_client()
            initial_tasks = initialize_user_tasks(user_obj, firestore_client)
            
            logger.info(f"Successfully created user {data['id']} with {len(initial_tasks)} initial tasks")
            
            return {
                'success': True,
                'message': 'User created successfully with initial tasks assigned',
                'data': user_dict,
                'initial_tasks_count': len(initial_tasks)
            }
            
        except Exception as task_error:
            logger.error(f"Failed to initialize tasks for user {data['id']}: {str(task_error)}")
            
            return {
                'success': True,
                'message': 'User created successfully (tasks will be assigned on first login)',
                'data': user_dict,
                'warning': 'Initial task assignment failed'
            }
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'error': 'Bad request',
                'message': f'Invalid data: {str(e)}'
            }
        )
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Internal server error',
                'message': 'Failed to create user'
            }
        )


@user_router.post('/update-tags', status_code=status.HTTP_200_OK)
def update_tags(request_data: UpdateTagsRequest, user: dict = Depends(authenticate_request)):
    try:
        if _update_user_tags_quiz(request_data.user_id, request_data.tags):
            logger.info("Updated User Tags")
            return {
                'success': True,
                'message': 'Tags updated successfully'
            }
        else:
            logger.warning("Failed to update User Tags")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'error': 'Internal server error',
                    'message': 'Failed to update tags'
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'error': 'Bad request',
                'message': 'Invalid data'
            }
        )


@user_router.post('/update-task-num', status_code=status.HTTP_200_OK)
def update_task_num(request_data: UpdateTaskNumRequest, user: dict = Depends(authenticate_request)):
    try:
        user_db = get_user_db()
        success = user_db.update_num_tasks_per_week(request_data.user_id, request_data.num_tasks)
        if success:
            return {
                'success': True,
                'message': 'Number of tasks updated successfully'
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'success': False,
                    'message': 'Failed to update number of tasks'
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating number of tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Internal server error',
                'message': 'Failed to update number of tasks'
            }
        )


@user_router.put('/{user_id}/update', status_code=status.HTTP_200_OK)
@user_router.patch('/{user_id}/update', status_code=status.HTTP_200_OK)
def update_user(user_id: str, request_data: UpdateUserRequest, user: dict = Depends(authenticate_request)):
    """
    Update user data with any fields provided in the request.
    Only the fields present in the request will be updated.
    """
    try:
        data = request_data.dict(exclude_unset=True)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'error': 'Bad request',
                    'message': 'No data provided'
                }
            )
        
        # Check if user exists
        user_db = get_user_db()
        existing_user = user_db.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    'error': 'Not found',
                    'message': 'User not found'
                }
            )
        
        # Fields that cannot be updated via this endpoint
        protected_fields = ['id', 'created_at']
        update_data = {}
        
        # Filter out protected fields
        for key, value in data.items():
            if key not in protected_fields:
                update_data[key] = value
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'error': 'Bad request',
                    'message': 'No valid fields to update'
                }
            )
        
        # Validate enum fields if provided
        try:
            if 'grade' in update_data and update_data['grade'] is not None:
                from models.users_schema import Grade
                Grade(update_data['grade'])
            
            if 'board' in update_data and update_data['board'] is not None:
                from models.users_schema import Board
                Board(update_data['board'])
            
            if 'preferences' in update_data:
                prefs = update_data['preferences']
                if 'language' in prefs:
                    from models.users_schema import Language
                    Language(prefs['language'])
                if 'accessibility' in prefs:
                    acc = prefs['accessibility']
                    if 'font_size' in acc:
                        from models.users_schema import FontSize
                        FontSize(acc['font_size'])
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'error': 'Bad request',
                    'message': f'Invalid enum value: {str(e)}'
                }
            )
        
        # Perform the update
        success = user_db.update_user(user_id, update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'error': 'Internal server error',
                    'message': 'Failed to update user'
                }
            )
        
        # Retrieve and return updated user data
        updated_user = user_db.get_user_by_id(user_id)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'error': 'Internal server error',
                    'message': 'User updated but could not retrieve updated data'
                }
            )
        
        user_obj = User.from_dict(updated_user)
        
        logger.info(f"Successfully updated user {user_id} with fields: {list(update_data.keys())}")
        
        return {
            'success': True,
            'message': 'User updated successfully',
            'data': user_obj.to_dict(),
            'updated_fields': list(update_data.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Internal server error',
                'message': 'Failed to update user'
            }
        )

# @user_router.delete('/{user_id}', status_code=status.HTTP_200_OK)
def delete_user(user_id: str, user: dict = Depends(authenticate_request)):
    """
    Delete a user and their associated leaderboard entry.
    """
    try:
        # Check if user exists
        user_db = get_user_db()
        existing_user = user_db.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    'error': 'Not found',
                    'message': 'User not found'
                }
            )
        
        # Delete from user database
        user_delete_success = user_db.delete_user(user_id)
        
        if not user_delete_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'error': 'Internal server error',
                    'message': 'Failed to delete user from database'
                }
            )
        
        # Delete from leaderboard database
        try:
            leaderboard_db = get_leaderboard_db()
            lb_delete_success = leaderboard_db.delete_entity(user_id)
            if not lb_delete_success:
                logger.warning(f"Failed to delete leaderboard entry for user {user_id}")
        except Exception as lb_error:
            logger.error(f"Error deleting leaderboard entry for user {user_id}: {str(lb_error)}")
        
        logger.info(f"Successfully deleted user {user_id}")
        
        return {
            'success': True,
            'message': 'User deleted successfully',
            'data': {
                'user_id': user_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Internal server error',
                'message': 'Failed to delete user'
            }
        )


@user_router.post('/report-issue', status_code=status.HTTP_201_CREATED)
def report_issue(request_data: ReportIssueRequest, user: dict = Depends(authenticate_request)):
    """
    Report an issue faced by a user while using the application.
    Issue types: bug, feature_request, other
    """
    try:
        from database.firebase_client import get_firestore_client
        import uuid
        
        db = get_firestore_client()
        
        # Generate a unique ID for the issue
        issue_id = str(uuid.uuid4())
        
        # Create the issue document
        issue_data = {
            'id': issue_id,
            'user_id': request_data.user_id,
            'issue_title': request_data.issue_title,
            'issue_description': request_data.issue_description,
            'issue_type': request_data.issue_type,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Store in user_issues collection
        db.collection('user_issues').document(issue_id).set(issue_data)
        
        logger.info(f"Issue reported successfully: {issue_id} by user {request_data.user_id}")
        
        return {
            'success': True,
            'message': 'Issue reported successfully',
            'data': {
                'issue_id': issue_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error reporting issue: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Internal server error',
                'message': 'Failed to report issue'
            }
        )


@user_router.post('/user-delete-request', status_code=status.HTTP_201_CREATED)
def user_delete_request(request_data: UserDeleteRequest, user: dict = Depends(authenticate_request)):
    """
    Request account deletion for a user.
    Creates a deletion request record with 'pending' status.
    """
    try:
        from database.firebase_client import get_firestore_client
        import uuid
        
        db = get_firestore_client()
        
        # Check if user exists
        user_db = get_user_db()
        existing_user = user_db.get_user_by_id(request_data.user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    'error': 'User not found',
                    'message': 'No user exists with the provided ID'
                }
            )
        
        # Generate a unique ID for the deletion request
        request_id = str(uuid.uuid4())
        
        # Create the deletion request document
        deletion_request_data = {
            'id': request_id,
            'user_id': request_data.user_id,
            'reason': request_data.reason,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'pending'
        }
        
        # Store in user_deletion_requests collection
        db.collection('user_deletion_requests').document(request_id).set(deletion_request_data)
        
        logger.info(f"Deletion request created: {request_id} for user {request_data.user_id}")
        
        return {
            'success': True,
            'message': 'Account deletion request submitted successfully',
            'data': {
                'request_id': request_id,
                'user_id': request_data.user_id,
                'status': 'pending'
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating deletion request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Internal server error',
                'message': 'Failed to submit deletion request'
            }
        )