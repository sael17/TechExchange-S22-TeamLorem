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
import model

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
    data = posts.find({})
    result = []
    for entry in data:
        result.append(model.create_post(author = entry['author'], group = entry['group'], content = entry['content'], date = entry['date'], image = entry['group_image']))
    if result:
        return render_template('index.html', home_posts=result)
    return render_template('index.html',error='There are no posts available')
