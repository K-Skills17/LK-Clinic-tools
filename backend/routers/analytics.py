"""
LK Clinic Tools - Unified Analytics Router
Cross-module analytics for the clinic dashboard.
"""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get unified dashboard stats for the clinic homepage."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    today = date.today().isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()

    # Today's appointments
    appointments_today = (
        db.table("appointments")
        .select("id, status, confirmation_status", count="exact")
        .eq("clinic_id", tenant.clinic_id)
        .eq("appointment_date", today)
        .neq("status", "cancelado")
        .execute()
    )

    # This week's appointments
    appointments_week = (
        db.table("appointments")
        .select("id", count="exact")
        .eq("clinic_id", tenant.clinic_id)
        .gte("appointment_date", week_ago)
        .lte("appointment_date", today)
        .execute()
    )

    # Pending review requests
    pending_reviews = (
        db.table("review_requests")
        .select("id", count="exact")
        .eq("clinic_id", tenant.clinic_id)
        .in_("status", ["scheduled", "sent"])
        .execute()
    )

    # Active chatbot conversations
    active_conversations = (
        db.table("bot_conversations")
        .select("id", count="exact")
        .eq("clinic_id", tenant.clinic_id)
        .in_("status", ["active", "bot", "human"])
        .execute()
    )

    # Conversations needing human
    human_queue = (
        db.table("bot_conversations")
        .select("id", count="exact")
        .eq("clinic_id", tenant.clinic_id)
        .eq("status", "human")
        .execute()
    )

    # SEO health score
    gbp = (
        db.table("gbp_snapshots")
        .select("health_score, average_rating, review_count")
        .eq("clinic_id", tenant.clinic_id)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )

    # Unread alerts
    unread_alerts = (
        db.table("seo_alerts")
        .select("id", count="exact")
        .eq("clinic_id", tenant.clinic_id)
        .eq("is_read", False)
        .execute()
    )

    today_data = appointments_today.data or []

    return {
        "appointments": {
            "today_total": len(today_data),
            "today_confirmed": sum(1 for a in today_data if a.get("confirmation_status") == "confirmado"),
            "this_week": appointments_week.count or 0,
        },
        "reviews": {
            "pending_requests": pending_reviews.count or 0,
        },
        "chatbot": {
            "active_conversations": active_conversations.count or 0,
            "needs_human": human_queue.count or 0,
        },
        "seo": {
            "health_score": gbp.data[0]["health_score"] if gbp.data else None,
            "average_rating": float(gbp.data[0]["average_rating"]) if gbp.data else None,
            "review_count": gbp.data[0]["review_count"] if gbp.data else None,
        },
        "alerts": {
            "unread": unread_alerts.count or 0,
        },
    }


@router.get("/appointments")
async def get_appointment_analytics(
    period_days: int = 30,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get appointment analytics for the specified period."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    start_date = (date.today() - timedelta(days=period_days)).isoformat()

    appointments = (
        db.table("appointments")
        .select("status, confirmation_status, doctor_name, procedure_name, appointment_date")
        .eq("clinic_id", tenant.clinic_id)
        .gte("appointment_date", start_date)
        .execute()
    )

    data = appointments.data or []
    total = len(data)
    completed = sum(1 for a in data if a["status"] == "concluido")
    no_shows = sum(1 for a in data if a["status"] == "no_show")
    cancelled = sum(1 for a in data if a["status"] == "cancelado")
    confirmed = sum(1 for a in data if a["confirmation_status"] == "confirmado")

    return {
        "period_days": period_days,
        "total": total,
        "completed": completed,
        "no_shows": no_shows,
        "no_show_rate": round(no_shows / total * 100, 1) if total > 0 else 0,
        "cancelled": cancelled,
        "confirmation_rate": round(confirmed / total * 100, 1) if total > 0 else 0,
    }


@router.get("/chatbot")
async def get_chatbot_analytics(
    period_days: int = 30,
    bot_id: Optional[str] = None,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get chatbot analytics."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    start_date = (date.today() - timedelta(days=period_days)).isoformat()

    query = (
        db.table("bot_conversations")
        .select("status, started_at, last_message_at, bot_id")
        .eq("clinic_id", tenant.clinic_id)
        .gte("started_at", start_date)
    )

    if bot_id:
        query = query.eq("bot_id", bot_id)

    result = query.execute()
    data = result.data or []

    total = len(data)
    resolved = sum(1 for c in data if c["status"] == "resolved")
    human_handoff = sum(1 for c in data if c["status"] == "human")

    # Contacts captured in this period
    contacts = (
        db.table("bot_contacts")
        .select("id", count="exact")
        .eq("clinic_id", tenant.clinic_id)
        .gte("created_at", start_date)
        .execute()
    )

    return {
        "period_days": period_days,
        "total_conversations": total,
        "resolved": resolved,
        "human_handoffs": human_handoff,
        "handoff_rate": round(human_handoff / total * 100, 1) if total > 0 else 0,
        "contacts_captured": contacts.count or 0,
    }


@router.get("/campaigns")
async def get_campaign_analytics(
    period_days: int = 30,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get reactivation campaign analytics."""
    from datetime import timedelta
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    start_date = (date.today() - timedelta(days=period_days)).isoformat()

    campaigns = (
        db.table("campaigns")
        .select("id, name, status, created_at")
        .eq("clinic_id", tenant.clinic_id)
        .gte("created_at", start_date)
        .execute()
    )

    all_campaigns = campaigns.data or []
    total_campaigns = len(all_campaigns)
    active = sum(1 for c in all_campaigns if c["status"] == "active")
    completed = sum(1 for c in all_campaigns if c["status"] == "completed")

    total_sent = 0
    total_failed = 0
    for campaign in all_campaigns:
        contacts = (
            db.table("campaign_contacts")
            .select("status")
            .eq("campaign_id", campaign["id"])
            .execute()
        )
        for contact in contacts.data or []:
            if contact["status"] == "sent":
                total_sent += 1
            elif contact["status"] == "failed":
                total_failed += 1

    ai_usage = (
        db.table("ai_usage_daily")
        .select("count")
        .eq("clinic_id", tenant.clinic_id)
        .gte("usage_date", start_date)
        .execute()
    )
    total_ai = sum(r["count"] for r in ai_usage.data or [])

    return {
        "period_days": period_days,
        "total_campaigns": total_campaigns,
        "active": active,
        "completed": completed,
        "messages_sent": total_sent,
        "messages_failed": total_failed,
        "success_rate": round(total_sent / (total_sent + total_failed) * 100, 1) if (total_sent + total_failed) > 0 else 0,
        "ai_generations": total_ai,
    }
