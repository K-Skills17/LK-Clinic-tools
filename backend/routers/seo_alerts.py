"""
LK Clinic Tools - SEO Alerts Router
Manage SEO alerts and notifications.
"""

from typing import Optional

from fastapi import APIRouter, Depends

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


@router.get("/")
async def list_alerts(
    is_read: Optional[bool] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List SEO alerts for the clinic."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    query = (
        db.table("seo_alerts")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .order("created_at", desc=True)
        .limit(limit)
    )

    if is_read is not None:
        query = query.eq("is_read", is_read)
    if severity:
        query = query.eq("severity", severity)

    result = query.execute()
    return {"alerts": result.data or []}


@router.patch("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Mark an alert as read."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    db.table("seo_alerts").update({"is_read": True}).eq("id", alert_id).eq("clinic_id", tenant.clinic_id).execute()
    return {"message": "Alerta marcado como lido."}


@router.post("/mark-all-read")
async def mark_all_read(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Mark all alerts as read for the clinic."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    db.table("seo_alerts").update({"is_read": True}).eq("clinic_id", tenant.clinic_id).eq("is_read", False).execute()
    return {"message": "Todos os alertas marcados como lidos."}
