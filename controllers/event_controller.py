from flask import jsonify, request, g
from pydantic import ValidationError
from models.event import EventCreate, EventUpdate
from models.todo import Todo
from services.exception_handler import default_error_response, validation_error_response
from services.response_handler import default_response
from datetime import datetime
from services.validation import validate_user, validate_event, validate_permission, validate_guest_phone

# Основная логика добавления события
def add_event(data, db):
    try:
        user_id = g.user.get("uid")
        # Валидация пользователя
        user_error = validate_user(user_id, db)
        if user_error:
            return user_error

        user_doc = db.collection('users').document(user_id).get()
        user_data = user_doc.to_dict()
        data['userId'] = user_id
        allowed_users = [{
            "id": user_id,
            "username": user_data.get("username"),
            "email": user_data.get("email"),
        }]
        data['allowedUsers'] = allowed_users
        data['created'] = datetime.utcnow()

        event_data = EventCreate(**data)
        db.collection('events').add(event_data.dict())

        return default_response({"message": "Event added successfully"}, 200)

    except ValidationError as e:
        return validation_error_response(str(e.errors()), 400)

    except Exception as e:
        return default_error_response(str(e), 500)

# Основная логика получения событий
def get_events(data, db):
    try:
        user_id = g.user.get("uid")
        # Валидация пользователя
        user_error = validate_user(user_id, db)
        if user_error:
            return user_error

        events_ref = db.collection('events')
        docs = events_ref.stream()

        events = []
        for doc in docs:
            event_data = doc.to_dict()
            event_data["id"] = doc.id
            allowed_users = event_data.get("allowedUsers", [])
            if any(user.get("id") == user_id for user in allowed_users):
                guest_ids = event_data.get("guests", [])
                guests = []
                for guest_id in guest_ids:
                    guest_doc = db.collection("guests").document(guest_id).get()
                    if guest_doc.exists:
                        guest_data = guest_doc.to_dict()
                        guest_data["id"] = guest_doc.id
                        guests.append(guest_data)
                event_data["guests"] = guests
                events.append(event_data)

        if events:
            return jsonify(events), 200
        else:
            return default_error_response("No events found for the user", 404)

    except Exception as e:
        return default_error_response(str(e), 500)



def get_event_by_id(data, db):
    try:
        event_id = data.get("eventId")
        # Валидация события
        event_doc = validate_event(event_id, db)  # Теперь возвращаем сам документ события
        if isinstance(event_doc, dict):  # Если возвращен словарь с ошибкой
            return event_doc  # Возвращаем ошибку, если событие не найдено

        event_data = event_doc.to_dict()  # Преобразуем документ в словарь
        event_data["id"] = event_doc.id

        guest_ids = event_data.get("guests", [])
        guests = []

        for guest_id in guest_ids:
            guest_doc = db.collection("guests").document(guest_id).get()
            if guest_doc.exists:
                guest_data = guest_doc.to_dict()  # Преобразуем гостя в словарь
                guest_data["id"] = guest_doc.id
                guests.append(guest_data)

        event_data["guests"] = sorted(guests, key=lambda g: g.get("created", ""), reverse=True)

        return jsonify(event_data), 200  # Возвращаем правильный JSON ответ

    except Exception as e:
        return default_error_response(str(e), 500)


# Логика удаления события
def delete_event(data, db):
    try:
        user_id = g.user.get("uid")
        # Валидация пользователя
        user_error = validate_user(user_id, db)
        if user_error:
            return user_error

        # Валидация события
        event_doc = validate_event(event_id, db)  # Теперь возвращаем сам документ события
        if isinstance(event_doc, dict):  # Если возвращен словарь с ошибкой
            return event_doc  # Возвращаем ошибку, если событие не найдено

        event_data = event_doc.to_dict()  # Преобразуем документ в словарь

        # Валидация прав доступа
        permission_error = validate_permission(user_id, event_doc, db)
        if permission_error:
            return permission_error

        guests_ref = db.collection('guests')
        guests_query = guests_ref.where("eventId", "==", data['eventId'])
        guests_docs = guests_query.stream()

        for guest in guests_docs:
            guest_ref = guests_ref.document(guest.id)
            guest_ref.delete()

        event_ref = db.collection('events').document(data['eventId'])
        event_ref.delete()

        return default_response("Event deleted successfully", 200)

    except Exception as e:
        return default_error_response(str(e), 500)


# Логика обновления события
def update_event(data, db):
    try:
        user_id = g.user.get("uid")
        # Валидация пользователя
        user_error = validate_user(user_id, db)
        if user_error:
            return user_error

        # Валидация события
        event_doc = validate_event(event_id, db)  # Теперь возвращаем сам документ события
        if isinstance(event_doc, dict):  # Если возвращен словарь с ошибкой
            return event_doc  # Возвращаем ошибку, если событие не найдено

        event_data = event_doc.to_dict()  # Преобразуем документ в словарь

        # Валидация прав доступа
        permission_error = validate_permission(user_id, event_doc, db)
        if permission_error:
            return permission_error

        data.pop("eventId", None)
        data['updated'] = datetime.utcnow()
        event_data = EventUpdate(**data)

        event_doc_ref = db.collection('events').document(data['eventId'])
        event_doc_ref.update(event_data.dict(exclude_unset=True))

        return default_response({"message": "Event updated successfully"}, 200)

    except ValidationError as e:
        return validation_error_response(str(e.errors()), 400)

    except Exception as e:
        return default_error_response(str(e), 500)



# Логика получения дизайнов
def get_event_designs(data, db):
    try:
        designs = []
        designs_ref = db.collection('designs')
        design_docs = designs_ref.stream()

        for doc in design_docs:
            desig_data = doc.to_dict()
            desig_data["id"] = doc.id
            designs.append(desig_data)

        return jsonify(designs), 200

    except Exception as e:
        return default_error_response(str(e), 500)

def update_todo(data, db):
    try:
        user_id = g.user.get("uid")

        # Валидация события
        event_doc = db.collection('events').document(data['eventId']).get()
        if not event_doc.exists:
            return default_error_response("Event not found", 404)

        # Валидация прав доступа
        permission_error = validate_permission(user_id, event_doc, db)
        if permission_error:
            return permission_error

        # Валидация входящего списка todo с Pydantic
        todo_list = [Todo(**todo).dict() for todo in data['todoList']]

        # Обновление списка todo в событии
        db.collection('events').document(data['eventId']).update({
            'todoList': todo_list
        })

        return default_response({"message": "Todo list updated successfully", "todoList": todo_list}, 200)

    except ValidationError as e:
        return validation_error_response(str(e.errors()), 400)

    except Exception as e:
        return default_error_response(str(e), 500)