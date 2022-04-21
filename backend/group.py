# from re import split
# from bson import ObjectId

# class Group():
    
#     def __init__(self, creator: ObjectId, name: str, date_created: TimeStamp):
#         self.creator = creator
#         self.name = name
#         self._camel_case_name = self.name_to_camel(self.name)
#         self.date_created = date_created
        
#         # Sets of ObjectIds
#         self.users = set()
#         self.posts = set()

    
#     @classmethod
#     def from_document(cls,document):
#         """Constructs and returns a new Group from a JSON Document """
        
#         group = Group(document['creator'], document['name'], document['date_created'])
       
#         group.users.union(document['users'])
#         group.posts.union(document['posts'])
        
#         return group

#     def to_document(self):
#         """Returns the group instance as a JSON Document """

#         return {
#             "creator":self.creator,
#             "name": self.name,
#             "users":self.users,
#             "posts":self.posts,
#             "date_created":self.date_created
#         }

#     def name_to_camel(self, name):
        
#         # regex to represent ANY character that isn't a letter
#         words = split('([^a-zA-Z])', name)
        
#         camel = []
#         for word in words:
#             if word.isalpha():
#                 camel.append(word.capitalize())
                
#         return ''.join(camel)        
