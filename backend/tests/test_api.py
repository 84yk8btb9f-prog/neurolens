# backend/tests/test_api.py
import io
import pytest
import numpy as np
from PIL import Image
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

_SCORES = {k: 50 for k in ["visual_cortex", "amygdala", "face_social", "hippocampus", "language_areas", "reward_circuit", "prefrontal", "motor_action"]}
_MOCK = {"type": "image", "scores": _SCORES, "meta": {}}


@pytest.fixture
def png_bytes():
    buf = io.BytesIO()
    Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_analyze_image_ok(png_bytes):
    from app.main import app
    with patch("app.main.route_content", return_value=_MOCK):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post("/analyze", files={"file": ("t.png", png_bytes, "image/png")})
    assert resp.status_code == 200
    data = resp.json()
    assert "scores" in data and "recommendations" in data


@pytest.mark.asyncio
async def test_analyze_text_ok():
    from app.main import app
    with patch("app.main.route_content", return_value=_MOCK):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post("/analyze", data={"text_content": "Buy now!"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_analyze_empty_body_fails():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/analyze")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_comparison_gives_two_analyses():
    from app.main import app
    out_a = {**_MOCK, "scores": {k: 70 for k in _SCORES}}
    out_b = {**_MOCK, "scores": {k: 40 for k in _SCORES}}
    with patch("app.main.route_content", side_effect=[out_a, out_b]):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post("/compare", data={"text_a": "Great!", "text_b": "Boring."})
    assert resp.status_code == 200
    data = resp.json()
    assert "a" in data and "b" in data


@pytest.mark.asyncio
async def test_compare_empty_body_fails():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/compare")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_model_status_returns_loaded_flag():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/model/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "loaded" in data
    assert "idle_timeout_seconds" in data


@pytest.mark.asyncio
async def test_model_unload_endpoint():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/model/unload")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("unloaded", "already_unloaded")
