import os
import yt_dlp
from app.processors.video_processor import process_video


def download_youtube(url: str, tmp_dir: str) -> dict:
    ydl_opts = {
        "format": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "outtmpl": os.path.join(tmp_dir, "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        video_path = os.path.splitext(filename)[0] + ".mp4"
        return {"video_path": video_path, "title": info.get("title", "Unknown")}


def process_youtube(url: str, tmp_dir: str = "/tmp") -> dict:
    downloaded = download_youtube(url, tmp_dir)
    out = process_video(downloaded["video_path"])
    out["type"] = "youtube"
    out["meta"]["title"] = downloaded["title"]
    out["meta"]["url"] = url
    return out
