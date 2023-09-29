from flask import jsonify, request, abort
from app import db
from app.models import User
from app.api import bp
from app.api.auth import token_auth


@bp.route('/users/<id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    user_data = db.users.find_one({'_id': id})

    if user_data:
        user = User(user_data)
        return jsonify(user.to_dict(include_email=True))
    else:
        return jsonify({'error': 'User not found'}), 404


@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    user_data_list = db.users.find() 

    users = []
    for user_data in user_data_list:
        user = User(user_data)
        users.append(user.to_dict(include_email=True))

    return jsonify(users)


@bp.route('/users/<id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    user_data = db.users.find_one({'_id': id})

    if user_data:
        followers = user_data.get('followers', [])

        return jsonify({'followers': followers})
    else:
        return jsonify({"error": "Usuario no encontrado"}), 404


@bp.route('/users/<id>/followed', methods=['GET'])
@token_auth.login_required
def get_followed(id):
    user_data = db.users.find_one({'_id': id})
    if user_data:
        following = user_data.get('following', [])

        return jsonify({'following': following})
    else:
        return jsonify({"error": "Usuario no encontrado"}), 404
    

@bp.route('/users', methods=['POST'])
@token_auth.login_required
def create_user():
    data = request.json

    new_user = User(data)

    if 'password_hash' in data:
        new_user.set_password(data['password_hash'])

    new_user.save()

    response = {
        'message': 'Usuario creado exitosamente',
        'user_id': str(new_user._id)
    }

    return jsonify(response), 201


@bp.route('/users/<id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    data = request.json

    user = db.users.find_one({'_id': id})

    user_data = User(user)

    if user_data:
        user_data.from_dict(data)

        user_data.update()

        response = {
            'message': 'Usuario actualizado exitosamente',
            'user_id': str(user._id)
        }

        return jsonify(response), 200
    else:
        return jsonify({"error": "Usuario no encontrado"}), 404 