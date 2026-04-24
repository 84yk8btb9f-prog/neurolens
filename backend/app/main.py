# backend/app/main.py
from __future__ import annotations
import asyncio
import functools
import os
import pathlib
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.content_processor import route_content
from app.recommendation_engine import get_recommendations
from app.model_manager import get_manager, LowMemoryError
from app.whisper_manager import get_whisper_manager
from app.tribe_manager import get_tribe_manager

app = FastAPI(title="NeuroPulse API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
    expose_headers=["*"],
)


def _enrich(result: dict) -> dict:
    recs = get_recommendations(result["scores"])
    return {
        **result,
        "recommendations": [
            {
                "region_key": r.region_key,
                "region_name": r.region_name,
                "score": r.score,
                "priority": r.priority,
                "message": r.message,
                "details": r.details,
                "steps": r.steps,
            }
            for r in recs
        ],
    }


@app.post("/analyze")
async def analyze(
    file: UploadFile | None = File(None),
    youtube_url: str | None = Form(None),
    text_content: str | None = Form(None),
):
    if not file and not youtube_url and not text_content:
        raise HTTPException(status_code=422, detail="Provide file, youtube_url, or text_content")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            fp = None
            if file and file.filename:
                fp = os.path.join(tmp, pathlib.Path(file.filename).name)
                with open(fp, "wb") as f:
                    f.write(await file.read())
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, functools.partial(route_content, file_path=fp, youtube_url=youtube_url, text_content=text_content, tmp_dir=tmp)
            )
        return _enrich(result)
    except LowMemoryError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/compare")
async def compare(
    file_a: UploadFile | None = File(None),
    file_b: UploadFile | None = File(None),
    youtube_url_a: str | None = Form(None),
    youtube_url_b: str | None = Form(None),
    text_a: str | None = Form(None),
    text_b: str | None = Form(None),
):
    with tempfile.TemporaryDirectory() as tmp:
        pa = pb = None
        if file_a and file_a.filename:
            pa = os.path.join(tmp, "a_" + pathlib.Path(file_a.filename).name)
            with open(pa, "wb") as f:
                f.write(await file_a.read())
        if file_b and file_b.filename:
            pb = os.path.join(tmp, "b_" + pathlib.Path(file_b.filename).name)
            with open(pb, "wb") as f:
                f.write(await file_b.read())
        if not pa and not youtube_url_a and not text_a:
            raise HTTPException(status_code=422, detail="Provide at least one input for 'a'")
        if not pb and not youtube_url_b and not text_b:
            raise HTTPException(status_code=422, detail="Provide at least one input for 'b'")
        try:
            loop = asyncio.get_running_loop()
            ra = await loop.run_in_executor(
                None, functools.partial(route_content, file_path=pa, youtube_url=youtube_url_a, text_content=text_a, tmp_dir=tmp)
            )
            rb = await loop.run_in_executor(
                None, functools.partial(route_content, file_path=pb, youtube_url=youtube_url_b, text_content=text_b, tmp_dir=tmp)
            )
        except LowMemoryError as e:
            raise HTTPException(status_code=503, detail=str(e))
    return {"a": _enrich(ra), "b": _enrich(rb)}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/model/status")
def model_status():
    return get_manager().status()


@app.post("/model/unload")
def model_unload():
    did_unload = get_manager().unload()
    return {"status": "unloaded" if did_unload else "already_unloaded"}


@app.get("/whisper/status")
def whisper_status():
    return get_whisper_manager().status()


@app.post("/whisper/unload")
def whisper_unload():
    did_unload = get_whisper_manager().unload()
    return {"status": "unloaded" if did_unload else "already_unloaded"}


@app.get("/tribe/status")
def tribe_status():
    return get_tribe_manager().status()


@app.post("/tribe/unload")
def tribe_unload():
    did_unload = get_tribe_manager().unload()
    return {"status": "unloaded" if did_unload else "already_unloaded"}


@app.exception_handler(LowMemoryError)
def low_memory_handler(_request, exc: LowMemoryError):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc), "error": "low_memory"},
        headers={"Access-Control-Allow-Origin": "http://localhost:3000"},
    )
