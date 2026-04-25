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
        # Set WAL mode outside any transaction (cannot be changed inside a transaction)
        _conn = sqlite3.connect(self._path)
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.close()
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
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


_store = PersonaStorage()
try:
    _store.init()
except Exception as exc:
    import logging
    logging.getLogger(__name__).error("Failed to initialize persona storage: %s", exc)
    raise


def get_persona_storage() -> PersonaStorage:
    return _store
