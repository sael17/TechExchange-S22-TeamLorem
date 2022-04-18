from post import Post


'''
Controller
'''
def create_post(author, group, content, date, image):
    return Post(author, group, content, date, image)
