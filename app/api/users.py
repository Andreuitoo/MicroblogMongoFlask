from flask import jsonify, request, url_for, abort
from app import db
from app.models import User
from app.api import bp

@bp.route('/users/<id>', methods=['GET'])
def get_user(id):
    user_data = db.users.find_one({'_id': id})

    if user_data:
        user = User(user_data)
        return jsonify(user.to_dict(include_email=True))
    else:
        return jsonify({'error': 'User not found'}), 404


@bp.route('/users', methods=['GET'])
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    user_data = User.to_collection_dict()
    return jsonify(user_data)

@bp.route('/users/<int:id>/followers', methods=['GET'])
def get_followers(id):
    pass

@bp.route('/users/<int:id>/followed', methods=['GET'])
def get_followed(id):
    pass

@bp.route('/users', methods=['POST'])
def create_user():
    pass

@bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    pass