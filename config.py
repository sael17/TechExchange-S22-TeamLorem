from os import environ, path
from dotenv import load_dotenv
import secrets

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

class Config:
    """Base config."""
    environ.update({'SECRET_KEY': secrets.token_hex(nbytes=16)})
    SECRET_KEY = environ.get('SECRET_KEY')

class ProdConfig(Config):
    FLASK_ENV = 'production'
    MONGO_DBNAME = 'GoalUp'

class DevConfig(Config):
    FLASK_ENV = 'development'
    MONGO_DBNAME = 'test'