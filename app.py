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
from bson import ObjectId

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

    elif request.method == 'GET':
        pass
        
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
        email=user_doc["email"],username=user_doc["username"],posts=result)


     # load account info with the one prev found in the user's document
    else:
        try:
            user_doc = users.find_one({"username":current_user})
            return render_template("account.html", session=session,
            firstname=user_doc["firstname"],lastname=user_doc["lastname"],
            bio=user_doc["bio"],password=user_doc["password"],
            email=user_doc["email"],username=user_doc["username"],posts=result)

        except:
            return render_template("account.html",session=session,firstname="",lastname="",bio="",
            password="******")
    


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

@app.route("/change/username",methods=["GET","POST"])
def change_username():
    if request.method == "GET":
        return render_template("update_account.html", session=session,change_username=True)
    else:
        # update old email with new email
        current_user = users.find_one({"username":session["username"]})
        if current_user:
            email = request.form["email"]
            if current_user["email"] == email:
                new_username = request.form["new_username"]
                # set the new value of the email
                newvalue = {"$set": { "username": new_username}}
                # validate the passwords match
                pw_from_db = current_user["password"]
                form_pw = request.form["password"].encode("utf-8")
                if bcrypt.checkpw(form_pw,pw_from_db):
                    # update user's old email with new email
                    users.update_one({"username":current_user["username"]}, newvalue)
                     # go back to account page
                    return redirect("/account")
            else:
                return render_template("update_account.html", session=session, error_message="Incorrect User",
                change_username=True)
        else:
            return render_template("update_account.html", session=session, error_message="Username not found",
            change_username=True)

@app.route("/change/profilepic",methods=["POST","GET"])
def change_profile_pic():
    if request.method == "GET":
        pass

    

"""
Delete the users account from the users data base 

Redirects to the logout where the account is also cleared from the current session
and it is redirected to the main page (index.html)
"""
@app.route("/delete/account",methods=["GET","POST"])
def delete_account():
    if request.method == "POST":
        users.delete_one({"username":session["username"]})
        return redirect("/logout")
    else:
        if session.get('username'):
            return redirect(url_for('login'))
        return render_template("account.html")





#TODO - If there are no posts and the user is not logged in it shows up blank, handle this edge case
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
        new_group = Group.from_document({
            'name': request.form['group-name'],
            'about': request.form['group-info'],
            'creator': session.get('username'),
            'date_created': datetime.datetime.now()
        })
        
        model.add_group(new_group, groups, errors)
        
        # TODO: error handling
        
        
        return redirect(url_for('get_group', group_name=new_group.name))
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
    current_user = session.get('username')
    group_to_view = model.get_group(group_query, groups)
    group_posts = model.get_posts_from_group(Group.from_document(group_to_view),groups, posts, errors)
    following = model.following(current_user, users)
    print(following)
    
    result = []
    for post in group_posts:
        post_instance = Post.from_document(post)
        post_instance.author = model.get_user_by_id(post_instance.author, users)['username']
        result.append(post_instance)
    
    # TODO: error handling
    
    return render_template('group.html', session=session, group=group_to_view, posts=result, current_user=current_user, following=following)

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

@app.route('/follow', methods=["POST"])
def follow():
    if request.method == 'POST':
        current_user = session.get('username')
        print(current_user)
        current_user = users.find_one({'username':current_user})

        user_to_be_followed = request.form['user_to_be_followed']
        print(user_to_be_followed)
        user_to_be_followed = users.find_one({'username':user_to_be_followed})

        group_name = request.form['group']
        if user_to_be_followed['_id'] not in current_user['following']:
            print('hi')
            current_user['following'].append(user_to_be_followed['_id'])
            user_to_be_followed['followers'].append(current_user['_id'])
            users.update_one({'_id':current_user['_id']}, {'$set':{'following':current_user['following']}})
            users.update_one({'_id':user_to_be_followed['_id']}, {'$set':{'followers':user_to_be_followed['followers']}})
        return redirect(url_for('get_group', group_name=group_name))
