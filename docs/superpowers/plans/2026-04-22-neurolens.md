# NeuroPulse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first brain activation analysis tool that predicts how marketing content (images, videos, YouTube, PDFs, text) engages key brain regions, with comparison and optimization recommendations.

**Architecture:** Python FastAPI backend runs CLIP ViT-B/32 locally (CPU, ~0.3s/image, no GPU needed, no cost). Content of any type is normalized into embeddings and scored against neuroscience-informed probe texts for 8 brain regions. A Next.js frontend visualizes scores as a radar chart with per-region breakdowns and actionable marketing recommendations.

**Tech Stack:** Python 3.11, FastAPI, transformers (CLIP), openai-whisper, yt-dlp, pdfplumber, opencv-python, Pillow · Next.js 14 (App Router), Tailwind CSS, shadcn/ui, Recharts · Fully local — no cloud, no GPU, no API keys.

---

## Why not TRIBE v2?

TRIBE v2 stacks LLaMA 3.2-3B + V-JEPA2 + Wav2Vec-BERT, needs GPU + gated HuggingFace access. Kairo almost certainly does not run TRIBE for the same reasons. CLIP ViT-B/32 is the right foundation: trained on 400M image-text pairs, its representations correlate with ventral visual stream activity, and it runs in ~300ms/image on CPU.

---

## File Map

```
neurolens/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── brain_mapper.py
│   │   ├── content_processor.py
│   │   ├── recommendation_engine.py
│   │   └── processors/
│   │       ├── __init__.py
│   │       ├── image_processor.py
│   │       ├── text_processor.py
│   │       ├── pdf_processor.py
│   │       ├── video_processor.py
│   │       └── youtube_processor.py
│   ├── tests/
│   │   ├── test_brain_mapper.py
│   │   ├── test_processors.py
│   │   └── test_api.py
│   ├── requirements.txt
│   └── start.sh
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── analysis/page.tsx
│   │   │   └── compare/page.tsx
│   │   ├── components/
│   │   │   ├── ContentUploader.tsx
│   │   │   ├── BrainRadarChart.tsx
│   │   │   ├── RegionCard.tsx
│   │   │   └── RecommendationPanel.tsx
│   │   ├── lib/api.ts
│   │   └── types/analysis.ts
│   └── package.json
└── README.md
```

---

## Task 1: Python backend scaffold

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/processors/__init__.py`
- Create: `backend/start.sh`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.9
transformers==4.44.0
torch==2.4.0
Pillow==10.4.0
openai-whisper==20231117
yt-dlp==2024.8.6
pdfplumber==0.11.4
opencv-python-headless==4.10.0.84
numpy==1.26.4
httpx==0.27.2
pytest==8.3.3
pytest-asyncio==0.24.0
```

- [ ] **Step 2: Create empty init files**

```python
# backend/app/__init__.py  (empty)
```

```python
# backend/app/processors/__init__.py  (empty)
```

- [ ] **Step 3: Create start.sh**

```bash
#!/usr/bin/env bash
# backend/start.sh
set -e
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
fi
.venv/bin/uvicorn app.main:app --reload --port 8000
```

```bash
chmod +x backend/start.sh
```

- [ ] **Step 4: Install dependencies**

```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Expected: packages install (~3–5 min first time).

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat: python backend scaffold"
```

---

## Task 2: Brain mapper — CLIP probe scoring

**Files:**
- Create: `backend/app/brain_mapper.py`
- Create: `backend/tests/test_brain_mapper.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_brain_mapper.py
import pytest
from PIL import Image
import numpy as np
from app.brain_mapper import get_brain_scores, REGIONS, normalize_score


def test_regions_has_eight_entries():
    assert len(REGIONS) == 8


def test_normalize_score_clamps_low():
    assert normalize_score(0.05) == 0


def test_normalize_score_clamps_high():
    assert normalize_score(0.45) == 100


def test_normalize_score_midpoint():
    score = normalize_score(0.225)
    assert 45 <= score <= 55


def test_brain_scores_image_has_all_keys():
    img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
    scores = get_brain_scores(image=img)
    assert set(scores.keys()) == set(REGIONS.keys())
    for v in scores.values():
        assert 0 <= v <= 100


def test_brain_scores_text_has_all_keys():
    scores = get_brain_scores(text="Buy our amazing product today. Limited time offer.")
    assert set(scores.keys()) == set(REGIONS.keys())
    for v in scores.values():
        assert 0 <= v <= 100


def test_emotional_copy_scores_above_bland_on_amygdala():
    emotional = get_brain_scores(text="Act NOW — life-changing. Do not miss out. Fear and desire.")
    bland = get_brain_scores(text="This spreadsheet has columns and rows for data entry.")
    assert emotional["amygdala"] > bland["amygdala"]
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd backend && .venv/bin/pytest tests/test_brain_mapper.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement brain_mapper.py**

```python
# backend/app/brain_mapper.py
from __future__ import annotations
import threading
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

_lock = threading.Lock()
_model: CLIPModel | None = None
_processor: CLIPProcessor | None = None
_MODEL_ID = "openai/clip-vit-base-patch32"

