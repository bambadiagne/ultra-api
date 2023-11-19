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
    JWT_EXPIRATION_DELTA = timedelta(seconds=86400)
    JWT_AUTH_USERNAME_KEY = 'email'


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
