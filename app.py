# -- Import section --
from base64 import decode
from crypt import methods
from flask import (
    Flask,
    abort,
    render_template,
    request,
    redirect,
    url_for,
    session
)
from rsa import verify

from backend.user import User
from flask_pymongo import PyMongo
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
from random import randint, random

import bcrypt 
import certifi
import google.auth.transport.requests
import gunicorn # for heroku deployment
import jwt
import model
import secrets
import os
import pathlib
import requests


# -- Initialization section --
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(nbytes=16)

# -- Mongo Section -- 

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

# -- GOOGLE API section -- 

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "654704100832-apsssepjo2lgl9iqine185m0faa8lj7t.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)



@app.route("/")
@app.route("/index",methods=["GET","POST"])
def index():
    if request.method == "POST":
        if request.form["credential"]:
            # return request.form["credential"]
            try:
                decoded = jwt.decode(request.form["credential"],verify=False)
                return decoded["email"]
            except:
                return "Error"
        
    else:
        data = posts.find({})
        result = []
        for entry in data:
            result.append(model.create_post(author = entry['author'], group = entry['group'], content = entry['content'], date = entry['date'], image = entry['group_image']))
            if result:
                return render_template('index.html', home_posts=result)
    return render_template('index.html',error='There are no posts available')

# -- GOOGLE API Routes -- 

@app.route("/login/google", methods=["GET","POST"])
def google_login():
    if request.method == "POST":
        if request.form["credential"]:
            # return request.form["credential"]
            try:
                decoded = jwt.decode(request.form["credential"],verify=False)
                decoded_email = decoded["email"]
                decoded_username = decoded_email[:decoded_email.find("@")+1] + str(randint(1,100))

                return render_template("session.html",session=session,sign_up = True, google_signup = True,
        google_email=decoded_email,username=decoded_username)


            except:
                return "Error"        
    
    else:
        return render_template("session.html",session=session,sign_up = True, google_signup = True)


    # authorization_url, state = flow.authorization_url()
    # session["state"] = state
    # return redirect(authorization_url)


# -- Normal Routes -- 
@app.route("/signup",methods=["GET","POST"])
def signup():
    errors = {"message":''}


    if request.method == "POST":

        new_user = User.from_document({
            "email":request.form["email"],
            "username":request.form["username"],
            "password":request.form["password"]})

        model.add_user(new_user,users,errors)

        if errors["message"]:
            return render_template("session.html",session=session,
            error_message=errors["message"],sign_up = True)

        else:
            session["username"] = request.form["username"]
            return redirect(url_for("index"))
    else:
        return render_template("session.html",session=session,sign_up=True)


@app.route("/login", methods=["GET","POST"])
def login():
    errors = {"message":""}
    if request.method == "POST":
        try:
            user_to_authenticate = User.from_document({
                "email":request.form["email"],
                "username":"tempUsername",
                "password":request.form["password"]
            })

        except ValueError:
            return render_template("session.html",error_message="Password is incorrect",
            sign_up=False)

        model.authenticate_user(user_to_authenticate,users,errors)

        if errors["message"]:
            return render_template("session.html",session=session,
            error_message=errors["message"],sign_up=False)

        else:
            session['username'] = user_to_authenticate.username
            return redirect(url_for('index'))
    
    else:
        if session.get('username'):
            return redirect(url_for('index'))
    return render_template("session.html", session=session,sign_up=False)

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



# Old code (sign up)
    #     existing_user = users.find_one({"email":request.form["email"]})
    #     if users.find_one({"username":request.form["username"]}):
    #         return render_template("session.html",session=session,
    #         error_message="This username already exists",sign_up = True)
        
    #     if not existing_user:
    #         email = request.form["email"]
    #         username = request.form["username"]
    #         # encode password for hashing
    #         password = request.form["password"].encode("utf-8")
    #         salt = bcrypt.gensalt()
    #         hashed_pw = bcrypt.hashpw(password,salt)
    #         # add user to db
    #         users.insert_one({"email":email,"username":username,"password":hashed_pw})
    #         # store user in session
    #         session["username"] = username
    #         return redirect(url_for("index"))

    #     else:
    #         return render_template("session.html", session=session,
    #         error_message="There is already an account with this email",sign_up=True)
    # else:
    #     return render_template("session.html",session=session,sign_up=True)


    # Old code (log in) 
    # if request.method == "POST":
    #     login_user = users.find_one({"email":request.form["email"]})

    #     if login_user:
    #         db_password = login_user["password"]
    #         # encode password to be compared
    #         password  = request.form["password"].encode("utf-8")
    #         # compare submitted password and the one in the form
    #         if bcrypt.checkpw(password,db_password):
    #             session["username"] = login_user["username"]
    #             return redirect(url_for("index"))
    #         else:
    #             return render_template("session.html",session=session,
    #             error_message="Invalid Password",signup=False)
    #     else:
    #         return render_template("session.html",session=session,
    #             error_message="User does not exist",signup=False)
    # else:
    #     return render_template("session.html",session=session,signup=False)
    