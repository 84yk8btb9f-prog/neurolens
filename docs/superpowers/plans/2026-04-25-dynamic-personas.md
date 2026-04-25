# Dynamic Persona Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move creator personas from hardcoded Python into SQLite so users can add, edit, and delete personas from a management UI without touching source code.

**Architecture:** A new `persona_storage.py` module (same SQLite pattern as `storage.py`) seeds the 4 existing personas on first run and exposes CRUD methods. `personas.py` is refactored to delegate `list_personas()` and `get_persona()` to storage — `apply_persona()` and `Persona` dataclass are unchanged. Five new REST endpoints (`GET/POST /personas`, `GET/PUT/DELETE /personas/{id}`) land in `main.py`. A management page at `/personas` lets users add/edit/delete personas using a textarea-per-brain-region form. The existing `PersonaSelector` already fetches from the API and needs only a "Manage" link added.

**Tech Stack:** Python `sqlite3` (stdlib), FastAPI, Pydantic, Next.js App Router, shadcn/ui, lucide-react

---

## File Structure

**Create:**
- `backend/app/persona_storage.py` — SQLite CRUD for personas + seed data
- `backend/tests/test_persona_storage.py` — 11 unit tests
- `frontend/src/app/personas/page.tsx` — management page (list + create/edit form)

**Modify:**
- `backend/app/personas.py` — remove `_PERSONAS` dict; delegate `list_personas()` and `get_persona()` to storage
- `backend/app/main.py` — add `PersonaRequest` model + 5 CRUD endpoints; update existing `/personas` GET to include `id`
- `backend/tests/test_personas.py` — add `autouse` fixture that patches `app.personas.get_persona_storage`
- `backend/tests/test_main.py` — add `mock_persona_storage` fixture + 5 persona endpoint tests
- `frontend/src/types/analysis.ts` — add `PersonaSummary` and `PersonaDetail` interfaces
- `frontend/src/lib/api.ts` — add persona CRUD API functions
- `frontend/src/components/PersonaSelector.tsx` — add "Manage" link at bottom

---

### Task 1: Backend persona storage module

**Files:**
- Create: `backend/app/persona_storage.py`
- Create: `backend/tests/test_persona_storage.py`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_persona_storage.py
import pytest
from app.persona_storage import PersonaStorage


@pytest.fixture
def store(tmp_path):
    s = PersonaStorage(str(tmp_path / "personas.db"))
    s.init()
    return s


def test_init_seeds_four_default_personas(store):
    personas = store.list_all()
    assert len(personas) == 4
    keys = [p["key"] for p in personas]
    assert "hormozi" in keys
    assert "garyvee" in keys
    assert "brunson" in keys
    assert "yadegari" in keys


def test_init_idempotent(store):
    store.init()
    assert len(store.list_all()) == 4


def test_save_custom_persona(store):
    pid = store.save("my-creator", "My Creator", "My tagline", {"amygdala": ["Do X", "Do Y"]})
    personas = store.list_all()
    assert len(personas) == 5
    assert any(p["key"] == "my-creator" for p in personas)
    assert pid > 0


def test_get_by_id(store):
    pid = store.save("test", "Test", "tagline", {"amygdala": ["Step A"]})
    persona = store.get_by_id(pid)
    assert persona is not None
    assert persona["key"] == "test"
    assert persona["step_overlays"]["amygdala"] == ["Step A"]


def test_get_by_key(store):
    persona = store.get_by_key("hormozi")
    assert persona is not None
    assert persona["name"] == "Alex Hormozi"
    assert "amygdala" in persona["step_overlays"]


def test_get_by_key_nonexistent(store):
    assert store.get_by_key("nonexistent") is None


def test_get_by_key_default_returns_none(store):
    assert store.get_by_key("default") is None
    assert store.get_by_key("") is None
    assert store.get_by_key(None) is None


def test_update_persona(store):
    pid = store.save("old-key", "Old Name", "old tagline", {})
    result = store.update(pid, "new-key", "New Name", "new tagline", {"amygdala": ["Updated step"]})
    assert result is True
    updated = store.get_by_id(pid)
    assert updated["key"] == "new-key"
    assert updated["name"] == "New Name"
    assert updated["step_overlays"]["amygdala"] == ["Updated step"]


def test_update_nonexistent(store):
    assert store.update(9999, "k", "n", "t", {}) is False


def test_delete_persona(store):
    pid = store.save("del-me", "Delete Me", "", {})
    assert store.delete(pid) is True
    assert store.get_by_id(pid) is None


def test_delete_nonexistent(store):
    assert store.delete(9999) is False
```

- [ ] **Step 2: Run tests, verify they fail**

```bash
cd /Users/nikolassapalidis/neurolens/backend && source .venv/bin/activate && pytest tests/test_persona_storage.py -v
```
Expected: `ModuleNotFoundError: No module named 'app.persona_storage'`

- [ ] **Step 3: Create persona_storage.py**

```python
# backend/app/persona_storage.py
from __future__ import annotations
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

