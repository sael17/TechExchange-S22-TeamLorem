from collections import defaultdict
import bcrypt
import re

# Make a regular expression
# for validating an Email
# regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'


"""

     Class that represents a User in the website. The Basic pieces needed for a user to be build 
     are: email,username and password. All other member variables pieces that not necessary will 
     be used by the User.

    Raises:
        TypeError: TypeErrors are raised when in at any moment the parameters for the User 
        constructor are not strings 
        ValueError: ValueErrors are raised when the the username or password does not have the
        required length 

    Returns:
        The Class has different methods that return or do not return, depending in their 
        functionality and Purpose
"""

class User:


    def __init__(self,email:str, username:str, password:str) -> None:

        # error message to be used to format raised Errors
        error_message = "has to be a string"

        if type(email) != str:
            raise TypeError("{}" + error_message.format("Email"))
        
        if type(username) != str:
            raise TypeError("{}" + error_message.format("Username"))
        
        if type(password) != str:
            raise TypeError("{}" + error_message.format("password"))

        if username == '' or username.isspace():
            raise ValueError("Username can not be empty")

        if len(username) < 6 or len(username) > 16:
            raise ValueError("Username must be greater than 6 but less than 16 characters")

        if password == "" or password.isspace():
            raise ValueError("Password can not be empty")

        if len(password) < 8 or len(password) > 24:
            raise ValueError("Password must be greater than 8 but less than 24 characters")

    
        self.email = email
        self.username = username
        # notice that the password is a private field since it has to be encapsulated for security 
        # purposes
        self.__password = password
        # member variable that holds the original password encoded in '*' format
        self.star_pw = self.pw_to_star(password)
        # only ADMINS can moderate a social group
        self.canModerate = False
        # list of users the instance user follows
        self.following = []
        # list of users that follow the instanced User
        self.followers = []
        # placeholder image for user DB collection
        self.profile_picture = "https://images.unsplash.com/photo-1529335764857-3f1164d1cb24?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxzZWFyY2h8OXx8Y2FydG9vbnxlbnwwfHwwfHw%3D&auto=format&fit=crop&w=800&q=60"

    def __str__(self) -> str:
        return "Email: {}'\n' " + "Username: {}'\n' " + "Password: {}".format(self.email,
        self.username,self.pw_to_star(self.getPW()))

    """
        Method that returns the original users password encoded in '*' characters

        returns: original user password in '*' format
    """
    def pw_to_star(self,password:str) -> str:
        # use lists for better time/space complexity
        star_pw = []
        password = self.getPW()
        for _ in password:
            star_pw.append("*")

        return "".join(star_pw)

    """ 
        Returns the user's password protected field

    """

    def getPW(self) -> str:
        return self.__password

    """Constructs and returns a new User from a JSON Document or JSON Document Format """
    @classmethod
    def from_document(cls,document):
        """Constructs and returns a new User from a JSON Document """
        return User(document['email'], document['username'], document['password'])


    """Returns the user instance as a JSON Document """
    def to_document(self):
    
        # encrypt password for security reasons
        salt = bcrypt.gensalt()

        return {
            "email":self.email,
            "username":self.username,
            # uncomment this for testing
            # "password":self.getPW()
            # comment this for testing
            "password":bcrypt.hashpw(self.getPW().encode('utf-8'),salt),
            # From here on all keys have default values for the DB to have when a new 
            # instance is made
            "firstname":"FirstName",
            "lastname":"LastName",
            "bio":"",
            "following":self.followers,
            "followers":self.following,
            "profile_pic":self.profile_picture
        }
