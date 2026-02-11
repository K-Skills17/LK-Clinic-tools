"""
LK Clinic Tools - SEO Monitor Router
Local SEO dashboard, GBP health, rankings, and competitor data.
"""

from typing import Optional

from fastapi import APIRouter, Depends

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


@router.get("/dashboard")
async def get_seo_dashboard(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get unified SEO dashboard data for the clinic."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()

    # Latest GBP snapshot
    gbp = (
        db.table("gbp_snapshots")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )

    # Latest rankings
    rankings = (
        db.table("ranking_snapshots")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .order("snapshot_date", desc=True)
        .limit(10)
        .execute()
    )

    # Recent alerts
    alerts = (
        db.table("seo_alerts")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .eq("is_read", False)
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )

    # Pending recommendations
    recommendations = (
        db.table("seo_recommendations")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .eq("status", "pending")
        .order("priority")
        .limit(5)
        .execute()
    )

    return {
        "gbp_snapshot": gbp.data[0] if gbp.data else None,
        "rankings": rankings.data or [],
        "alerts": alerts.data or [],
        "recommendations": recommendations.data or [],
    }


@router.get("/gbp-history")
async def get_gbp_history(
    days: int = 30,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get GBP snapshot history for trend charts."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("gbp_snapshots")
        .select("snapshot_date, review_count, average_rating, health_score, photo_count")
        .eq("clinic_id", tenant.clinic_id)
        .order("snapshot_date", desc=True)
        .limit(days)
        .execute()
    )

    return {"snapshots": result.data or []}


@router.get("/rankings")
async def get_ranking_history(
    keyword: Optional[str] = None,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get ranking history for configured keywords."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    query = (
        db.table("ranking_snapshots")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .order("snapshot_date", desc=True)
    )

    if keyword:
        query = query.eq("keyword", keyword)

    query = query.limit(100)
    result = query.execute()

    return {"rankings": result.data or []}


@router.get("/competitors")
async def get_competitor_data(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get latest competitor snapshot data."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()

    # Get clinic's current data
    clinic_gbp = (
        db.table("gbp_snapshots")
        .select("review_count, average_rating")
        .eq("clinic_id", tenant.clinic_id)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )

    # Get latest competitor data
    competitors = (
        db.table("competitor_snapshots")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .order("snapshot_date", desc=True)
        .execute()
    )

    # Deduplicate: latest snapshot per competitor
    latest_competitors = {}
    for comp in competitors.data or []:
        pid = comp["competitor_place_id"]
        if pid not in latest_competitors:
            latest_competitors[pid] = comp

    return {
        "clinic": clinic_gbp.data[0] if clinic_gbp.data else None,
        "competitors": list(latest_competitors.values()),
    }


@router.get("/recommendations")
async def get_seo_recommendations(
    status_filter: str = "pending",
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get AI-generated SEO recommendations."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("seo_recommendations")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .eq("status", status_filter)
        .order("priority")
        .execute()
    )

    return {"recommendations": result.data or []}


@router.patch("/recommendations/{recommendation_id}")
async def update_recommendation_status(
    recommendation_id: str,
    status: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Mark a recommendation as implemented or dismissed."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("seo_recommendations")
        .update({"status": status})
        .eq("id", recommendation_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    return {"recommendation": result.data[0] if result.data else None}
