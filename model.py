import bcrypt
from pymongo import collection
from bson import ObjectId
from backend import (
    admin,
    user
)

from post import Post


'''
Controller
'''
def create_post(author, group, content, date, image):
    return Post(author, group, content, date, image)


def add_user(user:user.User,users:collection,message:dict):
    """ Adds a user to the users collection in the DB

    Args:
        user (User): user to be added, if it doesnt exist
        users (collection): DB collection of existing users
        message (dict): dictionary of error messages to be used in case an error occurrs
    """

    # check if there exists a user with the given email
    existing_email = users.find_one({"email":user.email})
    if existing_email:
        message["error"] = "There already exists an account with this email"
        return

    # DB Insert error handling

    try:
        users.insert_one(user.to_document())
        # encode password for hashing
        password = user.password
        # hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        users.update_one({user.email:{"password":hashed}})

    except:
        message["error"] = "Could not sign up at the moment. Please make sure the field are correct or try again later."

def authenticate_user(user:user.User,users:collection,message):
    """ Retrieves a user from the Data Base

    Args:
        user (user.User): a user to be searched for in the DB
        users (collection): Existing users in the DB
        message (_type_): message to return if an error occurs
    """

    # get the username from the database
    login_user = users.find_one({"email":user.email})

    # if the user is in the database
    if login_user:
        # grab the password in the DB
        password_in_db = login_user["password"]
        # encode the password for security purposes
        encoded_password = user.password.encode("utf-8")
        # compare if the hashed user password is the same as the one in the db
        if not bcrypt.checkpw(encoded_password,password_in_db):
            # if we arrive here it means the password was invalid
            message["error"] = "Password is incorrect."

    else:
        message["error"] = "Incorrect User/User does not exist."

def get_user(user: user.User, users: collection):
    user = users.find_one({'username': user.username})
    return user

def get_user_by_id(id: ObjectId, users: collection):
    user = users.find_one({'_id': id})
    return user


