"""Webhook receivers for Todoist, Habitica and Google Pub/Sub."""
import hashlib
import hmac
import json
import logging

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.models import TodoTask

webhooks_bp = Blueprint("webhooks", __name__)
logger = logging.getLogger(__name__)


def _verify_todoist_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    """Return True when the HMAC-SHA256 signature matches."""
    expected = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig_header)


@webhooks_bp.post("/todoist")
def todoist_webhook():
    secret = current_app.config.get("TODOIST_WEBHOOK_SECRET", "")
    if secret:
        sig = request.headers.get("X-Todoist-Hmac-SHA256", "")
        if not _verify_todoist_signature(request.data, sig, secret):
            return jsonify({"error": "invalid signature"}), 401

    payload = request.get_json(force=True) or {}
    event_type = payload.get("event_name", "")
    event_data = payload.get("event_data", {})

    if event_type in ("item:added", "item:updated"):
        from app.services.todoist import TodoistService
        from app.sync import _upsert_task

        normalised = TodoistService.normalise(event_data)
        _upsert_task(normalised)
        db.session.commit()

    elif event_type == "item:completed":
        task = TodoTask.query.filter_by(
            source_service="todoist", source_id=str(event_data.get("id", ""))
        ).first()
        if task:
            task.completed = True
            db.session.commit()

    elif event_type == "item:deleted":
        task = TodoTask.query.filter_by(
            source_service="todoist", source_id=str(event_data.get("id", ""))
        ).first()
        if task:
            db.session.delete(task)
            db.session.commit()

    return jsonify({"ok": True})


@webhooks_bp.post("/habitica")
def habitica_webhook():
    payload = request.get_json(force=True) or {}
    web_type = payload.get("type", "")

    if web_type == "scored":
        task_data = payload.get("task", {})
        from app.services.habitica import HabiticaService
        from app.sync import _upsert_task

        normalised = HabiticaService.normalise(task_data)
        normalised["completed"] = True
        _upsert_task(normalised)
        db.session.commit()

    return jsonify({"ok": True})


@webhooks_bp.post("/google")
def google_pubsub_webhook():
    """Receives Google Pub/Sub push messages."""
    envelope = request.get_json(force=True) or {}
    message = envelope.get("message", {})
    if not message:
        return jsonify({"error": "no message"}), 400

    import base64

    data_bytes = base64.b64decode(message.get("data", ""))
    data = json.loads(data_bytes.decode("utf-8"))
    logger.info("Google Pub/Sub message received: %s", data)
    return jsonify({"ok": True})
