"""
LK Clinic Tools - Digest Tasks
Celery tasks for weekly summary digests sent to clinic owners.
"""

from workers.celery_app import app


@app.task(name="workers.digest_tasks.send_weekly_digests")
def send_weekly_digests():
    """
    Send weekly performance digest to all active clinic owners.
    Runs weekly on Monday at 8am via Celery Beat.

    For each active clinic:
    1. Aggregate weekly data (reviews, rankings, appointments, chatbot stats)
    2. Format WhatsApp message with summary
    3. Send to clinic owner (clinic_admin role)

    Message format:
    📊 Resumo semanal - {{clinica}}:
    ⭐ Avaliações: {{new_reviews}} novas (total: {{total}}, média: {{avg}})
    📍 Ranking '{{keyword}}': posição {{rank}} ({{change}})
    🏥 Saúde GBP: {{score}}/100
    ⚠️ Ações necessárias: {{action_items}}
    """
    # TODO: Phase 2 - Implement weekly digest
    pass
