from user import User

class Admin(User):
    
    def __init__(self):
        User.__init__(self,User.email,User.username,User.password)
        self.canModerate = True

    def __str__(self) -> str:
        return super().__str__()

        

    