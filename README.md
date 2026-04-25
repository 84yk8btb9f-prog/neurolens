# NeuroPulse

Drop in any ad — video, image, or copy. See how the brain reacts before you spend a dollar promoting it.

NeuroPulse is an open-source brain-response analysis tool for marketing content. It scores creative across 8 brain regions, gives you actionable recommendations, and lets you analyze content through the lens of well-known direct-response creators.

Runs fully local. No GPU. No API keys. No cloud calls.

## What it does

- Score any image, video, YouTube/TikTok/Instagram URL, PDF, or text across 8 brain regions
- Get a single-line verdict that tells you the weakest spot up front (e.g. *"Forgettable — this won't stick in memory five minutes after viewing"*)
- See per-region breakdowns and concrete recommendations
- Compare two pieces of content side-by-side
- Apply Creator Personas (Hormozi, GaryVee, Brunson, Yadegari, or your own) to layer creator-style tactical steps onto recommendations
- Save analyses as named projects and share read-only links

## What it isn't

- Not a peer-reviewed neuroscience instrument. Scores are derived from CLIP semantic embeddings against neuroscience-informed probe texts. Treat the output as a creative review heuristic, not a clinical signal.
- Not a substitute for real performance data. If you have ROAS / CTR / conversion data, use it.
- Not a hosted product. There's no auth, billing, or multi-user mode. Run it yourself.

## Quick start

Requires: Python 3.11+, Node.js 18+, ffmpeg (`brew install ffmpeg`).

```bash
git clone https://github.com/84yk8btb9f-prog/neurolens
cd neurolens
bash start.sh
```

Open http://localhost:3000. First run downloads ~600 MB of model weights (cached after that).

## How it works

CLIP ViT-B/32 encodes content into semantic embeddings. Those embeddings are scored against curated probe texts mapped to 8 brain regions:

| Region | What it captures |
|---|---|
| Visual Cortex | Whether the visual hook pulls attention |
| Face & Social | Human presence and trust signal |
| Amygdala | Emotional charge |
| Hippocampus | Memorability and narrative arc |
| Language Areas | Copy clarity and voice |
| Reward Circuit | Payoff signal — what's in it for them |
| Prefrontal Cortex | Logical proof and reasons to believe |
| Motor Action | Strength of the call to action |

Personas (Hormozi, GaryVee, Brunson, Yadegari) are stored in SQLite and editable from the `/personas` page — add your own without touching code.

## Stack

- **Backend:** FastAPI + SQLite + CLIP + Whisper + yt-dlp
- **Frontend:** Next.js App Router + shadcn/ui + Recharts + Tailwind
- **Storage:** Local SQLite (no Postgres, no cloud)

## Project structure

```
backend/
  app/
    main.py                 FastAPI routes
    content_processor.py    Routes uploads to the right processor
    brain_mapper.py         CLIP probe scoring
    recommendation_engine.py
    headline.py             One-line verdict generator
    personas.py             Persona application
    persona_storage.py      SQLite CRUD for personas
    storage.py              SQLite CRUD for projects + share tokens
    processors/             Per-format processors (image, video, pdf, youtube, text)
  tests/                    Pytest suite (122 tests)

frontend/
  src/
    app/                    Next.js routes (/, /analysis, /compare, /projects, /personas, /share/[token])
    components/             BrainRadarChart, RegionCard, RecommendationPanel, Headline, ShareButton, PersonaSelector, ...
    lib/api.ts              Backend client
    types/analysis.ts       Shared types
```

## Contributing

This is a side project / portfolio piece. PRs welcome — keep them tight and tested. Run `pytest tests/` for the backend and `npx tsc --noEmit` for the frontend before opening a PR.

## License

MIT.
