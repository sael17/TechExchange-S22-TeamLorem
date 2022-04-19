# -- Import section --
from backend.user import User
from crypt import methods
from flask_pymongo import PyMongo
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

import model
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

# Session Data/Cookie
app.secret_key = secrets.token_urlsafe(16)

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


@app.route("/signup",methods=["GET","POST"])
def signup():
    if request.method == "POST":
        # dictionary of possible errors to happen
        error_message = {"message":"", "error":None}

        # new user to be made
        new_user = User.from_document({
            "email":request.form["email"],
            "username":request.form["username"],
            "password": request.form["password"]
        })

        model.add_user(new_user,users,error_message)
        if error_message["error"]:
            return render_template("session.html",session=session,error_message=error_message["message"])
        session["username"] = new_user.username
        return render_template("session.html",session=session,error_message=error_message["message"])

    else:
        if session.get("username"):
            return redirect(url_for("index"))
        return render_template("session.html")


@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "POST":
        # dictionary of possible errors to happen
        error_message = {"message":"", "error":None}

        user_authentication =  User.from_document({
            "email": "TO_LOGIN",
            "username":request.form["username"],
            "password":request.form["password"]
        })

        model.authenticate_user(user_authentication,users,message)
        if error_message["error"]:
            return render_template("session.html",session=session,error_message=error_message["error"])

        session["username"] = user_authentication.username
        return redirect(url_for("index"))
    else:
        if session.get("username"):
            return redirect(url_for("index"))
        return render_template("login.html",session=session)
        

"""
Method that allows the user to logout their account from the page's current session
Returns:
    redirects user to main page (index.html) with their account logged out
"""
@app.route("/logout")
def logout():
    # clear user from session
    session.clear()
    return redirect(url_for("index"))








        
        


    