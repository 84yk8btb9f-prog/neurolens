import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.storage import ProjectStorage

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_storage(tmp_path):
    store = ProjectStorage(str(tmp_path / "test.db"))
    store.init()
    with patch("app.main.get_storage", return_value=store):
        yield store

def test_list_projects_empty(mock_storage):
    r = client.get("/projects")
    assert r.status_code == 200
    assert r.json() == []

def test_save_project(mock_storage):
    payload = {
        "name": "Nike Ad",
        "result": {"type": "text", "scores": {"visual_cortex": 80, "face_social": 70, "amygdala": 60, "hippocampus": 50, "language_areas": 40, "reward_circuit": 30, "prefrontal": 20, "motor_action": 10}, "recommendations": [], "meta": {}}
    }
    r = client.post("/projects", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["id"] > 0

def test_get_project(mock_storage):
    payload = {
        "name": "My Test",
        "result": {"type": "text", "scores": {"visual_cortex": 80, "face_social": 70, "amygdala": 60, "hippocampus": 50, "language_areas": 40, "reward_circuit": 30, "prefrontal": 20, "motor_action": 10}, "recommendations": [], "meta": {}}
    }
    pid = client.post("/projects", json=payload).json()["id"]
    r = client.get(f"/projects/{pid}")
    assert r.status_code == 200
    assert r.json()["name"] == "My Test"
    assert r.json()["result"]["type"] == "text"

def test_get_missing_project(mock_storage):
    r = client.get("/projects/9999")
    assert r.status_code == 404

def test_delete_project(mock_storage):
    payload = {
        "name": "Delete me",
        "result": {"type": "text", "scores": {"visual_cortex": 80, "face_social": 70, "amygdala": 60, "hippocampus": 50, "language_areas": 40, "reward_circuit": 30, "prefrontal": 20, "motor_action": 10}, "recommendations": [], "meta": {}}
    }
    pid = client.post("/projects", json=payload).json()["id"]
    r = client.delete(f"/projects/{pid}")
    assert r.status_code == 200
    assert client.get(f"/projects/{pid}").status_code == 404
