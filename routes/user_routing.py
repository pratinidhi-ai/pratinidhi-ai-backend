from flask import Blueprint, request, jsonify
from models.users_schema import User
from typing import Dict, Any
from database.user_db import getUserbyId, createUser, checkUserExists , _update_user_tags_quiz , get_user_db
from database.leaderboard_db import get_leaderboard_db
from models.leaderboard_schema import LeaderboardEntity, PerformanceMetric, Region
import time
from helper.middleware import authenticate_request
from datetime import datetime, timezone
import logging

user_bp = Blueprint('user',__name__,url_prefix='/api/users')
logger = logging.getLogger(__name__)


@user_bp.route('/<user_id>',methods=['GET'] )
@authenticate_request
def get_user(user_id: str) :
	try:
		item = getUserbyId(user_id=user_id)
		if not item:
			return jsonify({
				'error': 'User not found',
				'message': 'No user exists with the provided ID'
			}), 404
		user_obj = User.from_dict(item)
		user_obj.last_login = datetime.now(timezone.utc)
		return jsonify({
			'success' : True,
			'data' : user_obj.to_dict()
		}) , 200
	except Exception as e:
		logger.error(f"Error getting user {user_id}: {str(e)}")
		return jsonify({
			'error': 'Internal server error',
			'message': 'Failed to retrieve user'
		}) , 500

@user_bp.route('/' , methods = ['POST'])
@authenticate_request
def create_user():
	try:
		data = request.get_json()
		if not data:
			return jsonify({
				'error': 'Bad request',
				'message': 'No data provided'
			}) , 400
		required_fields = ['id', 'email', 'name']
		missing_fields = [field for field in required_fields if not data.get(field)]
		
		if missing_fields:
			return jsonify({
				'error': 'Bad request',
				'message': f'Missing required fields: {", ".join(missing_fields)}'
			}), 400
		
		# Check if user already exists
		existing_user = getUserbyId(data['id'])
		if existing_user:
			return jsonify({
				'error': 'Conflict',
				'message': 'User with this ID already exists'
			}), 409
		
		user_obj = User.from_dict(data)
		

		user_obj.created_at = datetime.now(timezone.utc)
		user_obj.updated_at = datetime.now(timezone.utc)
		
		user_dict = user_obj.to_dict()
		
		success = createUser(user_dict)
		
		if not success:
			return jsonify({
				'error': 'Internal server error',
				'message': 'Failed to create user in database'
			}), 500
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
				performance_metric=PerformanceMetric()  # ✅ Uses dataclass defaults
			)
			leaderboard_db = get_leaderboard_db()
			lb_success = leaderboard_db.create_or_update_entity(leaderboard_entity)
			if not lb_success:
				logger.error(f"Failed to create leaderboard entry for user {data['id']}")
		except Exception as lb_error:
			# Log leaderboard creation error but continue
			logger.error(f"Error creating leaderboard entry for user {data['id']}: {str(lb_error)}")
		
		# Initialize tasks for the new user
		try:
			from helper.task_service import initialize_user_tasks
			from database.firebase_client import get_firestore_client
			
			firestore_client = get_firestore_client()
			initial_tasks =  initialize_user_tasks(user_obj, firestore_client)
			
			logger.info(f"Successfully created user {data['id']} with {len(initial_tasks)} initial tasks")
			
			return jsonify({
				'success': True,
				'message': 'User created successfully with initial tasks assigned',
				'data': user_dict,
				'initial_tasks_count': len(initial_tasks)
			}), 201
			
		except Exception as task_error:
			# User was created but task initialization failed - log and continue
			logger.error(f"Failed to initialize tasks for user {data['id']}: {str(task_error)}")
			
			return jsonify({
				'success': True,
				'message': 'User created successfully (tasks will be assigned on first login)',
				'data': user_dict,
				'warning': 'Initial task assignment failed'
			}), 201
		
	except ValueError as e:
		logger.error(f"Validation error creating user: {str(e)}")
		return jsonify({
			'error': 'Bad request',
			'message': f'Invalid data: {str(e)}'
		}), 400
	except Exception as e:
		logger.error(f"Error creating user: {str(e)}")
		return jsonify({
			'error': 'Internal server error',
			'message': 'Failed to create user'
		}), 500

