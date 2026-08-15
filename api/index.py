from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import yt_dlp
import json


class handler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        video_id = params.get("id", [None])[0]

        if not video_id:
            self.send_json({
                "error": "Missing id parameter",
                "example": "/?id=dQw4w9WgXcQ"
            }, 400)
            return

        # YouTube video URL from ID
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,

            # Audio only
            "format": "bestaudio/best",

            # Don't download the file
            "skip_download": True,

            # Avoid playlist processing
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)

                # Find highest quality audio-only format
                audio_formats = [
                    f for f in info.get("formats", [])
                    if f.get("acodec") != "none"
                    and f.get("vcodec") == "none"
                    and f.get("url")
                ]

                if not audio_formats:
                    self.send_json({
                        "error": "No audio-only stream found"
                    }, 404)
                    return

                # Highest bitrate audio
                audio_formats.sort(
                    key=lambda f: (
                        f.get("abr") or 0,
                        f.get("tbr") or 0
                    ),
                    reverse=True
                )

                audio = audio_formats[0]

                result = {
                    "id": video_id,
                    "title": info.get("title"),
                    "duration": info.get("duration"),
                    "thumbnail": info.get("thumbnail"),

                    "audio_url": audio.get("url"),

                    "format_id": audio.get("format_id"),
                    "extension": audio.get("ext"),
                    "acodec": audio.get("acodec"),
                    "abr": audio.get("abr"),
                    "sample_rate": audio.get("asr")
                }

                self.send_json(result)

        except Exception as e:
            self.send_json({
                "error": str(e)
            }, 500)
