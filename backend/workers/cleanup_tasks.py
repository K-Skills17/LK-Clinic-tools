"""
LK Clinic Tools - Cleanup Tasks
Celery tasks for data maintenance and cleanup.
"""

from workers.celery_app import app


@app.task(name="workers.cleanup_tasks.cleanup_old_data")
def cleanup_old_data():
    """
    Clean up old/stale data. Runs daily at midnight.

    Actions:
    1. Expire waitlist entries older than 30 days
    2. Clean up resolved conversations older than 90 days (archive)
    3. Remove old bot message content for resolved conversations (keep metadata)
    4. Clean up expired review request reminders
    """
    # TODO: Phase 2 - Implement cleanup logic
    pass
