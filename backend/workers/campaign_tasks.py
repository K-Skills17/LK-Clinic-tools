"""
LK Clinic Tools - Campaign Workers
Celery tasks for campaign automation: auto-complete and usage cleanup.
"""

from workers.celery_app import app


@app.task(name="workers.campaign_tasks.auto_complete_campaigns")
def auto_complete_campaigns():
    """
    Auto-complete campaigns where all contacts have been processed
    (no more pending contacts).
    """
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()

    active_campaigns = (
        db.table("campaigns")
        .select("id, clinic_id")
        .eq("status", "active")
        .execute()
    )

    completed_count = 0
    for campaign in active_campaigns.data or []:
        pending = (
            db.table("campaign_contacts")
            .select("id", count="exact")
            .eq("campaign_id", campaign["id"])
            .eq("status", "pending")
            .execute()
        )

        if (pending.count or 0) == 0:
            total = (
                db.table("campaign_contacts")
                .select("id", count="exact")
                .eq("campaign_id", campaign["id"])
                .execute()
            )
            if (total.count or 0) > 0:
                db.table("campaigns").update(
                    {"status": "completed"}
                ).eq("id", campaign["id"]).execute()
                completed_count += 1

    return {"auto_completed": completed_count}


@app.task(name="workers.campaign_tasks.cleanup_old_ai_usage")
def cleanup_old_ai_usage():
    """Remove ai_usage_daily records older than 90 days."""
    from datetime import date, timedelta

    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    cutoff = (date.today() - timedelta(days=90)).isoformat()

    db.table("ai_usage_daily").delete().lt("usage_date", cutoff).execute()

    return {"cleaned_before": cutoff}
