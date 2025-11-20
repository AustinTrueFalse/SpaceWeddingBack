from flask import jsonify
try:
    from spotapi import Song
except ImportError:
    Song = None  # если пакет не установлен

class TrackInfo:
    def __init__(self, title, artists, url, image_url, source):
        self.title = title
        self.artists = artists
        self.url = url
        self.image_url = image_url
        self.source = source

    def dict(self):
        return {
            "title": self.title,
            "artists": self.artists,
            "url": self.url,
            "image_url": self.image_url,
            "source": self.source
        }

def default_error_response(message, code):
    return jsonify({"error": message}), code

def parse_spotify_track(query_or_url):
    try:
        if not query_or_url:
            return jsonify({"error": "URL or search query is required"}), 400

        if Song is None:
            return default_error_response("SpotAPI не установлен", 500)

        song_client = Song()
        print("[INFO] Song client initialized")

        # Определяем track ID из URL
        track_id = None
        if "open.spotify.com/track/" in query_or_url:
            track_id = query_or_url.split("track/")[1].split("?")[0]
        elif "spotify:track:" in query_or_url:
            track_id = query_or_url.split("spotify:track:")[1]

        # Всегда используем query_songs, чтобы не падало
        if track_id:
            print(f"[INFO] Searching track by ID via query_songs: {track_id}")
            result = song_client.query_songs(track_id, limit=1)
        else:
            print(f"[INFO] Searching track by query: {query_or_url}")
            result = song_client.query_songs(query_or_url, limit=1)

        print(f"[INFO] Raw search result: {result}")

        items = result.get("data", {}).get("searchV2", {}).get("tracksV2", {}).get("items", [])
        print(f"[INFO] Items extracted: {items}")

        if not items:
            return default_error_response("Трек не найден", 404)

        track_data = items[0].get("item", {}).get("data", {})
        print(f"[INFO] Track data extracted: {track_data}")

        # Название трека
        title = track_data.get("name", "Неизвестно")
        print(f"[INFO] Track title: {title}")

        # Артисты
        artists_list = track_data.get("artists", [])
        artists = []
        for a in artists_list:
            name = a.get("profile", {}).get("name")
            if name:
                artists.append(name)
        if not artists:
            artists = ["Неизвестен"]
        print(f"[INFO] Artists: {artists}")

        # Обложка альбома
        image_url = ""
        album_data = track_data.get("albumOfTrack", {})
        cover_sources = album_data.get("coverArt", {}).get("sources", [])
        if cover_sources and len(cover_sources) > 0:
            image_url = cover_sources[0].get("url", "")
        print(f"[INFO] Image URL: {image_url}")

        track_info = TrackInfo(
            title=title,
            artists=artists,
            url=query_or_url,
            image_url=image_url,
            source="spotify"
        )

        return jsonify(track_info.dict())

    except Exception as e:
        print(f"[ERROR] Exception caught: {str(e)}")
        return default_error_response(f"Ошибка парсинга Spotify: {str(e)}", 500)
