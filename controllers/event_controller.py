from flask import jsonify, request, g
from pydantic import ValidationError
from models.event import EventCreate, EventUpdate
from services.exception_handler import default_error_response, validation_error_response
from services.response_handler import default_response
from datetime import datetime

def add_event(data, db):
    try:
        # Получаем userId из контекста (декодированного токена)
        user_id = g.user.get("uid")

        if not user_id:
            return default_error_response("User ID not found", 400)

        # Проверяем, существует ли пользователь в коллекции users
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return default_error_response("User not found in Firestore", 404)

        # Добавляем userId (из Firestore, который равен UID Firebase) в данные события
        data['userId'] = user_id

        # Добавляем текущую дату и время для created
        data['created'] = datetime.utcnow()

        # Валидация данных с использованием модели Pydantic
        event_data = EventCreate(**data)

        # Добавление документа в коллекцию "events"
        db.collection('events').add(event_data.dict())

        # Возвращаем успешный ответ
        return default_response({"message": "Event added successfully"}, 200)

    except ValidationError as e:
        print("Ошибка валидации при попытке добавить event:", e)
        return validation_error_response(str(e.errors()), 400)

    except Exception as e:
        print("Ошибка при попытке добавить event")
        return default_error_response(str(e), 500)

def get_events(data, db):  # data, db параметры можно оставить для дальнейшей логики, если нужно
    try:
        # Получаем userId из контекста (декодированного токена)
        user_id = g.user.get("uid")

        if not user_id:
            return default_error_response("User ID not found", 400)

        # Проверяем, существует ли пользователь в коллекции users
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return default_error_response("User not found in Firestore", 404)

         # Получаем все события, принадлежащие текущему пользователю
        events_ref = db.collection('events')
        events_query = events_ref.where("userId", "==", user_id)  # Фильтруем события по userId
        docs = events_query.stream()

        events = []
        # Проходим по всем отфильтрованным документам и добавляем их в список
        for doc in docs:
            event_data = doc.to_dict()  # Получаем данные документа как словарь
            event_data["id"] = doc.id  # Добавляем id документа в данные ивента

            guest_ids = event_data.get("guests", [])

            guests = []

            for guest_id in guest_ids:
                guest_doc = db.collection("guests").document(guest_id).get()
                if guest_doc.exists:
                    guest_data = guest_doc.to_dict()
                    guest_data["id"] = guest_doc.id  # Добавляем id напитка
                    guests.append(guest_data)  # Добавляем полную информацию о напитке

            event_data["guests"] = guests
            events.append(event_data)  # Добавляем данные ивента в список

        # Возвращаем список пользователей как JSON
        return jsonify(events), 200

    except Exception as e:
        print("Ошибка при попытке получить events:", e)
        return default_error_response(str(e), 500)

def get_event_by_id(data, db):  
    try:
        # Получаем eventId из переданных данных
        event_id = data.get("eventId")
        if not event_id:
            return default_error_response("Event ID is required"), 400

        # Получаем документ с указанным eventId
        event_ref = db.collection('events').document(event_id)
        event_doc = event_ref.get()

        if not event_doc.exists:
            return default_error_response("Event not found"), 400

        # Получаем данные события
        event_data = event_doc.to_dict()
        event_data["id"] = event_doc.id  # Добавляем id документа в данные события

        # Получаем гостей, связанных с этим событием
        guest_ids = event_data.get("guests", [])
        guests = []

        for guest_id in guest_ids:
            guest_doc = db.collection("guests").document(guest_id).get()
            if guest_doc.exists:
                guest_data = guest_doc.to_dict()
                guest_data["id"] = guest_doc.id  # Добавляем id гостя
                guests.append(guest_data)  # Добавляем полную информацию о госте

        event_data["guests"] = guests

        # Возвращаем данные события
        return jsonify(event_data), 200

    except Exception as e:
        print("Ошибка при попытке получить event_by_id:", e)
        return default_error_response(str(e), 500)



