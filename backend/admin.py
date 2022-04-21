from user import User

class Admin(User):
    
    def __init__(self,email,username,password):
        User.__init__(self,email,username,password)
        self.canModerate = True

   

        

    