from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import yt_dlp


class handler(BaseHTTPRequestHandler):

    def do_GET(self):

        try:
            query = parse_qs(
                urlparse(self.path).query
            )

            playlist_id = query.get("id", [None])[0]

            if not playlist_id:
                self.send_json(
                    400,
                    {
                        "error": "Missing playlist ID",
                        "usage": "/?id=PLAYLIST_ID"
                    }
                )
                return

            playlist_url = (
                "https://www.youtube.com/playlist?list="
                + playlist_id
            )

            options = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "skip_download": True,
                "ignoreerrors": True
            }

            with yt_dlp.YoutubeDL(options) as ydl:

                info = ydl.extract_info(
                    playlist_url,
                    download=False
                )

            videos = []

            for item in info.get("entries", []):

                if not item:
                    continue

                video_id = item.get("id")

                if not video_id:
                    continue

                videos.append({
                    "id": video_id,
                    "title": item.get("title"),
                    "url": (
                        "https://www.youtube.com/watch?v="
                        + video_id
                    ),
                    "thumbnail": (
                        "https://i.ytimg.com/vi/"
                        + video_id
                        + "/hqdefault.jpg"
                    )
                })

            result = {
                "playlist": {
                    "id": info.get("id"),
                    "title": info.get("title"),
                    "description": info.get("description"),
                    "channel": info.get("channel"),
                    "thumbnail": info.get("thumbnail")
                },
                "videos": videos
            }

            self.send_json(200, result)

        except Exception as e:

            self.send_json(
                500,
                {
                    "error": str(e)
                }
            )


    def send_json(self, status, data):

        output = json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.end_headers()

        self.wfile.write(output)
