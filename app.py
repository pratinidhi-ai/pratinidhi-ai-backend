from flask import Flask , jsonify , json , request

from database.user_db import getUsers, checkUserExists , getUserbyId
from helper.middleware import authenticate_request
from routes.user_routing import user_bp
from routes.tutor_routing import tutor_bp
from routes.task_routing import task_bp
from routes.question_routing import question_bp

app = Flask(__name__)

@app.errorhandler(404)
def not_found(error):
	return {'error': 'Not found', 'message': 'The requested resource was not found'}, 404

@app.errorhandler(500)
def internal_error(error):
	return {'error': 'Internal server error', 'message': 'Something went wrong'}, 500

app.register_blueprint(user_bp)
app.register_blueprint(tutor_bp)
app.register_blueprint(task_bp, url_prefix='/api/tasks')
app.register_blueprint(question_bp, url_prefix='/api/questions')

# Health check endpoint
@app.route('/', methods=['GET'])
def health_check():
	return {'status': 'healthy', 'service': 'user-api'}, 200


@app.route('/check-user-exists' , methods = ['GET'])
@authenticate_request
def check_user_exists():
	arguments = request.args
	_uid = arguments.get('uid')
	if _uid is None:
		return jsonify({'error': 'uid parameter is required'}), 400
	exists = checkUserExists(user_id=_uid)
	return jsonify({'exists': exists}), 200


@app.route('/users' , methods = ['GET'])
@authenticate_request
def users():
	user_list = getUsers()
	return jsonify(user_list)

if __name__ == "__main__":
	app.run(host='0.0.0.0',port=8080)	