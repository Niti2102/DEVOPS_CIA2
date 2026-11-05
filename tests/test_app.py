from app import app


def test_home_page():
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert b"Task Manager" in response.data


def test_health():
    response = app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "UP"


def test_version():
    response = app.test_client().get("/api/version")
    data = response.get_json()
    assert response.status_code == 200
    assert data["app"] == "cicd-demo"
    assert data["version"] == "1.0.0"


def test_add_and_complete_task():
    client = app.test_client()
    response = client.post("/api/tasks", json={"title": "Write documentation"})
    task_id = response.get_json()["id"]
    assert response.status_code == 201

    response = client.put(f"/api/tasks/{task_id}", json={"done": True})
    assert response.get_json()["done"] is True
