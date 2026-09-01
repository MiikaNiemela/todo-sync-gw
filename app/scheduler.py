"""APScheduler-based background scheduler for periodic syncing."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

_scheduler: BackgroundScheduler | None = None


def start_scheduler(app) -> None:
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        return

    interval = app.config.get("SYNC_INTERVAL_MINUTES", 15)

    def _job():
        with app.app_context():
            from app.sync import sync_all

            sync_all()

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _job,
        trigger=IntervalTrigger(minutes=interval),
        id="sync_all",
        replace_existing=True,
    )
    _scheduler.start()


def get_scheduler() -> BackgroundScheduler | None:
    return _scheduler
