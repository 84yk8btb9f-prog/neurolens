import logging
import os
import yt_dlp

from app.processors.video_processor import process_video

_log = logging.getLogger(__name__)

# YouTube aggressively blocks the default 'web' player from cloud IPs (AWS,
# HF Spaces, GCP). Falling back through alternate player clients usually works
# for at least one of them at any given time.
_PLAYER_CLIENTS = ["ios", "android", "web_safari", "web"]


class YouTubeBlockedError(RuntimeError):
    """Raised when every player-client fallback failed to download."""


def _opts_for(client: str, tmp_dir: str) -> dict:
    return {
        "format": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "outtmpl": os.path.join(tmp_dir, "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {"youtube": {"player_client": [client]}},
        "socket_timeout": 30,
    }


def download_youtube(url: str, tmp_dir: str) -> dict:
    last_err: Exception | None = None
    for client in _PLAYER_CLIENTS:
        try:
            with yt_dlp.YoutubeDL(_opts_for(client, tmp_dir)) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                video_path = os.path.splitext(filename)[0] + ".mp4"
                return {
                    "video_path": video_path,
                    "title": info.get("title", "Unknown"),
                    "player_client": client,
                }
        except Exception as exc:
            _log.warning("yt-dlp %s client failed for %s: %s", client, url, exc)
            last_err = exc

    raise YouTubeBlockedError(
        "YouTube blocked every download attempt from this server's IP. "
        "This is common on free cloud hosts (HF Spaces, AWS, GCP). "
        "Workarounds: (1) download the video locally and upload the .mp4 file, "
        "or (2) run NeuroPulse on your own machine. "
        f"Last error: {last_err}"
    )


def process_youtube(url: str, tmp_dir: str = "/tmp") -> dict:
    downloaded = download_youtube(url, tmp_dir)
    out = process_video(downloaded["video_path"])
    out["type"] = "youtube"
    out["meta"]["title"] = downloaded["title"]
    out["meta"]["url"] = url
    out["meta"]["player_client"] = downloaded.get("player_client")
    return out
