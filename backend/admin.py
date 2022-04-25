from backend import user

"""
class that represents a Admin, which is a type of user that has some extra priviliges. This is 
why Admin inheritates from User, only difference being that the ADMIN can moderate a social
group
"""

class Admin(user.User):
    
    def __init__(self,email,username,password):
        user.User.__init__(self,email,username,password)
        self.canModerate = True

   

        

    