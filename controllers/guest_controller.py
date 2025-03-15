from flask import jsonify, request, g
from pydantic import ValidationError
from models.guest import GuestCreate, GuestUpdate
from models.drink import Drink
from services.exception_handler import default_error_response, validation_error_response
from services.response_handler import default_response
import firebase_admin
from firebase_admin import credentials, auth
from datetime import datetime
from google.cloud.firestore import ArrayUnion
from google.cloud import firestore
from services.validation import validate_user, validate_event, validate_permission, validate_guest_phone

def add_guest_auth(data, db):
    try:
        # Получаем userId из контекста (декодированного токена)
        user_id = g.user.get("uid")

        if not user_id:
            return default_error_response("User ID not found", 400)

        # Валидация пользователя
        user_error = validate_user(user_id, db)
        if user_error:
            return user_error

        # Добавляем текущую дату и время для created
        data['created'] = datetime.utcnow()

        # Валидация события
        event_doc = validate_event(data['eventId'], db)  # Теперь возвращаем сам event_doc
        if isinstance(event_doc, dict):  # Если ошибка, возвращаем ошибку
            return event_doc

        # Валидация разрешений пользователя для события
        permission_error = validate_permission(user_id, event_doc, db)
        if permission_error:
            return permission_error

        event_data = event_doc.to_dict()
        existing_guests = event_data.get('guests', [])

        for guest_id in existing_guests:
            guest_ref = db.collection('guests').document(guest_id)
            guest_doc = guest_ref.get()

            if guest_doc.exists:
                guest_data = guest_doc.to_dict()
                if guest_data.get('guestPhone') == data['guestPhone']:
                    return default_error_response("Guest with this phone number already exists in the event", 400)

        # Валидация данных с использованием модели Pydantic
        guest_data = GuestCreate(**data)

        # Добавление документа в коллекцию "guests"
        guests_ref = db.collection('guests')
        guest_doc_ref = guests_ref.add(guest_data.dict())  # Firestore генерирует id
        guest_id = guest_doc_ref[1].id  # Получение сгенерированного id

        # Добавляем только id гостя в массив гостей события
        db.collection('events').document(data['eventId']).update({
            'guests': ArrayUnion([guest_id])
        })

        return default_response({"message": "Guest added successfully", "guestId": guest_id}, 200)

    except ValidationError as e:
        return validation_error_response(str(e.errors()), 400)

    except Exception as e:
        return default_error_response(str(e), 500)


def add_guest(data, db):
    try:
        # Добавляем текущую дату и время для created
        data['created'] = datetime.utcnow()

        # Валидация события
        event_doc = validate_event(event_id, db)  # Теперь возвращаем сам документ события
        if isinstance(event_doc, dict):  # Если возвращен словарь с ошибкой
            return event_doc  # Возвращаем ошибку, если событие не найдено

        event_data = event_doc.to_dict()  # Преобразуем документ в словарь
        existing_guests = event_data.get('guests', [])

        for guest_id in existing_guests:
            guest_ref = db.collection('guests').document(guest_id)
            guest_doc = guest_ref.get()

            if guest_doc.exists:
                guest_data = guest_doc.to_dict()
                if guest_data.get('guestPhone') == data['guestPhone']:
                    return default_error_response("Guest with this phone number already exists in the event", 400)

        # Валидация данных с использованием модели Pydantic
        guest_data = GuestCreate(**data)

        # Добавление документа в коллекцию "guests"
        guests_ref = db.collection('guests')
        guest_doc_ref = guests_ref.add(guest_data.dict())  # Firestore генерирует id
        guest_id = guest_doc_ref[1].id  # Получение сгенерированного id

        # Добавляем только id гостя в массив гостей события
        db.collection('events').document(data['eventId']).update({
            'guests': ArrayUnion([guest_id])
        })

        return default_response({"message": "Guest added successfully", "guestId": guest_id}, 200)

    except ValidationError as e:
        return validation_error_response(str(e.errors()), 400)

    except Exception as e:
        return default_error_response(str(e), 500)



def update_guest(data, db):
    try:
        # Получаем userId из контекста (декодированного токена)
        user_id = g.user.get("uid")

        if not user_id:
            return default_error_response("User ID not found", 400)

        # Валидация пользователя
        user_error = validate_user(user_id, db)
        if user_error:
            return user_error

        guest_id = data.get("guestId")
        if not guest_id:
            return default_error_response("Guest ID is required", 400)

        # Проверка существования гостя
        guest_doc_ref = db.collection('guests').document(guest_id)
        guest_doc = guest_doc_ref.get()
        if not guest_doc.exists:
            return default_error_response("Guest not found", 404)

        guest_data = guest_doc.to_dict()
        event_id = guest_data.get("eventId")

        if not event_id:
            return default_error_response("Guest is not associated with any event", 400)


        # Валидация события
        event_doc = validate_event(event_id, db)  # Теперь возвращаем сам документ события
        if isinstance(event_doc, dict):  # Если возвращен словарь с ошибкой
            return event_doc  # Возвращаем ошибку, если событие не найдено

        event_data = event_doc.to_dict()  # Преобразуем документ в словарь

        # Валидация события
        # event_doc_ref = db.collection('events').document(event_id)
        # event_doc = event_doc_ref.get()
        # if not event_doc.exists:
        #     return default_error_response("Associated event not found", 404)

        # Валидация разрешений пользователя для события
        permission_error = validate_permission(user_id, event_doc, db)
        if permission_error:
            return permission_error

        # Удаляем guestId из данных, чтобы не обновлять это поле
        data.pop("guestId", None)

        # Добавляем обновленное время
        data['updated'] = datetime.utcnow()

        # Валидация данных с использованием модели Pydantic
        guest_update_data = GuestUpdate(**data)

        # Обновляем документ в коллекции "guests"
        guest_doc_ref.update(guest_update_data.dict(exclude_unset=True))

        return default_response({"message": "Guest updated successfully"}, 200)

    except ValidationError as e:
        return validation_error_response(str(e.errors()), 400)

    except Exception as e:
        return default_error_response(str(e), 500)


