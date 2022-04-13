# -- Import section --
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)
from flask_pymongo import PyMongo
import gunicorn # for heroku deployment
import secrets
import bcrypt 
import certifi
import os

# -- Initialization section --
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(nbytes=16)

# Name of database
db_name = 'test' if os.environ.get('DB_TEST') == '1' else 'GoalUp'
app.config['MONGO_DBNAME'] = db_name

# URI of database
mongodb_password = os.environ.get('MONGO_PASSWORD')
app.config['MONGO_URI'] = f"mongodb+srv://admin:{mongodb_password}@cluster0.3pto1.mongodb.net/{db_name}?retryWrites=true&w=majority"

# Initialize PyMongo
mongo = PyMongo(app, tlsCAFile=certifi.where())

# Collection References
users = mongo.db.users
posts = mongo.db.posts

# -- Routes section --

'''
INDEX route, initial route
'''
@app.route('/')
@app.route('/home')
def index():
    return render_template('index.html')
