"""Habitica API v3 integration."""
import requests

HABITICA_BASE = "https://habitica.com/api/v3"


class HabiticaService:
    def __init__(self, user_id: str, api_token: str):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "x-api-user": user_id,
                "x-api-key": api_token,
                "x-client": "todo-sync-gw",
            }
        )

    def get_tasks(self, task_type: str = "todos") -> list[dict]:
        resp = self.session.get(
            f"{HABITICA_BASE}/tasks/user",
            params={"type": task_type},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])

    def score_task(self, task_id: str, direction: str = "up") -> dict:
        resp = self.session.post(
            f"{HABITICA_BASE}/tasks/{task_id}/score/{direction}", timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def create_task(self, text: str, task_type: str = "todo", notes: str = "") -> dict:
        payload = {"text": text, "type": task_type, "notes": notes}
        resp = self.session.post(
            f"{HABITICA_BASE}/tasks/user", json=payload, timeout=10
        )
        resp.raise_for_status()
        return resp.json().get("data", {})

    @staticmethod
    def normalise(raw: dict) -> dict:
        """Convert Habitica task shape to internal TodoTask-compatible dict."""
        due_date = raw.get("date")
        if due_date:
            due_date = due_date.rstrip("Z").split(".")[0]
        return {
            "source_service": "habitica",
            "source_id": str(raw["id"]),
            "title": raw.get("text", ""),
            "notes": raw.get("notes", ""),
            "due_date": due_date,
            "completed": raw.get("completed", False),
            "priority": int(round(raw.get("priority", 1))),
        }