def delete_guest(data, db):
    try:
        guest_id = data.get("guestId")
        event_id = data.get("eventId")

        # Получаем userId из контекста (декодированного токена)
        user_id = g.user.get("uid")

        if not user_id:
            return default_error_response("User ID not found", 400)

        # Валидация пользователя
        user_error = validate_user(user_id, db)
        if user_error:
            return user_error

        if not guest_id or not event_id:
            return validation_error_response("Guest ID and Event ID are required", 400)

        # Валидация существования гостя
        guest_ref = db.collection("guests").document(guest_id)
        guest_doc = guest_ref.get()

        if not guest_doc.exists:
            return validation_error_response("Guest not found", 404)

        # Валидация события
        event_doc = validate_event(event_id, db)  # Теперь возвращаем сам документ события
        if isinstance(event_doc, dict):  # Если возвращен словарь с ошибкой
            return event_doc  # Возвращаем ошибку, если событие не найдено

        event_ref = db.collection("events").document(event_id)  # Создаем ссылку на документ события
        event_data = event_doc.to_dict()  # Преобразуем документ в словарь

        # Валидация разрешений пользователя для события
        permission_error = validate_permission(user_id, event_doc, db)
        if permission_error:
            return permission_error

        # Удаляем ID гостя из списка гостей события
        event_ref.update({
            "guests": firestore.ArrayRemove([guest_id])
        })

        # Удаляем самого гостя
        guest_ref.delete()

        return default_response({"message": "Guest deleted successfully"}, 200)

    except Exception as e:
        return default_error_response(str(e), 500)


def get_guests(data, db):
    try:
        event_id = data.get("eventId")
        # Валидация события
        event_doc = validate_event(event_id, db)  # Теперь возвращаем сам документ события
        if isinstance(event_doc, dict):  # Если возвращен словарь с ошибкой
            return event_doc  # Возвращаем ошибку, если событие не найдено

        event_data = event_doc.to_dict()  # Преобразуем документ в словарь


        # Получаем гостей по айди ивента
        guests_ref = db.collection("guests")
        guests_query = guests_ref.where("eventId", "==", event_id)
        guests_docs = guests_query.stream()

        guests = []
        # Проходим по всем отфильтрованным документам и добавляем их в список
        for doc in guests_docs:
            guest_data = doc.to_dict()  # Получаем данные документа как словарь
            guest_data["id"] = doc.id  # Добавляем id документа в данные гостя

            # Оставляем только массив строковых ID напитков
            guest_data["guestDrinks"] = [str(drink_id) for drink_id in guest_data.get("guestDrinks", [])]

            guests.append(guest_data)  # Добавляем данные гостя в список

        guests = sorted(guests, key=lambda g: g.get("created", ""), reverse=True)

        # Возвращаем список гостей
        return jsonify(guests), 200  # Возвращаем правильный JSON ответ

    except Exception as e:
        return default_error_response(str(e), 500)


def get_drinks(data, db):  # data, db параметры можно оставить для дальнейшей логики, если нужно
    try:
        # Получаем всех пользователей из Firebase Authentication
        drinks = []
              
         # Получаем все документы из коллекции "drinks"
        drinks_ref = db.collection('drinks')  # Замените 'events' на название вашей коллекции
        docs = drinks_ref.stream()
        
         # Проходим по всем документам и добавляем их в список
        for doc in docs:
            drink_data = doc.to_dict()  # Получаем данные документа как словарь
            drink_data["id"] = doc.id  # Добавляем id документа в данные ивента
            drinks.append(drink_data)  # Добавляем данные ивента в список

        # Возвращаем список пользователей как JSON
        return jsonify(drinks), 200

    except Exception as e:
        print("Ошибка при попытке получить drinks:", e)
        return default_error_response(str(e), 500)


def get_visit_sts(data, db):  # data, db параметры можно оставить для дальнейшей логики, если нужно
    try:
        # Получаем всех пользователей из Firebase Authentication
        visit_sts = []
              
         # Получаем все документы из коллекции "visitsts"
        visit_sts_ref = db.collection('visitsts')  # Замените 'events' на название вашей коллекции
        docs = visit_sts_ref.stream()
        
         # Проходим по всем документам и добавляем их в список
        for doc in docs:
            sts_data = doc.to_dict()  # Получаем данные документа как словарь
            sts_data["id"] = doc.id  # Добавляем id документа в данные ивента
            visit_sts.append(sts_data)  # Добавляем данные ивента в список

        # Возвращаем список пользователей как JSON
        return jsonify(visit_sts), 200

    except Exception as e:
        print("Ошибка при попытке получить visit_sts:", e)
        return default_error_response(str(e), 500)

   