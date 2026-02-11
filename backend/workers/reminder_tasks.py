"""
LK Clinic Tools - Reminder Tasks
Celery tasks for processing and sending appointment reminders.
"""

from workers.celery_app import app


@app.task(name="workers.reminder_tasks.process_pending_reminders")
def process_pending_reminders():
    """
    Process all pending reminders that are due to be sent.
    Runs every minute via Celery Beat.

    Logic:
    1. Query appointment_reminders WHERE status='scheduled' AND scheduled_for <= now()
    2. For each reminder:
       a. Load the appointment and clinic config
       b. Check sending hours (respect clinic's reminder_sending_hours)
       c. Check if reminder should be skipped (patient already confirmed, etc.)
       d. Render message template with patient/appointment variables
       e. Send via WhatsApp adapter
       f. Update reminder status to 'sent'
    """
    # TODO: Phase 2 - Implement full reminder processing
    pass


@app.task(name="workers.reminder_tasks.schedule_reminders_for_appointment")
def schedule_reminders_for_appointment(appointment_id: str):
    """
    Create reminder records for a new appointment.
    Called when an appointment is created or updated.

    Creates reminders based on clinic's reminder_schedule config:
    - before_48h: 48 hours before appointment
    - before_24h: 24 hours before (if not already confirmed)
    - before_2h: 2 hours before (confirmed patients only)
    - post: 2 hours after appointment ends (triggers review flow)
    - noshow: next business day if patient didn't show
    """
    # TODO: Phase 2 - Implement reminder scheduling
    pass


@app.task(name="workers.reminder_tasks.check_noshows")
def check_noshows():
    """
    Check for no-shows from yesterday.
    Runs daily at 7am via Celery Beat.

    Logic:
    1. Find appointments from yesterday that are still 'pendente' or 'confirmado' (not 'concluido')
    2. Mark them as 'no_show'
    3. Schedule no-show follow-up message
    4. Update no-show analytics
    """
    # TODO: Phase 2 - Implement no-show detection
    pass


@app.task(name="workers.reminder_tasks.process_patient_response")
def process_patient_response(clinic_id: str, patient_phone: str, response_text: str):
    """
    Process a patient's response to a reminder.
    Called from the WhatsApp webhook handler.

    Handles:
    - "Confirmar" / "Sim" → mark confirmed, stop further reminders
    - "Remarcar" → send available slots or instruct to call
    - "Ver orientações" → send pre-appointment instructions
    - Other text → route to clinic staff
    """
    # TODO: Phase 2 - Implement response processing
    pass
