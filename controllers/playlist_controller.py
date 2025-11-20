from flask import jsonify, request, g
from pydantic import ValidationError
from models.track import PlaylistCreate, PlaylistUpdate
from services.exception_handler import default_error_response, validation_error_response
from services.response_handler import default_response
from datetime import datetime
from services.validation import validate_user, validate_playlist

# Основная логика добавления плейлиста
def add_playlist(data, db):
    try:
        user_id = g.user.get("uid")
        # Валидация пользователя
        user_error = validate_user(user_id, db)
        if user_error:
            return user_error

        playlist_data = PlaylistCreate(**data)
        db.collection('playlists').add(playlist_data.dict())

        return default_response({"message": "Playlist added successfully"}, 200)

    except ValidationError as e:
        return validation_error_response(str(e.errors()), 400)

    except Exception as e:
        return default_error_response(str(e), 500)

# Основная логика получения плейлистов
def get_playlists(db):
    try:
        user_id = g.user.get("uid")
        # Валидация пользователя
        user_error = validate_user(user_id, db)
        if user_error:
            return user_error

        playlists_ref = db.collection('playlists')
        docs = playlists_ref.stream()

        playlists = []
        for doc in docs:
            playlist_data = doc.to_dict()
            playlist_data["id"] = doc.id
            playlists.append(playlist_data)

        if playlists:
            return jsonify(playlists), 200
        else:
            return default_error_response("No playlists found", 404)

    except Exception as e:
        return default_error_response(str(e), 500)

# Логика получения плейлиста по ID
def get_playlist_by_id(data, db):
    try:

        playlist_id = data.get("playlistId")
        # Валидация плейлиста
        playlist_doc = validate_playlist(playlist_id, db)
        if isinstance(playlist_doc, dict):
            return playlist_doc

        playlist_data = playlist_doc.to_dict()
        playlist_data["id"] = playlist_doc.id

        return jsonify(playlist_data), 200

    except Exception as e:
        return default_error_response(str(e), 500)

# Логика удаления плейлиста
def delete_playlist(data, db):
    try:
        user_id = g.user.get("uid")
        # Валидация пользователя
        user_error = validate_user(user_id, db)
        if user_error:
            return user_error

        playlist_id = data.get("playlistId")
        # Валидация плейлиста
        playlist_doc = validate_playlist(playlist_id, db)
        if isinstance(playlist_doc, dict):
            return playlist_doc

        playlist_ref = db.collection('playlists').document(playlist_id)
        playlist_ref.delete()

        return default_response("Playlist deleted successfully", 200)

    except Exception as e:
        return default_error_response(str(e), 500)

# Логика обновления плейлиста
def update_playlist(data, db):
    try:
        user_id = g.user.get("uid")
        # Валидация пользователя
        user_error = validate_user(user_id, db)
        if user_error:
            return user_error

        playlist_id = data.get("id")

        # Валидация плейлиста
        playlist_doc = validate_playlist(playlist_id, db)
        if isinstance(playlist_doc, dict):
            return playlist_doc

        playlist_data = PlaylistUpdate(**data)

        playlist_doc_ref = db.collection('playlists').document(playlist_id)
        playlist_doc_ref.update(playlist_data.dict(exclude_unset=True))

        return default_response({"message": "Playlist updated successfully"}, 200)

    except ValidationError as e:
        return validation_error_response(str(e.errors()), 400)

    except Exception as e:
        return default_error_response(str(e), 500)