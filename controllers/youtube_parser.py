import re
import json
import requests
from flask import jsonify
from models.track import TrackInfo
from services.exception_handler import default_error_response


def parse_youtube_track(url):
    try:
        if not url:
            return jsonify({"error": "URL is required"}), 400

        # oEmbed URL
        api_url = f"https://www.youtube.com/oembed?url={url}&format=json"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        title = data.get("title", "Неизвестно")
        artist = data.get("author_name", "Неизвестен")
        image_url = data.get("thumbnail_url", "")

        # Если хотим 1080p thumbnail
        # Меняем default → maxresdefault
        if image_url:
            image_url = re.sub(r"/[^/]+\.jpg$", "/maxresdefault.jpg", image_url)

        track_info = TrackInfo(
            title=title,
            artist=artist,
            url=url,
            image_url=image_url,
            source="youtube"
        )

        return jsonify(track_info.dict())

    except Exception as e:
        return default_error_response(f"Ошибка парсинга YouTube: {str(e)}", 500)
