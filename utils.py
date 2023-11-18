from functools import wraps
from flask import request
from flask_jwt import current_identity


def verify_body(required_fields):
    def _verify_body(f):
        @wraps(f)
        def __verify_body(*args, **kwargs):
            data = request.get_json(silent=True)

            if (not data):
                return {'message': "Empty body", 'status': 'FAILED'}
            if (len(data) != len(required_fields)):
                return {'message': "Longueur body incorrect", 'status': 'FAILED'}
            for required_field in required_fields:
                body_property = data.get(required_field[0])
                if (required_field[0] not in data):
                    return {"message": f"Champ {required_field[0]} requis", 'status': 'FAILED'}
                if (not type(body_property) is required_field[1]):
                    return {"message": f"Champ {required_field[0]} doit être de type {required_field[1]}", 'status': 'FAILED'}
            return f(*args, **kwargs)
        return __verify_body
    return _verify_body


def is_user_todo():
    def _is_user_todo(f):
        @wraps(f)
        def __is_user_todo(*args, **kwargs):
            result = f(*args, **kwargs)
            if (any(todo.id == int(request.view_args.get('id_todo')) for todo in current_identity.todos)):
                return result
            return {"requestStatus": False, "message": "NotAuthorized"}, 401
        return __is_user_todo
    return _is_user_todo
