from flask import Blueprint, request, jsonify, current_app, g
from .guest_controller import add_guest, get_guests, get_drinks, get_visit_sts
from .event_controller import add_event, get_events, get_event_by_id, delete_event, update_event, get_event_designs
from auth.utils import authenticate_request

guest_routes = Blueprint('guests', __name__)
event_routes = Blueprint('events', __name__)

# Маршрут для добавления гостя
@guest_routes.route('/api/guests/add', methods=['POST'])
def add_guest_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return add_guest(request.json, db)  # Передаем db как аргумент

# Маршрут для получения списка гостей
@guest_routes.route('/api/guests/list', methods=['POST'])
@authenticate_request
def get_guests_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return get_guests(request.json, db)  # Передаем request.json как аргумент


@guest_routes.route('/api/guests/drinks', methods=['POST'])
@authenticate_request
def get_drinks_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return get_drinks(request.json, db)  # Передаем request.json как аргумент

@guest_routes.route('/api/guests/visit_sts', methods=['POST'])
@authenticate_request
def get_visit_sts_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return get_visit_sts(request.json, db)  # Передаем request.json как аргумент

# Маршрут для добавления event
@event_routes.route('/api/events/add', methods=['POST'])
@authenticate_request
def add_event_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    if not hasattr(g, 'user'):
        return jsonify({"error": "User not authenticated"}), 401
    return add_event(request.json, db)  # Передаем db как аргумент

# Маршрут для получения списка events
@event_routes.route('/api/events/list', methods=['POST'])
@authenticate_request
def get_events_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return get_events(request.json, db)  # Передаем request.json как аргумент

# Маршрут для получения списка events
@event_routes.route('/api/events/id', methods=['POST'])
def get_event_by_id_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return get_event_by_id(request.json, db)  # Передаем request.json как аргумент

# Маршрут для удаления event
@event_routes.route('/api/events/delete', methods=['POST'])
@authenticate_request
def delete_event_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return delete_event(request.json, db)  # Передаем request.json как аргумент

# Маршрут для обновленния event
@event_routes.route('/api/events/update', methods=['POST'])
@authenticate_request
def update_event_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return update_event(request.json, db)  # Передаем request.json как аргумент

@event_routes.route('/api/events/designs', methods=['POST'])
@authenticate_request
def get_event_designs_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return get_event_designs(request.json, db)  # Передаем request.json как аргумент