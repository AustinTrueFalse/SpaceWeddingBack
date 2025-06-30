from flask import jsonify, request, g
from pydantic import ValidationError
from models.event import EventCreate, EventUpdate
from models.todo import Todo
from services.exception_handler import default_error_response, validation_error_response
from services.response_handler import default_response
from datetime import datetime
from services.validation import validate_user, validate_event, validate_permission, validate_guest_phone


def search_users(data, db):
    try:
        user_id = g.user.get("uid")

        # Валидация пользователя
        user_error = validate_user(user_id, db)
        if user_error:
            return user_error

        query = data.get("query")
        if not query:
            return validation_error_response("Search query is required", 400)

        # Приводим строку к нижнему регистру для сравнения
        query_lower = query.lower()

        matched_users = {}

        # Поиск по username
        username_query = db.collection("users").where("username_lower", ">=", query_lower).where("username_lower", "<=", query_lower + "\uf8ff").stream()
        for user in username_query:
            data = user.to_dict()
            matched_users[user.id] = {
                "id": user.id,
                "username": data.get("username", ""),
                "email": data.get("email", "")
            }

        # Поиск по email
        email_query = db.collection("users").where("email_lower", ">=", query_lower).where("email_lower", "<=", query_lower + "\uf8ff").stream()
        for user in email_query:
            if user.id not in matched_users:
                data = user.to_dict()
                matched_users[user.id] = {
                    "id": user.id,
                    "username": data.get("username", ""),
                    "email": data.get("email", "")
                }

        return default_response(list(matched_users.values()), 200)

    except Exception as e:
        return default_error_response(str(e), 500)


# Добавление нового юзера в allowedUsers
def add_allowed_user(data, db):
    try:
        user_id = g.user.get("uid")

        # Валидация пользователя
        user_error = validate_user(user_id, db)
        if user_error:
            return user_error

        event_id = data.get("eventId")
        adding_user_id = data.get("addingUserId")

        if not event_id or not adding_user_id:
            return validation_error_response("Missing eventId or adding_user_id", 400)

        # Валидация события
        event_doc = validate_event(event_id, db)
        if isinstance(event_doc, dict):  # Ошибка
            return event_doc

        # Валидация прав
        permission_error = validate_permission(user_id, event_doc, db)
        if permission_error:
            return permission_error

        event_data = event_doc.to_dict()

        # Проверка, есть ли уже такой пользователь в allowedUsers
        current_allowed_users = event_data.get("allowedUsers", [])
        if any(user.get("id") == adding_user_id for user in current_allowed_users):
            return default_response({"message": "User is already allowed"}, 200)

        # Получение данных нового пользователя
        new_user_doc = db.collection("users").document(adding_user_id).get()
        if not new_user_doc.exists:
            return validation_error_response("User to add not found", 404)

        new_user_data = new_user_doc.to_dict()
        # Можно уточнить какие поля вы хотите добавлять в allowedUsers
        new_user = {
            "id": adding_user_id,
            "email": new_user_data.get("email", ""),
            "username": new_user_data.get("username", ""),
        }

        current_allowed_users.append(new_user)

        # Обновляем только поле allowedUsers
        event_doc.reference.update({
            "allowedUsers": current_allowed_users,
            "updated": datetime.utcnow()
        })

        return default_response({"message": "User added to allowedUsers"}, 200)

    except ValidationError as e:
        return validation_error_response(str(e.errors()), 400)

    except Exception as e:
        return default_error_response(str(e), 500)

def remove_allowed_user(data, db):
    try:
        user_id = g.user.get("uid")

        # Валидация пользователя
        user_error = validate_user(user_id, db)
        if user_error:
            return user_error

        event_id = data.get("eventId")
        removing_user_id = data.get("removingUserId")

        if not event_id or not removing_user_id:
            return validation_error_response("Missing eventId or removingUserId", 400)

        # Валидация события
        event_doc = validate_event(event_id, db)
        if isinstance(event_doc, dict):  # Ошибка
            return event_doc

        # Валидация прав
        permission_error = validate_permission(user_id, event_doc, db)
        if permission_error:
            return permission_error

        event_data = event_doc.to_dict()

        current_allowed_users = event_data.get("allowedUsers", [])
        # Проверка, есть ли такой пользователь
        if not any(user.get("id") == removing_user_id for user in current_allowed_users):
            return validation_error_response("User not found in allowedUsers", 404)

        # Удаление пользователя
        updated_allowed_users = [
            user for user in current_allowed_users if user.get("id") != removing_user_id
        ]

        # Обновляем только поле allowedUsers
        event_doc.reference.update({
            "allowedUsers": updated_allowed_users,
            "updated": datetime.utcnow()
        })

        return default_response({"message": "User removed from allowedUsers"}, 200)

    except ValidationError as e:
        return validation_error_response(str(e.errors()), 400)

    except Exception as e:
        return default_error_response(str(e), 500)
