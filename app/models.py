from hashlib import md5

from flask import flash
from app import user_collection, post_collection, login
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash



@login.user_loader
def load_user(user_id):
    user_data = user_collection.find_one({'_id': user_id})
    if user_data:
        return User(user_data)
    return None


class User(UserMixin):
    def __init__(self, user_data):
        self._id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.password_hash = user_data['password_hash']
        self.about_me = user_data.get('about_me', '')
        self.last_seen = user_data.get('last_seen')
        self.followers = user_data.get("followers", [])
        self.following = user_data.get("following", []) 
    
    def get_id(self):
        return self._id

    def save(self):
        user_collection.insert_one(self.__dict__).inserted_id

    def update_2rgs(self, update_values):
        user_collection.update_one({"_id": self._id}, {'$set': update_values})

    def update(self):
        user_collection.update_one({"_id": self._id},{'$set': self.__dict__})

    @staticmethod
    def find_by_username(username):
        user_data = user_collection.find_one({'username': username})

        if user_data:
            return User(user_data)
        return None

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)
    
    def is_following(self, user_id):
        return str(user_id) in self.following
    
    def follow(self, user):
        if user._id != self._id and user._id not in self.following:
            self.following.append(user._id)
            self.update_2rgs({"following": self.following})

    def unfollow(self, user_to_unfollow):
        if user_to_unfollow._id != self._id and user_to_unfollow._id in self.following:
            self.following.remove(user_to_unfollow._id)
            self.update_2rgs({"following": self.following})
    
    def followed_posts(self):
        pass
    

class Post:
    def __init__(self, body, user_id):
        self.body = body
        self.timestamp = datetime.utcnow()
        self.user_id = user_id

    def save(self):
        post_collection.insert_one({
            'body': self.body,
            'timesstamp': self.timestamp,
            'user_id': self.user_id
        })

    @staticmethod
    def find_all_with_user_info():
        pipeline = [
            {
                "$lookup": {
                    "from": "users",
                    "localfield": "user_id",
                    "foreignField": "_id",
                    "as": "user"
                }
            },
            {
                "$unwind": "$user"
            }
        ]

        posts = post_collection.aggregate(pipeline)

        return posts
    
    @staticmethod
    def find_by_user_id(user_id):
        return post_collection.find({'user_id': user_id})