from re import split
from bson import ObjectId

"""
Class that represents a group in the DB. Each Group contains posts and the groups have a user
that created it, a date of creation and some descriptive text about the group

"""

class Group():
    
    def __init__(self, creator: ObjectId, name: str, about: str, date_created):
        self.creator = creator
        self.name = name
        self.about = about
        self.date_created = date_created
        
    
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

