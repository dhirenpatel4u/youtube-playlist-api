from http.server import BaseHTTPRequestHandler
import json
import yt_dlp


class handler(BaseHTTPRequestHandler):

    def do_POST(self):

        try:
            # Read POST body
            content_length = int(
                self.headers.get("Content-Length", 0)
            )

            body = self.rfile.read(
                content_length
            )

            data = json.loads(
                body.decode("utf-8")
            )

            video_id = data.get("id")

            if not video_id:
                self.send_json(
                    400,
                    {
                        "error": "Missing YouTube track id"
                    }
                )
                return

            # YouTube video URL
            video_url = (
                "https://www.youtube.com/watch?v="
                + video_id
            )

            options = {
                "quiet": True,
                "no_warnings": True,

                # Don't download
                "skip_download": True,

                # Best audio-only format
                "format": "bestaudio",

                "ignoreerrors": False
            }

            with yt_dlp.YoutubeDL(options) as ydl:

                info = ydl.extract_info(
                    video_url,
                    download=False
                )

            if not info:
                self.send_json(
                    404,
                    {
                        "error": "Track not found"
                    }
                )
                return

            # Make absolutely sure we return
            # an audio-only format.
            formats = info.get("formats", [])

            audio_formats = []

            for fmt in formats:

                url = fmt.get("url")

                acodec = fmt.get("acodec")

                vcodec = fmt.get("vcodec")

                if not url:
                    continue

                # Must contain audio
                if not acodec:
                    continue

                if acodec == "none":
                    continue

                # Must NOT contain video
                if vcodec not in (
                    None,
                    "none"
                ):
                    continue

                audio_formats.append(fmt)

            if not audio_formats:
                self.send_json(
                    404,
                    {
                        "error": "No audio-only format found"
                    }
                )
                return

            # Highest audio quality.
            #
            # Prefer audio bitrate (abr),
            # then total bitrate (tbr).
            best = max(
                audio_formats,
                key=lambda f: (
                    f.get("abr") or 0,
                    f.get("tbr") or 0
                )
            )

            result = {
                "id": video_id,

                "title": info.get(
                    "title"
                ),

                "artist": (
                    info.get("channel")
                    or info.get("uploader")
                ),

                "duration": info.get(
                    "duration"
                ),

                "acodec": best.get(
                    "acodec"
                ),

                "abr": best.get(
                    "abr"
                ),

                "ext": best.get(
                    "ext"
                ),

                "format_id": best.get(
                    "format_id"
                ),

                "stream": best.get(
                    "url"
                )
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


    def do_GET(self):

        self.send_json(
            405,
            {
                "error": "Use POST"
            }
        )


    def send_json(
        self,
        status,
        data
    ):

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

        self.send_header(
            "Cache-Control",
            "no-store"
        )

        self.end_headers()

        self.wfile.write(
            output
        )
