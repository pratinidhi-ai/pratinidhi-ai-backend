from flask import Flask , jsonify , json , request
import logging
import sys
import os

from database.user_db import getUsers, checkUserExists , getUserbyId
from helper.middleware import authenticate_request
from routes.user_routing import user_bp
from routes.tutor_routing import tutor_bp
from routes.task_routing import task_bp
from routes.question_routing import question_bp
from routes.analytics_routing import analytics_bp
from routes.math_tutor_routing import math_tutor_bp
from routes.leaderboard_routing import leaderboard_bp

# Configure logging for the entire application
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
	level=getattr(logging, log_level, logging.INFO),
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	handlers=[
		logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout for AWS App Runner
	],
	force=True  # Override any existing logging configuration
)

# Create logger for this module
logger = logging.getLogger(__name__)
logger.info(f"Application starting with log level: {log_level}")

app = Flask(__name__)

# Also configure Flask's built-in logger
app.logger.setLevel(getattr(logging, log_level, logging.INFO))
app.logger.info("Flask app initialized")

@app.errorhandler(404)
def not_found(error):
	logger.warning(f"404 Not Found: {request.path}")
	return {'error': 'Not found', 'message': 'The requested resource was not found'}, 404

@app.errorhandler(500)
def internal_error(error):
	logger.error(f"500 Internal Server Error: {request.path}", exc_info=True)
	return {'error': 'Internal server error', 'message': 'Something went wrong'}, 500

app.register_blueprint(user_bp)
app.register_blueprint(tutor_bp)
app.register_blueprint(task_bp, url_prefix='/api/tasks')
app.register_blueprint(question_bp, url_prefix='/api/questions')
app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
app.register_blueprint(math_tutor_bp, url_prefix='/api/math_tutor')
app.register_blueprint(leaderboard_bp)


# Health check endpoint
@app.route('/', methods=['GET'])
def health_check():
	logger.info("Health check endpoint called")
	return {'status': 'healthy', 'service': 'user-api'}, 200


@app.route('/check-user-exists' , methods = ['GET'])
@authenticate_request
def check_user_exists():
	arguments = request.args
	_uid = arguments.get('uid')
	logger.info(f"Checking user existence for uid: {_uid}")
	if _uid is None:
		logger.warning("check-user-exists called without uid parameter")
		return jsonify({'error': 'uid parameter is required'}), 400
	exists = checkUserExists(user_id=_uid)
	logger.info(f"User {_uid} exists: {exists}")
	return jsonify({'exists': exists}), 200


@app.route('/users' , methods = ['GET'])
@authenticate_request
def users():
	logger.info("Fetching all users")
	user_list = getUsers()
	logger.info(f"Retrieved {len(user_list)} users")
	return jsonify(user_list)

if __name__ == "__main__":
	logger.info("Starting Flask application on 0.0.0.0:8080")
	app.run(host='0.0.0.0',port=8080)	