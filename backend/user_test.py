import unittest
import user
# import admin


# Data For Initial Tests
test_email = "email@email.com"
test_username = "sael@17"
test_password = "colegio@2019"

class TestUser(unittest.TestCase):

     # User instances to test
    user01 = user.User(test_email,test_username,test_password)
    user02 = user.User("yan.aquino1@upr.edu","yanc@aquino","123456789")
    # user03 = admin.Admin("brandong.fung@techexchange.in","branfung","bran.fung12")
    # user04 = admin.Admin("user04@email.com","user04","user01_is_the_best")


    def test_argument_types(self):

        # Everything has to be a string
        self.assertRaises(TypeError,user.User,123,test_username,test_password)
        self.assertRaises(TypeError,user.User,["Harry","Potter"],test_username,test_password)
        self.assertRaises(TypeError,user.User,("Star","Wars"),test_username,test_password)
        self.assertRaises(TypeError,user.User,{"Hello":"There"},test_username,test_password)
        self.assertRaises(TypeError,user.User,True,test_username,test_password)
        self.assertRaises(TypeError,user.User,False,test_username,test_password)
        self.assertRaises(TypeError,user.User,None,test_username,test_password)

        self.assertRaises(TypeError,user.User,test_email,12345678910,test_password)
        self.assertRaises(TypeError,user.User,test_email,[True,False],test_password)
        self.assertRaises(TypeError,user.User,test_email,("Bilbo","Baggins"),test_password)
        self.assertRaises(TypeError,user.User,test_email,{"Luke":"Skywalker"},test_password)
        self.assertRaises(TypeError,user.User,test_email,True,test_password)
        self.assertRaises(TypeError,user.User,test_email,False,test_password)
        self.assertRaises(TypeError,user.User,test_email,None,test_password)

        self.assertRaises(TypeError,user.User,test_email,test_username,123423556336)
        self.assertRaises(TypeError,user.User,test_email,test_username,[1,2])
        self.assertRaises(TypeError,user.User,test_email,test_username,("Darth","Vader"))
        self.assertRaises(TypeError,user.User,test_email,test_username,({"Emperor":"Palpatine"}))
        self.assertRaises(TypeError,user.User,test_email,test_username,True)
        self.assertRaises(TypeError,user.User,test_email,test_username,False)
        self.assertRaises(TypeError,user.User,test_email,test_username,None)


    def test_argument_values(self):
        self.assertRaises(ValueError,user.User,"user",test_username,test_password)
        self.assertRaises(ValueError,user.User,"thebest@in@",test_username,test_password)
        self.assertRaises(ValueError,user.User,"thebest@in@email",test_username,test_password)
        self.assertRaises(ValueError,user.User,"thebest@in@email.com",test_username,test_password)
        self.assertRaises(ValueError,user.User," ",test_username,test_password)


        self.assertRaises(ValueError,user.User,test_email,"user",test_password)
        self.assertRaises(ValueError,user.User,test_email,"user01_is_the-best-user-in-PR",test_password)
        self.assertRaises(ValueError,user.User,test_email," ",test_password)
        self.assertRaises(ValueError,user.User,test_email,"",test_password)
        
        self.assertRaises(ValueError,user.User,test_email,test_username,"12345")
        self.assertRaises(ValueError,user.User,test_email,test_username,"this is the best password in the world jajaajaj")
        self.assertRaises(ValueError,user.User,test_email,test_username," ")
        self.assertRaises(ValueError,user.User,test_email,test_username, "")

    def test_pw_to_star(self):
        self.assertEqual(len(self.user01.getPW()),len(self.user01.star_pw))
        self.assertEqual(len(self.user02.getPW()),len(self.user02.star_pw))
        # self.assertEqual(len(self.user03.getPW()),len(self.user03.star_pw))
        # self.assertEqual(len(self.user04.getPW()),len(self.user04.star_pw))

        # self.assertEqual(self.user03.star_pw,"***********")


    def test_can_moderate(self):
        self.assertEqual(self.user01.canModerate,False)
        self.assertEqual(self.user02.canModerate,False)
        # self.assertEqual(self.user03.canModerate,True)
        # self.assertEqual(self.user04.canModerate,True)

    def test_to_document(self):
        self.assertEqual(self.user01.to_document(),{"email":test_email,"username":test_username,
        "password":test_password})
        self.assertEqual(self.user02.to_document(),{"email":"yan.aquino1@upr.edu",
        "username":"yanc@aquino","password":"123456789"})
        # self.assertEqual(self.user03.to_document(),{"email":"brandong.fung@techexchange.in",
        # "username":"branfung","password":"bran.fung12"})
        # self.assertEqual(self.user04.to_document(),{"email":"user04@email.com","username":"user04",
        # "password":"user01_is_the_best"})


    def test_from_document(self):
        self.temp = user.User.from_document({"email":"juan.delcampo@upr.edu",
        "username":"juan.delcampo@1","password":"google@2022"})

        
        # test object has been created
        self.assertEqual(self.temp.email,"juan.delcampo@upr.edu")
        self.assertEqual(self.temp.username, "juan.delcampo@1")
        self.assertEqual(self.temp.canModerate,False)
        
        # test if to document works too
        self.assertEqual(self.temp.to_document(),{"email":"juan.delcampo@upr.edu",
        "username":"juan.delcampo@1","password":"google@2022"})

if __name__ == '__main__':
    unittest.main()


