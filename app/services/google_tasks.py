"""Google Tasks REST API v1 integration."""
import requests

GTASKS_BASE = "https://tasks.googleapis.com/tasks/v1"


class GoogleTasksService:
    def __init__(self, access_token: str):
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {access_token}"})

    def get_task_lists(self) -> list[dict]:
        resp = self.session.get(f"{GTASKS_BASE}/users/@me/lists", timeout=10)
        resp.raise_for_status()
        return resp.json().get("items", [])

    def get_tasks(self, task_list_id: str = "@default") -> list[dict]:
        resp = self.session.get(
            f"{GTASKS_BASE}/lists/{task_list_id}/tasks",
            params={"showCompleted": "true", "showHidden": "true"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("items", [])

    def complete_task(self, task_list_id: str, task_id: str) -> dict:
        resp = self.session.patch(
            f"{GTASKS_BASE}/lists/{task_list_id}/tasks/{task_id}",
            json={"status": "completed"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def create_task(
        self,
        title: str,
        notes: str = "",
        due: str | None = None,
        task_list_id: str = "@default",
    ) -> dict:
        payload: dict = {"title": title, "notes": notes}
        if due:
            payload["due"] = due
        resp = self.session.post(
            f"{GTASKS_BASE}/lists/{task_list_id}/tasks",
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def normalise(raw: dict) -> dict:
        """Convert Google Tasks task shape to internal TodoTask-compatible dict."""
        due_date = raw.get("due")
        if due_date:
            due_date = due_date.rstrip("Z").split(".")[0]
        return {
            "source_service": "google_tasks",
            "source_id": str(raw["id"]),
            "title": raw.get("title", ""),
            "notes": raw.get("notes", ""),
            "due_date": due_date,
            "completed": raw.get("status") == "completed",
            "priority": 1,
        }
