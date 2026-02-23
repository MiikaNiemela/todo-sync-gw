"""Todoist REST API v2 integration."""
import requests

TODOIST_BASE = "https://api.todoist.com/rest/v2"


class TodoistService:
    def __init__(self, api_token: str):
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_token}"})

    def get_tasks(self, project_id: str | None = None) -> list[dict]:
        params = {}
        if project_id:
            params["project_id"] = project_id
        resp = self.session.get(f"{TODOIST_BASE}/tasks", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def close_task(self, task_id: str) -> bool:
        resp = self.session.post(
            f"{TODOIST_BASE}/tasks/{task_id}/close", timeout=10
        )
        return resp.status_code == 204

    def create_task(self, content: str, due_string: str | None = None) -> dict:
        payload = {"content": content}
        if due_string:
            payload["due_string"] = due_string
        resp = self.session.post(
            f"{TODOIST_BASE}/tasks", json=payload, timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def normalise(raw: dict) -> dict:
        """Convert Todoist task shape to internal TodoTask-compatible dict."""
        return {
            "source_service": "todoist",
            "source_id": str(raw["id"]),
            "title": raw.get("content", ""),
            "notes": raw.get("description", ""),
            "due_date": (raw.get("due") or {}).get("datetime")
            or (raw.get("due") or {}).get("date"),
            "completed": raw.get("is_completed", False),
            "priority": raw.get("priority", 1),
        }
