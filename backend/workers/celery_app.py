"""
LK Clinic Tools - Celery Application
Configures Celery with Redis broker and scheduled tasks (beat).
"""

from celery import Celery
from celery.schedules import crontab

from config import get_settings

settings = get_settings()

app = Celery(
    "lk_clinic_tools",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "workers.reminder_tasks",
        "workers.review_tasks",
        "workers.seo_tasks",
        "workers.digest_tasks",
        "workers.calendar_sync_tasks",
        "workers.cleanup_tasks",
    ],
)

app.conf.update(
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# ============================================================
# Celery Beat Schedule
# ============================================================

app.conf.beat_schedule = {
    # Every 1 minute: check for reminders to send
    "check-reminders": {
        "task": "workers.reminder_tasks.process_pending_reminders",
        "schedule": 60.0,  # Every 60 seconds
    },

    # Every 15 minutes: Google Calendar sync
    "calendar-sync": {
        "task": "workers.calendar_sync_tasks.sync_all_calendars",
        "schedule": 900.0,  # Every 15 minutes
    },

    # Daily 7am: GBP snapshots
    "daily-gbp-snapshot": {
        "task": "workers.seo_tasks.daily_gbp_snapshots",
        "schedule": crontab(hour=7, minute=0),
    },

    # Daily 7am: Review monitoring (poll Google for new reviews)
    "daily-review-monitor": {
        "task": "workers.review_tasks.monitor_google_reviews",
        "schedule": crontab(hour=7, minute=0),
    },

    # Daily 7am: Check no-shows from yesterday
    "daily-noshow-check": {
        "task": "workers.reminder_tasks.check_noshows",
        "schedule": crontab(hour=7, minute=0),
    },

    # Weekly Monday 8am: Rankings + competitor snapshots
    "weekly-rankings": {
        "task": "workers.seo_tasks.weekly_ranking_check",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),
    },

    # Weekly Monday 8am: Send digest to clinic owners
    "weekly-digest": {
        "task": "workers.digest_tasks.send_weekly_digests",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),
    },

    # Monthly 1st 6am: Generate monthly SEO reports
    "monthly-seo-report": {
        "task": "workers.seo_tasks.generate_monthly_reports",
        "schedule": crontab(hour=6, minute=0, day_of_month=1),
    },

    # Daily midnight: Cleanup old data
    "daily-cleanup": {
        "task": "workers.cleanup_tasks.cleanup_old_data",
        "schedule": crontab(hour=0, minute=0),
    },
}
