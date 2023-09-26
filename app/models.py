import jwt
from time import time
from hashlib import md5
from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login


user_collection = db.users
post_collection = db.posts


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
        self.avatar_uri= user_data.get('avatar', self.avatar(36))
    
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
    
    @staticmethod
    def find_by_email(email):
        user_data = user_collection.find_one({'email': email})

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

    def unfollow(self, user):
        if user._id != self._id and user._id in self.following:
            self.following.remove(user._id)
            self.update_2rgs({"following": self.following})
    
    def followed_posts(self):
        followed_ids = self.following
        
        followed_ids.append(self._id)
        
        followed_posts = post_collection.find({"user_id": {"$in": followed_ids}})
        
        followed_posts = followed_posts.sort("timestamp", -1)

        return followed_posts
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self._id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_password_token(token):
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = payload['reset_password']
        user_data = User.get_by_id(user_id)
        user = User(user_data) if user_data else None
        return user


    @staticmethod
    def get_by_id(user_id):
        return db.users.find_one({'_id': user_id})
    

class Post:
    def __init__(self, body, user_id):
        self.body = body
        self.timestamp = datetime.utcnow()
        self.user_id = user_id

    def save(self):
        post_data = {
            "body": self.body,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
        }
        result = post_collection.insert_one(post_data)
        self.id = result.inserted_id 

    @staticmethod
    def find_all_with_user_info():
        pipeline = [
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
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