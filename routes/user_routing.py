from flask import Blueprint, request, jsonify
from models.users_schema import User
from typing import Dict, Any
from database.user_db import getUserbyId, createUser, checkUserExists
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
async def create_user():
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
		
		# Initialize tasks for the new user
		try:
			from helper.task_service import initialize_user_tasks
			from database.firebase_client import get_firestore_client
			
			firestore_client = get_firestore_client()
			initial_tasks = await initialize_user_tasks(user_obj, firestore_client)
			
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