_DEFAULT_DB = Path(__file__).parent / "data" / "personas.db"

_SEED_DATA = [
    {
        "key": "hormozi",
        "name": "Alex Hormozi",
        "tagline": "Direct response. Quantify everything. Stack the value.",
        "step_overlays": {
            "amygdala": [
                "Quantify the pain with a number: replace 'bad sleep' with '3 years of waking up at 3am cost me $40k in productivity'",
                "Use the before/after contrast with specific states: 'Before: can't focus past 2pm. After: working until 8pm with energy to spare'",
            ],
            "reward_circuit": [
                "Build a value stack: list every component with a dollar value, then reveal the price ('worth $4,200, yours for $97')",
                "Use the 'Godfather Offer': make it so good they feel stupid saying no — quantify every element",
            ],
            "face_social": [
                "Replace vague testimonials with specific results: '$8,400 in 30 days' beats 'it changed my life'",
                "Show the avatar: the person giving the testimonial should look exactly like your buyer",
            ],
            "prefrontal": [
                "Add a Grand Slam guarantee: 'If you don't [specific result] in [timeframe], I'll [refund + extra]'",
                "Address the top objection directly with data: 'Still skeptical? Here's what happened to the 847 people who felt the same way'",
            ],
            "motor_action": [
                "Tie the CTA verb to value: 'Claim your free audit' not 'Submit'",
                "Use scarcity with a reason: 'We only onboard 12 clients/month because each gets a personal call with me'",
            ],
            "language_areas": [
                "Lead with the outcome, not the feature: '8 minutes to sleep' not 'Advanced sleep formula with proprietary blend'",
                "Cut word count by 40%: every word must earn its place or it gets cut",
            ],
        },
    },
    {
        "key": "garyvee",
        "name": "Gary Vaynerchuk",
        "tagline": "Native to the platform. Authentic. Volume over perfection.",
        "step_overlays": {
            "visual_cortex": [
                "Make it feel native: remove polish that makes it look like an ad — raw, spontaneous content wins on social",
                "Use the format the platform is currently rewarding: check what format is going viral this week and match it",
            ],
            "face_social": [
                "Document, don't create: show the behind-the-scenes process, not the highlight reel",
                "Direct eye contact to camera for at least the first 3 seconds — treat it like a 1-on-1 conversation",
            ],
            "amygdala": [
                "Lead with empathy, not pain: 'I know you're feeling X' lands softer but builds more trust than fear tactics",
                "Tell a real story from your life that connects to the viewer's situation — specific and personal beats polished",
            ],
            "motor_action": [
                "Keep the CTA low-commitment: 'comment below', 'DM me', 'save this' — micro-asks build the relationship",
                "Post the same concept in 5 different formats and let the data tell you which one to scale",
            ],
            "language_areas": [
                "Write like you talk: read the copy out loud — if it sounds like a press release, rewrite it",
                "Use platform-native slang and references — shows you're actually on the platform, not just advertising on it",
            ],
            "hippocampus": [
                "Create a recurring series: a consistent format, time, and hook builds pattern recognition and recall",
                "End with a callback to the beginning — 'remember what I said at the start? Here's the twist'",
            ],
        },
    },
    {
        "key": "brunson",
        "name": "Russell Brunson",
        "tagline": "Hook. Story. Offer. The funnel starts here.",
        "step_overlays": {
            "amygdala": [
                "Use the Epiphany Bridge: share the moment YOU discovered the solution — make the viewer feel the same aha moment",
                "Trigger identity: 'People like us do things like this' — connect the product to who they want to become",
            ],
            "hippocampus": [
                "Structure as a 3-act story: the struggle (problem), the wall (everything failed), the discovery (your solution)",
                "Use the 'future pacing' technique: paint a vivid picture of their life 30 days after buying",
            ],
            "reward_circuit": [
                "Create a 'false close': present the full offer, then add a bonus that makes saying no feel like a mistake",
                "Use the 'OTO stack': show the core offer, then add time-sensitive bonuses one by one to build desire",
            ],
            "prefrontal": [
                "Show the 'big domino': identify the ONE belief that, if true, makes all objections irrelevant — then prove that belief",
                "Use the 'Feel/Felt/Found' framework: 'I know how you feel, I felt the same, here's what I found'",
            ],
            "motor_action": [
                "Use a 'click trigger' just before the CTA: remind them of the pain, then the solution, then make the ask",
                "Make the CTA a logical next step in the story, not a sales pitch: 'The next step is...'",
            ],
            "face_social": [
                "Lead with your hero's journey: you were where they are, you found the secret, now you're sharing it",
                "Use a 'character' throughout the ad — consistent protagonist makes the story memorable and trustworthy",
            ],
        },
    },
    {
        "key": "yadegari",
        "name": "Zack Yadegari",
        "tagline": "Personal brand. Aspirational. Community-first.",
        "step_overlays": {
            "face_social": [
                "Lead with your authentic self — show the real person behind the brand, not a polished spokesperson",
                "Build parasocial connection: use 'we' language and reference your community directly ('you guys asked me about...')",
            ],
            "visual_cortex": [
                "Invest in lifestyle visuals that match the aspirational identity your audience wants — environments matter as much as people",
                "Use consistent color grading and visual style across all content to build instant brand recognition",
            ],
            "amygdala": [
                "Lean into aspiration over pain: show them the life they want, not the problem they have",
                "Create FOMO through community: 'Everyone in our community is already doing X — here's how to join them'",
            ],
            "hippocampus": [
                "Build a catchphrase or visual signature that anchors your brand — repeat it in every piece of content",
                "Document milestones and growth: 'When I started 2 years ago vs now' creates narrative arc and loyalty",
            ],
            "motor_action": [
                "Use community CTAs: 'Join X people who already...' makes the action feel like belonging, not buying",
                "Invite participation: 'comment your version below', 'tag someone who needs this' — action as connection",
            ],
            "reward_circuit": [
                "Sell the identity transformation, not the product: 'You're not buying a program, you're becoming the person who...'",
                "Use exclusivity as aspiration: 'This is for people who are serious about X' — make them qualify to buy",
            ],
        },
    },
]


