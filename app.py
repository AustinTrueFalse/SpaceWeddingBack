import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask
from flask_cors import CORS
from auth.routes import auth_routes
from controllers.routes import guest_routes
from controllers.routes import event_routes
from dotenv import load_dotenv
import os

# Загружаем переменные окружения из файла .env
load_dotenv()

# Инициализация Flask
app = Flask(__name__)

# Разрешаем CORS для всех доменов (или укажите нужный домен)
CORS(app, supports_credentials=True)  # Разрешаем отправку куки

# Инициализация Firebase Admin SDK с использованием сервисного аккаунта
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Инициализация Firestore
db = firestore.client()

# Добавляем клиент Firestore в объект приложения
app.db = db

# Регистрация маршрутов авторизации
app.register_blueprint(auth_routes)
app.register_blueprint(guest_routes)
app.register_blueprint(event_routes)

if __name__ == '__main__':
    app.run(debug=True)
