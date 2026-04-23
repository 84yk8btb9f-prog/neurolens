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
