import bcrypt
import re

# Make a regular expression
# for validating an Email
# regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

class User:


    def __init__(self,email:str, username:str, password:str) -> None:

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

        # if not re.fullmatch(regex,email):
        #     raise ValueError("Email must be a valid format")

        if password == "" or password.isspace():
            raise ValueError("Password can not be empty")

        if len(password) < 8 or len(password) > 24:
            raise ValueError("Password must be greater than 8 but less than 24 characters")

    
        self.email = email
        self.username = username
        self.__password = password
        self.star_pw = self.pw_to_star(password)
        self.canModerate = False
        self.following = []
        self.followers = []

    def __str__(self) -> str:
        return "Email: {}'\n' " + "Username: {}'\n' " + "Password: {}".format(self.email,
        self.username,self.pw_to_star(self.getPW()))


    def pw_to_star(self,password:str) -> str:
        star_pw = []
        password = self.getPW()
        for _ in password:
            star_pw.append("*")

        return "".join(star_pw)

        """ Returns the user's password protected field
        """
    def getPW(self) -> str:
        return self.__password


    @classmethod
    def from_document(cls,document):
        """Constructs and returns a new User from a JSON Document """
        return User(document['email'], document['username'], document['password'])

    def to_document(self):
        """Returns the user instance as a JSON Document """

        # encrypt password for security reasons
        salt = bcrypt.gensalt()

        return {
            "email":self.email,
            "username":self.username,
            # uncomment this for testing
            # "password":self.getPW()
            # comment this for testing
            "password":bcrypt.hashpw(self.getPW().encode('utf-8'),salt),
            "following":self.followers,
            "followers":self.following
        }