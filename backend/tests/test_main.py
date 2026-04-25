import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.storage import ProjectStorage
from app.persona_storage import PersonaStorage as PersonaStorageClass


@pytest.fixture(autouse=True)
def mock_storage(tmp_path):
    store = ProjectStorage(str(tmp_path / "test.db"))
    store.init()
    with patch("app.main.get_storage", return_value=store):
        yield store


@pytest.fixture(autouse=True)
def mock_persona_storage(tmp_path):
    store = PersonaStorageClass(str(tmp_path / "test_personas.db"))
    store.init()
    with patch("app.main.get_persona_storage", return_value=store):
        with patch("app.personas.get_persona_storage", return_value=store):
            yield store


@pytest.fixture
def client():
    return TestClient(app)


def test_list_projects_empty(mock_storage, client):
    r = client.get("/projects")
    assert r.status_code == 200
    assert r.json() == []


def test_save_project(mock_storage, client):
    payload = {
        "name": "Nike Ad",
        "result": {"type": "text", "scores": {"visual_cortex": 80, "face_social": 70, "amygdala": 60, "hippocampus": 50, "language_areas": 40, "reward_circuit": 30, "prefrontal": 20, "motor_action": 10}, "recommendations": [], "meta": {}}
    }
    r = client.post("/projects", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["id"] > 0


def test_get_project(mock_storage, client):
    payload = {
        "name": "My Test",
        "result": {"type": "text", "scores": {"visual_cortex": 80, "face_social": 70, "amygdala": 60, "hippocampus": 50, "language_areas": 40, "reward_circuit": 30, "prefrontal": 20, "motor_action": 10}, "recommendations": [], "meta": {}}
    }
    pid = client.post("/projects", json=payload).json()["id"]
    r = client.get(f"/projects/{pid}")
    assert r.status_code == 200
    assert r.json()["name"] == "My Test"
    assert r.json()["result"]["type"] == "text"


def test_get_missing_project(mock_storage, client):
    r = client.get("/projects/9999")
    assert r.status_code == 404


def test_delete_project(mock_storage, client):
    payload = {
        "name": "Delete me",
        "result": {"type": "text", "scores": {"visual_cortex": 80, "face_social": 70, "amygdala": 60, "hippocampus": 50, "language_areas": 40, "reward_circuit": 30, "prefrontal": 20, "motor_action": 10}, "recommendations": [], "meta": {}}
    }
    pid = client.post("/projects", json=payload).json()["id"]
    r = client.delete(f"/projects/{pid}")
    assert r.status_code == 200
    assert client.get(f"/projects/{pid}").status_code == 404


def test_list_personas_returns_seeded(mock_persona_storage, client):
    r = client.get("/personas")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 4
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


def test_create_persona_duplicate_key_returns_409(mock_persona_storage, client):
    payload = {"key": "dup", "name": "First", "tagline": "", "step_overlays": {}}
    client.post("/personas", json=payload)
    r = client.post("/personas", json=payload)
    assert r.status_code == 409


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


_SAMPLE_RESULT = {
    "type": "text",
    "scores": {"visual_cortex": 80, "face_social": 70, "amygdala": 60, "hippocampus": 50,
               "language_areas": 40, "reward_circuit": 30, "prefrontal": 20, "motor_action": 10},
    "recommendations": [],
    "meta": {},
}


def test_share_endpoint_returns_token(mock_storage, client):  # CLAUDE_SECRET_ALLOW
    pid = client.post("/projects", json={"name": "S", "result": _SAMPLE_RESULT}).json()["id"]
    r = client.post(f"/projects/{pid}/share")
    assert r.status_code == 200
    body = r.json()
    assert "token" in body
    assert isinstance(body["token"], str) and len(body["token"]) >= 16


def test_share_endpoint_missing_project(mock_storage, client):  # CLAUDE_SECRET_ALLOW
    r = client.post("/projects/9999/share")
    assert r.status_code == 404


def test_get_shared_project_by_token(mock_storage, client):
    pid = client.post("/projects", json={"name": "Public", "result": _SAMPLE_RESULT}).json()["id"]
    token = client.post(f"/projects/{pid}/share").json()["token"]
    r = client.get(f"/share/{token}")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Public"
    assert body["result"]["type"] == "text"


def test_get_shared_project_unknown_token(mock_storage, client):
    r = client.get("/share/no-such-token")
    assert r.status_code == 404


def test_share_endpoint_idempotent(mock_storage, client):  # CLAUDE_SECRET_ALLOW
    pid = client.post("/projects", json={"name": "Idem", "result": _SAMPLE_RESULT}).json()["id"]
    t1 = client.post(f"/projects/{pid}/share").json()["token"]
    t2 = client.post(f"/projects/{pid}/share").json()["token"]
    assert t1 == t2


_GENERATOR_LLM_OUTPUT = """{
  "visual_cortex": ["bold hook"],
  "face_social": ["lead with founder"],
  "amygdala": ["stack value"],
  "hippocampus": ["story arc"],
  "language_areas": ["cut filler"],
  "reward_circuit": ["quantify"],
  "prefrontal": ["show proof"],
  "motor_action": ["time-bound CTA"]
}"""


def test_generate_persona_endpoint_happy_path(client):
    with patch(
        "app.persona_generator._call_hf_inference",
        return_value=_GENERATOR_LLM_OUTPUT,
    ):
        r = client.post(
            "/personas/generate",
            json={"name": "Hormozi", "source": "lorem ipsum dolor " * 50},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Hormozi"
    assert "amygdala" in body["step_overlays"]


def test_generate_persona_endpoint_thin_source_returns_502(client):
    r = client.post("/personas/generate", json={"name": "X", "source": "tiny"})
    assert r.status_code == 502


def test_generate_persona_endpoint_handles_llm_error(client):
    from app.persona_generator import PersonaGeneratorError
    with patch(
        "app.persona_generator._call_hf_inference",
        side_effect=PersonaGeneratorError("HF Inference rate limit hit"),
    ):
        r = client.post(
            "/personas/generate",
            json={"name": "X", "source": "lorem ipsum " * 50},
        )
    assert r.status_code == 502
    assert "rate limit" in r.json()["detail"].lower()