REGIONS: dict[str, dict] = {
    "visual_cortex": {
        "name": "Visual Cortex",
        "description": "Visual richness, color, composition",
        "marketing": "Visual appeal and aesthetic impact",
        "probes": [
            "vivid colors, rich visual detail, beautiful imagery",
            "striking composition, high contrast, detailed texture",
            "aesthetically pleasing, visually stunning design",
        ],
    },
    "face_social": {
        "name": "Face & Social Areas",
        "description": "Human faces, social trust, connection",
        "marketing": "Human connection and social proof",
        "probes": [
            "human face, portrait, eye contact, personal connection",
            "people together, social interaction, community, belonging",
            "trust, authenticity, real person, genuine emotion",
        ],
    },
    "amygdala": {
        "name": "Emotional Core",
        "description": "Emotional intensity, urgency, desire",
        "marketing": "Emotional impact and urgency",
        "probes": [
            "intense emotion, fear, urgency, excitement, powerful feeling",
            "joy, happiness, love, aspiration, dream, hope",
            "missing out, problem, pain point, frustration, anxiety",
        ],
    },
    "hippocampus": {
        "name": "Memory Encoding",
        "description": "Memorability, novelty, narrative",
        "marketing": "Brand recall and memorability",
        "probes": [
            "memorable story, unique narrative, unforgettable moment",
            "unexpected surprise, novelty, stands out, distinctive",
            "before and after transformation, journey, sequence of events",
        ],
    },
    "language_areas": {
        "name": "Language Processing",
        "description": "Verbal clarity, messaging, persuasion",
        "marketing": "Message clarity and persuasive copy",
        "probes": [
            "clear message, compelling words, persuasive language, call to action",
            "headline, tagline, benefit statement, value proposition",
            "storytelling, dialogue, conversation, written communication",
        ],
    },
    "reward_circuit": {
        "name": "Reward Circuit",
        "description": "Desire, craving, purchase drive",
        "marketing": "Desire and purchase intent",
        "probes": [
            "desire, craving, want, need, must have, exclusive, premium",
            "reward, achievement, satisfaction, success, transformation",
            "deal, offer, save, get it now, own it, limited availability",
        ],
    },
    "prefrontal": {
        "name": "Decision Center",
        "description": "Rational appeal, credibility, logic",
        "marketing": "Trust, proof, and rational justification",
        "probes": [
            "proof, evidence, data, statistics, credible, trustworthy, verified",
            "logical reason, benefit, feature, how it works, why choose this",
            "guarantee, safety, reliable, quality, professional, expert",
        ],
    },
    "motor_action": {
        "name": "Action & Drive",
        "description": "Energy, movement, call-to-action activation",
        "marketing": "Action drive and engagement activation",
        "probes": [
            "action, movement, energy, dynamic, do it now, start today",
            "motion, fast, momentum, progress, change happening",
            "click, buy, sign up, get started, take action, join now",
        ],
    },
}


def _load() -> tuple[CLIPModel, CLIPProcessor]:
    global _model, _processor
    with _lock:
        if _model is None:
            _model = CLIPModel.from_pretrained(_MODEL_ID)
            _model.eval()
            _processor = CLIPProcessor.from_pretrained(_MODEL_ID)
    return _model, _processor


def normalize_score(raw: float, lo: float = 0.10, hi: float = 0.38) -> int:
    return max(0, min(100, int((raw - lo) / (hi - lo) * 100)))


def _img_score(image: Image.Image, probes: list[str], model: CLIPModel, proc: CLIPProcessor) -> float:
    with torch.no_grad():
        img_in = proc(images=image, return_tensors="pt")
        img_feat = model.get_image_features(**img_in)
        img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
        txt_in = proc(text=probes, return_tensors="pt", padding=True, truncation=True)
        txt_feat = model.get_text_features(**txt_in)
        txt_feat = txt_feat / txt_feat.norm(dim=-1, keepdim=True)
        return (img_feat @ txt_feat.T).squeeze(0).max().item()


def _txt_score(content: str, probes: list[str], model: CLIPModel, proc: CLIPProcessor) -> float:
    all_texts = [content[:300]] + probes
    with torch.no_grad():
        inputs = proc(text=all_texts, return_tensors="pt", padding=True, truncation=True)
        feats = model.get_text_features(**inputs)
        feats = feats / feats.norm(dim=-1, keepdim=True)
        return (feats[0:1] @ feats[1:].T).squeeze(0).max().item()


def get_brain_scores(
    image: Image.Image | None = None,
    text: str | None = None,
    images: list[Image.Image] | None = None,
    texts: list[str] | None = None,
) -> dict[str, int]:
    model, proc = _load()
    all_imgs: list[Image.Image] = list(images or []) + ([image] if image else [])
    all_txts: list[str] = list(texts or []) + ([text] if text else [])

    scores: dict[str, int] = {}
    for key, region in REGIONS.items():
        probes = region["probes"]
        raws: list[float] = []
        for img in all_imgs:
            raws.append(_img_score(img, probes, model, proc))
        for t in all_txts:
            raws.append(_txt_score(t, probes, model, proc))
        raw = sum(raws) / len(raws) if raws else 0.10
        scores[key] = normalize_score(raw)
    return scores
```

- [ ] **Step 4: Run tests**

```bash
cd backend && .venv/bin/pytest tests/test_brain_mapper.py -v
```

Expected: all 7 pass. First run downloads CLIP weights (~600 MB).

- [ ] **Step 5: Commit**

```bash
git add backend/app/brain_mapper.py backend/tests/test_brain_mapper.py
git commit -m "feat: CLIP probe-based brain region scoring"
```

---

## Task 3: Image processor

**Files:**
- Create: `backend/app/processors/image_processor.py`
- Create: `backend/tests/test_processors.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_processors.py
import pytest
from PIL import Image
import numpy as np
from app.processors.image_processor import process_image
from app.brain_mapper import REGIONS


def _make_png(path: str):
    img = Image.fromarray(np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8))
    img.save(path)
    return path


def test_process_image_has_all_region_keys(tmp_path):
    p = _make_png(str(tmp_path / "t.png"))
    out = process_image(p)
    assert out["type"] == "image"
    assert set(out["scores"].keys()) == set(REGIONS.keys())
    assert all(0 <= v <= 100 for v in out["scores"].values())
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd backend && .venv/bin/pytest tests/test_processors.py::test_process_image_has_all_region_keys -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement image_processor.py**

```python
# backend/app/processors/image_processor.py
from PIL import Image
from app.brain_mapper import get_brain_scores


def process_image(file_path: str) -> dict:
    image = Image.open(file_path).convert("RGB")
    scores = get_brain_scores(image=image)
    return {"type": "image", "scores": scores, "meta": {"path": file_path}}
```

- [ ] **Step 4: Run test**

```bash
cd backend && .venv/bin/pytest tests/test_processors.py::test_process_image_has_all_region_keys -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/processors/image_processor.py backend/tests/test_processors.py
git commit -m "feat: image processor"
```

---

## Task 4: Text processor

