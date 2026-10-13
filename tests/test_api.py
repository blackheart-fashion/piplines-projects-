import pytest

from app.api import create_app
from app.service import normalize_title


@pytest.fixture
def application(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "tasks.db")})


@pytest.fixture
def client(application):
    return application.test_client()


@pytest.mark.parametrize("value", [None, 42, True, "", "   ", "x" * 121])
def test_invalid_title(value):
    with pytest.raises(ValueError):
        normalize_title(value)


def test_normalize_title():
    assert normalize_title("  ship release  ") == "ship release"
    assert normalize_title("x" * 120) == "x" * 120


def test_health_and_version(client):
    assert client.get("/health").json == {"status": "ok"}
    assert client.get("/version").json == {"version": "dev"}


def test_task_lifecycle(client):
    assert client.get("/tasks").json == []
    response = client.post("/tasks", json={"title": "  first release "})
    assert response.status_code == 201
    task_id = response.json["id"]
    assert response.json["title"] == "first release"
    assert client.get("/tasks").json[0]["done"] is False
    assert client.patch(f"/tasks/{task_id}", json={"done": True}).json["done"] is True
    assert client.patch(f"/tasks/{task_id}", json={"done": False}).json["done"] is False


@pytest.mark.parametrize("payload", [{}, {"title": " "}, {"title": 4}, []])
def test_bad_create_payload(client, payload):
    assert client.post("/tasks", json=payload).status_code == 400


def test_non_json(client):
    assert client.post("/tasks", data="bad").status_code == 400
    assert client.patch("/tasks/1", data="bad").status_code == 400


@pytest.mark.parametrize("payload", [{}, {"done": "true"}, {"done": 1}, []])
def test_bad_update_payload(client, payload):
    assert client.patch("/tasks/1", json=payload).status_code == 400


def test_missing_task(client):
    assert client.patch("/tasks/999", json={"done": True}).status_code == 404


def test_sql_injection_is_data(client):
    title = "'); DROP TABLE tasks; --"
    assert client.post("/tasks", json={"title": title}).status_code == 201
    assert client.get("/tasks").json[0]["title"] == title


def test_persistence_across_application_restart(application):
    application.test_client().post("/tasks", json={"title": "keep me"})
    restarted = create_app({"TESTING": True, "DATABASE": application.config["DATABASE"]})
    assert restarted.test_client().get("/tasks").json[0]["title"] == "keep me"


def test_injected_unhealthy(application):
    application.config["DEMO_BROKEN"] = True
    assert application.test_client().get("/health").status_code == 503


def test_database_failure(application):
    import sqlite3
    from contextlib import closing

    with closing(sqlite3.connect(application.config["DATABASE"])) as connection:
        connection.execute("DROP TABLE tasks")
        connection.commit()
    assert application.test_client().get("/health").status_code == 503
