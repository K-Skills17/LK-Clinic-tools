"""
LK Clinic Tools - Campaigns Router
Module 5: Reactivation campaigns - CRUD, contact import, message queue, blocklist, drafts.
"""

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


# ============================================================
# Schemas
# ============================================================

class CampaignCreate(BaseModel):
    name: str


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None


class ContactImport(BaseModel):
    contacts: list[dict]


class ContactBlock(BaseModel):
    phone: str
    reason: Optional[str] = None


class MarkSent(BaseModel):
    contact_id: str


class MarkFailed(BaseModel):
    contact_id: str
    error: str


class DraftCreate(BaseModel):
    name: str
    template_text: str


class DraftUpdate(BaseModel):
    name: Optional[str] = None
    template_text: Optional[str] = None


class SetMessage(BaseModel):
    contact_id: str
    message: str


# ============================================================
# Campaign CRUD
# ============================================================

@router.get("/")
async def list_campaigns(
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List all campaigns for the clinic."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    campaigns = svc.list_campaigns(status=status_filter, limit=limit, offset=offset)

    for campaign in campaigns:
        campaign["stats"] = svc.get_campaign_stats(campaign["id"])

    return {"campaigns": campaigns, "count": len(campaigns)}


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get a campaign with stats."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    campaign = svc.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha nao encontrada.")

    campaign["stats"] = svc.get_campaign_stats(campaign_id)
    return campaign


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: CampaignCreate,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Create a new reactivation campaign."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    return svc.create_campaign(data.name)


@router.patch("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    data: CampaignUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Update campaign name or status."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar.")

    if "status" in update_data and update_data["status"] not in (
        "draft", "active", "paused", "completed"
    ):
        raise HTTPException(status_code=400, detail="Status invalido.")

    result = svc.update_campaign(campaign_id, update_data)
    if not result:
        raise HTTPException(status_code=404, detail="Campanha nao encontrada.")
    return result


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Delete a campaign and all its contacts."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    if not svc.delete_campaign(campaign_id):
        raise HTTPException(status_code=404, detail="Campanha nao encontrada.")
    return {"message": "Campanha excluida com sucesso."}


# ============================================================
# Contact Management
# ============================================================

@router.get("/{campaign_id}/contacts")
async def list_contacts(
    campaign_id: str,
    status_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List contacts in a campaign."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    contacts = svc.list_contacts(campaign_id, status=status_filter, limit=limit, offset=offset)
    return {"contacts": contacts, "count": len(contacts)}


@router.post("/{campaign_id}/contacts")
async def import_contacts(
    campaign_id: str,
    data: ContactImport,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Import contacts into a campaign (JSON body)."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    if not svc.get_campaign(campaign_id):
        raise HTTPException(status_code=404, detail="Campanha nao encontrada.")

    return svc.import_contacts(campaign_id, data.contacts)


@router.post("/{campaign_id}/import-csv")
async def import_contacts_csv(
    campaign_id: str,
    file: UploadFile = File(...),
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Import contacts from a CSV file. Columns: name/nome, phone/telefone."""
    from services.campaign_service import CampaignService

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV.")

    svc = CampaignService(tenant.clinic_id)
    if not svc.get_campaign(campaign_id):
        raise HTTPException(status_code=404, detail="Campanha nao encontrada.")

    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")

    contacts = []
    for row in reader:
        contacts.append({
            "name": row.get("name", row.get("nome", "")).strip(),
            "phone": row.get("phone", row.get("telefone", "")).strip(),
        })

    return svc.import_contacts(campaign_id, contacts)


@router.patch("/{campaign_id}/contacts/{contact_id}/message")
async def set_contact_message(
    campaign_id: str,
    contact_id: str,
    data: SetMessage,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Set personalized message for a contact."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("campaign_contacts")
        .update({"personalized_message": data.message})
        .eq("id", contact_id)
        .eq("campaign_id", campaign_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Contato nao encontrado.")
    return result.data[0]


# ============================================================
# Message Queue (for WhatsApp sender)
# ============================================================

@router.get("/{campaign_id}/queue")
async def get_message_queue(
    campaign_id: str,
    limit: int = 50,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get next batch of pending messages to send."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    messages = svc.get_pending_messages(campaign_id, limit=limit)
    return {"messages": messages, "count": len(messages)}


@router.post("/{campaign_id}/mark-sent")
async def mark_message_sent(
    campaign_id: str,
    data: MarkSent,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Mark a contact as successfully sent."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    svc.mark_sent(data.contact_id)
    return {"message": "Contato marcado como enviado."}


@router.post("/{campaign_id}/mark-failed")
async def mark_message_failed(
    campaign_id: str,
    data: MarkFailed,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Mark a contact as failed."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    svc.mark_failed(data.contact_id, data.error)
    return {"message": "Contato marcado como falha."}


# ============================================================
# Blocklist (Do Not Contact - LGPD)
# ============================================================

@router.get("/blocklist")
async def list_blocked_phones(
    limit: int = 100,
    offset: int = 0,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List all blocked phone numbers."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    blocked = svc._list("do_not_contact", limit=limit, offset=offset)
    return {"blocked": blocked, "count": len(blocked)}


@router.post("/blocklist")
async def block_phone(
    data: ContactBlock,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Add a phone to the do-not-contact list."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    try:
        return svc.block_phone(data.phone, data.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/blocklist/{phone_id}")
async def unblock_phone(
    phone_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Remove a phone from the blocklist."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    if not svc.unblock_phone(phone_id):
        raise HTTPException(status_code=404, detail="Registro nao encontrado.")
    return {"message": "Telefone desbloqueado."}


# ============================================================
# Message Drafts (Templates)
# ============================================================

@router.get("/drafts")
async def list_drafts(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List saved message templates."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    return {"drafts": svc.list_drafts()}


@router.post("/drafts", status_code=status.HTTP_201_CREATED)
async def create_draft(
    data: DraftCreate,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Save a new message template."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    return svc.create_draft(data.name, data.template_text)


@router.patch("/drafts/{draft_id}")
async def update_draft(
    draft_id: str,
    data: DraftUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Update a message template."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar.")
    result = svc.update_draft(draft_id, update_data)
    if not result:
        raise HTTPException(status_code=404, detail="Rascunho nao encontrado.")
    return result


@router.delete("/drafts/{draft_id}")
async def delete_draft(
    draft_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Delete a message template."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    if not svc.delete_draft(draft_id):
        raise HTTPException(status_code=404, detail="Rascunho nao encontrado.")
    return {"message": "Rascunho excluido."}
