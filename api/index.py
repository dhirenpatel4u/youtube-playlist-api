from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import yt_dlp


class handler(BaseHTTPRequestHandler):

    def do_GET(self):

        try:
            # Get ?id=PLAYLIST_ID
            query = parse_qs(
                urlparse(self.path).query
            )

            playlist_id = query.get("id", [None])[0]

            if not playlist_id:
                self.send_json(
                    400,
                    {
                        "error": "Missing playlist ID"
                    }
                )
                return

            playlist_url = (
                "https://www.youtube.com/playlist?list="
                + playlist_id
            )

            ydl_options = {
                "quiet": True,
                "no_warnings": True,

                # Don't download videos
                "skip_download": True,

                # Get playlist entries
                "extract_flat": True,

                "ignoreerrors": True
            }

            with yt_dlp.YoutubeDL(ydl_options) as ydl:

                info = ydl.extract_info(
                    playlist_url,
                    download=False
                )

            result = []

            entries = info.get("entries") or []

            for entry in entries:

                if not entry:
                    continue

                video_id = entry.get("id")

                if not video_id:
                    continue

                title = (
                    entry.get("title")
                    or ""
                )

                artist = (
                    entry.get("channel")
                    or entry.get("uploader")
                    or ""
                )

                duration = entry.get("duration")

                # Ensure duration is a number
                if duration is not None:
                    duration = float(duration)

                item = {
                    "id": video_id,

                    "title": title,

                    "artist": artist,

                    "album": None,

                    "duration": duration,

                    "cover": (
                        "https://i.ytimg.com/vi/"
                        + video_id
                        + "/hqdefault.jpg"
                    ),

                    "rawTitle": title
                }

                result.append(item)

            self.send_json(
                200,
                result
            )

        except Exception as error:

            self.send_json(
                500,
                {
                    "error": str(error)
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
