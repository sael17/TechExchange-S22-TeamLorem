# -- Import section --
from base64 import decode
# from crypt import methods
from pickle import FALSE
from time import time
from flask import (
    Flask,
    abort,
    current_app,
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

import config
import datetime
import bcrypt 
import certifi
import google.auth.transport.requests
import gunicorn # for heroku deployment
import jwt
import model
import os
import pathlib
import requests


# -- Initialization section --
app = Flask(__name__)

# -- App config --
app.config.from_object(config.Config)

if os.environ.get('DEV_MODE') == '1':
    app.config.from_object(config.DevConfig)
else:
    app.config.from_object(config.ProdConfig)

# -- Session config --
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"

# -- Mongo Section -- 

# Name of database
db_name = app.config['MONGO_DBNAME']

# URI of database
mongodb_password = os.environ.get('MONGO_PASSWORD')
app.config['MONGO_URI'] = f"mongodb+srv://admin:{mongodb_password}@cluster0.3pto1.mongodb.net/{db_name}?retryWrites=true&w=majority"

# Initialize PyMongo
mongo = PyMongo(app, tlsCAFile=certifi.where())

# # Session Data/Cookie
# app.secret_key = secrets.token_urlsafe(16)

# Collection References
users = mongo.db.users
posts = mongo.db.posts
groups = mongo.db.groups
test_groups = mongo.db.test_group

# -- GOOGLE API section -- 

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Client ID and Info to use with the API
GOOGLE_CLIENT_ID = "654704100832-apsssepjo2lgl9iqine185m0faa8lj7t.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

"""
Main Route of the page where the posts from the groups the user is part of and the users he or she
follows are displayed

"""
@app.route("/")
@app.route("/index",methods=["GET","POST"])
def index():
    if request.method == "POST":
        if request.form["credential"]:
            try:
                decoded = jwt.decode(request.form["credential"],verify=False)
                return decoded["email"]
            except:
                return "Error"

    elif request.method == 'GET':
        current_user = session.get('username')
        if current_user:
            recent_posts = model.get_recent_posts(current_user, users, posts)
            if recent_posts:
                return render_template('index.html', recent_posts=recent_posts)
            return render_template('index.html')

        else:
            return redirect(url_for('signup'))
        
    else:
        return render_template('index.html',error='There method is not supported')


# -- GOOGLE API Routes -- 

"""
Route that makes a user base in the the jwt document returned by the Google API
It also generate a basic username for the user 

"""
@app.route("/signup/google", methods=["GET","POST"])
def google_signup():
    if request.method == "POST":
        if request.form["credential"]:
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


"""
Route that allows the user to log in with his google account
"""
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
"""
Route that allows the user to create an accoun in the DB
"""
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


"""
Route that allows the user to log in into his accoun in the DB
"""
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
Allows the user to modify their account and profile and the option to delete
their account and connect to different platforms

Returns:
    JinjaTemplate: renders the same page again with all the changed made present.
    It can also redirect to delete the account.
"""
@app.route("/account", methods=["GET","POST"])
# this router shall be only available if a user is logged in
def account():
    errors = {"message":""}
    
    if not session.get('username'):
        return redirect(url_for('login'))
    
    current_user = session["username"]
    user_doc = users.find_one({"username":current_user})
    # save the current user to modify its info
    current_user_instance = User.from_document({
        "email":"email@temp.com",
        "username": session["username"],
        "password": "QUERYPASSWORD"
    })
    
    user_posts = model.get_posts_from_user(current_user_instance,users,posts,errors)
    result = []
    for post in user_posts:
            result.append(Post(author = session["username"], 
            group = post["group"], 
            content = post['content'], 
            date = post['date'], 
            image = post['group_image']))

    user=users.find_one({'username':current_user})

    followers = user['followers']
    following = user["following"]
    followers_count = len(followers)
    following_count = len(following)
    followers_names = []
    following_names = []
    for id in followers:
        user_info = users.find_one({'_id':id})
        following_names.append(user_info['username'])
    
    for id in following:
        user_info = users.find_one({'_id':id})
        followers_names.append(user_info["username"])

    if request.method =="POST":        
        # get the input firstname from the form in order to update it
        new_firstname = {"$set":{"firstname":request.form["firstname"]}}
        users.update_one({"username":current_user},new_firstname)

        # get the input lastame from the form in order to update it
        new_lastname = {"$set":{"lastname":request.form["lastname"]}}
        users.update_one({"username":current_user},new_lastname)

        # get the input bio from the form in order to update it
        new_bio = {"$set":{"bio":request.form["bio"]}}
        users.update_one({"username":current_user},new_bio)

    
        user_doc = users.find_one({"username":current_user})

        return render_template("account.html", session=session,
        firstname=user_doc["firstname"],lastname=user_doc["lastname"],
        bio=user_doc["bio"],password=user_doc["password"],
        email=user_doc["email"],username=user_doc["username"],profile_pic=user_doc["profile_pic"],
        following_count = following_count, followers_count = followers_count,posts=result)


     # load account info with the one prev found in the user's document
    else:
        
            user_doc = users.find_one({"username":current_user})
            return render_template("account.html", session=session,
            firstname=user_doc["firstname"],lastname=user_doc["lastname"],
            bio=user_doc["bio"],password=user_doc["password"],
            email=user_doc["email"],username=user_doc["username"],posts=result,
            profile_pic=user_doc["profile_pic"],following_count = following_count, 
            followers_count = followers_count)

        # except:
        #     return render_template("account.html",session=session,firstname="",lastname="",bio="",
        #     password="******")
    
"""
Allows the user to reset or change their current password to a new one
For now, the only validation is the username since these are unique
More validation is needed for the future

Returns:
    If sucessful, returns user to login page, else the user made a mistake
    (user not found) and it throws an error for the user to see
"""
@app.route("/change/password",methods=["GET","POST"])
def change_password():
    if request.method == "GET":
        return render_template("update_account.html", session=session,change_password=True)

    else:
        # get document from current user, if there is one
        current_user = users.find_one({"username":session["username"]})
        if current_user:
            current_user_email = current_user["email"]
            form_email = request.form["email"]
            if current_user_email == form_email:
                # obtain new password and encrypt it for security reasons
                password = request.form['new_password'].encode('utf-8')
                salt = bcrypt.gensalt()
                hashed_pasword = bcrypt.hashpw(password, salt)
                # set the new value of the password
                new_pw = {"$set": { "password": hashed_pasword }}
                # update user's old password with new password
                users.update_one({"email":current_user_email}, new_pw)
                # go back to index page
                return redirect("/account")
            else:
                return render_template("update_account.html",session=session,change_password=True,
                error_message="Incorrect Email")
        else:
            return render_template("update_account.html", session=session,change_password=True,
            error_message="Incorrect Email for this user")


"""
Allows the user to change their current email to a new one
For now, the only validation is the username since these are unique
More validation is needed for the future

Returns:
    If sucessful, returns user to login page, else the user made a mistake
    (user not found) and it throws an error for the user to see
"""
@app.route("/change/email",methods=["GET","POST"])
def change_email():
    if request.method == "GET":
        return render_template("update_account.html", session=session,change_email=True)
    else:
        # update old email with new email
        current_user = users.find_one({"username":session["username"]})
        if current_user:
            email = request.form["email"]
            if current_user["email"] == email:
                new_email = request.form["new_email"]
                if users.find_one({"email":new_email}):
                    return render_template("update_account.html", session=session, 
                    error_message="Email Already Exists",change_email=True)
                # set the new value of the email
                newvalue = {"$set": { "email": new_email }}
                # validate the passwords match
                pw_from_db = current_user["password"]
                form_pw = request.form["password"].encode("utf-8")
                if bcrypt.checkpw(form_pw,pw_from_db):
                    # update user's old email with new email
                    users.update_one({"email":current_user["email"]}, newvalue)
                     # go back to account page
                    return redirect("/account")
            else:
                return render_template("update_account.html", session=session, error_message="Incorrect User",
                change_email=True)
        else:
            return render_template("update_account.html", session=session, error_message="Username not found",
            change_email=True)


"""
Route that allows the user to change his account username, if sucessful

Returns -> it renders the page with a message error if an error occurs, otherwise it 
redirects to the account page
"""
@app.route("/change/username",methods=["GET","POST"])
def change_username():
    if request.method == "GET":
        return render_template("update_account.html", session=session,change_username=True)
    else:
        current_user = users.find_one({"username":session["username"]})
        if current_user:
            email = request.form["email"]
            if current_user["email"] == email:
                new_username = request.form["new_username"]
                if users.find_one({"username":new_username}):
                    return render_template("update_account.html", session=session, error_message="Incorrect User",
                    change_username=True)
            
                # set the new value of the username
                newvalue = {"$set": { "username": new_username}}
                # validate the passwords match
                pw_from_db = current_user["password"]
                form_pw = request.form["password"].encode("utf-8")
                if bcrypt.checkpw(form_pw,pw_from_db):
                    # update user's old username with new username
                    users.update_one({"username":current_user["username"]}, newvalue)
                    session["username"] = new_username
                     # go back to account page
                    return redirect("/account")
            else:
                return render_template("update_account.html", session=session, error_message="Incorrect User",
                change_username=True)
        else:
            return render_template("update_account.html", session=session, error_message="Username not found",
            change_username=True)

"""
Route that allows the user to change his profile picture, if sucessful

Returns -> it renders the page with a message error if an error occurs, otherwise it 
redirects to the account page
"""

@app.route("/change/profilepic",methods=["POST","GET"])
def change_profile_pic():
    if request.method == "GET":
        return render_template("update_account.html",session=session,change_img=True)
    else:  
        current_user = users.find_one({"username":session["username"]})
        if current_user:
            email = request.form["email"]
            if current_user["email"] == email:
                profile_picture = request.form["image_url"]
               #Fetching the image_url from the user to check if it gives us headers        
                try:
                    url = profile_picture
                    response = requests.get(url)
                except:
                    # Handle error
                    return render_template("update_account.html",session=session,change_img=True,
                    error_message="Something went wrong with your image URL")
                
                # Validating image_url to see if it's an image
                if response.headers.get('content-type') not in ['image/png', 'image/jpeg']:
                    return render_template("update_account.html",session=session,change_img=True,
                    error_message="URL is not a valid image URL! Please use a correct URL")
               
                # set the new value of the email
                newvalue = {"$set": { "profile_pic":profile_picture }}
                # validate the passwords match
                pw_from_db = current_user["password"]
                form_pw = request.form["password"].encode("utf-8")
                if bcrypt.checkpw(form_pw,pw_from_db):
                    # update user's old email with new email
                    users.update_one({"username":current_user["username"]}, newvalue)
                     # go back to account page
                    return redirect("/account")
                else:
                    return render_template("update_account.html",session=session,
                    error_message="Incorrect Password",change_img=True)
            else:
                return render_template("update_account.html", session=session, error_message="Incorrect Email",
                change_img=True)
        else:
            return render_template("update_account.html", session=session, error_message="Incorrect User",
            change_img=True)
    

"""
Delete the users account from the users data base 

Redirects to the logout where the account is also cleared from the current session
and it is redirected to the main page (index.html)
"""
@app.route("/deleteacc",methods=["POST"])
def delete_account():
    errors = {'message': None}
    
    if not session.get('username'):
        return redirect('login')
    
    user_to_delete = User.from_document({
        'username': session.get('username'),
        'email': 'FOR_QUERY',
        'password': 'FOR_QUERY'
    })
    
    model.delete_posts_from_user(user_to_delete, users, posts, errors)
    if not errors['message']:
        model.delete_user(user_to_delete, users, errors)
    
    if errors['message']:
        return render_template("account.html", session=session, firstname="", lastname="", bio="", password="******", error=errors['message'])
    return redirect(url_for('logout'))

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
    
    groups_to_view = model.get_groups(groups, errors)
    
    if errors['message']:
        return render_template('groups.html', session=session, groups=groups_to_view, error=errors['message'])


    if request.method == 'POST':
        new_group = Group.from_document({
            'name': request.form['group-name'],
            'about': request.form['group-info'],
            'creator': session.get('username'),
            'date_created': datetime.datetime.now()
        })
        
        model.add_group(new_group, groups, errors)
        
        if errors['message']:
            return render_template('groups.html', session=session, groups=groups_to_view, error=errors['message'])
        
        return redirect(url_for('get_group', group_name=new_group.name))
    
    else:
        return render_template('groups.html', session=session, groups=groups_to_view)


'''
Renders the post associated with the group the user selected
'''
@app.route('/group/<group_name>')
def get_group(group_name):
    errors = {'message': None}
        
    if not session.get('username'):
        return render_template('session.html', session=session, sign_up=False, display=True)

    
    group_query = Group.from_document({
        'name': group_name,
        'creator': 'FOR_QUERY',
        'about': 'FOR_QUERY',
        'date_created': 'FOR_QUERY'
    })

    current_user = session.get('username')
    group_to_view = model.get_group(group_query, groups, errors)
    
    if errors['message']:
        return render_template('group.html', session=session, group=group_to_view, posts=result, current_user=current_user, following=following, error=errors['message'])

    group_posts = model.get_posts_from_group(Group.from_document(group_to_view),groups, posts, errors)
    following = model.following(current_user, users)
    
    result = []
    for post in group_posts:
        post_instance = Post.from_document(post)
        post_instance.author = model.get_user_by_id(post_instance.author, users)['username']
        result.append(post_instance)
        
    return render_template('group.html', session=session, group=group_to_view, posts=result, current_user=current_user, following=following, error=errors['message'])

'''
Inserts the new post into the database and redirects 
the user to the group where they made the post. 
'''
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
    
    if errors['message']:
        group_to_view = groups.find_one({'name': group_name})
        
        group_posts = model.get_posts_from_group(Group.from_document(group_to_view),groups, posts, errors)
        current_user = session.get('username')
        following = model.following(current_user, users)

        result = []
        for post in group_posts:
            post_instance = Post.from_document(post)
            post_instance.author = model.get_user_by_id(post_instance.author, users)['username']
            result.append(post_instance)

        return render_template('group.html', session=session, group=group_to_view, posts=result, current_user=current_user, following=following, error=errors['message'])
    
    return redirect(url_for('get_group', group_name=group_name, error=errors['message']))

'''
If the user is not already following the user they selected then it follows them and updates the user.
Also adds the current user to the list of followers of the user they just followed 
'''
@app.route('/follow', methods=["POST"])
def follow():
    if request.method == 'POST':
        current_user = session.get('username')
        current_user = users.find_one({'username':current_user})

        user_to_be_followed = request.form['user_to_be_followed']
        user_to_be_followed = users.find_one({'username':user_to_be_followed})

        group_name = request.form['group']

        if user_to_be_followed['_id'] not in current_user['following']:
            current_user['following'].append(user_to_be_followed['_id'])
            user_to_be_followed['followers'].append(current_user['_id'])
            users.update_one({'_id':current_user['_id']}, {'$set':{'following':current_user['following']}})
            users.update_one({'_id':user_to_be_followed['_id']}, {'$set':{'followers':user_to_be_followed['followers']}})
        return redirect(url_for('get_group', group_name=group_name))
