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
