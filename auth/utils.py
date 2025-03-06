from functools import wraps
from flask import request, jsonify, make_response, g
import firebase_admin
from firebase_admin import auth
import os
import requests
from services.exception_handler import default_error_response, validation_error_response, firebase_error_response

# Получаем ключ API из переменных окружения
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')

def authenticate_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        # Получаем id_token и refresh_token из куки
        token = request.cookies.get('firebase_token')
        refresh_token = request.cookies.get('refresh_token')
        
        if not token or not refresh_token:
            return firebase_error_response("Could not refresh token", 401)

        try:
            # Попытка проверки токена
            decoded_token = auth.verify_id_token(token)

            email_verified = decoded_token.get("email_verified", False)
            print("Статус подверждения емаил:", email_verified)

            if not email_verified:
                return firebase_error_response("Email not verified", 403)

            g.user = decoded_token  # Сохраняем данные пользователя в контексте
            

        except auth.ExpiredIdTokenError:
            # Если токен истек, обновляем его
            new_id_token, new_refresh_token = refresh_token_method(refresh_token)
            if new_id_token:
                # Создаем ответ с новыми куками для токенов
                resp = make_response(f(*args, **kwargs))
                resp.set_cookie('firebase_token', new_id_token, httponly=True, samesite='Lax', secure=False)
                resp.set_cookie('refresh_token', new_refresh_token, httponly=True, samesite='Lax', secure=False)

                # Проверяем и сохраняем пользователя с новым id_token
                decoded_token = auth.verify_id_token(new_id_token)
                email_verified = decoded_token.get("email_verified", False)
                print("Статус подверждения емаил:", email_verified)

                if not email_verified:
                    return firebase_error_response("Email not verified", 403)

                g.user = decoded_token
                

                return resp
            else:
                return firebase_error_response("Could not refresh token", 401)

        except Exception as e:
            print("Ошибка при проверке токена:", str(e))
            return default_error_response(str(e), 500)

        return f(*args, **kwargs)

    return decorated_function

# Функция для обновления токенов
def refresh_token_method(refresh_token):
    try:
        # Запрос на обновление токена
        response = requests.post(
            f'https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}',
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }
        )
        
        # Проверяем, есть ли ошибка в ответе
        response_data = response.json()
        if 'error' in response_data:
            raise Exception(response_data['error']['message'])  # Выбросить исключение вместо возврата ошибки
        
        # Возвращаем новый idToken и refreshToken
        new_id_token = response_data.get("id_token")
        new_refresh_token = response_data.get("refresh_token")
        
        if not new_id_token or not new_refresh_token:
            raise Exception("Failed to get id_token or refresh_token")
        
        return new_id_token, new_refresh_token
    
    except Exception as e:
        return default_error_response(str(e), 500)  # Обработать ошибку в вызывающем методе