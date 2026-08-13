from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import yt_dlp


class handler(BaseHTTPRequestHandler):

    def do_GET(self):

        try:
            # Read ?id= from URL
            query = parse_qs(
                urlparse(self.path).query
            )

            video_id = query.get("id", [None])[0]

            if not video_id:
                self.send_json(
                    400,
                    {
                        "error": "Missing id",
                        "usage": "/?id=YOUTUBE_VIDEO_ID"
                    }
                )
                return

            video_url = (
                "https://www.youtube.com/watch?v="
                + video_id
            )

            options = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(
                    video_url,
                    download=False
                )

            result = {
                "id": video_id,
                "title": info.get("title"),
                "artist": (
                    info.get("channel")
                    or info.get("uploader")
                ),
                "duration": info.get("duration"),
                "cover": (
                    "https://i.ytimg.com/vi/"
                    + video_id
                    + "/hqdefault.jpg"
                ),
                "youtubeUrl": video_url
            }

            self.send_json(
                200,
                result
            )

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
