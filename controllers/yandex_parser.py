import re
import json
import requests
from flask import jsonify
from models.track import TrackInfo
from services.exception_handler import default_error_response


import re
import json
import requests
from flask import jsonify
from models.track import TrackInfo
from services.exception_handler import default_error_response


def parse_yandex_music_track(url):
    try:
        if not url:
            return jsonify({"error": "URL is required"}), 400

        # Извлекаем ID трека
        match = re.search(r"/track/(\d+)", url)
        if not match:
            return jsonify({"error": "Invalid Yandex Music track URL"}), 400

        track_id = match.group(1)

        # API Яндекс.Музыки
        api_url = f"https://music.yandex.ru/handlers/track.jsx?track={track_id}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/plain, */*"
        }

        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Парсим JSON
        track = data.get("track", {})

        title = track.get("title", "Неизвестно")
        image_url = ""

        # Обложка
        cover_uri = track.get("coverUri")
        if cover_uri:
            image_url = cover_uri.replace("%%", "300x300")

        # Артист
        artist = "Неизвестен"
        if track.get("artists"):
            artist = track["artists"][0].get("name", artist)

        # Ответ
        track_info = TrackInfo(
            title=title,
            artist=artist,
            url=url,
            image_url=image_url,
            source="yandex_music"
        )

        return jsonify(track_info.dict())

    except Exception as e:
        return default_error_response(f"Ошибка парсинга: {str(e)}", 500)
