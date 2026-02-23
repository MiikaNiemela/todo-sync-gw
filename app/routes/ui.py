"""Web UI blueprint – settings and credential management."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import ServiceCredential, SyncSettings, TodoTask

ui_bp = Blueprint("ui", __name__)


@ui_bp.get("/")
def index():
    tasks = TodoTask.query.order_by(TodoTask.updated_at.desc()).limit(50).all()
    settings = {s.service: s for s in SyncSettings.query.all()}
    return render_template("index.html", tasks=tasks, settings=settings)


@ui_bp.get("/settings")
def settings():
    all_settings = SyncSettings.query.all()
    credentials = {c.service: c for c in ServiceCredential.query.all()}
    return render_template(
        "settings.html", settings=all_settings, credentials=credentials
    )


@ui_bp.post("/settings/<service>")
def update_settings(service):
    s = SyncSettings.query.filter_by(service=service).first_or_404()
    s.enabled = "enabled" in request.form
    interval = request.form.get("sync_interval_minutes", "15")
    try:
        s.sync_interval_minutes = int(interval)
    except ValueError:
        flash("Sync interval must be a number.", "error")
        return redirect(url_for("ui.settings"))
    s.project_filter = request.form.get("project_filter") or None
    db.session.commit()
    flash(f"{service} settings saved.", "success")
    return redirect(url_for("ui.settings"))


@ui_bp.get("/auth/<service>")
def auth(service):
    if service not in ("todoist", "habitica", "google_tasks"):
        return "Unknown service", 404
    cred = ServiceCredential.query.filter_by(service=service).first()
    return render_template("auth.html", service=service, credential=cred)


@ui_bp.post("/auth/<service>")
def save_auth(service):
    if service not in ("todoist", "habitica", "google_tasks"):
        return "Unknown service", 404
    cred = ServiceCredential.query.filter_by(service=service).first()
    if cred is None:
        cred = ServiceCredential(service=service)
        db.session.add(cred)
    cred.api_key = request.form.get("api_key", "").strip()
    cred.user_id = request.form.get("user_id", "").strip() or None
    db.session.commit()
    flash(f"{service} credentials saved.", "success")
    return redirect(url_for("ui.settings"))
