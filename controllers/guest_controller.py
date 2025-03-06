from flask import jsonify, request
from pydantic import ValidationError
from models.guest import GuestCreate
from models.drink import Drink
from services.exception_handler import default_error_response, validation_error_response
from services.response_handler import default_response
import firebase_admin
from firebase_admin import credentials, auth
from datetime import datetime
from google.cloud.firestore import ArrayUnion


def add_guest(data, db):
    try:
        # Добавляем текущую дату и время для created
        data['created'] = datetime.utcnow()

        # Получаем ссылку на документ события
        event_ref = db.collection('events').document(data['eventId'])
        event_doc = event_ref.get()

        if not event_doc.exists:
            return validation_error_response("Event not found", 404)

        # Проверяем, есть ли гость с таким номером телефона в этом событии
        event_data = event_doc.to_dict()
        existing_guests = event_data.get('guests', [])
        
        for guest_id in existing_guests:
            # Получаем документ гостя по его ID
            guest_ref = db.collection('guests').document(guest_id)
            guest_doc = guest_ref.get()
            
            if guest_doc.exists:
                guest_data = guest_doc.to_dict()
                # Если номер телефона совпадает, то возвращаем ошибку
                if guest_data.get('guestPhone') == data['guestPhone']:
                    return default_error_response("Guest with this phone number already exists in the event", 400)

       

        # Валидация данных с использованием модели Pydantic
        guest_data = GuestCreate(**data)

        # Добавление документа в коллекцию "guests"
        guests_ref = db.collection('guests')
        guest_doc_ref = guests_ref.add(guest_data.dict())  # Firestore генерирует id
        guest_id = guest_doc_ref[1].id  # Получение сгенерированного id

        # Добавляем только id гостя в массив гостей события
        event_ref.update({
            'guests': ArrayUnion([guest_id])  # ArrayUnion используется для добавления уникальных значений
        })

        # Возвращаем успешный ответ
        return default_response({"message": "Guest added successfully", "guestId": guest_id}, 200)

    except ValidationError as e:
        print("Ошибка валидации при попытке добавить guest:", e)
        return validation_error_response(str(e.errors()), 400)

    except Exception as e:
        print("Ошибка при попытке добавить guest:", e)
        return default_error_response(str(e), 500)



def get_guests(data, db):
    try:
        # Получаем гостей по айди ивента
        guests_ref = db.collection('guests')
        guests_query = guests_ref.where("eventId", "==", data['eventId'])
        guests_docs = guests_query.stream()

        guests = []
        # Проходим по всем отфильтрованным документам и добавляем их в список
        for doc in guests_docs:
            guest_data = doc.to_dict()  # Получаем данные документа как словарь
            guest_data["id"] = doc.id  # Добавляем id документа в данные гостя

            # Получение идентификаторов напитков гостя
            guest_drinks_ids = guest_data.get("guestDrinks", [])  # Список id напитков
            
            # Получение полной информации о напитках
            guest_drinks = []
            for drink_id in guest_drinks_ids:
                drink_doc = db.collection('drinks').document(drink_id).get()  # Получаем документ напитка
                if drink_doc.exists:
                    drink_data = drink_doc.to_dict()
                    # drink_data["id"] = drink_doc.id  # Добавляем id напитка
                    guest_drinks.append(drink_data)  # Добавляем полную информацию о напитке

            guest_data["guestDrinks"] = guest_drinks  # Заменяем id напитков на полные данные

            guests.append(guest_data)  # Добавляем данные гостя в список

        # Возвращаем список гостей как JSON
        return jsonify(guests), 200

    except Exception as e:
        print("Ошибка при попытке получить guests:", e)
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


   