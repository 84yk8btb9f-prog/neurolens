import pytest
from PIL import Image
import numpy as np
import unittest.mock as mock
from app.brain_mapper import REGIONS


def _make_png(path: str):
    img = Image.fromarray(np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8))
    img.save(path)
    return path


def test_process_image_has_all_region_keys(tmp_path):
    from app.processors.image_processor import process_image
    p = _make_png(str(tmp_path / "t.png"))
    out = process_image(p)
    assert out["type"] == "image"
    assert set(out["scores"].keys()) == set(REGIONS.keys())
    assert all(0 <= v <= 100 for v in out["scores"].values())


def test_chunk_text_splits_long_input():
    from app.processors.text_processor import chunk_text
    long = " ".join(["word"] * 500)
    chunks = chunk_text(long)
    assert len(chunks) > 1


def test_chunk_text_keeps_short_input_as_one():
    from app.processors.text_processor import chunk_text
    assert len(chunk_text("Buy now, limited time only!")) == 1


def test_process_text_has_scores():
    from app.processors.text_processor import process_text
    out = process_text("This product will transform your life.")
    assert out["type"] == "text"
    assert all(0 <= v <= 100 for v in out["scores"].values())


def test_process_pdf_extracts_and_scores(tmp_path):
    from app.processors.pdf_processor import process_pdf
    mock_page = mock.MagicMock()
    mock_page.extract_text.return_value = "Amazing product, buy now, transform your life today!"
    mock_pdf = mock.MagicMock()
    mock_pdf.__enter__ = mock.MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = mock.MagicMock(return_value=False)
    mock_pdf.pages = [mock_page]
    with mock.patch("pdfplumber.open", return_value=mock_pdf):
        out = process_pdf("/fake/path.pdf")
    assert out["type"] == "pdf"
    assert out["meta"]["page_count"] == 1
    assert all(0 <= v <= 100 for v in out["scores"].values())


def test_extract_frames_produces_pil_images():
    from app.processors.video_processor import extract_frames
    cap = mock.MagicMock()
    cap.isOpened.side_effect = [True, True, False]
    cap.get.return_value = 25.0
    cap.read.side_effect = [
        (True, np.zeros((480, 640, 3), dtype=np.uint8)),
        (False, None),
    ]
    with mock.patch("cv2.VideoCapture", return_value=cap):
        frames = extract_frames("/fake/vid.mp4", fps=1)
    assert len(frames) >= 1
    from PIL import Image as PILImage
    assert all(isinstance(f, PILImage.Image) for f in frames)


def test_process_video_merges_visual_and_audio():
    from app.processors.video_processor import process_video
    with mock.patch("app.processors.video_processor.extract_frames") as ef, \
         mock.patch("app.processors.video_processor.transcribe_audio") as ta:
        ef.return_value = [Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))]
        ta.return_value = "Amazing product buy now limited offer"
        out = process_video("/fake/vid.mp4")
    assert out["type"] == "video"
    assert all(0 <= v <= 100 for v in out["scores"].values())


_MOCK_SCORES = {k: 50 for k in ["visual_cortex", "amygdala", "face_social", "hippocampus", "language_areas", "reward_circuit", "prefrontal", "motor_action"]}


def test_process_youtube_delegates_to_video(tmp_path):
    from app.processors.youtube_processor import process_youtube
    with mock.patch("app.processors.youtube_processor.download_youtube") as dl, \
         mock.patch("app.processors.youtube_processor.process_video") as pv:
        dl.return_value = {"video_path": "/tmp/abc.mp4", "title": "Test Ad"}
        pv.return_value = {"type": "video", "scores": _MOCK_SCORES, "meta": {}}
        out = process_youtube("https://youtube.com/watch?v=x", tmp_dir=str(tmp_path))
    assert out["type"] == "youtube"
    assert out["meta"]["title"] == "Test Ad"
    dl.assert_called_once()
    pv.assert_called_once()


def test_process_video_blends_tribe_and_vlm(tmp_path):
    from unittest.mock import patch, MagicMock
    from app.processors.video_processor import process_video

    fake_video = tmp_path / "ad.mp4"
    fake_video.write_bytes(b"fake")
    all_regions = [
        "visual_cortex", "amygdala", "face_social", "hippocampus",
        "language_areas", "reward_circuit", "prefrontal", "motor_action",
    ]
    vlm_scores = {k: 40 for k in all_regions}
    tribe_cortical = {
        "visual_cortex": 80, "face_social": 75,
        "language_areas": 70, "motor_action": 65, "prefrontal": 60,
    }

    with patch("app.processors.video_processor.extract_frames", return_value=[MagicMock()]), \
         patch("app.processors.video_processor.transcribe_audio", return_value="hello"), \
         patch("app.processors.video_processor.score_video", return_value=tribe_cortical), \
         patch("app.processors.video_processor.get_tribe_manager") as mock_tribe_mgr, \
         patch("app.brain_mapper.get_brain_scores", return_value=vlm_scores):
        mock_tribe_mgr.return_value.unload.return_value = True
        result = process_video(str(fake_video))

    assert result["scores"]["visual_cortex"] == 80    # from TRIBE
    assert result["scores"]["face_social"] == 75      # from TRIBE
    assert result["scores"]["amygdala"] == 40          # from VLM (subcortical)
    assert result["scores"]["hippocampus"] == 40       # from VLM (subcortical)
    assert result["scores"]["reward_circuit"] == 40   # from VLM (subcortical)
    assert result["meta"]["tribe_used"] is True


def test_process_video_falls_back_to_vlm_only(tmp_path):
    from unittest.mock import patch, MagicMock
    from app.processors.video_processor import process_video

    fake_video = tmp_path / "ad.mp4"
    fake_video.write_bytes(b"fake")
    all_regions = [
        "visual_cortex", "amygdala", "face_social", "hippocampus",
        "language_areas", "reward_circuit", "prefrontal", "motor_action",
    ]
    vlm_scores = {k: 55 for k in all_regions}

    with patch("app.processors.video_processor.extract_frames", return_value=[MagicMock()]), \
         patch("app.processors.video_processor.transcribe_audio", return_value="hello"), \
         patch("app.processors.video_processor.score_video", return_value=None), \
         patch("app.brain_mapper.get_brain_scores", return_value=vlm_scores):
        result = process_video(str(fake_video))

    for region, score in result["scores"].items():
        assert score == 55, f"{region} should be 55, got {score}"
    assert result["meta"]["tribe_used"] is False
