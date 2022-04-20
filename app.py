# -- Import section --
from backend.user import User
from crypt import methods
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from flask_pymongo import PyMongo
import model
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
@app.route('/index')
def index():
    data = posts.find({})
    result = []
    for entry in data:
        result.append(model.create_post(author = entry['author'], group = entry['group'], content = entry['content'], date = entry['date'], image = entry['group_image']))
    if result:
        return render_template('index.html', home_posts=result)
    return render_template('index.html',error='There are no posts available')


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




    # Old code
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
    




@app.route("/login",methods=["GET","POST"])
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


    # Old code 
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
Method that allows the user to logout their account from the page's current session
Returns:
    redirects user to main page (index.html) with their account logged out
"""
@app.route("/logout")
def logout():
    # clear user from session
    session.clear()
    return redirect(url_for("index"))








        
        


    
