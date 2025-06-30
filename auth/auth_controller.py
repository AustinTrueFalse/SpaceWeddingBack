import requests
from flask import request, jsonify, g, make_response, current_app
from pydantic import ValidationError
from models.user import UserCreate
from services.exception_handler import default_error_response, validation_error_response, firebase_error_response
from services.response_handler import default_response
from auth.utils import refresh_token_method
from firebase_admin import credentials, auth, firestore
import logging
import os

logging.basicConfig(level=logging.DEBUG)

# Получаем ключ API из переменных окружения
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')

def sign_in_cookie():
    id_token = request.cookies.get('firebase_token')

    print ("Token:", id_token)
    
    if not id_token:
        print ("Missing id_token")
        return firebase_error_response("Missing id_token", 401)

    try:
        # Проверяем и декодируем токен
        decoded_token = auth.verify_id_token(id_token)
        
        # Получаем uid из токена
        user_id = decoded_token['uid']
        email_verified = decoded_token.get("email_verified", False)
            
        # Возвращаем email
        resp = make_response(jsonify({"user": user_id, "is_account_confirmed": email_verified}), 200)
        
        
        return resp


    except Exception as e:
        print("Ошибка при авторизации через cookie", e)
        default_error_response(str(e), 500)

def sign_in_with_google():
    try:
        data = request.get_json()
        id_token = data.get("idToken")
        refresh_token = data.get("refreshToken")

        if not id_token or not refresh_token:
            return firebase_error_response("Missing idToken or refreshToken", 400)

        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        email_verified = decoded_token.get("email_verified", False)
        email = decoded_token.get("email")

        if not email:
            return firebase_error_response("Missing email in token", 400)

        db = current_app.db

        existing_user = db.collection('users').document(user_id).get()
        if not existing_user.exists:
            username = email.split('@')[0]
            username_check = check_username({"username": username})
            if not username_check['available']:
                username += user_id[:6]

            user_data = {
                "email": email,
                "username": username,
                "email_lower": email.lower(),
                "username_lower": username.lower()
            }

            add_user_result = add_user(user_data, db, user_id)
            if add_user_result[1] != 201:
                remove_user_from_firebase(id_token)
                return add_user_result

        # Создаем ответ и безопасные куки
        resp = make_response(jsonify({
            "user": user_id,
            "is_account_confirmed": email_verified
        }), 200)

        # Устанавливаем HttpOnly куки
        resp.set_cookie(
            'firebase_token',
            id_token,
            httponly=True,
            secure=False,  # включи HTTPS
            samesite='Lax',
            max_age=60 * 60  # 1 час
        )
        resp.set_cookie(
            'refresh_token',
            refresh_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=60 * 60 * 24 * 30  # 30 дней
        )

        return resp

    except Exception as e:
        print("Google sign-in error:", e)
        return jsonify({"error": str(e)}), 500




def sign_in(data):
    email = data['email']
    password = data['password']
    
    try:
        response = requests.post(
            f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}', 
            json={"email": email, "password": password, "returnSecureToken": True}
        )

        response_data = response.json()


        if 'error' in response_data:
            print("Ошибка firebase при авторизации")
            return firebase_error_response(response_data['error']['message'], 503)
        # Получаем токены
        id_token = response_data["idToken"]
        refresh_token = response_data["refreshToken"]

        # Декодируем токен
        decoded_token = auth.verify_id_token(id_token)
        email_verified = decoded_token.get("email_verified", False)
        user_id = decoded_token['uid']
        
        

        # Формируем ответ с куками
        resp = make_response(jsonify({
            "user": user_id,
            "is_account_confirmed": email_verified
        }), 200)
        resp.set_cookie('firebase_token', id_token, httponly=True, samesite='Lax', secure=False)
        resp.set_cookie('refresh_token', refresh_token, httponly=True, samesite='Lax', secure=False)
        

        return resp

    except Exception as e:
        print("Ошибка при авторизации:", str(e))
        return jsonify({"error": "Ошибка при авторизации", "details": str(e)}), 500

def sign_out():
    resp = make_response("Cookies deleted")
    resp.set_cookie('firebase_token', '', max_age=0, httponly=True, samesite='Lax', secure=False)
    resp.set_cookie('refresh_token', '', max_age=0, httponly=True, samesite='Lax', secure=False)
    return resp


