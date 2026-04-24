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
