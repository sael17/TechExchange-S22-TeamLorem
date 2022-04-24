from re import split
from bson import ObjectId

class Group():
    
    def __init__(self, creator: ObjectId, name: str, about: str, date_created):
        self.creator = creator
        self.name = self.strip_spaces(name)
        self.about = about
        self.date_created = date_created
        
        # Sets of ObjectIds
        # self.users = []
        # self.posts = []

    
    @classmethod
    def from_document(cls,document):
        """Constructs and returns a new Group from a JSON Document """
        
        group = Group(document['creator'], document['name'],document['about'], document['date_created'])
               
        return group

    def to_document(self):
        """Returns the group instance as a JSON Document """

        return {
            "creator":self.creator,
            "name": self.name,
            "about": self.about,
            "date_created":self.date_created
        }

    def strip_spaces(self, name):
        words = split(' ', name)
        return ''.join(words)        
