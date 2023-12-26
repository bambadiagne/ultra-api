from datetime import datetime, timedelta
import logging
import os
from utils import build_query, verify_body
from dotenv import load_dotenv
import secrets
from flask import Flask, jsonify, request
from flask_caching import Cache
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import create_access_token, set_access_cookies, jwt_required, get_jwt_identity, unset_jwt_cookies, JWTManager
from flask_apscheduler import APScheduler
from mailing import send_email, template_create
from models import Todo, User, db
from werkzeug.security import generate_password_hash, check_password_hash
from watchtower import CloudWatchLogHandler


load_dotenv()
logging.basicConfig(level=logging.INFO)

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
cache.init_app(app)
compress = Compress(app)
cloudwatch_handler = CloudWatchLogHandler(
    log_group=app.config["AWS_LOG_GROUP"], stream_name=app.config['AWS_LOG_STREAM'],)
logger = logging.getLogger(__name__)
logger.addHandler(cloudwatch_handler)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

CORS(app, origins=app.config['ALLOWED_HOSTS'])
with app.app_context():
    db.create_all()


jwt = JWTManager(app)


@scheduler.task('interval', id='send_remainder_todo',
                seconds=3600)
def send_remainder_todo():
    logger.info({"message": 'send_remainder_todo', "url": request.url,
                "method": request.method, })
    try:
        time_threshold = datetime.utcnow() + timedelta(hours=1)
        todos = [todo.serialize for todo in Todo.query.filter(
            Todo.deadline < time_threshold, Todo.completed == False).all()]
        users = User.query.filter(User.id.in_(
            [todo['user_id'] for todo in todos]), User.has_subscribed == True).all()
        for user in users:
            send_email(os.environ['AWS_MAIL_SENDER'], user.email, "Rappel tache à faire", f"""
                <h2>Bonjour {user.name},</h2><br>
                <p>Vous avez des tâches à faire dans moins d'une heure</p>
                <ul>
                    {"".join([f"<li>{todo['title']}</li>" for todo in todos if todo['user_id'] == user.id])}
                </ul>
                        """)
    except BaseException as e:
        logger.error({"url": request.url, "error": str(e)})


@app.route('/')
@limiter.limit("100/hour")
def hello():
    return 'OK', 200


@app.route('/api/v1/login', methods=['POST'])
@verify_body([('email', str), ('password', str),])
def login():
    logger.info({"message": 'try_to_login', "url": request.url,
                "method": request.method, })
    try:
        request_body = request.get_json(silent=True)
        user = User.query.filter_by(email=request_body['email']).first()
        if (user and check_password_hash(user.password, request_body['password'])):
            access_token = create_access_token(identity=user.email)
            response = jsonify(
                {'message': "Connexion réussie", 'requestStatus': True, })
            set_access_cookies(response, access_token)
            return response, 200
        return jsonify({'message': 'Identifiants incorrects', 'requestStatus': False, }), 401
    except BaseException as e:
        logger.error({"url": request.url, "error": str(e),
                     "payload": request_body})
        return jsonify({'message': str(e), 'requestStatus': False}), 500


@app.route('/api/v1/logout', methods=['POST'])
def logout():
    response = jsonify(
        {'requestStatus': True, 'message': 'Déconnexion réussie'})
    unset_jwt_cookies(response)
    return response, 200


@app.route('/api/v1/users', methods=['POST'])
@verify_body([('name', str), ('email', str), ('password', str),])
def signup():
    logger.info({"message": 'signup', "url": request.url,
                "method": request.method, })
    try:
        request_body = request.get_json(silent=True)
        token = secrets.token_hex(16)
        check_if_user_exists = User.query.filter_by(
            name=request_body['name']).first()
        if (check_if_user_exists):
            return jsonify({'message': 'Pseudo deja pris', 'requestStatus': False}), 400
        check_if_user_exists = User.query.filter_by(
            email=request_body['email']).first()
        if (check_if_user_exists):
            return jsonify({'message': 'Email deja pris', 'requestStatus': False}), 400
        user = User(name=request_body['name'], email=request_body['email'],
                    password=generate_password_hash(request_body['password']), token=token, role="simple")
        db.session.add(user)
        db.session.commit()
        if (app.config['DEBUG'] == False):
            template_create(user)
        return jsonify({'message': 'Utilisateur créé', 'requestStatus': True}), 201
    except BaseException as e:
        logger.error({"url": request.url, "error": str(e),
                     "payload": request_body})
        return jsonify({'message': str(e), 'requestStatus': False}), 500


@app.route('/check-account', methods=['POST'])
@verify_body([('token', str),])
@jwt_required()
def check_account():
    logger.info({"message": 'check_account',
                "url": request.url, "method": request.method, })
    try:
        request_body = request.get_json(silent=True)
        user = User.query.filter_by(token=request_body['token']).first()
        if (user):
            user.token = secrets.token_hex(16)
            user.emailChecked = True
            db.session.commit()
            return jsonify({'message': 'User\'mail checked', 'requestStatus': True}), 200
        return jsonify({'message': 'TokenNotValid', 'requestStatus': False}), 404
    except BaseException as e:
        logger.error({"url": request.url, "error": str(e)})
        return jsonify({'message': str(e), 'requestStatus': False}), 500


