import bcrypt
from pymongo import collection
from bson import ObjectId
from backend.user import User
from backend.admin import Admin
from backend.post import Post
from backend.group import Group


# -- MODEL functions --

'''
Controller
'''

def authenticate_user(user:User,users:collection,errors:dict):
    """ Retrieves a user from the Data Base

    Args:
        user (user.User):a user to be searched for in the DB
        users (collection): Existing users in the DB
        message (_type_): message to return if an error occurs
    """

    # get the user from the database
    # login_user = users.find_one({"email":user.email})
    login_user = get_user_by_email(user, users)

    # if the user is in the database
    if login_user:
        # update the username to the existing user username
        user.username = login_user["username"]
        # grab the password in the DB
        password_in_db = login_user["password"]
        # encode the password for security purposes
        encoded_password = user.getPW().encode("utf-8")
        # compare if the hashed user password is the same as the one in the db
        if not bcrypt.checkpw(encoded_password,password_in_db):
            # if we arrive here it means the password was invalid
            errors["message"] = "Password is incorrect."
    else:
        errors["message"] = "Incorrect User/User does not exist."

# -- MONGODB CRUD Functions --

'''
CREATE user
'''
def add_user(user:User,users:collection,errors:dict):
    """ Adds a user to the users collection in the DB

    Args:
        user (User): user to be added, if it doesnt exist
        users (collection): DB collection of existing users
        message (dict): dictionary of error messages to be used in case an error occurrs
    """

    # check if there exists a user with the given email
    # if users.find_one({"email":user.email}):
    if get_user_by_email(user, users):
        errors["message"] = "There already exists an account with this email"
        return

    # check if there exists a user with the given username
    # if users.find_one({"username":user.username}):
    if get_user(user, users):
        errors["message"] = "This username is already taken/Username already exists"
        return

    # DB Insert error handling
    try:
        users.insert_one(user.to_document())
        
    except:
        errors["message"] = "Could not sign up at the moment. Please make sure the field are correct or try again later."


'''
CREATE post
'''
def create_post(author, group, content, date, image):
    
    try:
        post = Post(author, group, content, date, image)
        return post
    except TypeError:
        # TODO: return error message for TypeError
        pass
    except ValueError:
        # TODO: return error message for ValueError
        pass

'''
CREATE group
'''
def add_group(group: Group, groups: collection, errors: dict):
    """Adds a Group to the group collection in the DB

    Args:
        group (Group): Group object to insert to the DB
        groups (collection): Reference to the groups collection from the DB 
        message (dict): dictionary of error messages to be used in case an error occurrs

    """

    # Check for an existing group
    try:
      existing_group = groups.find_one({'name': group.name})
    except:
      errors["message"] = "Couldn't perform this action. Please try again later"
    
    if existing_group:
        errors["message"] = "There already exists an account with this email"
        return
    
    # DB insert handler
    try:
        groups.insert_one(group.to_document())
    except:
        errors["message"] = "Could not create a Group at the moment. Please make sure the information is correct or try again later."

    
# READ user

def get_user(user: User, users: collection):
    try:
        user = users.find_one({'username': user.username})
    except:
        print('An exception occurred')
    return user

def get_user_by_email(user: User, users: collection):
    try:
        user = users.find_one({'email': user.email})
    except:
        print('An exception occurred')

    return user

def get_user_by_id(id: ObjectId, users: collection):
    try:
        user = users.find_one({'_id': id})
    except:
        print('An exception occurred')

    return user

'''
READ post
'''

'''
READ group
'''
def get_groups(groups: collection):
    """Retrieves every group available

    Args:
        groups (collection): Reference to the groups collection from the DB
    """
    try:
        groups = groups.find()      
    except:
        # TODO:
        print('An exception occurred')
    return groups

# def get_group(group: Group, groups: collection):
#     """Gets a specific group from the DB 

#     Args:
#         group (Group): Group object 
#         groups (collection): Reference to the groups collection from the DB
#     """
#     try:
#         group = groups.find_one({'name': group.name})
#     except:
#         # TODO:
#         print('An exception occurred')
#     return group 

def get_group_by_id(id: ObjectId, groups: collection):
    """Gets a specific group from the DB by its id

    Args:
        id (ObjectId): Group ObjectId
        groups (collection): Reference to the groups collection from the DB
    """
    try:
        group = groups.find_one({'_id': id})
    except:
        # TODO:
        print('An exception occurred')
    return group   

'''
UPDATE user
'''

'''
UPDATE post
'''

'''
UPDATE group
'''

'''
DELETE user
'''

'''
DELETE post
'''

'''
DELETE group
'''