from datetime import datetime
from flask import jsonify
from app.api import bp
from app.api.auth import basic_auth, token_auth


@bp.route('/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    token = basic_auth.current_user().get_token()
    basic_auth.current_user().token = token
    basic_auth.current_user().update()
    return jsonify({'token': token})


@bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    token_auth.current_user().revoke_token()
    token_auth.current_user().token = ''
    token_auth.current_user().token_expiration = datetime.utcnow()
    token_auth.current_user().update()
    return '', 204