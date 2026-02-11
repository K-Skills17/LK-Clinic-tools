"""
LK Clinic Tools - Agency Dashboard Router
Overview dashboard for LK Digital agency (all clinics at a glance).
"""

from fastapi import APIRouter, Depends

from dependencies import CurrentUser, require_role

router = APIRouter()


@router.get("/overview")
async def get_agency_overview(
    user: CurrentUser = Depends(require_role("agency_admin", "agency_operator")),
):
    """Get overview of all clinics for the agency dashboard."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()

    # All active clinics
    clinics = (
        db.table("clinics")
        .select("id, business_name, city, state, plan, subscription_status, whatsapp_number")
        .eq("is_active", True)
        .order("business_name")
        .execute()
    )

    clinic_summaries = []
    for clinic in clinics.data or []:
        clinic_id = clinic["id"]

        # Quick stats per clinic (latest GBP snapshot)
        gbp = (
            db.table("gbp_snapshots")
            .select("health_score, average_rating, review_count")
            .eq("clinic_id", clinic_id)
            .order("snapshot_date", desc=True)
            .limit(1)
            .execute()
        )

        # Active conversations count
        active_convos = (
            db.table("bot_conversations")
            .select("id", count="exact")
            .eq("clinic_id", clinic_id)
            .in_("status", ["active", "bot", "human"])
            .execute()
        )

        # Unread alerts count
        alerts = (
            db.table("seo_alerts")
            .select("id", count="exact")
            .eq("clinic_id", clinic_id)
            .eq("is_read", False)
            .execute()
        )

        clinic_summaries.append({
            **clinic,
            "seo_health_score": gbp.data[0]["health_score"] if gbp.data else None,
            "average_rating": float(gbp.data[0]["average_rating"]) if gbp.data else None,
            "review_count": gbp.data[0]["review_count"] if gbp.data else None,
            "active_conversations": active_convos.count or 0,
            "unread_alerts": alerts.count or 0,
        })

    return {
        "total_clinics": len(clinic_summaries),
        "clinics": clinic_summaries,
    }


@router.get("/clinics/{clinic_id}/users")
async def list_clinic_users(
    clinic_id: str,
    user: CurrentUser = Depends(require_role("agency_admin", "agency_operator")),
):
    """List users for a specific clinic."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("clinic_users")
        .select("*")
        .eq("clinic_id", clinic_id)
        .eq("is_active", True)
        .order("role")
        .execute()
    )

    return {"users": result.data or []}
