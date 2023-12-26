from werkzeug.security import generate_password_hash
from models import User, Todo
from datetime import datetime
import os
from secrets import token_hex
import unittest
from flask_jwt_extended import create_access_token, get_csrf_token
from flask_testing import TestCase
from dotenv import load_dotenv
from faker import Faker
load_dotenv()
os.environ['APP_SETTINGS'] = 'config.TestingConfig'
from app import app, db

fake = Faker()


class TestApp(TestCase):
    def create_app(self):
        """
        This method is used by Flask-Testing to create the Flask app instance.
        """
        return app

    def setUp(self):
        """
        This method is called before each test.
        """
        db.create_all()
        user = User(name=fake.name(), email=fake.email(), password=generate_password_hash(
            "@password1234"), role='simple', token=token_hex(16))
        db.session.add(user)
        db.session.commit()
        self.user = user
        self.client.testing = True

    def tearDown(self):
        """
        This method is called after each test.
        """
        db.session.remove()
        db.drop_all()

    def test_hello_route(self):
        """
        Should return status code 200 and message OK
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode('utf-8'), 'OK')

    def test_signup_route(self):
        """
        Should return status code 201,message Utilisateur créé
        """
        response = self.client.post(
            '/api/v1/users',
            json={'name': 'testuser', 'email': 'test@example.com',
                  'password': 'password123'}
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue('requestStatus' in response.json)
        self.assertTrue(response.json['requestStatus'])

    def test_login_route(self):
        """
        Should return status code 200,message Connexion réussie and token
        """

        response = self.client.post(
            '/api/v1/login',
            json={'email': self.user.email, 'password': "@password1234"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['requestStatus'])
        self.assertEqual(response.json['message'], "Connexion réussie")

    def test_add_todo_route(self):
        """
        Should return status code 201,message TodoCreated and data of the todo created
        """
        access_token = create_access_token(identity=self.user.email)
        headers = {'X-CSRF-TOKEN': get_csrf_token(access_token)}
        self.client.set_cookie('access_token_cookie', access_token)
        response = self.client.post(
            '/api/v1/todos',
            json={'title': 'Test Todo', 'description': 'Testing',
                  'completed': False, 'deadline': '01/01/24 12:00:00'},
            headers=headers
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json['requestStatus'])
        self.assertEqual(response.json['data']['title'], 'Test Todo')

    def test_get_todos_route(self):
        """
        Should return all todos of the user and status code 200
        """
        access_token = create_access_token(identity=self.user.email)
        headers = {'X-CSRF-TOKEN': get_csrf_token(access_token)}
        self.client.set_cookie('access_token_cookie', access_token)
        for i in range(3):
            todo = Todo(title=f'Test Todo {i}', description='Testing', completed=False, deadline=datetime(
                2024, 1, 5), user_id=self.user.id)
            db.session.add(todo)
            db.session.commit()
        response = self.client.get(
            '/api/v1/todos',
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['requestStatus'])
        self.assertEqual(len(response.json['data']), 3)
        self.assertEqual(response.json['data'][0]['title'], 'Test Todo 0')

    def test_get_todo_route(self):
        """
        Should only return 1 todo of the user and status code 200
        """
        access_token = create_access_token(identity=self.user.email)
        headers = {'X-CSRF-TOKEN': get_csrf_token(access_token)}
        self.client.set_cookie('access_token_cookie', access_token)
        todo = Todo(title='Test Todo', description='Testing', completed=False,
                    deadline=datetime(2024, 1, 5), user_id=self.user.id)
        db.session.add(todo)
        db.session.commit()
        response = self.client.get(
            f'/api/v1/todos/{todo.id}',
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['requestStatus'])
        self.assertEqual(response.json['data']['title'], 'Test Todo')

    def test_update_todo_route(self):
        """
        Should return status code 200 and todo updated 
        """
        access_token = create_access_token(identity=self.user.email)
        headers = {'X-CSRF-TOKEN': get_csrf_token(access_token)}
        self.client.set_cookie('access_token_cookie', access_token)
        todo = Todo(title='Test Todo', description='Testing', completed=False,
                    deadline=datetime(2024, 1, 5), user_id=self.user.id)
        db.session.add(todo)
        db.session.commit()
        response = self.client.put(
            f'/api/v1/todos/{todo.id}',
            json={'title': 'Test Todo Updated', 'description': 'Testing',
                  'completed': False, 'deadline': '01/01/24 12:00:00'},
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['requestStatus'])
        self.assertEqual(response.json['data']['title'], 'Test Todo Updated')

    def test_delete_todo_route(self):
        """
        Should return status code 200 and message TodoDeleted 
        """
        access_token = create_access_token(identity=self.user.email)
        headers = {'X-CSRF-TOKEN': get_csrf_token(access_token)}
        self.client.set_cookie('access_token_cookie', access_token)
        todo = Todo(title='Test Todo', description='Testing', completed=False,
                    deadline=datetime(2024, 1, 5), user_id=self.user.id)
        db.session.add(todo)
        db.session.commit()
        response = self.client.delete(
            f'/api/v1/todos/{todo.id}',
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['requestStatus'])
        self.assertEqual(response.json['message'], 'TodoDeleted')

    def test_logout_route(self):
        """
        Should return status code 200 and message LoggedOut
        """
        response = self.client.post('/api/v1/logout')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('requestStatus' in response.json)
        self.assertTrue(response.json['requestStatus'])


if __name__ == '__main__':
    unittest.main()