**Files:**
- Modify: `backend/tests/test_processors.py`
- Create: `backend/app/processors/text_processor.py`

- [ ] **Step 1: Add tests** (append to test_processors.py)

```python
from app.processors.text_processor import process_text, chunk_text


def test_chunk_text_splits_long_input():
    long = " ".join(["word"] * 500)
    chunks = chunk_text(long)
    assert len(chunks) > 1
    assert all(len(c) <= 400 for c in chunks)


def test_chunk_text_keeps_short_input_as_one():
    assert len(chunk_text("Buy now, limited time only!")) == 1


def test_process_text_has_scores():
    out = process_text("This product will transform your life.")
    assert out["type"] == "text"
    assert all(0 <= v <= 100 for v in out["scores"].values())
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd backend && .venv/bin/pytest tests/test_processors.py -k "text" -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement text_processor.py**

```python
# backend/app/processors/text_processor.py
from app.brain_mapper import get_brain_scores


def chunk_text(text: str, words_per_chunk: int = 150) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunks.append(" ".join(words[i : i + words_per_chunk])[:400])
    return chunks[:15]


def process_text(text: str) -> dict:
    chunks = chunk_text(text)
    scores = get_brain_scores(texts=chunks)
    return {"type": "text", "scores": scores, "meta": {"char_count": len(text)}}
```

- [ ] **Step 4: Run tests**

```bash
cd backend && .venv/bin/pytest tests/test_processors.py -k "text" -v
```

Expected: all 3 pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/processors/text_processor.py backend/tests/test_processors.py
git commit -m "feat: text processor with chunking"
```

---

## Task 5: PDF processor

**Files:**
- Modify: `backend/tests/test_processors.py`
- Create: `backend/app/processors/pdf_processor.py`

- [ ] **Step 1: Add test** (append)

```python
import unittest.mock as mock
from app.processors.pdf_processor import process_pdf


def test_process_pdf_extracts_and_scores(tmp_path):
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd backend && .venv/bin/pytest tests/test_processors.py::test_process_pdf_extracts_and_scores -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement pdf_processor.py**

```python
# backend/app/processors/pdf_processor.py
import pdfplumber
from app.processors.text_processor import process_text


def process_pdf(file_path: str) -> dict:
    with pdfplumber.open(file_path) as pdf:
        text = " ".join((p.extract_text() or "") for p in pdf.pages)
        page_count = len(pdf.pages)
    out = process_text(text)
    out["type"] = "pdf"
    out["meta"]["page_count"] = page_count
    return out
```

- [ ] **Step 4: Run test**

```bash
cd backend && .venv/bin/pytest tests/test_processors.py::test_process_pdf_extracts_and_scores -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/processors/pdf_processor.py backend/tests/test_processors.py
git commit -m "feat: PDF processor"
```

---

## Task 6: Video processor

**Files:**
- Modify: `backend/tests/test_processors.py`
- Create: `backend/app/processors/video_processor.py`

- [ ] **Step 1: Add tests** (append)

```python
from app.processors.video_processor import extract_frames, process_video


def test_extract_frames_produces_pil_images():
    cap = mock.MagicMock()
    cap.isOpened.side_effect = [True, True, False]
    cap.get.return_value = 25.0
    import numpy as np
    cap.read.side_effect = [
        (True, np.zeros((480, 640, 3), dtype=np.uint8)),
        (False, None),
    ]
    with mock.patch("cv2.VideoCapture", return_value=cap):
        frames = extract_frames("/fake/vid.mp4", fps=1)
    assert len(frames) >= 1


def test_process_video_merges_visual_and_audio():
    with mock.patch("app.processors.video_processor.extract_frames") as ef, \
         mock.patch("app.processors.video_processor.transcribe_audio") as ta:
        from PIL import Image
        import numpy as np
        ef.return_value = [Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))]
        ta.return_value = "Amazing product buy now limited offer"
        out = process_video("/fake/vid.mp4")
    assert out["type"] == "video"
    assert all(0 <= v <= 100 for v in out["scores"].values())
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd backend && .venv/bin/pytest tests/test_processors.py -k "video" -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement video_processor.py**

```python
# backend/app/processors/video_processor.py
from __future__ import annotations
import os
import subprocess
import threading
import whisper
import cv2
import numpy as np
from PIL import Image
from app.brain_mapper import get_brain_scores

_wlock = threading.Lock()
_wmodel = None


def _get_whisper():
    global _wmodel
    with _wlock:
        if _wmodel is None:
            _wmodel = whisper.load_model("tiny")
    return _wmodel


def extract_frames(video_path: str, fps: float = 0.5, max_frames: int = 24) -> list[Image.Image]:
    cap = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    interval = max(1, int(video_fps / fps))
    frames: list[Image.Image] = []
    idx = 0
    while cap.isOpened() and len(frames) < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % interval == 0:
            frames.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        idx += 1
    cap.release()
    return frames


def transcribe_audio(video_path: str) -> str:
    audio_path = video_path.rsplit(".", 1)[0] + "_audio.wav"
    subprocess.run(
        ["ffmpeg", "-i", video_path, "-ar", "16000", "-ac", "1", "-y", audio_path],
        capture_output=True,
    )
    if not os.path.exists(audio_path):
        return ""
    result = _get_whisper().transcribe(audio_path)
    os.remove(audio_path)
    return result.get("text", "")


def process_video(file_path: str) -> dict:
    frames = extract_frames(file_path)
    transcript = transcribe_audio(file_path)
    scores = get_brain_scores(
        images=frames or None,
        text=transcript.strip() or None,
    )
    return {
        "type": "video",
        "scores": scores,
        "meta": {
            "frame_count": len(frames),
            "transcript_preview": transcript[:200],
        },
    }
```

- [ ] **Step 4: Run tests**

```bash
cd backend && .venv/bin/pytest tests/test_processors.py -k "video" -v
```

Expected: both pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/processors/video_processor.py backend/tests/test_processors.py
git commit -m "feat: video processor with frame extraction and whisper"
```

---

## Task 7: YouTube processor

**Files:**
- Modify: `backend/tests/test_processors.py`
- Create: `backend/app/processors/youtube_processor.py`

- [ ] **Step 1: Add test** (append)

```python
from app.processors.youtube_processor import process_youtube

