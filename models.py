
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Todo(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Todo {self.title}>'

    @property
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'user_id': self.user_id
        }


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    # picture = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(32), nullable=False, unique=True)
    emailChecked = db.Column(db.Boolean, nullable=False, default=False)
    role = db.Column(db.String(100), nullable=False)
    todos = db.relationship('Todo', backref='user')

    def __repr__(self):
        return f'<User {self.name}>'

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'emailChecked': self.emailChecked,
            'role': self.role,
            'todos': self.todos
        }
