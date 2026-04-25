import pytest, os, tempfile
from app.storage import ProjectStorage

@pytest.fixture
def store(tmp_path):
    db = str(tmp_path / "test.db")
    s = ProjectStorage(db)
    s.init()
    return s

def test_save_and_list(store):
    result = {"type": "text", "scores": {"visual_cortex": 80}, "recommendations": [], "meta": {}}
    pid = store.save("My Ad", result)
    projects = store.list_all()
    assert len(projects) == 1
    assert projects[0]["id"] == pid
    assert projects[0]["name"] == "My Ad"
    assert projects[0]["type"] == "text"
    assert "created_at" in projects[0]

def test_get_project(store):
    result = {"type": "image", "scores": {"visual_cortex": 60}, "recommendations": [{"region_key": "visual_cortex", "score": 60}], "meta": {}}
    pid = store.save("Test", result)
    project = store.get(pid)
    assert project is not None
    assert project["name"] == "Test"
    assert project["result"]["type"] == "image"
    assert project["result"]["scores"]["visual_cortex"] == 60

def test_get_nonexistent(store):
    assert store.get(999) is None

def test_delete_project(store):
    pid = store.save("Delete me", {"type": "text", "scores": {}, "recommendations": [], "meta": {}})
    assert store.delete(pid) is True
    assert store.get(pid) is None

def test_delete_nonexistent(store):
    assert store.delete(999) is False

def test_list_sorted_newest_first(store):
    store.save("First", {"type": "text", "scores": {}, "recommendations": [], "meta": {}})
    store.save("Second", {"type": "text", "scores": {}, "recommendations": [], "meta": {}})
    projects = store.list_all()
    assert projects[0]["name"] == "Second"


def test_share_creates_and_persists_token(store):  # CLAUDE_SECRET_ALLOW
    pid = store.save("X", {"type": "text", "scores": {}, "recommendations": [], "meta": {}})
    token = store.share(pid)
    assert token and isinstance(token, str)
    assert len(token) >= 16
    again = store.share(pid)
    assert again == token


def test_share_invalid_id_yields_none(store):  # CLAUDE_SECRET_ALLOW
    assert store.share(9999) is None


def test_lookup_by_token_yields_project(store):
    pid = store.save("Y", {"type": "text", "scores": {"amygdala": 30}, "recommendations": [], "meta": {}})
    token = store.share(pid)
    fetched = store.get_by_token(token)
    assert fetched is not None
    assert fetched["id"] == pid
    assert fetched["result"]["scores"]["amygdala"] == 30


def test_lookup_by_unknown_token_yields_none(store):
    assert store.get_by_token("does-not-exist") is None
    assert store.get_by_token("") is None


def test_get_includes_share_token_field(store):
    pid = store.save("Z", {"type": "text", "scores": {}, "recommendations": [], "meta": {}})
    project = store.get(pid)
    assert "share_token" in project
    assert project["share_token"] is None
    store.share(pid)
    assert store.get(pid)["share_token"] is not None
