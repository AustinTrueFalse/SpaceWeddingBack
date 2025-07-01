from functools import wraps
from flask import request, jsonify, make_response, g
import firebase_admin
from firebase_admin import auth
import os
import requests
from werkzeug.wrappers import Response
import traceback
from services.exception_handler import default_error_response, validation_error_response, firebase_error_response

# Получаем ключ API из переменных окружения
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')

def authenticate_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("\n--- Начало аутентификации ---")
        
        # Получаем токены из куки
        token = request.cookies.get('firebase_token')
        refresh_token = request.cookies.get('refresh_token')
        print(f"Токены из куки - firebase_token: {'есть' if token else 'нет'}, refresh_token: {'есть' if refresh_token else 'нет'}")

        # Обработка отсутствия токенов
        if not token and not refresh_token:
            print("Ошибка: Отсутствуют оба токена")
            return firebase_error_response("Authentication required", 401)

        try:
            # Если токен невалиден или отсутствует
            if not token or not _is_token_valid(token):
                if not refresh_token:
                    return firebase_error_response("Could not refresh token", 401)
                
                # Обновляем токен
                new_token, new_refresh_token = _handle_token_refresh(refresh_token)
                if not new_token:
                    return firebase_error_response("Could not refresh token", 401)
                
                # Проверяем новый токен и устанавливаем g.user
                auth_response = _verify_token(new_token)
                if isinstance(auth_response, Response):
                    return auth_response
                
                # Создаем ответ с установкой куки
                response = make_response(f(*args, **kwargs))
                response.set_cookie('firebase_token', new_token, httponly=True, samesite='Lax', secure=False)
                return response

            # Основная проверка валидного токена
            auth_response = _verify_token(token)
            if isinstance(auth_response, Response):
                return auth_response
            
            return f(*args, **kwargs)

        except Exception as e:
            print(f"Ошибка аутентификации: {str(e)}")
            print(f"Тип ошибки: {type(e).__name__}")
            print(f"Traceback: {traceback.format_exc()}")
            return default_error_response("Authentication failed", 500)

    return decorated_function

def _is_token_valid(token):
    try:
        auth.verify_id_token(token)
        return True
    except auth.ExpiredIdTokenError:
        return False
    except Exception:
        return False

def _handle_token_refresh(refresh_token):
    print("Попытка обновления токена...")
    new_id_token, new_refresh_token = refresh_token_method(refresh_token)
    if new_id_token:
        print("Токены успешно обновлены")
        return new_id_token, new_refresh_token
    return None, None

def _verify_token(token):
    try:
        print("Проверка токена...")
        decoded_token = auth.verify_id_token(token)
        
        email_verified = decoded_token.get("email_verified", False)
        print(f"Статус подтверждения email: {email_verified}")
        
        if not email_verified:
            print("Ошибка: Email не подтвержден")
            return firebase_error_response("Email not verified", 403)
        
        g.user = decoded_token
        print("Аутентификация успешна")
        return None
        
    except Exception as e:
        print(f"Ошибка проверки токена: {str(e)}")
        return default_error_response("Token verification failed", 401)



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

