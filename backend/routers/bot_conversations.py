"""
LK Clinic Tools - Bot Conversations Router
Live chat inbox and conversation management.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


class SendMessageRequest(BaseModel):
    text: str


class AssignConversationRequest(BaseModel):
    assigned_to: str


@router.get("/")
async def list_conversations(
    status_filter: Optional[str] = None,
    bot_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List conversations for the clinic (live chat inbox)."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    query = (
        db.table("bot_conversations")
        .select("*, bot_contacts(name, phone), bots(name)")
        .eq("clinic_id", tenant.clinic_id)
        .order("last_message_at", desc=True)
    )

    if status_filter:
        query = query.eq("status", status_filter)
    if bot_id:
        query = query.eq("bot_id", bot_id)

    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    return {"conversations": result.data or []}


@router.get("/needs-human")
async def get_human_queue(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get conversations waiting for human agent."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("bot_conversations")
        .select("*, bot_contacts(name, phone), bots(name)")
        .eq("clinic_id", tenant.clinic_id)
        .eq("status", "human")
        .order("last_message_at", desc=True)
        .execute()
    )

    return {"conversations": result.data or [], "count": len(result.data or [])}


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get conversation details with messages."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()

    conversation = (
        db.table("bot_conversations")
        .select("*, bot_contacts(name, phone, email), bots(name)")
        .eq("id", conversation_id)
        .eq("clinic_id", tenant.clinic_id)
        .single()
        .execute()
    )

    if not conversation.data:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")

    messages = (
        db.table("bot_messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )

    return {
        "conversation": conversation.data,
        "messages": messages.data or [],
    }


@router.post("/{conversation_id}/messages")
async def send_human_message(
    conversation_id: str,
    data: SendMessageRequest,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Send a message as a human agent in a conversation."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()

    # Verify conversation belongs to clinic
    conversation = (
        db.table("bot_conversations")
        .select("id, status, contact_id, channel")
        .eq("id", conversation_id)
        .eq("clinic_id", tenant.clinic_id)
        .single()
        .execute()
    )

    if not conversation.data:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")

    # Save message to DB
    message = db.table("bot_messages").insert({
        "conversation_id": conversation_id,
        "direction": "outbound",
        "sender_type": "human_agent",
        "content": data.text,
        "message_type": "text",
    }).execute()

    # Update conversation timestamp
    from datetime import datetime, timezone
    db.table("bot_conversations").update({
        "last_message_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", conversation_id).execute()

    # TODO: Send via channel adapter (WhatsApp/Web) - Phase 2

    return {"message": message.data[0] if message.data else {}}


@router.post("/{conversation_id}/assign")
async def assign_conversation(
    conversation_id: str,
    data: AssignConversationRequest,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Assign a conversation to a staff member."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("bot_conversations")
        .update({"assigned_to": data.assigned_to})
        .eq("id", conversation_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")

    return {"message": "Conversa atribuída.", "conversation": result.data[0]}


@router.post("/{conversation_id}/resolve")
async def resolve_conversation(
    conversation_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Mark a conversation as resolved."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("bot_conversations")
        .update({"status": "resolved"})
        .eq("id", conversation_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")

    return {"message": "Conversa resolvida.", "conversation": result.data[0]}
