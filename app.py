from flask import Flask , jsonify , json
from helper.firebase import getUsers 
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
   

@app.route('/users' , methods = ['GET'])
def users() -> json:
	user_list = getUsers()
	return jsonify(user_list)

if __name__ == "__main__":
	app.run(host='0.0.0.0',port=8080)	