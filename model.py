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


def add_user(user:user.User,users:collection,errors:dict):
    """ Adds a user to the users collection in the DB

    Args:
        user (User): user to be added, if it doesnt exist
        users (collection): DB collection of existing users
        message (dict): dictionary of error messages to be used in case an error occurrs
    """

    # check if there exists a user with the given email
    if users.find_one({"email":user.email}):
        errors["message"] = "There already exists an account with this email"
        return

    # check if there exists a user with the given username
    if users.find_one({"username":user.username}):
        errors["message"] = "This username is already taken/Username already exists"
        return

    # DB Insert error handling
    try:
        users.insert_one(user.to_document())
        
    except:
        errors["message"] = "Could not sign up at the moment. Please make sure the field are correct or try again later."

def authenticate_user(user:user.User,users:collection,errors:dict):
    """ Retrieves a user from the Data Base

    Args:
        user (user.User):a user to be searched for in the DB
        users (collection): Existing users in the DB
        message (_type_): message to return if an error occurs
    """

    # get the user from the database
    login_user = users.find_one({"email":user.email})

    # if the user is in the database
    if login_user:
        # update the username to the existing user username
        user.username = login_user["username"]
        # grab the password in the DB
        password_in_db = login_user["password"]
        # encode the password for security purposes
        encoded_password = user.password.encode("utf-8")
        # compare if the hashed user password is the same as the one in the db
        if not bcrypt.checkpw(encoded_password,password_in_db):
            # if we arrive here it means the password was invalid
            errors["message"] = "Password is incorrect."
    else:
        errors["message"] = "Incorrect User/User does not exist."


def get_user(user: user.User, users: collection):
    user = users.find_one({'username': user.username})
    return user

def get_user_by_id(id: ObjectId, users: collection):
    user = users.find_one({'_id': id})
    return user


