"""
LK Clinic Tools - Bot Contacts Router
Manage contacts captured by chatbots.
"""

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


@router.get("/")
async def list_contacts(
    tag: Optional[str] = None,
    source_bot_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List bot contacts for the clinic."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    query = (
        db.table("bot_contacts")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .order("created_at", desc=True)
    )

    if source_bot_id:
        query = query.eq("source_bot_id", source_bot_id)
    if tag:
        query = query.contains("tags", [tag])

    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    return {"contacts": result.data or []}


@router.get("/export")
async def export_contacts_csv(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Export all contacts as CSV."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("bot_contacts")
        .select("name, phone, email, tags, source_channel, conversation_count, created_at")
        .eq("clinic_id", tenant.clinic_id)
        .order("created_at", desc=True)
        .execute()
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Nome", "Telefone", "Email", "Tags", "Canal", "Conversas", "Criado em"])

    for contact in result.data or []:
        writer.writerow([
            contact.get("name", ""),
            contact.get("phone", ""),
            contact.get("email", ""),
            ", ".join(contact.get("tags") or []),
            contact.get("source_channel", ""),
            contact.get("conversation_count", 0),
            contact.get("created_at", ""),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contatos.csv"},
    )


@router.get("/{contact_id}")
async def get_contact(
    contact_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get contact details with captured data."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("bot_contacts")
        .select("*")
        .eq("id", contact_id)
        .eq("clinic_id", tenant.clinic_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Contato não encontrado.")

    return result.data


@router.patch("/{contact_id}/tags")
async def update_contact_tags(
    contact_id: str,
    tags: list[str],
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Update tags for a contact."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("bot_contacts")
        .update({"tags": tags})
        .eq("id", contact_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Contato não encontrado.")

    return result.data[0]
