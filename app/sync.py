"""Sync engine: pull tasks from each enabled service and upsert into DB."""
import json
from datetime import datetime, timezone

from app.extensions import db
from app.models import ServiceCredential, SyncSettings, TodoTask


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_credential(service: str) -> ServiceCredential | None:
    return ServiceCredential.query.filter_by(service=service).first()


def _upsert_task(normalised: dict) -> TodoTask:
    task = TodoTask.query.filter_by(
        source_service=normalised["source_service"],
        source_id=normalised["source_id"],
    ).first()

    if task is None:
        task = TodoTask(
            source_service=normalised["source_service"],
            source_id=normalised["source_id"],
        )
        db.session.add(task)

    task.title = normalised["title"]
    task.notes = normalised.get("notes") or ""
    task.completed = normalised.get("completed", False)
    task.priority = normalised.get("priority", 1)

    raw_due = normalised.get("due_date")
    if raw_due:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                task.due_date = datetime.strptime(raw_due[:19], fmt)
                break
            except (ValueError, TypeError):
                pass
    else:
        task.due_date = None

    task.updated_at = _now()
    return task


def sync_service(service: str) -> int:
    """Pull tasks for *service* and upsert into the local DB.

    Returns the number of tasks processed.
    """
    settings = SyncSettings.query.filter_by(service=service).first()
    if settings is None or not settings.enabled:
        return 0

    cred = _get_credential(service)
    if cred is None:
        return 0

    raw_tasks: list[dict] = []

    if service == "todoist":
        from app.services.todoist import TodoistService

        svc = TodoistService(api_token=cred.api_key)
        raw_tasks = svc.get_tasks(project_id=settings.project_filter or None)
        normalised = [TodoistService.normalise(t) for t in raw_tasks]

    elif service == "habitica":
        from app.services.habitica import HabiticaService

        extra = json.loads(cred.extra or "{}")
        svc = HabiticaService(user_id=cred.user_id or "", api_token=cred.api_key)
        raw_tasks = svc.get_tasks()
        normalised = [HabiticaService.normalise(t) for t in raw_tasks]

    elif service == "google_tasks":
        from app.services.google_tasks import GoogleTasksService

        svc = GoogleTasksService(access_token=cred.api_key)
        raw_tasks = svc.get_tasks(
            task_list_id=settings.project_filter or "@default"
        )
        normalised = [GoogleTasksService.normalise(t) for t in raw_tasks]

    else:
        return 0

    for item in normalised:
        _upsert_task(item)

    settings.last_synced_at = _now()
    db.session.commit()
    return len(normalised)


def sync_all() -> dict[str, int]:
    """Sync all enabled services. Returns a map of service -> task count."""
    results: dict[str, int] = {}
    for service in ("todoist", "habitica", "google_tasks"):
        results[service] = sync_service(service)
    return results
