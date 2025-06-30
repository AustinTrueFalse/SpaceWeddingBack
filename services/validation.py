from firebase_admin import auth
from google.cloud.firestore import ArrayUnion
from services.exception_handler import default_error_response

def validate_user(user_id, db):
    if not user_id:
        return default_error_response("User ID not found", 400)
    
    user_doc = db.collection('users').document(user_id).get()
    if not user_doc.exists:
        return default_error_response("User not found in Firestore", 404)
    
    return None

def validate_event(event_id, db):
    event_ref = db.collection('events').document(event_id)
    event_doc = event_ref.get()

    if not event_doc.exists:
        return default_error_response("Event not found", 404)

    return event_doc  # Возвращаем сам объект события, если оно найдено

def validate_permission(user_id, event_doc, db):
    if not user_id:
        return default_error_response("User ID not found", 400)
    # Проверяем наличие пользователя в Firestore
    user_doc = db.collection('users').document(user_id).get()
    if not user_doc.exists:
        return default_error_response("User not found in Firestore", 404)
    
    user_data = user_doc.to_dict()
    
    # Если пользователь админ, разрешаем доступ сразу
    if user_data.get("role") == "admin":
        return None

    print(user_id)

    # Проверяем разрешения на основе allowedUsers
    event_data = event_doc.to_dict()
    allowed_users = event_data.get("allowedUsers", [])

    print(user_id)

    if not any(user.get("id") == user_id for user in allowed_users):
        return default_error_response("Access denied: You do not have permission to edit this event", 403)

    return None

def validate_guest_phone(event_data, guest_phone, db):
    existing_guests = event_data.get('guests', [])
    
    for guest_id in existing_guests:
        guest_ref = db.collection('guests').document(guest_id)
        guest_doc = guest_ref.get()
        
        if guest_doc.exists:
            guest_data = guest_doc.to_dict()
            if guest_data.get('guestPhone') == guest_phone:
                return default_error_response("Guest with this phone number already exists in the event", 400)
    
    return None
