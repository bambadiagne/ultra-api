# ultra-api
This is a optimized RESTful API. It's built with Flask,PostgresSQL,Redis and Docker.The aim is to show the different concepts of a backend(caching,security,...) that are sometimes considered as just CRUD operations.

## Project stack 
| Stack | Logo |
| ----- | ---- |
| Docker| <a href="https://www.docker.com/" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/docker/docker-original-wordmark.svg" alt="docker" width="40" height="40"/> </a>     |
| Flask | <a href="https://flask.palletsprojects.com/" target="_blank" rel="noreferrer"> <img src="https://www.vectorlogo.zone/logos/pocoo_flask/pocoo_flask-icon.svg" alt="flask" width="40" height="40"/> </a> |
| PostgreSQL |<a href="https://www.postgresql.org" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/postgresql/postgresql-original-wordmark.svg" alt="postgresql" width="40" height="40"/> </a> |
| Redis |  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/redis/redis-original-wordmark.svg" alt="redis" width="40" height="40"/> </a> |


## Features

- User registration and authentication and authorization(JWT+CORS)
- CRUD operations for todos
- Caching(with redis)
- Pagination and search for todos
- Rate limiting
- Logging system(with CloudWatch)


## Endpoints

- `/api/v1/user`: Register a new user
- `/auth`: Log in a user
- `/api/v1/todos`: Get all todos for the current user
- `/api/v1/todo/<int:id_todo>`: Get, update, or delete a specific todo

## Installation
1. Clone the repository: `git clone https://github.com/yourusername/yourrepository.git`

2. Create .env file copy .env.sample contents and change the values(if you not change it,sending mail and logging system aren't running)

3. You can use the docker-compose file it's so simple but you need that Docker installed in your device
4. You can generate data by running gen_todos.py script who uses threading and generate 100k todo rows in your db

```bash
docker-compose up -d
```
Otherwise, you need to setup your own postgres server and also redis
## Usage

To get all todos for the current user:

``` 
GET /api/v1/todos?page=1&per_page=10&query=test 
```
To update a specific todo:
```
PUT /api/v1/todo/1 Content-Type: application/json

{ "title": "New title", "description": "New description", "completed": true, "deadline": "12/31/21 23:59:59" }
```

## Contributing
Pull requests are welcome [CONTRIBUTING](CONTRIBUTING.md).
## License
[MIT](LICENSE.md)
