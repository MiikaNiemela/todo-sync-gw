"""Tests for service normalise helpers (no network calls)."""
import pytest

from app.services.todoist import TodoistService
from app.services.habitica import HabiticaService
from app.services.google_tasks import GoogleTasksService


def test_todoist_normalise_basic():
    raw = {
        "id": "123",
        "content": "Buy groceries",
        "description": "milk, eggs",
        "is_completed": False,
        "priority": 3,
        "due": {"date": "2024-06-01"},
    }
    n = TodoistService.normalise(raw)
    assert n["source_service"] == "todoist"
    assert n["source_id"] == "123"
    assert n["title"] == "Buy groceries"
    assert n["notes"] == "milk, eggs"
    assert n["priority"] == 3
    assert n["due_date"] == "2024-06-01"
    assert n["completed"] is False


def test_todoist_normalise_no_due():
    raw = {
        "id": "456",
        "content": "No deadline",
        "description": "",
        "is_completed": True,
        "priority": 1,
        "due": None,
    }
    n = TodoistService.normalise(raw)
    assert n["due_date"] is None
    assert n["completed"] is True


def test_habitica_normalise():
    raw = {
        "id": "abc",
        "text": "Morning run",
        "notes": "5 km",
        "completed": False,
        "priority": 2,
        "date": "2024-05-10T08:00:00.000Z",
    }
    n = HabiticaService.normalise(raw)
    assert n["source_service"] == "habitica"
    assert n["source_id"] == "abc"
    assert n["title"] == "Morning run"
    assert n["due_date"] == "2024-05-10T08:00:00"


def test_habitica_normalise_no_date():
    raw = {
        "id": "xyz",
        "text": "No date",
        "notes": "",
        "completed": True,
        "priority": 1,
        "date": None,
    }
    n = HabiticaService.normalise(raw)
    assert n["due_date"] is None
    assert n["completed"] is True


def test_google_tasks_normalise():
    raw = {
        "id": "gtask-1",
        "title": "Finish report",
        "notes": "Q4",
        "status": "completed",
        "due": "2024-07-01T00:00:00.000Z",
    }
    n = GoogleTasksService.normalise(raw)
    assert n["source_service"] == "google_tasks"
    assert n["source_id"] == "gtask-1"
    assert n["title"] == "Finish report"
    assert n["completed"] is True
    assert n["due_date"] == "2024-07-01T00:00:00"


def test_google_tasks_normalise_open():
    raw = {
        "id": "gtask-2",
        "title": "Read book",
        "notes": "",
        "status": "needsAction",
        "due": None,
    }
    n = GoogleTasksService.normalise(raw)
    assert n["completed"] is False
    assert n["due_date"] is None
