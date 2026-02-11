"""
LK Clinic Tools - Review Tasks
Celery tasks for review request flow and Google review monitoring.
"""

from workers.celery_app import app


@app.task(name="workers.review_tasks.send_review_request")
def send_review_request(review_request_id: str):
    """
    Send the satisfaction check message to a patient.
    Triggered 2 hours after appointment ends.

    Flow:
    1. Load review request and clinic config
    2. Check dedup (no duplicate within 90 days)
    3. Render satisfaction check template
    4. Send via WhatsApp
    5. Update status to 'sent'
    """
    # TODO: Phase 2 - Implement review request sending
    pass


@app.task(name="workers.review_tasks.send_review_link")
def send_review_link(review_request_id: str):
    """
    Send Google review link to a patient who gave positive feedback.
    Called after satisfaction_score >= threshold.
    """
    # TODO: Phase 2 - Implement review link sending
    pass


@app.task(name="workers.review_tasks.send_review_reminder")
def send_review_reminder(review_request_id: str):
    """
    Send a gentle reminder to leave a Google review.
    Scheduled 24h after review link was sent.
    """
    # TODO: Phase 2 - Implement review reminder
    pass


@app.task(name="workers.review_tasks.monitor_google_reviews")
def monitor_google_reviews():
    """
    Poll Google Places API for new reviews across all clinics.
    Runs daily at 7am via Celery Beat.

    Logic:
    1. For each active clinic with google_place_id:
       a. Fetch reviews from Google Places API
       b. Compare with stored reviews
       c. Store new reviews with sentiment analysis
       d. Create alerts for new negative reviews
       e. Auto-generate AI response options for each new review
    """
    # TODO: Phase 2 - Implement Google review monitoring
    pass


@app.task(name="workers.review_tasks.handle_negative_feedback")
def handle_negative_feedback(review_request_id: str, complaint: str):
    """
    Handle negative feedback from a patient.
    Creates urgent ticket and alerts clinic manager.
    """
    # TODO: Phase 2 - Implement negative feedback handling
    pass
