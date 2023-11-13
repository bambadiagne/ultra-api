from datetime import datetime
import os
from dotenv import load_dotenv
import secrets
from flask import Flask, jsonify, request
from flask_caching import Cache
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt import JWT, jwt_required, current_identity
from flask_migrate import Migrate
from sqlalchemy import delete
from models import Todo, User, db
from werkzeug.security import generate_password_hash, check_password_hash
from utils import is_user_todo, verify_body
load_dotenv()
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
limiter = Limiter(
    get_remote_address,
    app=app, storage_uri="memory://",
)
migrate = Migrate(app, db)
cache = Cache(app)
compress = Compress(app)

with app.app_context():
    db.create_all()


def identity(payload):
    return User.query.get(payload['user_id'])


def authenticate(email, password):
    user = User.query.filter_by(email=email).first()
    if (user and check_password_hash(user.password, password)):
        return user


jwt = JWT(app, authenticate, identity)


@jwt.jwt_payload_handler
def make_payload(identity):
    return {'user_id': identity.id, 'iat': datetime.utcnow(), 'exp': datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA'], 'nbf': datetime.utcnow()}


@jwt.jwt_error_handler
def error_handler(error):
    return jsonify({'message': error.description, 'status': 'FAILED'}), 401


@app.route('/')
def hello():
    return 'OK', 200


@app.route('/api/v1/todo', methods=['POST'])
@jwt_required()
@verify_body([('title', str), ('description', str), ('completed', bool),])
def add_todo():
    request_body = request.get_json(silent=True)
    todo = Todo(
        title=request_body['title'],
        description=request_body['description'],
        completed=request_body['completed'],
        user_id=current_identity.id
    )
    db.session.add(todo)
    db.session.commit()
    return {"status": "SUCCESSFUL", "data": todo.serialize}, 201


@app.route('/signup', methods=['POST'])
@verify_body([('name', str), ('email', str), ('password', str),])
def signup():
    try:
        request_body = request.get_json(silent=True)
        token = secrets.token_hex(16)
        check_if_user_exists = User.query.filter_by(
            name=request_body['name']).first()
        if (check_if_user_exists):
            return jsonify({'message': 'Pseudo deja pris', 'status': 'FAILED'})
        check_if_user_exists = User.query.filter_by(
            email=request_body['email']).first()
        if (check_if_user_exists):
            return jsonify({'message': 'Email deja pris', 'status': 'FAILED'})
        user = User(name=request_body['name'], email=request_body['email'],
                    password=generate_password_hash(request_body['password']), token=token, role="simple")
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'Utilisateur créé', 'status': 'SUCCESSFUL'}), 201
    except BaseException as e:
        return jsonify({'message': str(e), 'status': 'FAILED'}), 500


@app.route('/api/v1/todo/<int:id_todo>', methods=['GET'])
@jwt_required()
@limiter.limit("100/hour")
@cache.cached(timeout=15)
def get_one_todo(id_todo):
    try:
        todo = Todo.query.get(id_todo)
        if (todo):
            return {"requestStatus": True, "todo": todo.serialize}, 200
        return {"requestStatus": True, "message": "TodoNotFound"}, 404
    except BaseException as e:
        return {"requestStatus": False, "message": "TodoNotFound", "error": str(e)}, 404


@app.route('/api/v1/todo/<int:id_todo>', methods=['DELETE'])
@jwt_required()
@is_user_todo()
def delete_one_todo(id_todo):
    try:
        deleted_todo = Todo.query.filter_by(id=id_todo).delete()
        if (deleted_todo):
            db.session.commit()
            return {"requestStatus": True, "message": "TodoDeleted"}, 200
        return {"requestStatus": True, "message": "TodoNotFound"}, 404
    except BaseException as e:
        return {"requestStatus": False, "message": "TodoNotFound", "error": str(e)}, 404


@app.route('/api/v1/todos', methods=['GET'])
@jwt_required()
@limiter.limit("200/hour")
@cache.cached(timeout=15)
def get_todos():
    try:
        results = [todo.serialize for todo in current_identity.todos]
        return {"count": len(results), "todos": results}, 200
    except BaseException as e:
        return {"requestStatus": False, "message": "TodosNotFound", "error": str(e)}, 404


if (__name__ == '__main__'):
    app.run(host='0.0.0.0')