def register(data):
    email = data['email']
    password = data['password']
    username = data['username']

    if not username:  # Теперь это точно словарь
        print("Не передан username")
        return default_error_response("Не передан username", 500)
    # Проверяем доступность имени пользователя
    username_check = check_username(data)
    print("usernamecheck:", username_check['available'])
    if not username_check['available']:  # Теперь это точно словарь
        return firebase_error_response("USERNAME_EXISTS", 400)
    
    # Регистрация в Firebase
    try:
        # Отправляем запрос в Firebase для создания пользователя
        response = requests.post(
            f'https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}', 
            json={"email": email, "password": password, "returnSecureToken": True}
        )
        response_data = response.json()
        
        # Если произошла ошибка в Firebase
        if 'error' in response_data:
            print("Ошибка firebase при регистрации")
            return firebase_error_response(response_data['error']['message'], 503)
        
        # Получаем UID пользователя (localId) из Firebase
        user_id = response_data["localId"]
        id_token = response_data["idToken"]
        refresh_token = response_data["refreshToken"]


        # Подготовка данных для Firestore
        user_data = {
            "email": email,
            "username": username,
            "email_lower": email.lower(),
            "username_lower": username.lower()
        }

        email_verify(id_token)

        # Теперь добавляем пользователя в Firestore
        db = current_app.db
        add_user_result = add_user(user_data, db, user_id)  # Передаем user_id в функцию add_user

        # Если добавление пользователя в базу не прошло, удаляем пользователя из Firebase
        if add_user_result[1] != 201:
            # Пытаемся удалить пользователя из Firebase (удаляем только, если произошла ошибка с Firestore)
            remove_user_from_firebase(id_token)
            return add_user_result  # Возвращаем ошибку, если добавление в базу не удалось

        # Создаем ответ
        resp = make_response(jsonify({"user": email}), 200)

        # Устанавливаем куки
        resp.set_cookie('firebase_token', id_token, httponly=True, samesite='Lax', secure=False)  # Сохраняем токен в куку с флагом HttpOnly
        resp.set_cookie('refresh_token', refresh_token, httponly=True, samesite='Lax', secure=False)


        return resp

    except Exception as e:
        # В случае любой ошибки, возвращаем ошибку
        print("Ошибка при регистрации")
        return default_error_response(str(e), 500)


def check_username(data):
    username = data['username']
    db = current_app.db

    if not username:
        print("Не передан username")
        return default_error_response("Не передан username", 500)
    
    try:
        # Запрос к коллекции "users" для поиска документа с данным username
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username).limit(1).stream()

         # Если документ найден, то возвращаем False, иначе True
        for user in query:
            return {"available": False}  # Username already exists

        return {"available": True}  # Username is available


    except Exception as e:
        print(f"Ошибка проверки username: {e}")
        return default_error_response(str(e), 500)


def resend_email_verify():
    id_token = request.cookies.get('firebase_token')
    
    if not id_token:
        print("Ошибка: id_token отсутствует.")
        return firebase_error_response("Missing id_token", 400)

    try:
        # Вызываем функцию верификации email
        result = email_verify(id_token)
        return result  # Возвращаем результат функции email_verify

    except Exception as e:
        # В случае любой ошибки, возвращаем ошибку
        print("Ошибка при вызове функции повторной отправки Email")
        return default_error_response(str(e), 500)


def email_verify(id_token):

    if not id_token:
        print("Ошибка: id_token отсутствует.")
        return firebase_error_response("Missing id_token", 400)
    
    # Регистрация в Firebase
    try:
        # Отправляем email для подтверждения
        email_verify_response = requests.post(
            f'https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}',
            json={"requestType": "VERIFY_EMAIL", "idToken": id_token}
        )
        email_verify_data = email_verify_response.json()

        if 'error' in email_verify_data:
            print("Ошибка при отправке email для подтверждения")
            return firebase_error_response(email_verify_data['error']['message'], 503)
        
        print("Email для подтверждения отправлен")

        return default_response("Email для подтверждения отправлен", 200)

    except Exception as e:
        # В случае любой ошибки, возвращаем ошибку
        print("Ошибка при регистрации")
        return default_error_response(str(e), 500)


def confirm():
    # Метод для подтверждения email с обработкой oobCode и обновления токенов.
    data = request.get_json()
    oob_code = data.get('oobCode') if data else None
    refresh_token = request.cookies.get('refresh_token')

    if not oob_code:
        print("Ошибка: oobCode отсутствует.")
        return firebase_error_response("Missing oobCode", 400)

    # After adding this verification, the email started getting confirmed successfully!!
    try:
        verify_response = requests.post(
            f'https://identitytoolkit.googleapis.com/v1/accounts:update?key={FIREBASE_API_KEY}',
            json={"oobCode": oob_code}
        )
        if verify_response.status_code != 200:
            print("Ошибка подтверждения oobCode:", verify_response.json())
            return firebase_error_response("Failed to verify email", 400)
        print("Email успешно подтверждён.")

    except Exception as e:
        print("Ошибка подтверждения email:", str(e))
        return default_error_response(str(e), 500)

    # Обновляем токен после подтверждения email
    if not refresh_token:
        print("Ошибка: refresh_token отсутствует.")
        return firebase_error_response("No refresh_token found", 401)

    try:
        refresh_response = requests.post(
            f'https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}',
            data={'grant_type': 'refresh_token', 'refresh_token': refresh_token}
        )
        if refresh_response.status_code != 200:
            print("Ошибка обновления токенов:", refresh_response.json())
            return firebase_error_response("Failed to refresh token", 400)

        tokens = refresh_response.json()
        new_id_token = tokens.get("id_token")
        new_refresh_token = tokens.get("refresh_token")

        if not new_id_token:
            print("Ошибка: не удалось получить новый id_token.")
            return firebase_error_response("Could not refresh token", 401)

        # Устанавливаем новые куки
        resp = make_response(jsonify({"message": "Email confirmation successful!"}))
        resp.set_cookie('firebase_token', new_id_token, httponly=True, samesite='Lax', secure=False)
        resp.set_cookie('refresh_token', new_refresh_token, httponly=True, samesite='Lax', secure=False)
        print("Новые токены установлены.")

        return resp

    except Exception as e:
        print("Ошибка обновления токенов:", str(e))
        return default_error_response(str(e), 500)


