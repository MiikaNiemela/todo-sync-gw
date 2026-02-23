"""Tests for the webhook receivers."""
import base64
import json


def test_todoist_webhook_item_added(client, app):
    payload = {
        "event_name": "item:added",
        "event_data": {
            "id": "wh-001",
            "content": "Webhook task",
            "description": "",
            "is_completed": False,
            "priority": 2,
            "due": None,
        },
    }
    resp = client.post("/webhooks/todoist", json=payload)
    assert resp.status_code == 200

    with app.app_context():
        from app.models import TodoTask

        task = TodoTask.query.filter_by(
            source_service="todoist", source_id="wh-001"
        ).first()
        assert task is not None
        assert task.title == "Webhook task"


def test_todoist_webhook_item_completed(client, app):
    # first create the task
    client.post(
        "/api/tasks",
        json={
            "source_service": "todoist",
            "source_id": "wh-002",
            "title": "To complete",
        },
    )
    payload = {
        "event_name": "item:completed",
        "event_data": {"id": "wh-002"},
    }
    resp = client.post("/webhooks/todoist", json=payload)
    assert resp.status_code == 200

    with app.app_context():
        from app.models import TodoTask

        task = TodoTask.query.filter_by(
            source_service="todoist", source_id="wh-002"
        ).first()
        assert task.completed is True


def test_todoist_webhook_item_deleted(client, app):
    client.post(
        "/api/tasks",
        json={
            "source_service": "todoist",
            "source_id": "wh-003",
            "title": "To delete",
        },
    )
    payload = {
        "event_name": "item:deleted",
        "event_data": {"id": "wh-003"},
    }
    resp = client.post("/webhooks/todoist", json=payload)
    assert resp.status_code == 200

    with app.app_context():
        from app.models import TodoTask

        task = TodoTask.query.filter_by(
            source_service="todoist", source_id="wh-003"
        ).first()
        assert task is None


def test_habitica_webhook_scored(client, app):
    payload = {
        "type": "scored",
        "task": {
            "id": "hab-wh-1",
            "text": "Meditate",
            "notes": "",
            "completed": False,
            "priority": 1,
            "date": None,
        },
    }
    resp = client.post("/webhooks/habitica", json=payload)
    assert resp.status_code == 200

    with app.app_context():
        from app.models import TodoTask

        task = TodoTask.query.filter_by(
            source_service="habitica", source_id="hab-wh-1"
        ).first()
        assert task is not None
        assert task.completed is True


def test_google_pubsub_webhook(client):
    data = json.dumps({"action": "task_created", "task_id": "g-1"}).encode()
    envelope = {
        "message": {
            "data": base64.b64encode(data).decode(),
            "messageId": "1234",
        }
    }
    resp = client.post("/webhooks/google", json=envelope)
    assert resp.status_code == 200
