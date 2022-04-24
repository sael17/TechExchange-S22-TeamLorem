from backend import user
class Admin(user.User):
    
    def __init__(self,email,username,password):
        user.User.__init__(self,email,username,password)
        self.canModerate = True

   

        

    