def send_email_password_reset():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return firebase_error_response("Missing email", 400)

    try:
        # Проверяем существует ли email в коллекции users
        db = firestore.client()
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1).stream()

        user_exists = False
        for _ in query:
            user_exists = True
            break

        if not user_exists:
            print("Email не найден в коллекции users:", email)
            return firebase_error_response("Email not found", 404)

        # Отправляем запрос на сброс пароля в Firebase
        reset_response = requests.post(
            f'https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}',
            json={
                "requestType": "PASSWORD_RESET",
                "email": email
            }
        )

        if reset_response.status_code != 200:
            print("Ошибка отправки письма:", reset_response.json())
            return firebase_error_response("Failed to send password reset email", 400)

        print("Письмо для сброса пароля отправлено на:", email)
        return jsonify({"message": "Password reset email sent."}), 200

    except Exception as e:
        print("Ошибка при отправке письма:", str(e))
        return default_error_response(str(e), 500)


def reset_password():
    data = request.get_json()
    oob_code = data.get('oobCode')
    new_password = data.get('newPassword')

    if not oob_code or not new_password:
        return make_response(jsonify({"error": "Missing oobCode or newPassword"}), 400)

    try:
        reset_response = requests.post(
            f'https://identitytoolkit.googleapis.com/v1/accounts:resetPassword?key={FIREBASE_API_KEY}',
            json={
                "oobCode": oob_code,
                "newPassword": new_password
            }
        )

        if reset_response.status_code != 200:
            print("Ошибка сброса пароля:", reset_response.json())
            return make_response(jsonify({"error": "Failed to reset password"}), 400)

        print("Пароль успешно сброшен.")
        return make_response(jsonify({"message": "Password reset successful!"}), 200)

    except Exception as e:
        print("Ошибка сброса пароля:", str(e))
        return make_response(jsonify({"error": str(e)}), 500)


def verify_token(data):
    try:
        # Получаем токен из тела запроса
        id_token = data.get('idToken')

        # Проверяем токен через Firebase
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']

        # Возвращаем информацию о пользователе, если токен валиден
        return jsonify({
            'uid': uid,
            'message': 'Token is valid'
        }), 200
        
    except Exception as e:
        print("Ошибка при проверке токена")
        # Обрабатываем ошибки, если токен недействителен
        return firebase_error_response(str(e), 401)


def add_user(data, db, user_id):
    try:
        # Валидация данных с использованием модели Pydantic
        user_data = UserCreate(**data)

        # Добавление документа в коллекцию "users" Firestore с использованием user_id как ID
        user_ref = db.collection('users').document(user_id)
        user_ref.set(user_data.dict())  # Используем set() для создания/обновления документа с конкретным ID

        return jsonify({"id": user_ref.id, "message": "Юзер успешно добавлен!"}), 201

    except ValidationError as e:
        print("Ошибка валидации при попытке добавить юзера")
        # Возвращаем ошибки валидации, если данные не проходят проверку
        return validation_error_response(str(e.errors()), 400)

    except Exception as e:
        print("Другая ошибка при попытке добавить юзера")
        return default_error_response(str(e), 500)

def remove_user_from_firebase(id_token):
    # Функция для удаления пользователя из Firebase с использованием idToken
    try:
        # Удаляем пользователя из Firebase с помощью REST API, передавая idToken
        response = requests.post(
            f'https://identitytoolkit.googleapis.com/v1/accounts:delete?key={FIREBASE_API_KEY}',
            json={"idToken": id_token}  # Передаем токен авторизации, а не user_id
        )
        
        response_data = response.json()
        
        if 'error' in response_data:
            # Логируем ошибку и ее сообщение
            print(f"Ошибка при удалении пользователя из Firebase: {response_data['error']['message']}")
            return firebase_error_response(response_data['error']['message'], 503)
        else:
            print("Пользователь успешно удален из Firebase")
    
    except Exception as e:
        # Логируем ошибку, если запрос не удался
        print(f"Ошибка при попытке удалить пользователя из Firebase: {str(e)}")
        return default_error_response(str(e), 500)