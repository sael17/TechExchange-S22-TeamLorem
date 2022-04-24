# -- Import section --
from base64 import decode
# from crypt import methods
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

# -- Classes
from backend.user import User
from backend.group import Group
from backend.post import Post

from flask_pymongo import PyMongo
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
from random import randint, random
from datetime import date
from bson import ObjectId

import datetime
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
groups = mongo.db.groups

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
        data = model.get_posts(posts)
        result = []
        for entry in data:
            # result.append(model.create_post(author = entry['author'], group = entry['group'], content = entry['content'], date = entry['date'], image = entry['group_image']))
            result.append(Post.from_document(entry))
            if result:
                return render_template('index.html', home_posts=result)
    return render_template('index.html',error='There are no posts available')


# -- GOOGLE API Routes -- 
@app.route("/signup/google", methods=["GET","POST"])
def google_signup():
    if request.method == "POST":
        if request.form["credential"]:
            # return request.form["credential"]
            try:
                decoded = jwt.decode(request.form["credential"],verify=False)
                decoded_email = decoded["email"]
                decoded_username = decoded_email[:decoded_email.find("@")+1] + str(randint(1,100))

                return render_template("session.html",session=session,sign_up = True, 
                google_signup = True, display=False, google_email=decoded_email,username=decoded_username)


            except:
                return render_template("session.html",session=session,sign_up = True, 
                google_signup = True, display=True,error_message="Something Went Wrong")        
    
    else:
        return render_template("session.html",session=session,sign_up = True, 
        google_signup = True, display=True)

@app.route("/login/google",methods=["GET","POST"])
def google_login():
    if request.method == "POST":
        if request.form["credential"]:
            try:
                decoded = jwt.decode(request.form["credential"],verify=False)
                decoded_email = decoded["email"]
                return render_template("session.html",session=session,sign_up = False, 
                google_signup = True, display=False, google_email=decoded_email)


            except:
                return render_template("session.html",session=session,sign_up = False, 
                google_signup = True, display=True, error_message="Something Went Wrong.")
    else:
        return render_template("session.html",session=session,sign_up = False, google_signup = True, 
        display=True)
            



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

"""
ROUTE /group
METHODS: GET, POST
GET: Displays all available groups, or by search
POST: Creates a group
"""
@app.route("/group", methods=['GET', 'POST'])
def group():
    errors = {'message':None}
    
    if not session.get('username'):
        return render_template('session.html', session=session, sign_up=False, display=True)
    
    if request.method == 'POST':
        try:
            new_group = Group.from_document({
                'name': request.form['group_name'],
                'about': request.form['about'],
                'creator': session.get(),
                'date_created': datetime.datetime.now()
            })
        except:
            errors['message'] = 'Could not read form and/or session data'
        
        model.add_group(new_group, groups, errors)
        
        # TODO: error handling
        
        return render_template("group.html", session=session,group=new_group.to_document(), errors=errors)
    else:
        
        groups_to_view = model.get_groups(groups)
        
        return render_template('groups.html', session=session, groups=groups_to_view)

@app.route('/group/<group_name>')
def get_group(group_name):
    errors = {'message': None}
    
    # #TODO: get author from the session
    # is_active = False
    # current_user = session.get('username')
    
    # # even though usernames are unique we use find one because if not it returns a cursor object
    # author = users.find_one({'username':current_user})
    # if author:
    #     is_active = True

    
    if not session.get('username'):
        return render_template('session.html', session=session, sign_up=False, display=True)

    
    group_query = Group.from_document({
        'name': group_name,
        'creator': 'FOR_QUERY',
        'about': 'FOR_QUERY',
        'date_created': 'FOR_QUERY',
        'users': [],
        'posts': []
    })
    
    group_to_view = model.get_group(group_query, groups)
    group_posts = model.get_posts_from_group(Group.from_document(group_to_view),groups, posts, errors)
    
    result = []
    for post in group_posts:
        post_instance = Post.from_document(post)
        post_instance.author = model.get_user_by_id(post_instance.author, users)['username']
        result.append(post_instance)
    
    # TODO: error handling
    
    return render_template('group.html', session=session, group=group_to_view, posts=result)

@app.route('/post', methods=['POST'])
def post():
    errors = {'message': None}
    
    if not session.get('username'):
        return redirect('login')
    
    group_name = request.form['group_name']
    user = User.from_document({
                "email": "FOR_QUERY",
                "username": session.get('username') ,
                "password": "FOR_QUERY"
            })  
      
    author_id = model.get_user(user, users)['_id']
    content = request.form['content']
    time = datetime.datetime.now()
    
    new_post = Post.from_document({
        'author': author_id,
        'group': group_name,
        'content': content,
        'date': time,
        'group_image': 'https://imageio.forbes.com/blogs-images/forbestechcouncil/files/2019/01/canva-photo-editor-8-7.jpg?fit=bounds&format=jpg&width=960'
    })
    
    model.create_post(new_post, posts, errors)
    
    print(errors['message'])
    # TODO: error handling
    
    return redirect(url_for('get_group', group_name=group_name))

#TODO: - If there are no posts and the user is not logged in it shows up blank, handle this edge case
# @app.route("/group", methods=['GET', 'POST'])
# def group():
#     # if request method == post 
#     # collect data from post
#     # add to db 
#     # render all the posts in the db
#     # else display the current posts inside the db

#     #TODO: get author from the session
#     is_active = False
#     current_user = session.get('username')
#     # even though usernames are unique we use find one because if not it returns a cursor object
#     author = users.find_one({'username':current_user})
#     if author:
#         is_active = True

#     if request.method == 'POST':
#         #TODO get group from session
#         group = ObjectId('6261acca285a88b547479b78')
#         content = request.form['content']
#         time = date.today().strftime("%B %d, %Y")
#         #TODO get image from session
#         image = 'https://imageio.forbes.com/blogs-images/forbestechcouncil/files/2019/01/canva-photo-editor-8-7.jpg?fit=bounds&format=jpg&width=960'

#         #create post
#         new_post = Post(author=author['_id'],group=group,content=content,date=time,image=image)
#         posts.insert_one({'author':new_post.author,'group':new_post.group,'content':new_post.content,'date':new_post.date,'group_image':new_post.image})

#         group_info = groups.find_one({})
#         group_posts = posts.find({'group': group_info['_id']})
#         result = []
#         for post in group_posts:
#             author_name = users.find_one({'_id':post['author']})
#             result.append(Post.from_document({
#                 author_name['username'],
#                 group_info['group_name'],
#                 post['content'],
#                 post['date'],
#                 post['group_image']
#             }))
    
#         if result:
#             return render_template('groups.html', posts=result, group_id=group_info['_id'], active=is_active)

#     else:
#         # group_info = test_groups.find_one({})
#         group_posts = posts.find({'group': group_info['_id']})
#         result = []
#         for post in group_posts:
#             author_name = users.find_one({'_id':post['author']})
#             result.append(Post.from_document({
#                 author_name['username'],
#                 group_info['group_name'],
#                 post['content'],
#                 post['date'],
#                 post['group_image']
#             }))
#         return render_template('groups.html', posts=result, group_id=group_info['_id'], active=is_active)