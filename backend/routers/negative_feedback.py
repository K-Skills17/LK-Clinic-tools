"""
LK Clinic Tools - Negative Feedback Router
Manage negative/neutral feedback tickets from patients.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


class FeedbackUpdate(BaseModel):
    assigned_to: Optional[str] = None
    resolution_status: Optional[str] = None
    resolution_notes: Optional[str] = None


@router.get("/")
async def list_negative_feedback(
    status_filter: Optional[str] = None,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List negative feedback tickets."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    query = (
        db.table("negative_feedback")
        .select("*, clinic_users(name)")
        .eq("clinic_id", tenant.clinic_id)
        .order("created_at", desc=True)
    )

    if status_filter:
        query = query.eq("resolution_status", status_filter)

    result = query.execute()
    return {"feedback": result.data or []}


@router.patch("/{feedback_id}")
async def update_feedback(
    feedback_id: str,
    data: FeedbackUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Update feedback ticket (assign, resolve, add notes)."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    update_data = data.model_dump(exclude_none=True)

    if data.resolution_status == "resolvido":
        from datetime import datetime, timezone
        update_data["resolved_at"] = datetime.now(timezone.utc).isoformat()

    result = (
        db.table("negative_feedback")
        .update(update_data)
        .eq("id", feedback_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Feedback não encontrado.")

    return result.data[0]
