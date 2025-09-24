from flask import Flask , jsonify , json , request

from helper.firebase import getUsers , _getMetaData , _getQuestions , checkUserExists
from helper.middleware import authenticate_request
from routes.user_routing import user_bp
app = Flask(__name__)

app.register_blueprint(user_bp)

@app.errorhandler(404)
def not_found(error):
	return {'error': 'Not found', 'message': 'The requested resource was not found'}, 404

@app.errorhandler(500)
def internal_error(error):
	return {'error': 'Internal server error', 'message': 'Something went wrong'}, 500

# Health check endpoint
@app.route('/', methods=['GET'])
def health_check():
	return {'status': 'healthy', 'service': 'user-api'}, 200
   

@app.route('/get-questions' , methods = ['GET'])
# @authenticate_request
def getQuestions():
	attributes = request.args 

	required_params = ['subject', 'subcategory', 'standard', 'difficulty']
	if not all(param in attributes for param in required_params):
		return {'_error' : 'Missing one or more required query parameters' }, 422
	
	questions_list = _getQuestions(attributes)
	return jsonify(questions_list)

@app.route('/get-metadata' , methods = ['GET'])
@authenticate_request
def getMetaData():
	if _getMetaData() is not None:
		return jsonify(_getMetaData())
	return {'_error:' "No MetaData was found"} , 404

@app.route('/check-user-exists' , methods = ['GET'])
@authenticate_request
def check_user_exists():
	arguments = request.args
	_uid = arguments.get('uid')
	exists = checkUserExists(user_id=_uid)
	return jsonify({'exists': exists}), 200


@app.route('/users' , methods = ['GET'])
@authenticate_request
def users() -> json:
	user_list = getUsers()
	return jsonify(user_list)

if __name__ == "__main__":
	app.run(host='0.0.0.0',port=8080)	