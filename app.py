from flask import Flask , jsonify , json
from helper.firebase import getUsers
app = Flask(__name__)


@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "Flask app is running"}), 200

@app.route('/users' , methods = ['GET'])
def users() -> json:
	user_list = getUsers()
	return jsonify(user_list)

if __name__ == "__main__":
	app.run(host='0.0.0.0',port=8080)