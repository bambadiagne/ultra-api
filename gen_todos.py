from datetime import datetime
import time
from faker import Faker
from werkzeug.security import generate_password_hash
from models import db
from secrets import token_hex
from random import choices
from app import app
from models import Todo, User
import threading

fake = Faker()
users = []
TOTAL_TODOS = 100_000
THREAD_COUNT = 4


def generate_todo(id):
    with app.app_context():

        todo = Todo(
            title=fake.sentence(),
            description=fake.text(),
            completed=fake.boolean(),
            user_id=choices(users)[0].id,
            deadline=fake.date_between_dates(date_start=datetime(
                2023, 11, 16), date_end=datetime(2024, 4, 10)),
        )
        db.session.add(todo)
        db.session.commit()
        print(f"{id} {todo}")


def create_todos_in_threads(start_id, end_id):
    for todo_id in range(start_id, end_id):
        generate_todo(todo_id)


def run_threaded_function():
    threads = []
    todos_per_thread = TOTAL_TODOS // THREAD_COUNT

    for i in range(THREAD_COUNT):
        start_id = i * todos_per_thread
        end_id = (i + 1) * todos_per_thread if i < THREAD_COUNT - \
            1 else TOTAL_TODOS
        thread = threading.Thread(
            target=create_todos_in_threads, args=(start_id, end_id))
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


with app.app_context():
    start_time = time.time()
    for i in range(3):
        user = User(name=fake.name(), email=fake.email(), password=generate_password_hash(
            f"User{str(i).zfill(5)}"), role='simple', token=token_hex(16))
        db.session.add(user)
        db.session.commit()
        users.append(user)

    run_threaded_function()
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
