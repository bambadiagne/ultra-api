from flask import Flask
import os
from dotenv import load_dotenv
from models import Todo,db
load_dotenv()
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
@app.route('/')
def hello():
    return 'OK',200
@app.route('/todo', methods=['POST'])
def add_todo():
    todo = Todo(
        title='First Todo',
        description='A description of my first todo',
        completed=False  
    )
    db.session.add(todo)
    db.session.commit()
    return 'OK',200
@app.route('/todos', methods=['GET'])
def get_todos():
    todos = Todo.query.all()
    results = [
        {
            "title": todo.title,
            "description": todo.description
        } for todo in todos]
    return {"count": len(results), "todos": results}

if __name__ == '__main__':
    app.run(host='0.0.0.0')