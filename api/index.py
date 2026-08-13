from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import yt_dlp


class handler(BaseHTTPRequestHandler):

    def do_GET(self):

        try:
            # =========================================================
            # GET PLAYLIST ID
            #
            # Example:
            # https://xxxxx.vercel.app?id=PLxxxxxxxxxxxx
            # =========================================================

            parsed_url = urlparse(self.path)

            query = parse_qs(
                parsed_url.query
            )

            playlist_id = query.get(
                "id",
                [None]
            )[0]

            if not playlist_id:

                self.send_json(
                    400,
                    {
                        "error": "Missing playlist ID",
                        "example": "?id=PLxxxxxxxxxxxx"
                    }
                )

                return


            # =========================================================
            # CREATE PLAYLIST URL
            # =========================================================

            playlist_url = (
                "https://www.youtube.com/playlist?list="
                + playlist_id
            )


            # =========================================================
            # STEP 1
            # GET PLAYLIST VIDEO IDS
            #
            # extract_flat=True makes this first request lighter.
            # =========================================================

            playlist_options = {

                "quiet": True,

                "no_warnings": True,

                "skip_download": True,

                "extract_flat": True,

                "ignoreerrors": True
            }


            with yt_dlp.YoutubeDL(
                playlist_options
            ) as ydl:

                playlist_info = ydl.extract_info(
                    playlist_url,
                    download=False
                )


            if not playlist_info:

                self.send_json(
                    404,
                    {
                        "error": "Playlist could not be found."
                    }
                )

                return


            entries = (
                playlist_info.get("entries")
                or []
            )


            # =========================================================
            # RESULT ARRAY
            # =========================================================

            result = []


            # =========================================================
            # STEP 2
            # EXTRACT EACH VIDEO
            # =========================================================

            for entry in entries:

                if not entry:
                    continue


                video_id = entry.get("id")

                if not video_id:
                    continue


                video_url = (
                    "https://www.youtube.com/watch?v="
                    + video_id
                )


                # =====================================================
                # VIDEO EXTRACTION OPTIONS
                #
                # IMPORTANT:
                #
                # bestaudio[acodec!=none]
                #
                # means audio format only.
                #
                # No video stream is selected.
                # =====================================================

                video_options = {

                    "quiet": True,

                    "no_warnings": True,

                    "skip_download": True,

                    "format": (
                        "bestaudio[acodec!=none]/"
                        "bestaudio"
                    ),

                    "ignoreerrors": True
                }


                try:

                    with yt_dlp.YoutubeDL(
                        video_options
                    ) as ydl:

                        video_info = ydl.extract_info(
                            video_url,
                            download=False
                        )


                    if not video_info:

                        continue


                    # =================================================
                    # BASIC INFORMATION
                    # =================================================

                    title = (
                        video_info.get("title")
                        or entry.get("title")
                        or ""
                    )


                    artist = (
                        video_info.get("channel")
                        or video_info.get("uploader")
                        or entry.get("channel")
                        or entry.get("uploader")
                        or ""
                    )


                    duration = video_info.get(
                        "duration"
                    )


                    if duration is not None:

                        duration = float(
                            duration
                        )


                    # =================================================
                    # FIND AUDIO-ONLY FORMATS
                    #
                    # vcodec == "none"
                    #
                    # means the format has NO video.
                    # =================================================

                    formats = (
                        video_info.get("formats")
                        or []
                    )


                    audio_formats = []


                    for fmt in formats:

                        fmt_url = fmt.get(
                            "url"
                        )

                        acodec = fmt.get(
                            "acodec"
                        )

                        vcodec = fmt.get(
                            "vcodec"
                        )


                        if not fmt_url:
                            continue


                        # Must have audio
                        if not acodec:
                            continue


                        if acodec == "none":
                            continue


                        # Must NOT have video
                        if vcodec not in (
                            None,
                            "none"
                        ):
                            continue


                        audio_formats.append(
                            fmt
                        )


                    # =================================================
                    # SELECT BEST AUDIO
                    #
                    # Prefer:
                    # 1. Higher audio bitrate
                    # 2. Higher total bitrate
                    # =================================================

                    best_audio = None


                    if audio_formats:

                        best_audio = max(
                            audio_formats,
                            key=lambda fmt: (
                                fmt.get("abr") or 0,
                                fmt.get("tbr") or 0
                            )
                        )


                    # =================================================
                    # STREAM URL
                    # =================================================

                    stream_url = None


                    if best_audio:

                        stream_url = best_audio.get(
                            "url"
                        )


                    # =================================================
                    # COVER
                    # =================================================

                    cover = (
                        "https://i.ytimg.com/vi/"
                        + video_id
                        + "/hqdefault.jpg"
                    )


                    # =================================================
                    # FINAL JSON ITEM
                    # =================================================

                    result.append({

                        "id": video_id,

                        "title": title,

                        "artist": artist,

                        "album": None,

                        "duration": duration,

                        "cover": cover,

                        "rawTitle": title,

                        "stream": stream_url

                    })


                except Exception as video_error:

                    # Don't stop the entire playlist
                    # if one video fails.

                    print(
                        "Video extraction failed:",
                        video_id,
                        repr(video_error)
                    )


                    # Add the video with stream=null

                    result.append({

                        "id": video_id,

                        "title": (
                            entry.get("title")
                            or ""
                        ),

                        "artist": (
                            entry.get("channel")
                            or entry.get("uploader")
                            or ""
                        ),

                        "album": None,

                        "duration": (
                            entry.get("duration")
                        ),

                        "cover": (
                            "https://i.ytimg.com/vi/"
                            + video_id
                            + "/hqdefault.jpg"
                        ),

                        "rawTitle": (
                            entry.get("title")
                            or ""
                        ),

                        "stream": None

                    })


            # =========================================================
            # RETURN JSON ARRAY
            # =========================================================

            self.send_json(
                200,
                result
            )


        except Exception as error:

            print(
                "Playlist extraction error:",
                repr(error)
            )


            self.send_json(
                500,
                {
                    "error": str(error)
                }
            )


    # =============================================================
    # SEND JSON RESPONSE
    # =============================================================

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


        self.send_response(
            status
        )


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
