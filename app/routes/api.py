"""REST API blueprint – CRUD on tasks plus manual sync trigger."""
from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import ServiceCredential, SyncSettings, TodoTask

api_bp = Blueprint("api", __name__)


# ── Tasks ─────────────────────────────────────────────────────────────────────

@api_bp.get("/tasks")
def list_tasks():
    service = request.args.get("service")
    completed = request.args.get("completed")
    query = TodoTask.query
    if service:
        query = query.filter_by(source_service=service)
    if completed is not None:
        query = query.filter_by(completed=completed.lower() == "true")
    tasks = query.order_by(TodoTask.updated_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks])


@api_bp.get("/tasks/<int:task_id>")
def get_task(task_id):
    task = db.get_or_404(TodoTask, task_id)
    return jsonify(task.to_dict())


@api_bp.post("/tasks")
def create_task():
    data = request.get_json(force=True)
    required = ("source_service", "source_id", "title")
    if not data or not all(k in data for k in required):
        return jsonify({"error": "source_service, source_id and title are required"}), 400
    task = TodoTask(
        source_service=data["source_service"],
        source_id=data["source_id"],
        title=data["title"],
        notes=data.get("notes", ""),
        completed=data.get("completed", False),
        priority=data.get("priority", 1),
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201


@api_bp.patch("/tasks/<int:task_id>")
def update_task(task_id):
    task = db.get_or_404(TodoTask, task_id)
    data = request.get_json(force=True) or {}
    for field in ("title", "notes", "completed", "priority"):
        if field in data:
            setattr(task, field, data[field])
    db.session.commit()
    return jsonify(task.to_dict())


@api_bp.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    task = db.get_or_404(TodoTask, task_id)
    db.session.delete(task)
    db.session.commit()
    return "", 204


# ── Manual sync trigger ────────────────────────────────────────────────────────

@api_bp.post("/sync")
def trigger_sync():
    """Manually trigger a sync of all (or a specific) service."""
    service = request.args.get("service")
    from app.sync import sync_all, sync_service

    if service:
        count = sync_service(service)
        return jsonify({"synced": {service: count}})
    return jsonify({"synced": sync_all()})


# ── Settings / credentials ─────────────────────────────────────────────────────

@api_bp.get("/settings")
def get_settings():
    settings = SyncSettings.query.all()
    return jsonify(
        [
            {
                "service": s.service,
                "enabled": s.enabled,
                "sync_interval_minutes": s.sync_interval_minutes,
                "last_synced_at": s.last_synced_at.isoformat()
                if s.last_synced_at
                else None,
                "project_filter": s.project_filter,
            }
            for s in settings
        ]
    )


@api_bp.put("/settings/<service>")
def update_settings(service):
    settings = SyncSettings.query.filter_by(service=service).first_or_404()
    data = request.get_json(force=True) or {}
    for field in ("enabled", "sync_interval_minutes", "project_filter"):
        if field in data:
            setattr(settings, field, data[field])
    db.session.commit()
    return jsonify({"ok": True})


@api_bp.put("/credentials/<service>")
def update_credentials(service):
    data = request.get_json(force=True) or {}
    cred = ServiceCredential.query.filter_by(service=service).first()
    if cred is None:
        cred = ServiceCredential(service=service)
        db.session.add(cred)
    if "api_key" in data:
        cred.api_key = data["api_key"]
    if "user_id" in data:
        cred.user_id = data["user_id"]
    if "extra" in data:
        import json
        cred.extra = json.dumps(data["extra"])
    db.session.commit()
    return jsonify({"ok": True})
