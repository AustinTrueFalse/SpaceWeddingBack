from flask import Blueprint, request, jsonify, current_app, g
from .guest_controller import add_guest, add_guest_auth, update_guest, update_guest_list, delete_guest, get_guests, get_drinks, get_tags, get_visit_sts
from .event_controller import add_event, update_todo, get_events, get_event_by_id, delete_event, update_event, get_event_designs
from .playlist_controller import add_playlist, get_playlists, get_playlist_by_id, delete_playlist, update_playlist  # Добавьте этот импорт
from .users_controller import add_allowed_user, search_users, remove_allowed_user
from .yandex_parser import parse_yandex_music_track
from .youtube_parser import parse_youtube_track
from .spotify_parser import parse_spotify_track


from auth.utils import authenticate_request

guest_routes = Blueprint('guests', __name__)
event_routes = Blueprint('events', __name__)
music_routes = Blueprint('music', __name__)
playlist_routes = Blueprint('playlists', __name__)

# Маршрут для добавления гостя c проверкой юзера
@guest_routes.route('/api/guests/add_auth', methods=['POST'])
@authenticate_request
def add_guest_auth_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return add_guest_auth(request.json, db)  # Передаем db как аргумент

# Маршрут для добавления гостя
@guest_routes.route('/api/guests/add', methods=['POST'])
def add_guest_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return add_guest(request.json, db)  # Передаем db как аргумент

# Маршрут для обновления гостя
@guest_routes.route('/api/guests/update', methods=['POST'])
@authenticate_request
def update_guest_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return update_guest(request.json, db)  # Передаем db как аргумент

# Маршрут для обновления списка гостей
@guest_routes.route('/api/guests/update_list', methods=['POST'])
@authenticate_request
def update_guest_list_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return update_guest_list(request.json, db)  # Передаем db как аргумент

# Маршрут для удаления гостя
@guest_routes.route('/api/guests/delete', methods=['POST'])
@authenticate_request
def delete_guest_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return delete_guest(request.json, db)  # Передаем db как аргумент

# Маршрут для получения списка гостей
@guest_routes.route('/api/guests/list', methods=['POST'])
@authenticate_request
def get_guests_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return get_guests(request.json, db)  # Передаем request.json как аргумент

# Маршрут для получения словаря напитков
@guest_routes.route('/api/guests/drinks', methods=['POST'])
@authenticate_request
def get_drinks_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return get_drinks(db)  # Передаем request.json как аргумент

# Маршрут для получения словаря тэгов
@guest_routes.route('/api/guests/tags', methods=['POST'])
@authenticate_request
def get_tags_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return get_tags(db)  # Передаем request.json как аргумент


@guest_routes.route('/api/guests/visit_sts', methods=['POST'])
@authenticate_request
def get_visit_sts_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return get_visit_sts(db)  # Передаем request.json как аргумент

# Маршрут для добавления event
@event_routes.route('/api/events/add', methods=['POST'])
@authenticate_request
def add_event_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    if not hasattr(g, 'user'):
        return jsonify({"error": "User not authenticated"}), 401
    return add_event(request.json, db)  # Передаем db как аргумент

# Маршрут для добавления todo
@event_routes.route('/api/events/update_todo', methods=['POST'])
@authenticate_request
def update_todo_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return update_todo(request.json, db)  # Передаем db как аргумент


# Маршрут для получения списка events
@event_routes.route('/api/events/list', methods=['POST'])
@authenticate_request
def get_events_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return get_events(db)  # Передаем request.json как аргумент

# Маршрут для получения event по id
@event_routes.route('/api/events/id', methods=['POST'])
@authenticate_request
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
    return get_event_designs(db)  # Передаем request.json как аргумент

# Маршрут для добавление нового пользователя в событие
@event_routes.route('/api/users/add_allowed_user', methods=['POST'])
@authenticate_request
def add_allowed_user_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return add_allowed_user(request.json, db)  # Передаем request.json как аргумент

# Маршрут для поиска юзеров по email/username
@event_routes.route('/api/users/search_users', methods=['POST'])
@authenticate_request
def search_users_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return search_users(request.json, db)  # Передаем request.json как аргумент

# Маршрут для добавление нового пользователя в событие
@event_routes.route('/api/users/remove_allowed_user', methods=['POST'])
@authenticate_request
def remove_allowed_user_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return remove_allowed_user(request.json, db)  # Передаем request.json как аргумент

# Маршрут для парсинга трека с Яндекс.Музыки
@music_routes.route('/api/music/parse_yandex', methods=['POST'])
@authenticate_request
def parse_yandex_music_track_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return parse_yandex_music_track(request.json)  # Передаем request.json как аргумент

# Маршрут для парсинга трека с YouTube
@music_routes.route('/api/music/parse_youtube', methods=['POST'])
@authenticate_request
def parse_youtube_trackroute():
    db = current_app.db  # Получаем объект db из текущего приложения
    return parse_youtube_track(request.json)  # Передаем request.json как аргумент


# Маршрут для парсинга трека с YouTube
@music_routes.route('/api/music/parse_spotify', methods=['POST'])
@authenticate_request
def parse_spotify_trackroute():
    db = current_app.db  # Получаем объект db из текущего приложения
    return parse_spotify_track(request.json)  # Передаем request.json как аргумент

# Маршрут для добавления плейлиста
@playlist_routes.route('/api/playlists/add', methods=['POST'])
@authenticate_request
def add_playlist_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    if not hasattr(g, 'user'):
        return jsonify({"error": "User not authenticated"}), 401
    return add_playlist(request.json, db)  # Передаем db как аргумент

# Маршрут для получения списка плейлистов
@playlist_routes.route('/api/playlists/list', methods=['POST'])
@authenticate_request
def get_playlists_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return get_playlists(db)  # Передаем request.json как аргумент

# Маршрут для получения плейлиста по id
@playlist_routes.route('/api/playlists/id', methods=['POST'])
def get_playlist_by_id_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return get_playlist_by_id(request.json, db)  # Передаем request.json как аргумент

# Маршрут для удаления плейлиста
@playlist_routes.route('/api/playlists/delete', methods=['POST'])
@authenticate_request
def delete_playlist_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return delete_playlist(request.json, db)  # Передаем request.json как аргумент

# Маршрут для обновления плейлиста
@playlist_routes.route('/api/playlists/update', methods=['POST'])
@authenticate_request
def update_playlist_route():
    db = current_app.db  # Получаем объект db из текущего приложения
    return update_playlist(request.json, db)  # Передаем request.json как аргумент