def delete_event(data, db):
    try:
        # Получаем userId из контекста (декодированного токена)
        user_id = g.user.get("uid")

        if not user_id:
            return default_error_response("User ID not found", 400)

        # Проверяем, существует ли пользователь в коллекции users
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return default_error_response("User not found in Firestore", 404)

        # Получаем событие по id
        event_ref = db.collection('events').document(data['eventId'])
        event_doc = event_ref.get()

        # Проверяем, существует ли событие с таким id и принадлежит ли оно пользователю
        if not event_doc.exists:
            return default_error_response("Event not found", 404)

        event_data = event_doc.to_dict()
        if event_data.get("userId") != user_id:
            return default_error_response("You do not have permission to delete this event", 403)

        # Удаляем всех гостей, у которых eventId совпадает с переданным
        guests_ref = db.collection('guests')
        guests_query = guests_ref.where("eventId", "==", data['eventId'])  # Фильтруем гостей по eventId
        guests_docs = guests_query.stream()

        for guest in guests_docs:
            guest_ref = guests_ref.document(guest.id)
            guest_ref.delete()  # Удаляем гостя

        # Удаляем событие
        event_ref.delete()

        # Возвращаем успешный ответ
        return default_response("Event deleted successfully", 200)

    except Exception as e:
        print("Ошибка при попытке удалить event:", e)
        return default_error_response(str(e), 500)


def update_event(data, db):
    try:
        # Получаем userId из контекста (декодированного токена)
        user_id = g.user.get("uid")

        if not user_id:
            return default_error_response("User ID not found", 400)

        # Проверяем, существует ли пользователь в коллекции users
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return default_error_response("User not found in Firestore", 404)

        # Извлекаем eventId из data
        event_id = data.get("eventId")
        if not event_id:
            return default_error_response("Event ID is required", 400)

        # Проверяем, существует ли событие с указанным ID
        event_doc_ref = db.collection('events').document(event_id)
        event_doc = event_doc_ref.get()
        if not event_doc.exists:
            return default_error_response("Event not found", 404)

        # Проверяем, что текущий пользователь имеет доступ к этому событию
        if event_doc.to_dict().get("userId") != user_id:
            return default_error_response("Access denied: You do not own this event", 403)

        # Удаляем eventId из данных, чтобы не обновлять это поле
        data.pop("eventId", None)

        # Добавляем обновленное время
        data['updated'] = datetime.utcnow()

        # Валидация данных с использованием модели Pydantic
        event_data = EventUpdate(**data)  # Используйте EventUpdate для валидации обновляемых данных

        # Обновляем документ в коллекции "events"
        event_doc_ref.update(event_data.dict(exclude_unset=True))

        # Возвращаем успешный ответ
        return default_response({"message": "Event updated successfully"}, 200)

    except ValidationError as e:
        print("Ошибка валидации при попытке обновить event:", e)
        return validation_error_response(str(e.errors()), 400)

    except Exception as e:
        print("Ошибка при попытке обновить event:", e)
        return default_error_response(str(e), 500)


def get_event_designs(data, db):  # data, db параметры можно оставить для дальнейшей логики, если нужно
    try:
        # Получаем всех пользователей из Firebase Authentication
        designs = []
              
         # Получаем все документы из коллекции "events"
        designs_ref = db.collection('designs')  # Замените 'events' на название вашей коллекции
        design_docs = designs_ref.stream()
        
         # Проходим по всем документам и добавляем их в список
        for doc in design_docs:
            desig_data = doc.to_dict()  # Получаем данные документа как словарь
            desig_data["id"] = doc.id  # Добавляем id документа в данные ивента
            designs.append(desig_data)  # Добавляем данные ивента в список

        # Возвращаем список пользователей как JSON
        return jsonify(designs), 200

    except Exception as e:
        print("Ошибка при попытке получить designs:", e)
        return default_error_response(str(e), 500)

   