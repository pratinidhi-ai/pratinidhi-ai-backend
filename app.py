from flask import Flask , jsonify , json
from helper.firebase import getUsers
from helper.middleware import authenticate_request
app = Flask(__name__)


@app.route('/')
# @authenticate_request
def index():
    return jsonify({"status": "ok", "message": "Flask app is running"}), 200

@app.route('/users' , methods = ['GET'])
def users() -> json:
	user_list = getUsers()
	return jsonify(user_list)

if __name__ == "__main__":
	app.run(host='0.0.0.0',port=8080)	