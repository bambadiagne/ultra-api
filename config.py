from datetime import timedelta
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
    CACHE_TYPE = os.environ['CACHE_TYPE']
    CACHE_REDIS_HOST = os.environ['CACHE_REDIS_HOST']
    CACHE_REDIS_PORT = os.environ['CACHE_REDIS_PORT']
    CACHE_REDIS_DB = os.environ['CACHE_REDIS_DB']
    CACHE_REDIS_URL = os.environ['CACHE_REDIS_URL']
    CACHE_DEFAULT_TIMEOUT = os.environ['CACHE_DEFAULT_TIMEOUT']
    JWT_SECRET_KEY = SECRET_KEY
    JWT_TOKEN_LOCATION = "cookies"
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_ACCESS_CSRF_HEADER_NAME = "X-CSRF-TOKEN"
    JWT_EXPIRATION_DELTA = timedelta(seconds=86400)
    JWT_AUTH_USERNAME_KEY = 'email'
    ALLOWED_HOSTS = ["*"]
    AWS_LOG_GROUP = os.environ['AWS_LOG_GROUP']
    AWS_LOG_STREAM = os.environ['AWS_LOG_STREAM']


class ProductionConfig(Config):
    DEBUG = False
    ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')
    JWT_COOKIE_SECURE = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
