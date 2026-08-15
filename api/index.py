import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import yt_dlp


class handler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):

        params = parse_qs(urlparse(self.path).query)
        video_id = params.get("id", [None])[0]

        if not video_id:
            self.send_json({
                "error": "Missing YouTube video ID",
                "example": "/?id=ANcPW7zP3eI"
            }, 400)
            return

        youtube_url = f"https://www.youtube.com/watch?v={video_id}"

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,

            # Audio only
            "format": "bestaudio",

            # Explicitly do NOT use cookies
            "cookiefile": None,

            # Anonymous client
            "extractor_args": {
                "youtube": {
                    "player_client": ["android_vr"]
                }
            }
        }

        try:

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(
                    youtube_url,
                    download=False
                )

            # Find audio-only streams
            audio_formats = []

            for f in info.get("formats", []):

                if not f.get("url"):
                    continue

                # No video
                if f.get("vcodec") != "none":
                    continue

                # Must contain audio
                if f.get("acodec") == "none":
                    continue

                audio_formats.append(f)

            if not audio_formats:
                self.send_json({
                    "error": "No audio-only stream found",
                    "id": video_id
                }, 404)
                return

            # Sort from LOWEST bitrate to highest
            audio_formats.sort(
                key=lambda f: (
                    f.get("abr") or 999999,
                    f.get("tbr") or 999999
                )
            )

            # Lowest bitrate audio stream
            audio = audio_formats[0]

            self.send_json({
                "success": True,
                "id": video_id,
                "title": info.get("title"),
                "audio_url": audio.get("url"),
                "format_id": audio.get("format_id"),
                "extension": audio.get("ext"),
                "codec": audio.get("acodec"),
                "bitrate": audio.get("abr"),
                "sample_rate": audio.get("asr")
            })

        except Exception as e:

            self.send_json({
                "success": False,
                "id": video_id,
                "error": str(e)
            }, 500)
