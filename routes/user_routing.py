from flask import Blueprint, request, jsonify
from models.users_schema import User
from typing import Dict, Any
from helper.firebase import getUserbyId
import time
from datetime import datetime, timezone
import logging

user_bp = Blueprint('user',__name__,url_prefix='api/users')
logger = logging.getLogger(__name__)


@user_bp.route('/<user_id>',methods=['GET'] )
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

