"""
LK Clinic Tools - Reminders Router
Manage appointment reminders configuration and status.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


@router.get("/")
async def list_reminders(
    appointment_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List reminders for the clinic, optionally filtered by appointment."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    query = (
        db.table("appointment_reminders")
        .select("*, appointments!inner(clinic_id, patient_name, patient_phone, appointment_date, appointment_time)")
        .eq("appointments.clinic_id", tenant.clinic_id)
        .order("scheduled_for", desc=True)
    )

    if appointment_id:
        query = query.eq("appointment_id", appointment_id)
    if status_filter:
        query = query.eq("status", status_filter)

    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    return {"reminders": result.data or []}


@router.get("/pending")
async def get_pending_reminders(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get all pending (scheduled) reminders for the clinic."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("appointment_reminders")
        .select("*, appointments!inner(clinic_id, patient_name, patient_phone, appointment_date, appointment_time, doctor_name)")
        .eq("appointments.clinic_id", tenant.clinic_id)
        .eq("status", "scheduled")
        .order("scheduled_for")
        .execute()
    )

    return {"pending_reminders": result.data or [], "count": len(result.data or [])}


@router.patch("/{reminder_id}/skip")
async def skip_reminder(
    reminder_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Skip a scheduled reminder."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()

    # Verify the reminder belongs to this clinic via the appointment
    reminder = (
        db.table("appointment_reminders")
        .select("*, appointments!inner(clinic_id)")
        .eq("id", reminder_id)
        .eq("appointments.clinic_id", tenant.clinic_id)
        .single()
        .execute()
    )

    if not reminder.data:
        raise HTTPException(status_code=404, detail="Lembrete não encontrado.")

    result = (
        db.table("appointment_reminders")
        .update({"status": "skipped"})
        .eq("id", reminder_id)
        .execute()
    )

    return {"message": "Lembrete cancelado.", "reminder": result.data[0] if result.data else None}
