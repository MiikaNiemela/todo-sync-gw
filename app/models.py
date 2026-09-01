from datetime import datetime, timezone
from app.extensions import db


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ServiceCredential(db.Model):
    """Stores OAuth tokens or API keys for external todo services."""

    __tablename__ = "service_credentials"

    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(50), nullable=False, unique=True)
    api_key = db.Column(db.String(512), nullable=True)
    user_id = db.Column(db.String(256), nullable=True)
    extra = db.Column(db.Text, nullable=True)  # JSON-encoded additional fields
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    def __repr__(self):
        return f"<ServiceCredential service={self.service}>"


class SyncSettings(db.Model):
    """Stores per-service sync preferences."""

    __tablename__ = "sync_settings"

    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(50), nullable=False, unique=True)
    enabled = db.Column(db.Boolean, default=False)
    sync_interval_minutes = db.Column(db.Integer, default=15)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    project_filter = db.Column(db.String(256), nullable=True)

    def __repr__(self):
        return f"<SyncSettings service={self.service} enabled={self.enabled}>"


class TodoTask(db.Model):
    """Canonical task record kept in sync across services."""

    __tablename__ = "todo_tasks"

    id = db.Column(db.Integer, primary_key=True)
    # Which service owns this copy of the task
    source_service = db.Column(db.String(50), nullable=False)
    source_id = db.Column(db.String(256), nullable=False)
    title = db.Column(db.String(512), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.Integer, default=1)  # 1 (low) – 4 (urgent)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    __table_args__ = (
        db.UniqueConstraint("source_service", "source_id", name="uq_service_task"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "source_service": self.source_service,
            "source_id": self.source_id,
            "title": self.title,
            "notes": self.notes,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed": self.completed,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<TodoTask {self.source_service}:{self.source_id} '{self.title}'>"
