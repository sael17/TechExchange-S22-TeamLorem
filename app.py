import pymongo


client = pymongo.MongoClient("mongodb+srv://admin:DomQpADqhp2BF1Lg@cluster0.3pto1.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.test

db.create_collection("users")
