# -- Import section --
from base64 import decode
from crypt import methods
from pickle import FALSE
from time import time
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
from datetime import date
from backend.post import Post
from bson import ObjectId

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
test_groups = mongo.db.test_group

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
                display=False, google_email=decoded_email,username=decoded_username)


            except:
                return "Error"        
    
    else:
        return render_template("session.html",session=session,sign_up = True, google_signup = True, 
        display=True)


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
            error_message=errors["message"],sign_up=True,display=True)

        else:
            session["username"] = request.form["username"]
            return redirect(url_for("index"))
    else:
        return render_template("session.html",session=session,sign_up=True,display=True)


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
            sign_up=False,display=True)

        model.authenticate_user(user_to_authenticate,users,errors)

        if errors["message"]:
            return render_template("session.html",session=session,
            error_message=errors["message"],sign_up=False,display=True)

        else:
            session['username'] = user_to_authenticate.username
            return redirect(url_for('index'))
    
    else:
        if session.get('username'):
            return redirect(url_for('index'))
    return render_template("session.html", session=session,sign_up=False,display=True)

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

#TODO - If there are no posts and the user is not logged in it shows up blank, handle this edge case
@app.route("/group", methods=['GET', 'POST'])
def group():
    # if request method == post 
    # collect data from post
    # add to db 
    # render all the posts in the db
    # else display the current posts inside the db

    #TODO get author from the session
    is_active = False
    current_user = session.get('username')
    # even though usernames are unique we use find one because if not it returns a cursor object
    author = users.find_one({'username':current_user})
    if author:
        is_active = True

    if request.method == 'POST':
        #TODO get group from session
        group = ObjectId('6261acca285a88b547479b78')
        content = request.form['content']
        time = date.today().strftime("%B %d, %Y")
        #TODO get image from session
        image = 'https://imageio.forbes.com/blogs-images/forbestechcouncil/files/2019/01/canva-photo-editor-8-7.jpg?fit=bounds&format=jpg&width=960'

        #create post
        new_post = Post(author=author['_id'],group=group,content=content,date=time,image=image)
        posts.insert_one({'author':new_post.author,'group':new_post.group,'content':new_post.content,'date':new_post.date,'group_image':new_post.image})

        group_info = test_groups.find_one({})
        group_posts = posts.find({'group': group_info['_id']})
        result = []
        for post in group_posts:
            author_name = users.find_one({'_id':post['author']})
            result.append(model.create_post(author = author_name['username'], group = group_info['group_name'], content = post['content'], date = post['date'], image = post['group_image']))
    
        if result:
            return render_template('groups.html', posts=result, group_id=group_info['_id'], active=is_active)

    else:
        group_info = test_groups.find_one({})
        group_posts = posts.find({'group': group_info['_id']})
        result = []
        for post in group_posts:
            author_name = users.find_one({'_id':post['author']})
            result.append(model.create_post(author = author_name['username'], group = group_info['group_name'], content = post['content'], date = post['date'], image = post['group_image']))
        return render_template('groups.html', posts=result, group_id=group_info['_id'], active=is_active)