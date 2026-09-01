"""Tests for the REST API blueprint."""
import json

import pytest


def test_list_tasks_empty(client):
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_and_get_task(client):
    payload = {
        "source_service": "todoist",
        "source_id": "t001",
        "title": "Buy milk",
        "priority": 2,
    }
    resp = client.post("/api/tasks", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["title"] == "Buy milk"
    assert data["source_service"] == "todoist"
    task_id = data["id"]

    resp2 = client.get(f"/api/tasks/{task_id}")
    assert resp2.status_code == 200
    assert resp2.get_json()["id"] == task_id


def test_create_task_missing_fields(client):
    resp = client.post("/api/tasks", json={"title": "No source"})
    assert resp.status_code == 400


def test_update_task(client):
    # create
    resp = client.post(
        "/api/tasks",
        json={"source_service": "habitica", "source_id": "h001", "title": "Exercise"},
    )
    task_id = resp.get_json()["id"]

    # patch
    patch = client.patch(f"/api/tasks/{task_id}", json={"completed": True})
    assert patch.status_code == 200
    assert patch.get_json()["completed"] is True


def test_delete_task(client):
    resp = client.post(
        "/api/tasks",
        json={
            "source_service": "google_tasks",
            "source_id": "g001",
            "title": "Read book",
        },
    )
    task_id = resp.get_json()["id"]

    del_resp = client.delete(f"/api/tasks/{task_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/tasks/{task_id}")
    assert get_resp.status_code == 404


def test_get_settings(client):
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    services = {s["service"] for s in resp.get_json()}
    assert {"todoist", "habitica", "google_tasks"}.issubset(services)


def test_update_settings(client):
    resp = client.put(
        "/api/settings/todoist",
        json={"enabled": True, "sync_interval_minutes": 30},
    )
    assert resp.status_code == 200

    settings = client.get("/api/settings").get_json()
    todoist = next(s for s in settings if s["service"] == "todoist")
    assert todoist["enabled"] is True
    assert todoist["sync_interval_minutes"] == 30


def test_update_credentials(client):
    resp = client.put(
        "/api/credentials/todoist",
        json={"api_key": "mytoken123"},
    )
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}


def test_trigger_sync_no_credentials(client):
    """Sync with no credentials configured should return 0 tasks synced."""
    resp = client.post("/api/sync")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "synced" in data
    for count in data["synced"].values():
        assert count == 0


def test_filter_tasks_by_service(client):
    client.post(
        "/api/tasks",
        json={"source_service": "todoist", "source_id": "f001", "title": "T1"},
    )
    client.post(
        "/api/tasks",
        json={"source_service": "habitica", "source_id": "f002", "title": "H1"},
    )
    resp = client.get("/api/tasks?service=todoist")
    assert resp.status_code == 200
    tasks = resp.get_json()
    assert all(t["source_service"] == "todoist" for t in tasks)