@user_bp.route('/update-tags' , methods = ['POST'])
@authenticate_request
def update_tags():
	try:
		data = request.get_json()
		if _update_user_tags_quiz(data.get('user_id'), data.get('tags')):
			logger.info("Updated User Tags")
			return jsonify({
				'success': True,
				'message': 'Tags updated successfully'
			}), 200
			
		else:
			logger.warning("Failed to update User Tags")
			return jsonify({
				'error': 'Internal server error',
				'message': 'Failed to update tags'
			}), 500
		
	except Exception as e:
		logger.error(f"Error parsing JSON data: {str(e)}")
		return jsonify({
			'error': 'Bad request',
			'message': 'Invalid JSON data'
		}), 400
	
@user_bp.route('/update-task-num' , methods = ['POST'])
@authenticate_request
def update_task_num():
	try:
		data = request.get_json()
		user_id = data.get('user_id')
		num_tasks = data.get('num_tasks',16)
		if not isinstance(num_tasks, int) or num_tasks < 0:
			return jsonify({
				'success': False,
				'message': 'Invalid number of tasks provided'
			}), 400
		user_db = get_user_db()
		success = user_db.update_num_tasks_per_week(user_id, num_tasks)
		if success:
			return jsonify({
				'success': True,
				'message': 'Number of tasks updated successfully'
			}), 200
		else:
			return jsonify({
				'success': False,
				'message': 'Failed to update number of tasks'
			}) , 400
	except Exception as e:
		logger.error(f"Error updating number of tasks: {str(e)}")
		return jsonify({
			'error': 'Internal server error',
			'message': 'Failed to update number of tasks'
		}), 500

@user_bp.route('/<user_id>/update', methods=['PUT', 'PATCH'])
@authenticate_request
def update_user(user_id: str):
	"""
	Update user data with any fields provided in the request.
	Only the fields present in the request will be updated.
	"""
	try:
		data = request.get_json()
		if not data:
			return jsonify({
				'error': 'Bad request',
				'message': 'No data provided'
			}), 400
		
		# Check if user exists
		user_db = get_user_db()
		existing_user = user_db.get_user_by_id(user_id)
		if not existing_user:
			return jsonify({
				'error': 'Not found',
				'message': 'User not found'
			}), 404
		
		# Fields that cannot be updated via this endpoint
		protected_fields = ['id', 'created_at']
		update_data = {}
		
		# Filter out protected fields and None values
		for key, value in data.items():
			if key not in protected_fields:
				update_data[key] = value
		
		if not update_data:
			return jsonify({
				'error': 'Bad request',
				'message': 'No valid fields to update'
			}), 400
		
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
			return jsonify({
				'error': 'Bad request',
				'message': f'Invalid enum value: {str(e)}'
			}), 400
		
		# Perform the update
		success = user_db.update_user(user_id, update_data)
		
		if not success:
			return jsonify({
				'error': 'Internal server error',
				'message': 'Failed to update user'
			}), 500
		
		# Retrieve and return updated user data
		updated_user = user_db.get_user_by_id(user_id)
		if not updated_user:
			return jsonify({
				'error': 'Internal server error',
				'message': 'User updated but could not retrieve updated data'
			}), 500
		
		user_obj = User.from_dict(updated_user)
		
		logger.info(f"Successfully updated user {user_id} with fields: {list(update_data.keys())}")
		
		return jsonify({
			'success': True,
			'message': 'User updated successfully',
			'data': user_obj.to_dict(),
			'updated_fields': list(update_data.keys())
		}), 200
		
	except Exception as e:
		logger.error(f"Error updating user {user_id}: {str(e)}")
		return jsonify({
			'error': 'Internal server error',
			'message': 'Failed to update user'
		}), 500
