"""
LK Clinic Tools - Waitlist Router
Manage patient waitlist for cancellation slots.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


class WaitlistCreate(BaseModel):
    patient_name: str
    patient_phone: str
    preferred_dates: Optional[list] = None
    preferred_procedures: Optional[list[str]] = None


class WaitlistUpdate(BaseModel):
    preferred_dates: Optional[list] = None
    preferred_procedures: Optional[list[str]] = None
    status: Optional[str] = None


@router.get("/")
async def list_waitlist(
    status_filter: str = "waiting",
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List waitlist entries for the clinic."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    query = (
        db.table("waitlist")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .order("created_at", desc=True)
    )

    if status_filter:
        query = query.eq("status", status_filter)

    result = query.execute()
    return {"waitlist": result.data or []}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_to_waitlist(
    data: WaitlistCreate,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Add a patient to the waitlist."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    entry = data.model_dump(exclude_none=True)
    entry["clinic_id"] = tenant.clinic_id

    result = db.table("waitlist").insert(entry).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao adicionar à lista de espera.")

    return result.data[0]


@router.patch("/{waitlist_id}")
async def update_waitlist_entry(
    waitlist_id: str,
    data: WaitlistUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Update a waitlist entry."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    update_data = data.model_dump(exclude_none=True)

    result = (
        db.table("waitlist")
        .update(update_data)
        .eq("id", waitlist_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Entrada não encontrada.")

    return result.data[0]


@router.delete("/{waitlist_id}")
async def remove_from_waitlist(
    waitlist_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Remove a patient from the waitlist."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("waitlist")
        .delete()
        .eq("id", waitlist_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    return {"message": "Removido da lista de espera."}