@app.route('/api/v1/todos', methods=['POST'])
@jwt_required()
@verify_body([('title', str), ('description', str), ('completed', bool), ('deadline', str)])
def add_todo():
    current_user = User.query.filter_by(email=get_jwt_identity()).first()
    logger.info({"message": 'add_todo', "url": request.url,
                "method": request.method, })
    try:
        request_body = request.get_json(silent=True)
        deadline = datetime.strptime(
            request_body['deadline'], '%m/%d/%y %H:%M:%S')
        todo = Todo(
            title=request_body['title'],
            description=request_body['description'],
            completed=request_body['completed'],
            user_id=current_user.id,
            deadline=deadline
        )
        db.session.add(todo)
        db.session.commit()
        return {'requestStatus': True, "data": todo.serialize}, 201
    except BaseException as e:
        logger.error({"url": request.url, "error": str(e)})
        return {'message': str(e), 'requestStatus': False}, 500


@app.route('/api/v1/todos', methods=['GET'])
@jwt_required()
@limiter.limit("200/hour")
@cache.cached(timeout=90, query_string=True,)
def get_todos():
    logger.info({"message": 'get_todos', "url": request.url,
                "method": request.method, })
    try:
        current_user = User.query.filter_by(email=get_jwt_identity()).first()

        page = request.args.get('page', 1, type=int)
        per_page = 1000
        query_results = build_query(request.args, current_user.id)
        if (query_results.count() == 0):
            return {"requestStatus": True, "count": 0, "data": [], "total": 0, "current_page": page}, 200
        paginated_data = [todo.serialize for todo in query_results.paginate(
            page=page, per_page=per_page, max_per_page=1000, error_out=False).items]
        return {"requestStatus": True, "count": len(paginated_data), "data": paginated_data, "total": query_results.count(), "current_page": page, }, 200
    except BaseException as e:
        cache.delete_memoized(get_todos)
        logger.error({"url": request.url, "error": str(e)})
        return {"requestStatus": False, "message": "TodosNotFound", "error": str(e), }, 404


@app.route('/api/v1/todos/<int:id_todo>', methods=['GET'])
@jwt_required()
@limiter.limit("100/hour")
@cache.cached(timeout=90, key_prefix='get_one_todo')
def get_one_todo(id_todo):
    logger.info({"message": 'get_one_todo', "url": request.url,
                "method": request.method, })
    try:
        current_user = User.query.filter_by(
            email=get_jwt_identity()).first()
        todo = Todo.query.filter(
            Todo.id == id_todo, Todo.user_id == current_user.id).first()
        if (todo):
            logger.info({"message": 'success', "data": todo.serialize})
            return {"requestStatus": True, "data": todo.serialize}, 200
        return {"requestStatus": True, "message": "TodoNotFound"}, 404
    except BaseException as e:
        logger.error({"url": request.url, "error": str(e)})
        return {"requestStatus": False, "message": "TodoNotFound", "error": str(e)}, 404


@app.route('/api/v1/todos/<int:id_todo>', methods=['PUT'])
@jwt_required()
@verify_body([('title', str), ('description', str), ('completed', bool), ('deadline', str)])
def update_one_todo(id_todo):
    logger.info({"message": 'update_one_todo',
                "url": request.url, "method": request.method, })
    try:
        request_body = request.get_json(silent=True)
        current_user = User.query.filter_by(
            email=get_jwt_identity()).first()
        todo = Todo.query.filter(
            Todo.id == id_todo, Todo.user_id == current_user.id).first()
        if (todo):
            todo.title = request_body['title']
            todo.description = request_body['description']
            todo.completed = request_body['completed']
            todo.deadline = datetime.strptime(
                request_body['deadline'], '%m/%d/%y %H:%M:%S')
            db.session.commit()
            cache.delete_memoized(get_todos)
            cache.delete_memoized(get_one_todo, id_todo)

            return {"requestStatus": True, "data": todo.serialize}, 200
        return {"requestStatus": True, "message": "TodoNotFound"}, 404
    except BaseException as e:
        logger.error({"url": request.url, "error": str(e),
                     "payload": request_body})
        return {"requestStatus": False, "message": "TodoNotFound", "error": str(e)}, 404


@app.route('/api/v1/todos/<int:id_todo>', methods=['DELETE'])
@jwt_required()
def delete_one_todo(id_todo):
    logger.info({"message": 'delete_one_todo',
                "url": request.url, "method": request.method, })
    try:
        current_user = User.query.filter_by(
            email=get_jwt_identity()).first()
        deleted_todo = Todo.query.filter(
            Todo.id == id_todo, Todo.user_id == current_user.id).delete()
        if (deleted_todo):
            db.session.commit()
            return {"requestStatus": True, "message": "TodoDeleted"}, 200
        return {"requestStatus": True, "message": "TodoNotFound"}, 404
    except BaseException as e:
        logger.error({"url": request.url, "error": str(e)})
        return {"requestStatus": False, "message": "TodoNotFound", "error": str(e)}, 404


if (__name__ == '__main__'):
    app.run(host='0.0.0.0')
