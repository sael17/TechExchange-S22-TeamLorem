class Post:
    def __init__(self, author, group, content, date, image):
        self.author = author
        self.group = group
        self.content = content
        self.date = date
        self.image = image
    
    @classmethod
    def from_document(cls,document):
        """Constructs and returns a new Post from a JSON Document """
        
        post = Post(document['author'], document['group'],document['content'], document['date'], document['group_image'])
               
        return post

    def to_document(self):
        """Returns the post instance as a JSON Document """

        return {
            "author": self.author,
            "group": self.group,
            "content": self.content,
            "date": self.date,
            "group_image": self.image
        }
