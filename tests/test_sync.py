"""Tests for the sync engine."""
from unittest.mock import MagicMock, patch

import pytest

from app.models import ServiceCredential, SyncSettings, TodoTask
from app.extensions import db


def _setup_service(app, service, api_key="testtoken", user_id=None):
    with app.app_context():
        s = SyncSettings.query.filter_by(service=service).first()
        s.enabled = True
        cred = ServiceCredential.query.filter_by(service=service).first()
        if cred is None:
            cred = ServiceCredential(service=service)
            db.session.add(cred)
        cred.api_key = api_key
        if user_id:
            cred.user_id = user_id
        db.session.commit()


def test_sync_disabled_service(app):
    with app.app_context():
        from app.sync import sync_service

        # default: all disabled
        result = sync_service("todoist")
        assert result == 0


def test_sync_todoist(app):
    _setup_service(app, "todoist")
    fake_tasks = [
        {
            "id": "111",
            "content": "Test task",
            "description": "",
            "is_completed": False,
            "priority": 2,
            "due": None,
        }
    ]
    with app.app_context():
        with patch("app.services.todoist.TodoistService.get_tasks", return_value=fake_tasks):
            from app.sync import sync_service

            count = sync_service("todoist")

        assert count == 1
        task = TodoTask.query.filter_by(source_service="todoist", source_id="111").first()
        assert task is not None
        assert task.title == "Test task"


def test_sync_habitica(app):
    _setup_service(app, "habitica", api_key="htoken", user_id="huser")
    fake_tasks = [
        {
            "id": "hab-1",
            "text": "Drink water",
            "notes": "",
            "completed": False,
            "priority": 1,
            "date": None,
        }
    ]
    with app.app_context():
        with patch("app.services.habitica.HabiticaService.get_tasks", return_value=fake_tasks):
            from app.sync import sync_service

            count = sync_service("habitica")

        assert count == 1
        task = TodoTask.query.filter_by(source_service="habitica", source_id="hab-1").first()
        assert task is not None
        assert task.title == "Drink water"


def test_sync_google_tasks(app):
    _setup_service(app, "google_tasks")
    fake_tasks = [
        {
            "id": "gt-1",
            "title": "Write report",
            "notes": "",
            "status": "needsAction",
            "due": None,
        }
    ]
    with app.app_context():
        with patch(
            "app.services.google_tasks.GoogleTasksService.get_tasks",
            return_value=fake_tasks,
        ):
            from app.sync import sync_service

            count = sync_service("google_tasks")

        assert count == 1
        task = TodoTask.query.filter_by(source_service="google_tasks", source_id="gt-1").first()
        assert task is not None
        assert task.title == "Write report"


def test_upsert_deduplication(app):
    _setup_service(app, "todoist")
    fake_tasks = [
        {
            "id": "dup-1",
            "content": "Original title",
            "description": "",
            "is_completed": False,
            "priority": 1,
            "due": None,
        }
    ]
    with app.app_context():
        with patch("app.services.todoist.TodoistService.get_tasks", return_value=fake_tasks):
            from app.sync import sync_service

            sync_service("todoist")

        # Update the title and sync again
        fake_tasks[0]["content"] = "Updated title"
        with patch("app.services.todoist.TodoistService.get_tasks", return_value=fake_tasks):
            sync_service("todoist")

        tasks = TodoTask.query.filter_by(source_service="todoist", source_id="dup-1").all()
        assert len(tasks) == 1
        assert tasks[0].title == "Updated title"
