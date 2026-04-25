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
    persona = get_persona(persona_key)
    if persona is None:
        return
    for rec in recommendations:
        extra = persona.step_overlays.get(rec.region_key, [])
        if extra:
            rec.steps = extra + rec.steps