_MOCK_SCORES = {k: 50 for k in ["visual_cortex", "amygdala", "face_social", "hippocampus", "language_areas", "reward_circuit", "prefrontal", "motor_action"]}


def test_process_youtube_delegates_to_video(tmp_path):
    with mock.patch("app.processors.youtube_processor.download_youtube") as dl, \
         mock.patch("app.processors.youtube_processor.process_video") as pv:
        dl.return_value = {"video_path": "/tmp/abc.mp4", "title": "Test Ad"}
        pv.return_value = {"type": "video", "scores": _MOCK_SCORES, "meta": {}}
        out = process_youtube("https://youtube.com/watch?v=x", tmp_dir=str(tmp_path))
    assert out["type"] == "youtube"
    assert out["meta"]["title"] == "Test Ad"
    dl.assert_called_once()
    pv.assert_called_once()
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd backend && .venv/bin/pytest tests/test_processors.py::test_process_youtube_delegates_to_video -v
```

- [ ] **Step 3: Implement youtube_processor.py**

```python
# backend/app/processors/youtube_processor.py
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
        video_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp4"
        return {"video_path": video_path, "title": info.get("title", "Unknown")}


def process_youtube(url: str, tmp_dir: str = "/tmp") -> dict:
    downloaded = download_youtube(url, tmp_dir)
    out = process_video(downloaded["video_path"])
    out["type"] = "youtube"
    out["meta"]["title"] = downloaded["title"]
    out["meta"]["url"] = url
    return out
```

- [ ] **Step 4: Run test**

```bash
cd backend && .venv/bin/pytest tests/test_processors.py::test_process_youtube_delegates_to_video -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/processors/youtube_processor.py backend/tests/test_processors.py
git commit -m "feat: YouTube processor via yt-dlp"
```

---

## Task 8: Recommendation engine

**Files:**
- Create: `backend/app/recommendation_engine.py`
- Modify: `backend/tests/test_brain_mapper.py`

- [ ] **Step 1: Add tests** (append to test_brain_mapper.py)

```python
from app.recommendation_engine import get_recommendations, Recommendation

_ALL_KEYS = ["visual_cortex", "amygdala", "face_social", "hippocampus", "language_areas", "reward_circuit", "prefrontal", "motor_action"]


def test_get_recs_has_one_per_region():
    scores = {k: 50 for k in _ALL_KEYS}
    recs = get_recommendations(scores)
    assert len(recs) == 8


def test_low_amygdala_shows_high_priority():
    scores = {k: 80 for k in _ALL_KEYS}
    scores["amygdala"] = 10
    recs = get_recommendations(scores)
    amygdala = [r for r in recs if r.region_key == "amygdala"]
    assert amygdala[0].priority == "high"


def test_all_high_scores_produce_no_high_priority():
    scores = {k: 90 for k in _ALL_KEYS}
    recs = get_recommendations(scores)
    assert all(r.priority != "high" for r in recs)
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd backend && .venv/bin/pytest tests/test_brain_mapper.py -k "recs or priority" -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement recommendation_engine.py**

```python
# backend/app/recommendation_engine.py
from dataclasses import dataclass

@dataclass
class Recommendation:
    region_key: str
    region_name: str
    score: int
    priority: str  # "high" | "medium" | "ok"
    message: str


_ADVICE: dict[str, dict[str, str]] = {
    "visual_cortex": {
        "high": "Strong visual appeal — your content is aesthetically engaging.",
        "medium": "Visual impact is moderate. Try bolder composition or richer imagery.",
        "low": "Weak visual engagement. Upgrade image quality and use high-contrast design.",
    },
    "face_social": {
        "high": "Excellent human connection — faces and social proof are landing well.",
        "medium": "Add a real human face or testimonial to strengthen trust.",
        "low": "No human connection. Include a face, social proof, or people-focused visuals.",
    },
    "amygdala": {
        "high": "High emotional impact — your content creates a strong feeling response.",
        "medium": "Emotional resonance is moderate. Sharpen your hook — deeper desire or fear.",
        "low": "Low emotional impact. Add urgency, a pain point, or an aspirational outcome.",
    },
    "hippocampus": {
        "high": "Highly memorable — this content will stick.",
        "medium": "Memorability is average. Add a unique hook or unexpected element.",
        "low": "Easily forgotten. Use a surprising twist, strong story, or distinctive visual.",
    },
    "language_areas": {
        "high": "Clear, persuasive messaging — your language is working.",
        "medium": "Messaging clarity is moderate. Make the headline more direct and benefit-focused.",
        "low": "Weak messaging. Rewrite your headline for clarity and add a strong CTA.",
    },
    "reward_circuit": {
        "high": "Strong desire — your content makes people want it.",
        "medium": "Moderate desire. Make the value and transformation more tangible.",
        "low": "Low desire activation. Show the transformation clearly. Make the offer feel exclusive.",
    },
    "prefrontal": {
        "high": "Strong rational justification — trust signals are well established.",
        "medium": "Add more proof: statistics, guarantees, or reviews.",
        "low": "No rational justification. Add social proof, data, or credibility indicators.",
    },
    "motor_action": {
        "high": "Strong action drive — your content activates and moves people.",
        "medium": "Action drive is moderate. Use more energetic CTA words.",
        "low": "No action drive. Add an explicit, urgent CTA with action verbs.",
    },
}


def get_recommendations(scores: dict[str, int]) -> list[Recommendation]:
    from app.brain_mapper import REGIONS

    def level(s: int) -> tuple[str, str]:
        if s < 35:
            return "low", "high"
        if s < 65:
            return "medium", "medium"
        return "high", "ok"

    recs = []
    for key, score in scores.items():
        lvl, priority = level(score)
        recs.append(Recommendation(
            region_key=key,
            region_name=REGIONS[key]["name"],
            score=score,
            priority=priority,
            message=_ADVICE[key][lvl],
        ))

    recs.sort(key=lambda r: ({"high": 0, "medium": 1, "ok": 2}[r.priority], r.score))
    return recs
```

