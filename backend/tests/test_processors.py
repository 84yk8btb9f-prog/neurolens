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