class PersonaStorage:
    def __init__(self, db_path: str | Path = _DEFAULT_DB):
        self._path = str(db_path)

    def init(self) -> None:
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS personas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    tagline TEXT NOT NULL DEFAULT '',
                    step_overlays_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            count = conn.execute("SELECT COUNT(*) FROM personas").fetchone()[0]
            if count == 0:
                for p in _SEED_DATA:
                    conn.execute(
                        "INSERT INTO personas (key, name, tagline, step_overlays_json) VALUES (?, ?, ?, ?)",
                        (p["key"], p["name"], p["tagline"], json.dumps(p["step_overlays"])),
                    )

    def list_all(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, key, name, tagline FROM personas ORDER BY id ASC"
            ).fetchall()
        return [{"id": r[0], "key": r[1], "name": r[2], "tagline": r[3]} for r in rows]

    def get_by_id(self, persona_id: int) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, key, name, tagline, step_overlays_json FROM personas WHERE id = ?",
                (persona_id,),
            ).fetchone()
        if row is None:
            return None
        return {"id": row[0], "key": row[1], "name": row[2], "tagline": row[3], "step_overlays": json.loads(row[4])}

    def get_by_key(self, key: str | None) -> dict | None:
        if not key or key == "default":
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, key, name, tagline, step_overlays_json FROM personas WHERE key = ?",
                (key,),
            ).fetchone()
        if row is None:
            return None
        return {"id": row[0], "key": row[1], "name": row[2], "tagline": row[3], "step_overlays": json.loads(row[4])}

    def save(self, key: str, name: str, tagline: str, step_overlays: dict) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO personas (key, name, tagline, step_overlays_json) VALUES (?, ?, ?, ?)",
                (key, name, tagline, json.dumps(step_overlays)),
            )
            row_id = cur.lastrowid
            if row_id is None:
                raise RuntimeError("INSERT succeeded but returned no row ID")
            return row_id

    def update(self, persona_id: int, key: str, name: str, tagline: str, step_overlays: dict) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE personas SET key=?, name=?, tagline=?, step_overlays_json=? WHERE id=?",
                (key, name, tagline, json.dumps(step_overlays), persona_id),
            )
            return cur.rowcount > 0

    def delete(self, persona_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM personas WHERE id = ?", (persona_id,))
            return cur.rowcount > 0

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._path)
        conn.execute("PRAGMA journal_mode=WAL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


_store = PersonaStorage()
_store.init()


def get_persona_storage() -> PersonaStorage:
    return _store
```

- [ ] **Step 4: Run tests, verify they pass**

```bash
cd /Users/nikolassapalidis/neurolens/backend && source .venv/bin/activate && pytest tests/test_persona_storage.py -v
```
Expected: 11 tests passing.

- [ ] **Step 5: Commit**

```bash
cd /Users/nikolassapalidis/neurolens/backend && git add app/persona_storage.py tests/test_persona_storage.py && git commit -m "feat: SQLite persona storage with seed data"
```

---

### Task 2: Refactor personas.py to use storage + update test_personas.py

**Files:**
- Modify: `backend/app/personas.py`
- Modify: `backend/tests/test_personas.py`

- [ ] **Step 1: Run existing persona tests to capture baseline**

```bash
cd /Users/nikolassapalidis/neurolens/backend && source .venv/bin/activate && pytest tests/test_personas.py -v
```
Expected: 9 tests passing. Record which tests pass so you can verify they still pass after the refactor.

- [ ] **Step 2: Rewrite personas.py**

Replace the entire content of `backend/app/personas.py` with:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from app.persona_storage import get_persona_storage


@dataclass
class Persona:
    key: str
    name: str
    tagline: str
    step_overlays: dict[str, list[str]] = field(default_factory=dict)


def list_personas() -> list[dict]:
    return get_persona_storage().list_all()


def get_persona(key: str | None) -> Persona | None:
    if not key or key == "default":
        return None
    row = get_persona_storage().get_by_key(key)
    if row is None:
        return None
    return Persona(
        key=row["key"],
        name=row["name"],
        tagline=row["tagline"],
        step_overlays=row["step_overlays"],
    )


def apply_persona(persona_key: str | None, recommendations: list) -> None:
    """Prepends persona-specific steps to matching recommendations in-place."""
    persona = get_persona(persona_key)
    if persona is None:
        return
    for rec in recommendations:
        extra = persona.step_overlays.get(rec.region_key, [])
        if extra:
            rec.steps = extra + rec.steps
```

- [ ] **Step 3: Update test_personas.py to mock storage**

Add a `mock_persona_storage` fixture at the top of `backend/tests/test_personas.py`, after the existing imports. The fixture must be `autouse=True` so every test uses the temp DB:

```python
# Add these imports at the top:
import pytest
from unittest.mock import patch
from app.persona_storage import PersonaStorage

# Add this fixture before the first test:
@pytest.fixture(autouse=True)
def mock_persona_storage(tmp_path):
    store = PersonaStorage(str(tmp_path / "test_personas.db"))
    store.init()
    with patch("app.personas.get_persona_storage", return_value=store):
        yield store
```

The full updated `backend/tests/test_personas.py` must be:

```python
import pytest
from unittest.mock import patch
from app.persona_storage import PersonaStorage
from app.personas import get_persona, list_personas, apply_persona
from app.recommendation_engine import Recommendation, get_recommendations


@pytest.fixture(autouse=True)
def mock_persona_storage(tmp_path):
    store = PersonaStorage(str(tmp_path / "test_personas.db"))
    store.init()
    with patch("app.personas.get_persona_storage", return_value=store):
        yield store


def _rec(region_key: str, priority: str = "medium") -> Recommendation:
    return Recommendation(
        region_key=region_key,
        region_name="Test Region",
        score=50,
        priority=priority,
        message="Test message",
        details="Test details",
        steps=["Generic step 1", "Generic step 2"],
    )


def test_list_personas_includes_known_creators():
    personas = list_personas()
    keys = [p["key"] for p in personas]
    assert "hormozi" in keys
    assert "garyvee" in keys
    assert "brunson" in keys
    assert "yadegari" in keys


def test_get_persona_returns_none_for_default():
    assert get_persona("default") is None
    assert get_persona(None) is None
    assert get_persona("") is None


def test_get_persona_returns_known():
    p = get_persona("hormozi")
    assert p is not None
    assert p.key == "hormozi"
    assert p.name == "Alex Hormozi"


def test_apply_persona_adds_steps_at_front():
    rec = _rec("amygdala")
    original_steps = list(rec.steps)
    apply_persona("hormozi", [rec])
    assert len(rec.steps) > len(original_steps)
    for s in original_steps:
        assert s in rec.steps


def test_apply_persona_default_no_change():
    rec = _rec("amygdala")
    original_steps = list(rec.steps)
    apply_persona(None, [rec])
    assert rec.steps == original_steps


def test_apply_persona_unknown_no_change():
    rec = _rec("amygdala")
    original_steps = list(rec.steps)
    apply_persona("nonexistent", [rec])
    assert rec.steps == original_steps


def test_apply_persona_region_not_in_overlay_no_extra_steps():
    rec = _rec("hippocampus")
    apply_persona("hormozi", [rec])
    assert len(rec.steps) >= 2


_SCORES = {
    "visual_cortex": 40, "face_social": 40, "amygdala": 40,
    "hippocampus": 40, "language_areas": 40, "reward_circuit": 40,
    "prefrontal": 40, "motor_action": 40,
}


def test_get_recommendations_with_persona():
    recs_default = get_recommendations(_SCORES, persona_key=None)
    recs_hormozi = get_recommendations(_SCORES, persona_key="hormozi")
    assert len(recs_default) == len(recs_hormozi)
    amygdala_default = next(r for r in recs_default if r.region_key == "amygdala")
    amygdala_hormozi = next(r for r in recs_hormozi if r.region_key == "amygdala")
    assert len(amygdala_hormozi.steps) > len(amygdala_default.steps)


def test_get_recommendations_unknown_persona_no_crash():
    recs = get_recommendations(_SCORES, persona_key="nonexistent_persona")
    assert len(recs) == 8
```

- [ ] **Step 4: Run all persona tests**

```bash
cd /Users/nikolassapalidis/neurolens/backend && source .venv/bin/activate && pytest tests/test_personas.py tests/test_persona_storage.py -v
```
Expected: 20 tests passing (9 persona + 11 storage).

- [ ] **Step 5: Commit**

```bash
cd /Users/nikolassapalidis/neurolens/backend && git add app/personas.py tests/test_personas.py && git commit -m "refactor: personas.py delegates to SQLite storage"
```

---

### Task 3: Persona CRUD endpoints in main.py + tests

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_main.py`

- [ ] **Step 1: Write failing tests**

Open `backend/tests/test_main.py`. Add the following at the end of the file. First add the `mock_persona_storage` fixture and import (add to the top of the file along with other imports if they're not there):

At the top of `test_main.py`, add:
```python
from app.persona_storage import PersonaStorage as PersonaStorageClass
```

Then add this fixture after the existing `mock_storage` fixture:

```python
@pytest.fixture(autouse=True)
def mock_persona_storage(tmp_path):
    store = PersonaStorageClass(str(tmp_path / "test_personas.db"))
    store.init()
    with patch("app.main.get_persona_storage", return_value=store):
        with patch("app.personas.get_persona_storage", return_value=store):
            yield store
```

Then add these test functions at the end of the file:

```python
def test_list_personas_returns_seeded(mock_persona_storage, client):
    r = client.get("/personas")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 4
    keys = [p["key"] for p in data]
    assert "hormozi" in keys


def test_create_persona(mock_persona_storage, client):
    payload = {
        "key": "new-creator",
        "name": "New Creator",
        "tagline": "My tagline",
        "step_overlays": {"amygdala": ["Use story hooks", "Lead with empathy"]},
    }
    r = client.post("/personas", json=payload)
    assert r.status_code == 200
    assert "id" in r.json()
    assert r.json()["id"] > 0


def test_get_persona_by_id(mock_persona_storage, client):
    pid = client.post("/personas", json={"key": "test-p", "name": "Test", "tagline": "", "step_overlays": {}}).json()["id"]
    r = client.get(f"/personas/{pid}")
    assert r.status_code == 200
    assert r.json()["key"] == "test-p"
    assert "step_overlays" in r.json()


def test_get_persona_missing(mock_persona_storage, client):
    r = client.get("/personas/9999")
    assert r.status_code == 404


def test_update_persona(mock_persona_storage, client):
    pid = client.post("/personas", json={"key": "upd", "name": "Before", "tagline": "", "step_overlays": {}}).json()["id"]
    r = client.put(f"/personas/{pid}", json={"key": "upd", "name": "After", "tagline": "new", "step_overlays": {"amygdala": ["New step"]}})
    assert r.status_code == 200
    updated = client.get(f"/personas/{pid}").json()
    assert updated["name"] == "After"
    assert updated["step_overlays"]["amygdala"] == ["New step"]


def test_delete_persona_endpoint(mock_persona_storage, client):
    pid = client.post("/personas", json={"key": "del-p", "name": "Del", "tagline": "", "step_overlays": {}}).json()["id"]
    r = client.delete(f"/personas/{pid}")
    assert r.status_code == 200
    assert client.get(f"/personas/{pid}").status_code == 404
```

- [ ] **Step 2: Run tests, verify they fail**

```bash
cd /Users/nikolassapalidis/neurolens/backend && source .venv/bin/activate && pytest tests/test_main.py -v -k "persona"
```
Expected: tests fail with 404 or 405 (routes don't exist yet).

- [ ] **Step 3: Update main.py**

Add `from app.persona_storage import get_persona_storage as get_persona_storage` to the imports at the top of `backend/app/main.py`, alongside the existing storage import:

```python
from app.storage import get_storage
from app.persona_storage import get_persona_storage
```

Add the following after the existing `/projects` delete endpoint and before `@app.exception_handler`:

```python
class PersonaRequest(BaseModel):
    key: str
    name: str
    tagline: str
    step_overlays: dict[str, list[str]]


@app.get("/personas")
def list_personas_endpoint():
    return get_persona_storage().list_all()


@app.post("/personas")
def create_persona(req: PersonaRequest):
    pid = get_persona_storage().save(req.key, req.name, req.tagline, req.step_overlays)
    return {"id": pid}


@app.get("/personas/{persona_id}")
def get_persona_endpoint(persona_id: int):
    row = get_persona_storage().get_by_id(persona_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Persona not found")
    return row


@app.put("/personas/{persona_id}")
def update_persona(persona_id: int, req: PersonaRequest):
    updated = get_persona_storage().update(persona_id, req.key, req.name, req.tagline, req.step_overlays)
    if not updated:
        raise HTTPException(status_code=404, detail="Persona not found")
    return {"status": "updated"}


@app.delete("/personas/{persona_id}")
def delete_persona_endpoint(persona_id: int):
    deleted = get_persona_storage().delete(persona_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Persona not found")
    return {"status": "deleted"}
```

Also remove the old `/personas` GET endpoint that was calling `list_personas` from personas.py. Find and delete this block:

```python
@app.get("/personas")
def personas():
    from app.personas import list_personas as _list_personas
    return _list_personas()
```

- [ ] **Step 4: Run tests, verify they pass**

```bash
cd /Users/nikolassapalidis/neurolens/backend && source .venv/bin/activate && pytest tests/test_main.py -v
```
Expected: all tests passing (5 project + 6 persona = 11 total).

- [ ] **Step 5: Run full test suite**

```bash
cd /Users/nikolassapalidis/neurolens/backend && source .venv/bin/activate && pytest tests/ -v 2>&1 | tail -10
```
Expected: all tests passing.

- [ ] **Step 6: Commit**

```bash
cd /Users/nikolassapalidis/neurolens/backend && git add app/main.py tests/test_main.py && git commit -m "feat: persona CRUD endpoints (GET/POST/GET/{id}/PUT/{id}/DELETE/{id})"
```

---

### Task 4: Frontend types and API client

**Files:**
- Modify: `frontend/src/types/analysis.ts`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Add PersonaSummary and PersonaDetail to analysis.ts**

Append at the end of `frontend/src/types/analysis.ts`:

```typescript
export interface PersonaSummary {
  id: number;
  key: string;
  name: string;
  tagline: string;
}

export interface PersonaDetail extends PersonaSummary {
  step_overlays: Record<string, string[]>;
}
```

- [ ] **Step 2: Update api.ts import line**

Change the import at line 2 of `frontend/src/lib/api.ts`:

From:
```typescript
import type { AnalysisResult, CompareResult, ProjectSummary, Project } from "@/types/analysis";
```

To:
```typescript
import type { AnalysisResult, CompareResult, ProjectSummary, Project, PersonaSummary, PersonaDetail } from "@/types/analysis";
```

- [ ] **Step 3: Add persona API functions to api.ts**

Append at the end of `frontend/src/lib/api.ts`:

```typescript
async function json_put(path: string, body: unknown): Promise<unknown> {
  const res = await fetch(`${BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

export const listPersonas = (): Promise<PersonaSummary[]> =>
  json_get("/personas") as Promise<PersonaSummary[]>;

export const getPersona = (id: number): Promise<PersonaDetail> =>
  json_get(`/personas/${id}`) as Promise<PersonaDetail>;

export const createPersona = (data: Omit<PersonaDetail, "id">): Promise<{ id: number }> =>
  json_post("/personas", data) as Promise<{ id: number }>;

export const updatePersona = (id: number, data: Omit<PersonaDetail, "id">): Promise<void> =>
  json_put(`/personas/${id}`, data).then(() => undefined) as Promise<void>;

export const deletePersona = (id: number): Promise<void> =>
  fetch(`${BASE}/personas/${id}`, { method: "DELETE" }).then(() => undefined);
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd /Users/nikolassapalidis/neurolens/frontend && npx tsc --noEmit
```
Expected: no output.

- [ ] **Step 5: Commit**

```bash
cd /Users/nikolassapalidis/neurolens/frontend && git add src/types/analysis.ts src/lib/api.ts && git commit -m "feat: persona types and API client functions"
```

---

### Task 5: Persona management page + PersonaSelector "Manage" link

**Files:**
- Create: `frontend/src/app/personas/page.tsx`
- Modify: `frontend/src/components/PersonaSelector.tsx`

- [ ] **Step 1: Create the personas management page**

Create `frontend/src/app/personas/page.tsx` with this exact content:

```tsx
"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Plus, Pencil, Trash2, Users } from "lucide-react";
import { listPersonas, getPersona, createPersona, updatePersona, deletePersona } from "@/lib/api";
import type { PersonaSummary, PersonaDetail } from "@/types/analysis";

const REGIONS = [
  { key: "visual_cortex", label: "Visual Cortex" },
  { key: "face_social", label: "Face & Social" },
  { key: "amygdala", label: "Amygdala (Emotion)" },
  { key: "hippocampus", label: "Hippocampus (Memory)" },
  { key: "language_areas", label: "Language Areas" },
  { key: "reward_circuit", label: "Reward Circuit" },
  { key: "prefrontal", label: "Prefrontal (Logic)" },
  { key: "motor_action", label: "Motor Action" },
];

type FormState = {
  key: string;
  name: string;
  tagline: string;
  overlays: Record<string, string>;
};

function overlaysToSteps(overlays: Record<string, string>): Record<string, string[]> {
  const result: Record<string, string[]> = {};
  for (const [k, v] of Object.entries(overlays)) {
    const steps = v.split("\n").map((s) => s.trim()).filter(Boolean);
    if (steps.length > 0) result[k] = steps;
  }
  return result;
}

function stepsToOverlays(step_overlays: Record<string, string[]>): Record<string, string> {
  const result: Record<string, string> = {};
  for (const [k, v] of Object.entries(step_overlays)) {
    result[k] = v.join("\n");
  }
  return result;
}

const emptyForm = (): FormState => ({
  key: "",
  name: "",
  tagline: "",
  overlays: Object.fromEntries(REGIONS.map((r) => [r.key, ""])),
});

export default function PersonasPage() {
  const router = useRouter();
  const [personas, setPersonas] = useState<PersonaSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<number | "new" | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm());
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    listPersonas()
      .then(setPersonas)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function startEdit(id: number) {
    try {
      const p = await getPersona(id);
      setForm({
        key: p.key,
        name: p.name,
        tagline: p.tagline,
        overlays: { ...Object.fromEntries(REGIONS.map((r) => [r.key, ""])), ...stepsToOverlays(p.step_overlays) },
      });
      setEditing(id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }

  function startNew() {
    setForm(emptyForm());
    setEditing("new");
  }

  function cancelEdit() {
    setEditing(null);
    setError(null);
  }

  async function handleSave() {
    if (!form.key.trim() || !form.name.trim()) {
      setError("Key and name are required.");
      return;
    }
    setSaving(true);
    setError(null);
    const data = {
      key: form.key.trim(),
      name: form.name.trim(),
      tagline: form.tagline.trim(),
      step_overlays: overlaysToSteps(form.overlays),
    };
    try {
      if (editing === "new") {
        const { id } = await createPersona(data);
        setPersonas((prev) => [...prev, { id, key: data.key, name: data.name, tagline: data.tagline }]);
      } else if (typeof editing === "number") {
        await updatePersona(editing, data);
        setPersonas((prev) =>
          prev.map((p) => (p.id === editing ? { ...p, key: data.key, name: data.name, tagline: data.tagline } : p))
        );
      }
      setEditing(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number, e: React.MouseEvent) {
    e.stopPropagation();
    try {
      await deletePersona(id);
      setPersonas((prev) => prev.filter((p) => p.id !== id));
      if (editing === id) setEditing(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  }

  return (
    <main className="min-h-screen px-4 py-10 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-8">
        <Button variant="ghost" size="sm" onClick={() => router.push("/")}>
          <ArrowLeft className="w-4 h-4 mr-1" /> Back
        </Button>
        <div className="flex items-center gap-2 flex-1">
          <Users className="w-5 h-5 text-muted-foreground" />
          <h1 className="text-2xl font-bold">Creator Personas</h1>
        </div>
        {editing === null && (
          <Button size="sm" onClick={startNew}>
            <Plus className="w-4 h-4 mr-1" /> New Persona
          </Button>
        )}
      </div>

      {error && <p className="text-sm text-rose-500 mb-4">{error}</p>}

      {/* Form panel */}
      {editing !== null && (
        <div className="border border-border rounded-xl p-5 mb-6 bg-card">
          <h2 className="text-sm font-semibold mb-4">{editing === "new" ? "New Persona" : "Edit Persona"}</h2>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Key (slug)</label>
              <input
                type="text"
                value={form.key}
                onChange={(e) => setForm((f) => ({ ...f, key: e.target.value.toLowerCase().replace(/\s+/g, "-") }))}
                placeholder="e.g. my-creator"
                className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Display Name</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="e.g. Alex Hormozi"
                className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
          <div className="mb-5">
            <label className="text-xs text-muted-foreground block mb-1">Tagline</label>
            <input
              type="text"
              value={form.tagline}
              onChange={(e) => setForm((f) => ({ ...f, tagline: e.target.value }))}
              placeholder="e.g. Direct response. Quantify everything."
              className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
            Brain Region Steps — one per line, leave blank to skip a region
          </p>
          <div className="space-y-3">
            {REGIONS.map((region) => (
              <div key={region.key}>
                <label className="text-xs text-muted-foreground block mb-1">{region.label}</label>
                <textarea
                  value={form.overlays[region.key] ?? ""}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, overlays: { ...f.overlays, [region.key]: e.target.value } }))
                  }
                  rows={2}
                  placeholder={`Steps for ${region.label}…`}
                  className="w-full px-3 py-2 text-sm border rounded-lg bg-background resize-none focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            ))}
          </div>

          <div className="flex gap-2 mt-5">
            <Button size="sm" disabled={saving} onClick={handleSave}>
              {saving ? "Saving…" : editing === "new" ? "Create" : "Save changes"}
            </Button>
            <Button variant="ghost" size="sm" onClick={cancelEdit}>
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Persona list */}
      {loading && <p className="text-sm text-muted-foreground">Loading…</p>}

      {!loading && personas.length === 0 && (
        <div className="text-center py-20 text-muted-foreground">
          <Users className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-sm">No personas yet.</p>
        </div>
      )}

      <div className="space-y-2">
        {personas.map((p) => (
          <div
            key={p.id}
            className="flex items-center gap-4 px-4 py-3 rounded-xl border border-border bg-card transition-colors"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="font-medium text-sm truncate">{p.name}</p>
                <span className="text-xs text-muted-foreground border border-border rounded px-1.5 py-0.5 shrink-0">
                  {p.key}
                </span>
              </div>
              {p.tagline && <p className="text-xs text-muted-foreground mt-0.5 truncate">{p.tagline}</p>}
            </div>
            <button
              onClick={() => startEdit(p.id)}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors shrink-0"
            >
              <Pencil className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={(e) => handleDelete(p.id, e)}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors shrink-0"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </main>
  );
}
```

- [ ] **Step 2: Add "Manage" link to PersonaSelector**

Open `frontend/src/components/PersonaSelector.tsx`. Add `Link` import and the manage link. Replace the entire file content with:

```tsx
"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

interface PersonaOption {
  key: string;
  name: string;
  tagline: string;
}

interface Props {
  value: string;
  onChange: (key: string) => void;
}

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function PersonaSelector({ value, onChange }: Props) {
  const [personas, setPersonas] = useState<PersonaOption[]>([]);

  useEffect(() => {
    fetch(`${BASE}/personas`)
      .then((r) => r.json())
      .then(setPersonas)
      .catch(() => {/* non-critical */});
  }, []);

  return (
    <div className="flex flex-col items-center gap-1.5 mb-6">
      <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
        Analyze through the lens of
      </p>
      <div className="flex flex-wrap gap-2 justify-center">
        <button
          onClick={() => onChange("default")}
          className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
            value === "default"
              ? "bg-foreground text-background border-foreground"
              : "border-border text-muted-foreground hover:border-foreground/50 hover:text-foreground"
          }`}
        >
          Default
        </button>
        {personas.map((p) => (
          <button
            key={p.key}
            title={p.tagline}
            onClick={() => onChange(p.key)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
              value === p.key
                ? "bg-foreground text-background border-foreground"
                : "border-border text-muted-foreground hover:border-foreground/50 hover:text-foreground"
            }`}
          >
            {p.name}
          </button>
        ))}
      </div>
      {value !== "default" && (
        <p className="text-xs text-muted-foreground italic mt-0.5">
          {personas.find((p) => p.key === value)?.tagline}
        </p>
      )}
      <Link
        href="/personas"
        className="text-xs text-muted-foreground hover:text-foreground transition-colors mt-0.5"
      >
        Manage personas
      </Link>
    </div>
  );
}
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd /Users/nikolassapalidis/neurolens/frontend && npx tsc --noEmit
```
Expected: no output.

- [ ] **Step 4: Test manually**
  - Open http://localhost:3000
  - Confirm "Manage personas" link appears below the persona pills
  - Click it → `/personas` page shows 4 default personas
  - Click "New Persona" → form appears with key/name/tagline inputs and 8 region textareas
  - Fill in: key=`mr-beast`, name=`MrBeast`, tagline=`Spectacle. Scale. Generosity.`
  - In "Reward Circuit" textarea, type: `Frame the product as an insane deal that feels like winning a prize`
  - Click Create → new persona appears in list
  - Go back to home (/) → "MrBeast" pill appears in PersonaSelector
  - Select MrBeast → analyze with text → verify reward_circuit recommendation has the custom step at top
  - Return to `/personas`, click pencil on MrBeast → edit, change tagline, save
  - Click delete on MrBeast → removed from list

- [ ] **Step 5: Commit**

```bash
cd /Users/nikolassapalidis/neurolens/frontend && git add src/app/personas/page.tsx src/components/PersonaSelector.tsx && git commit -m "feat: persona management page with create/edit/delete"
```

---

## Self-Review

**Spec coverage:**
- ✅ Add new personas from the UI — Task 5 create form
- ✅ Edit existing personas — Task 5 edit form (pencil button)
- ✅ Delete personas — Task 5 delete button
- ✅ Personas persist across restarts — SQLite storage (Task 1)
- ✅ Existing 4 personas seeded from code — Task 1 `_SEED_DATA` in `init()`
- ✅ PersonaSelector shows "Manage personas" link — Task 5
- ✅ Per-region step editing — 8 textarea fields in the form (Task 5)
- ✅ No code changes needed to add a new persona — all managed through UI

**Placeholder scan:** None found. All code blocks are complete and runnable.

**Type consistency:**
- `PersonaDetail.step_overlays: Record<string, string[]>` ↔ `createPersona(data: Omit<PersonaDetail, "id">)` ✅
- `PersonaRequest.step_overlays: dict[str, list[str]]` ↔ `PersonaStorage.save(step_overlays: dict)` → `json.dumps` ✅
- `overlaysToSteps()` returns `Record<string, string[]>` passed as `step_overlays` ✅
- `stepsToOverlays()` converts `Record<string, string[]>` → `Record<string, string>` for textarea editing ✅
- `updatePersona(id, data)` → `json_put` → `PUT /personas/{id}` → `PersonaStorage.update(...)` ✅