- [ ] **Step 4: Run tests**

```bash
cd backend && .venv/bin/pytest tests/test_brain_mapper.py -k "recs or priority" -v
```

Expected: all 3 pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/recommendation_engine.py backend/tests/test_brain_mapper.py
git commit -m "feat: recommendation engine with per-region marketing advice"
```

---

## Task 9: Content router + FastAPI app

**Files:**
- Create: `backend/app/content_processor.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_api.py`

- [ ] **Step 1: Write API tests**

```python
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd backend && .venv/bin/pytest tests/test_api.py -v 2>&1 | head -20
```

Expected: `ImportError`.

- [ ] **Step 3: Implement content_processor.py**

```python
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
```

- [ ] **Step 4: Implement main.py**

```python
# backend/app/main.py
from __future__ import annotations
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.content_processor import route_content
from app.recommendation_engine import get_recommendations

app = FastAPI(title="NeuroPulse API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _enrich(result: dict) -> dict:
    recs = get_recommendations(result["scores"])
    return {
        **result,
        "recommendations": [
            {"region_key": r.region_key, "region_name": r.region_name,
             "score": r.score, "priority": r.priority, "message": r.message}
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
        raise HTTPException(422, "Provide file, youtube_url, or text_content")
    with tempfile.TemporaryDirectory() as tmp:
        fp = None
        if file and file.filename:
            fp = os.path.join(tmp, file.filename)
            with open(fp, "wb") as f:
                f.write(await file.read())
        result = route_content(file_path=fp, youtube_url=youtube_url, text_content=text_content, tmp_dir=tmp)
    return _enrich(result)


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
            pa = os.path.join(tmp, "a_" + file_a.filename)
            with open(pa, "wb") as f:
                f.write(await file_a.read())
        if file_b and file_b.filename:
            pb = os.path.join(tmp, "b_" + file_b.filename)
            with open(pb, "wb") as f:
                f.write(await file_b.read())
        ra = route_content(file_path=pa, youtube_url=youtube_url_a, text_content=text_a, tmp_dir=tmp)
        rb = route_content(file_path=pb, youtube_url=youtube_url_b, text_content=text_b, tmp_dir=tmp)
    return {"a": _enrich(ra), "b": _enrich(rb)}


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run all tests**

```bash
cd backend && .venv/bin/pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Smoke test**

```bash
cd backend && .venv/bin/uvicorn app.main:app --port 8000 &
sleep 3
curl -s -X POST http://localhost:8000/analyze \
  -F "text_content=Buy our amazing product today! Life-changing results!" \
  | python3 -m json.tool | head -30
kill %1
```

Expected: JSON with `scores` (8 keys) and `recommendations` (8 items).

- [ ] **Step 7: Commit**

```bash
git add backend/app/content_processor.py backend/app/main.py backend/tests/test_api.py
git commit -m "feat: FastAPI app with /analyze and /compare endpoints"
```

---

## Task 10: Next.js frontend scaffold

**Files:**
- Create: `frontend/` (Next.js project)

- [ ] **Step 1: Bootstrap**

```bash
npx create-next-app@latest frontend \
  --typescript --tailwind --eslint --app --src-dir --no-import-alias
```

- [ ] **Step 2: Add dependencies**

```bash
cd frontend
npm install recharts lucide-react
npx shadcn@latest init --defaults
npx shadcn@latest add card badge button tabs separator
```

- [ ] **Step 3: Create shared types**

```typescript
// frontend/src/types/analysis.ts
export interface BrainScores {
  visual_cortex: number;
  face_social: number;
  amygdala: number;
  hippocampus: number;
  language_areas: number;
  reward_circuit: number;
  prefrontal: number;
  motor_action: number;
}

export interface Recommendation {
  region_key: keyof BrainScores;
  region_name: string;
  score: number;
  priority: "high" | "medium" | "ok";
  message: string;
}

export interface AnalysisResult {
  type: "image" | "video" | "youtube" | "pdf" | "text";
  scores: BrainScores;
  recommendations: Recommendation[];
  meta: Record<string, unknown>;
}

export interface CompareResult {
  a: AnalysisResult;
  b: AnalysisResult;
}
```

- [ ] **Step 4: Create API client**

```typescript
// frontend/src/lib/api.ts
import type { AnalysisResult, CompareResult } from "@/types/analysis";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function post(path: string, body: FormData): Promise<unknown> {
  const res = await fetch(`${BASE}${path}`, { method: "POST", body });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

export const analyzeFile = (file: File): Promise<AnalysisResult> => {
  const f = new FormData(); f.append("file", file);
  return post("/analyze", f) as Promise<AnalysisResult>;
};

export const analyzeYoutube = (url: string): Promise<AnalysisResult> => {
  const f = new FormData(); f.append("youtube_url", url);
  return post("/analyze", f) as Promise<AnalysisResult>;
};

export const analyzeText = (text: string): Promise<AnalysisResult> => {
  const f = new FormData(); f.append("text_content", text);
  return post("/analyze", f) as Promise<AnalysisResult>;
};

export const comparePair = (a: FormData, b: FormData): Promise<CompareResult> => {
  const f = new FormData();
  a.forEach((v, k) => f.append(k + "_a", v));
  b.forEach((v, k) => f.append(k + "_b", v));
  return post("/compare", f) as Promise<CompareResult>;
};
```

- [ ] **Step 5: Add env file**

```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > frontend/.env.local
```

- [ ] **Step 6: Verify build**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

Expected: `✓ Compiled successfully`.

- [ ] **Step 7: Commit**

```bash
cd .. && git add frontend/
git commit -m "feat: Next.js frontend scaffold with types and API client"
```

---

## Task 11: ContentUploader component

**Files:**
- Create: `frontend/src/components/ContentUploader.tsx`

- [ ] **Step 1: Implement**

```tsx
// frontend/src/components/ContentUploader.tsx
"use client";
import { useState, useCallback } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Upload, Link, FileText, Loader2 } from "lucide-react";

interface Props {
  onResult: (result: unknown) => void;
  onError: (msg: string) => void;
  label?: string;
}

export function ContentUploader({ onResult, onError, label }: Props) {
  const [loading, setLoading] = useState(false);
  const [ytUrl, setYtUrl] = useState("");
  const [txt, setTxt] = useState("");
  const [dragging, setDragging] = useState(false);

  const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  async function submit(form: FormData) {
    setLoading(true);
    try {
      const res = await fetch(`${BASE}/analyze`, { method: "POST", body: form });
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
      onResult(await res.json());
    } catch (e) {
      onError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  const handleFile = useCallback((file: File) => {
    const f = new FormData(); f.append("file", file); submit(f);
  }, []);

  return (
    <div className="w-full max-w-xl">
      {label && <p className="text-sm font-medium text-muted-foreground mb-2">{label}</p>}
      <Tabs defaultValue="file">
        <TabsList className="w-full">
          <TabsTrigger value="file" className="flex-1"><Upload className="w-4 h-4 mr-1" />File</TabsTrigger>
          <TabsTrigger value="youtube" className="flex-1"><Link className="w-4 h-4 mr-1" />YouTube</TabsTrigger>
          <TabsTrigger value="text" className="flex-1"><FileText className="w-4 h-4 mr-1" />Text</TabsTrigger>
        </TabsList>

        <TabsContent value="file">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
            onClick={() => document.getElementById("file-in")?.click()}
            className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${dragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"}`}
          >
            <Upload className="w-8 h-8 mx-auto mb-3 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Drop image, video, or PDF<br />
              <span className="text-xs">JPG PNG MP4 MOV PDF supported</span>
            </p>
            <input id="file-in" type="file" className="hidden"
              accept=".jpg,.jpeg,.png,.gif,.webp,.mp4,.mov,.avi,.pdf"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
          </div>
        </TabsContent>

        <TabsContent value="youtube">
          <div className="flex gap-2 mt-2">
            <input type="url" value={ytUrl} onChange={(e) => setYtUrl(e.target.value)}
              placeholder="https://youtube.com/watch?v=..."
              className="flex-1 px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary" />
            <Button disabled={!ytUrl || loading} onClick={() => { const f = new FormData(); f.append("youtube_url", ytUrl); submit(f); }}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Analyze"}
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="text">
          <textarea value={txt} onChange={(e) => setTxt(e.target.value)}
            placeholder="Paste ad copy, script, book chapter, or any text..."
            rows={5}
            className="w-full px-3 py-2 text-sm border rounded-lg bg-background resize-none focus:outline-none focus:ring-2 focus:ring-primary mt-2" />
          <Button disabled={!txt.trim() || loading} className="w-full mt-2"
            onClick={() => { const f = new FormData(); f.append("text_content", txt); submit(f); }}>
            {loading ? <><Loader2 className="w-4 h-4 animate-spin mr-2" />Analyzing...</> : "Analyze Brain Response"}
          </Button>
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

- [ ] **Step 2: Build check**

```bash
cd frontend && npm run build 2>&1 | grep -c "error"
```

Expected: `0`.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ContentUploader.tsx
git commit -m "feat: ContentUploader component"
```

---

## Task 12: BrainRadarChart component

**Files:**
- Create: `frontend/src/components/BrainRadarChart.tsx`

- [ ] **Step 1: Implement**

```tsx
// frontend/src/components/BrainRadarChart.tsx
"use client";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from "recharts";
import type { BrainScores } from "@/types/analysis";

const LABELS: Record<keyof BrainScores, string> = {
  visual_cortex: "Visual",
  face_social: "Social",
  amygdala: "Emotion",
  hippocampus: "Memory",
  language_areas: "Language",
  reward_circuit: "Reward",
  prefrontal: "Decision",
  motor_action: "Action",
};

interface Props {
  scores: BrainScores;
  compareScores?: BrainScores;
  color?: string;
  compareColor?: string;
}

export function BrainRadarChart({ scores, compareScores, color = "#6366f1", compareColor = "#f59e0b" }: Props) {
  const data = (Object.keys(LABELS) as (keyof BrainScores)[]).map((k) => ({
    region: LABELS[k], A: scores[k], B: compareScores?.[k],
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis dataKey="region" tick={{ fontSize: 12, fill: "#6b7280" }} />
        <Tooltip formatter={(v: number, name: string) => [`${v}/100`, name === "A" ? "Content" : "Compare"]} />
        <Radar name="A" dataKey="A" stroke={color} fill={color} fillOpacity={0.25} strokeWidth={2} />
        {compareScores && (
          <Radar name="B" dataKey="B" stroke={compareColor} fill={compareColor} fillOpacity={0.15} strokeWidth={2} />
        )}
      </RadarChart>
    </ResponsiveContainer>
  );
}
```

- [ ] **Step 2: Build check**

```bash
cd frontend && npm run build 2>&1 | grep "error" | head -5
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/BrainRadarChart.tsx
git commit -m "feat: BrainRadarChart with Recharts radar"
```

---

## Task 13: RegionCard + RecommendationPanel

**Files:**
- Create: `frontend/src/components/RegionCard.tsx`
- Create: `frontend/src/components/RecommendationPanel.tsx`

- [ ] **Step 1: Implement RegionCard**

```tsx
// frontend/src/components/RegionCard.tsx
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { BrainScores } from "@/types/analysis";

const META: Record<keyof BrainScores, { name: string; sub: string }> = {
  visual_cortex: { name: "Visual Cortex", sub: "Visual appeal" },
  face_social:   { name: "Face & Social", sub: "Human connection" },
  amygdala:      { name: "Emotional Core", sub: "Emotional impact" },
  hippocampus:   { name: "Memory", sub: "Memorability" },
  language_areas:{ name: "Language Areas", sub: "Message clarity" },
  reward_circuit:{ name: "Reward Circuit", sub: "Desire & intent" },
  prefrontal:    { name: "Decision Center", sub: "Trust & proof" },
  motor_action:  { name: "Action Drive", sub: "CTA activation" },
};

function bar(score: number) {
  if (score >= 65) return "bg-emerald-500";
  if (score >= 35) return "bg-amber-500";
  return "bg-rose-500";
}

export function RegionCard({ regionKey, score }: { regionKey: keyof BrainScores; score: number }) {
  const m = META[regionKey];
  const label = score >= 65 ? "Strong" : score >= 35 ? "Moderate" : "Weak";
  const variant: "default" | "secondary" | "destructive" = score >= 65 ? "default" : score >= 35 ? "secondary" : "destructive";
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <div>
            <p className="text-sm font-semibold">{m.name}</p>
            <p className="text-xs text-muted-foreground">{m.sub}</p>
          </div>
          <Badge variant={variant}>{label}</Badge>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
            <div className={`h-full rounded-full transition-all ${bar(score)}`} style={{ width: `${score}%` }} />
          </div>
          <span className="text-sm font-mono font-bold w-8 text-right">{score}</span>
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Implement RecommendationPanel**

```tsx
// frontend/src/components/RecommendationPanel.tsx
import type { Recommendation } from "@/types/analysis";
import { AlertCircle, AlertTriangle, CheckCircle2 } from "lucide-react";

const ICON = {
  high:   <AlertCircle   className="w-4 h-4 text-rose-500    shrink-0 mt-0.5" />,
  medium: <AlertTriangle className="w-4 h-4 text-amber-500   shrink-0 mt-0.5" />,
  ok:     <CheckCircle2  className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />,
};

const BG = {
  high:   "bg-rose-50    border-rose-100    dark:bg-rose-950/20    dark:border-rose-900",
  medium: "bg-amber-50   border-amber-100   dark:bg-amber-950/20   dark:border-amber-900",
  ok:     "bg-emerald-50 border-emerald-100 dark:bg-emerald-950/20 dark:border-emerald-900",
};

export function RecommendationPanel({ recommendations, showOk = false }: { recommendations: Recommendation[]; showOk?: boolean }) {
  const visible = showOk ? recommendations : recommendations.filter((r) => r.priority !== "ok");
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Optimization</h3>
      {visible.map((r) => (
        <div key={r.region_key} className={`flex gap-3 p-3 rounded-lg border text-sm ${BG[r.priority]}`}>
          {ICON[r.priority]}
          <div><span className="font-medium">{r.region_name}: </span>{r.message}</div>
        </div>
      ))}
      {visible.length === 0 && (
        <p className="text-sm text-muted-foreground italic">All regions scoring well.</p>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Build check**

```bash
cd frontend && npm run build 2>&1 | grep -c "error"
```

Expected: `0`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/RegionCard.tsx frontend/src/components/RecommendationPanel.tsx
git commit -m "feat: RegionCard and RecommendationPanel"
```

---

## Task 14: Pages

**Files:**
- Modify: `frontend/src/app/layout.tsx`
- Modify: `frontend/src/app/page.tsx`
- Create: `frontend/src/app/analysis/page.tsx`
- Create: `frontend/src/app/compare/page.tsx`

- [ ] **Step 1: Update layout.tsx**

```tsx
// frontend/src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "NeuroPulse — Brain Analysis for Marketing",
  description: "See how your content activates key brain regions",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

- [ ] **Step 2: Implement home page**

```tsx
// frontend/src/app/page.tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ContentUploader } from "@/components/ContentUploader";

export default function Home() {
  const router = useRouter();
  const [err, setErr] = useState<string | null>(null);

  function handleResult(result: unknown) {
    sessionStorage.setItem("np_result", JSON.stringify(result));
    router.push("/analysis");
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 py-16">
      <div className="text-center mb-10 max-w-xl">
        <h1 className="text-4xl font-bold tracking-tight mb-3">NeuroPulse</h1>
        <p className="text-muted-foreground text-lg">
          Analyze how your marketing content activates the brain.<br />
          Image, video, YouTube, PDF, or plain text.
        </p>
      </div>
      <ContentUploader onResult={handleResult} onError={setErr} />
      {err && <p className="mt-4 text-sm text-rose-500 text-center max-w-sm">{err}</p>}
      <p className="mt-8 text-xs text-muted-foreground">Runs fully local — your content never leaves your machine.</p>
    </main>
  );
}
```

- [ ] **Step 3: Implement analysis page**

```tsx
// frontend/src/app/analysis/page.tsx
"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BrainRadarChart } from "@/components/BrainRadarChart";
import { RegionCard } from "@/components/RegionCard";
import { RecommendationPanel } from "@/components/RecommendationPanel";
import { Button } from "@/components/ui/button";
import { ArrowLeft, BarChart2 } from "lucide-react";
import type { AnalysisResult, BrainScores } from "@/types/analysis";

export default function AnalysisPage() {
  const router = useRouter();
  const [result, setResult] = useState<AnalysisResult | null>(null);

  useEffect(() => {
    const raw = sessionStorage.getItem("np_result");
    if (!raw) { router.push("/"); return; }
    setResult(JSON.parse(raw));
  }, [router]);

  if (!result) return null;

  const keys = Object.keys(result.scores) as (keyof BrainScores)[];
  const avg = Math.round(Object.values(result.scores).reduce((a, b) => a + b, 0) / keys.length);

  return (
    <main className="min-h-screen px-4 py-10 max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-8">
        <Button variant="ghost" size="sm" onClick={() => router.push("/")}>
          <ArrowLeft className="w-4 h-4 mr-1" /> New
        </Button>
        <Button variant="outline" size="sm" onClick={() => router.push("/compare")}>
          <BarChart2 className="w-4 h-4 mr-1" /> Compare
        </Button>
      </div>

      <div className="grid md:grid-cols-2 gap-8 mb-8">
        <div>
          <h2 className="text-2xl font-bold mb-1">Brain Activation</h2>
          <p className="text-muted-foreground text-sm mb-4">
            Overall: <span className="font-semibold text-foreground">{avg}/100</span>
            <span className="ml-2 capitalize text-xs">({result.type})</span>
          </p>
          <BrainRadarChart scores={result.scores} />
        </div>
        <div className="space-y-2">
          <h3 className="font-semibold mb-3">Region Breakdown</h3>
          {keys.map((k) => <RegionCard key={k} regionKey={k} score={result.scores[k]} />)}
        </div>
      </div>

      <RecommendationPanel recommendations={result.recommendations} />
    </main>
  );
}
```

- [ ] **Step 4: Implement compare page**

```tsx
// frontend/src/app/compare/page.tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { BrainRadarChart } from "@/components/BrainRadarChart";
import { RegionCard } from "@/components/RegionCard";
import { RecommendationPanel } from "@/components/RecommendationPanel";
import { ContentUploader } from "@/components/ContentUploader";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import type { AnalysisResult, BrainScores } from "@/types/analysis";

export default function ComparePage() {
  const router = useRouter();
  const [a, setA] = useState<AnalysisResult | null>(null);
  const [b, setB] = useState<AnalysisResult | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const keys = a ? (Object.keys(a.scores) as (keyof BrainScores)[]) : [];

  return (
    <main className="min-h-screen px-4 py-10 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-8">
        <Button variant="ghost" size="sm" onClick={() => router.push("/")}>
          <ArrowLeft className="w-4 h-4 mr-1" /> Back
        </Button>
        <h1 className="text-2xl font-bold">A/B Brain Comparison</h1>
      </div>

      {!(a && b) && (
        <div className="grid md:grid-cols-2 gap-8">
          <ContentUploader label="Content A" onResult={(r) => setA(r as AnalysisResult)} onError={setErr} />
          <ContentUploader label="Content B" onResult={(r) => setB(r as AnalysisResult)} onError={setErr} />
        </div>
      )}
      {err && <p className="text-sm text-rose-500 mt-4">{err}</p>}

      {a && b && (
        <>
          <div className="grid md:grid-cols-2 gap-8 mb-8">
            <div>
              <h3 className="font-semibold mb-2 text-indigo-500">Content A vs B</h3>
              <BrainRadarChart scores={a.scores} compareScores={b.scores} />
            </div>
            <div className="space-y-2">
              {keys.map((k) => (
                <div key={k} className="grid grid-cols-2 gap-2">
                  <RegionCard regionKey={k} score={a.scores[k]} />
                  <RegionCard regionKey={k} score={b.scores[k]} />
                </div>
              ))}
            </div>
          </div>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <p className="text-sm font-semibold text-indigo-500 mb-2">A — Recommendations</p>
              <RecommendationPanel recommendations={a.recommendations} />
            </div>
            <div>
              <p className="text-sm font-semibold text-amber-500 mb-2">B — Recommendations</p>
              <RecommendationPanel recommendations={b.recommendations} />
            </div>
          </div>
          <Button variant="outline" className="mt-8" onClick={() => { setA(null); setB(null); }}>
            New Comparison
          </Button>
        </>
      )}
    </main>
  );
}
```

- [ ] **Step 5: Build check**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

Expected: `✓ Compiled successfully`.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/
git commit -m "feat: home, analysis, and compare pages"
```

---

## Task 15: Root start script + README

**Files:**
- Create: `start.sh`
- Create: `README.md`

- [ ] **Step 1: Root start script**

```bash
#!/usr/bin/env bash
# start.sh
set -e
echo "Starting NeuroPulse..."
(cd backend && bash start.sh) &
BPID=$!
(cd frontend && npm run dev) &
FPID=$!
trap "kill $BPID $FPID 2>/dev/null" EXIT
echo "Backend  → http://localhost:8000"
echo "Frontend → http://localhost:3000"
wait
```

```bash
chmod +x start.sh
```

- [ ] **Step 2: README**

```markdown
# NeuroPulse

Predicts how marketing content activates brain regions — locally, free, no GPU.

## Inputs

| Type | How |
|---|---|
| Image | Upload JPG/PNG (ads, screenshots) |
| Video | Upload MP4/MOV |
| YouTube | Paste URL |
| PDF | Upload (books, scripts) |
| Text | Paste any copy |

## Quick start

Requires: Python 3.11+, Node.js 18+, ffmpeg (`brew install ffmpeg`)

```bash
git clone <repo> && cd neurolens
bash start.sh
```

Open http://localhost:3000. First run downloads ~600 MB of model weights (cached after that).

## How it works

CLIP ViT-B/32 encodes content into semantic embeddings. These are scored against neuroscience-informed probe texts for 8 brain regions (Visual Cortex, Face/Social, Emotional Core, Memory, Language, Reward Circuit, Decision Center, Action Drive). No cloud, no GPU, no API keys.

## Stack

Backend: Python FastAPI + CLIP + Whisper + yt-dlp  
Frontend: Next.js 14 + Recharts + shadcn/ui
```

- [ ] **Step 3: Final test run**

```bash
cd backend && .venv/bin/pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: all tests pass, no failures.

- [ ] **Step 4: Commit**

```bash
cd ..
git add start.sh README.md
git commit -m "feat: root start script and README — NeuroPulse v1 complete"
```

---

## Self-Review

### Spec coverage

| Requirement | Task |
|---|---|
| No servers / no cash | CLIP CPU inference, no cloud deps |
| YouTube input | Task 7 |
| PDF/book input | Task 5 |
| Image/video | Tasks 3, 6 |
| Text/script | Task 4 |
| Brain activation visualization | Task 12 |
| Per-region breakdown | Task 13 |
| Marketing recommendations | Tasks 8, 13 |
| A/B comparison | Tasks 9, 14 |

### Type consistency check

- `BrainScores` defined Task 10, used consistently Tasks 12–14
- Python `Recommendation` dataclass fields (`region_key`, `region_name`, `score`, `priority`, `message`) match TypeScript `Recommendation` interface exactly
- `route_content()` signature in `content_processor.py` and `main.py` use identical kwargs
- `get_brain_scores()` kwargs (`image`, `images`, `text`, `texts`) used correctly in all processors
- All 8 region keys are consistent across `REGIONS` dict, `_ADVICE` dict, `META` (frontend), and `LABELS` (frontend)

### Placeholder scan

No TBD, TODO, or placeholder patterns found. All code blocks are complete and self-contained.
