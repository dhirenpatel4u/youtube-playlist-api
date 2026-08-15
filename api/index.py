import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import yt_dlp


class handler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):

        params = parse_qs(urlparse(self.path).query)
        video_id = params.get("id", [None])[0]

        if not video_id:
            self.send_json({
                "error": "Missing YouTube ID"
            }, 400)
            return

        youtube_url = f"https://www.youtube.com/watch?v={video_id}"

        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,

            # ONLY AUDIO
            "format": "bestaudio",

            # No cookies
            "cookiefile": None,

            # Anonymous YouTube client
            "extractor_args": {
                "youtube": {
                    "player_client": ["android_vr"]
                }
            }
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(
                    youtube_url,
                    download=False
                )

            # Keep ONLY audio formats
            audio_formats = []

            for f in info.get("formats", []):

                if not f.get("url"):
                    continue

                # Audio stream only
                if f.get("vcodec") == "none" and f.get("acodec") != "none":
                    audio_formats.append(f)

            if not audio_formats:
                self.send_json({
                    "error": "No audio-only format available",
                    "id": video_id
                }, 404)
                return

            # Highest quality audio
            audio_formats.sort(
                key=lambda f: (
                    f.get("abr") or 0,
                    f.get("tbr") or 0,
                    f.get("asr") or 0
                ),
                reverse=True
            )

            best = audio_formats[0]

            self.send_json({
                "id": video_id,
                "title": info.get("title"),
                "audio_url": best["url"],
                "format_id": best.get("format_id"),
                "extension": best.get("ext"),
                "codec": best.get("acodec"),
                "bitrate": best.get("abr"),
                "sample_rate": best.get("asr")
            })

        except Exception as e:

            self.send_json({
                "error": str(e),
                "id": video_id
            }, 500)
