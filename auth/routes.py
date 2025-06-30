from flask import Blueprint, request, jsonify
from .auth_controller import sign_in_cookie, sign_in, sign_out, register, check_username, verify_token, confirm, send_email_password_reset, reset_password, resend_email_verify

auth_routes = Blueprint('auth', __name__)

@auth_routes.route('/auth/signin_cookie', methods=['POST'])
def sign_in_cookie_route():
    return sign_in_cookie()

@auth_routes.route('/auth/signin', methods=['POST'])
def sign_in_route():
    return sign_in(request.json)

@auth_routes.route('/auth/signout', methods=['POST'])
def sign_out_route():
    return sign_out()

@auth_routes.route('/auth/register', methods=['POST'])
def register_route():
    return register(request.json)

@auth_routes.route('/auth/confirm', methods=['POST'])
def confirm_route():
    return confirm()

@auth_routes.route('/auth/send_email_password_reset', methods=['POST'])
def send_email_password_reset_route():
    return send_email_password_reset()

@auth_routes.route('/auth/reset_password', methods=['POST'])
def password_reset_email_route():
    return reset_password()

@auth_routes.route('/auth/resend_email_verify', methods=['POST'])
def resend_email_verify_route():
    return resend_email_verify()

@auth_routes.route('/auth/check_username', methods=['POST'])
def check_username_route():
    return check_username(request.json)

@auth_routes.route('/verify-token', methods=['POST'])
def verify_token_route():
    return verify_token(request.json)