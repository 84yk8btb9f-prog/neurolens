# backend/app/content_processor.py
import os

_IMAGE = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
_VIDEO = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
_PDF   = {".pdf"}


def route_content(
    file_path: str | None = None,
    youtube_url: str | None = None,
    text_content: str | None = None,
    tmp_dir: str = "/tmp",
) -> dict:
    if youtube_url:
        from app.processors.youtube_processor import process_youtube
        return process_youtube(youtube_url, tmp_dir=tmp_dir)

    if text_content and not file_path:
        from app.processors.text_processor import process_text
        return process_text(text_content)

    if file_path:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in _IMAGE:
            from app.processors.image_processor import process_image
            return process_image(file_path)
        if ext in _VIDEO:
            from app.processors.video_processor import process_video
            return process_video(file_path)
        if ext in _PDF:
            from app.processors.pdf_processor import process_pdf
            return process_pdf(file_path)
        with open(file_path, "r", errors="ignore") as f:
            from app.processors.text_processor import process_text
            return process_text(f.read())

    raise ValueError("No valid input provided")
