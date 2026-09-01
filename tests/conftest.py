import pytest
from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    _app = create_app(TestingConfig)
    return _app


@pytest.fixture()
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def clean_db(app):
    """Delete all mutable rows after each test to ensure isolation."""
    yield
    with app.app_context():
        from app.models import ServiceCredential, SyncSettings, TodoTask

        _db.session.query(TodoTask).delete()
        _db.session.query(ServiceCredential).delete()
        # Reset settings to defaults instead of deleting them
        for s in SyncSettings.query.all():
            s.enabled = False
            s.sync_interval_minutes = 15
            s.project_filter = None
            s.last_synced_at = None
        _db.session.commit()
