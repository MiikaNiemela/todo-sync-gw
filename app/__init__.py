from flask import Flask
from app.config import Config
from app.extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialise extensions
    db.init_app(app)

    # Register blueprints
    from app.routes.api import api_bp
    from app.routes.webhooks import webhooks_bp
    from app.routes.ui import ui_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(webhooks_bp, url_prefix="/webhooks")
    app.register_blueprint(ui_bp)

    # Create tables
    with app.app_context():
        db.create_all()
        _seed_default_settings()

    # Start background scheduler (skipped in tests)
    if app.config.get("SCHEDULER_ENABLED", True):
        from app.scheduler import start_scheduler
        start_scheduler(app)

    return app


def _seed_default_settings():
    """Insert default SyncSettings rows if they don't exist yet."""
    from app.models import SyncSettings

    for service in ("todoist", "habitica", "google_tasks"):
        if not SyncSettings.query.filter_by(service=service).first():
            db.session.add(SyncSettings(service=service, enabled=False))
    db.session.commit()
