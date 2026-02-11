"""
LK Clinic Tools - Message Templates Router
Manage message templates for reminders, reviews, and chatbot.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


class TemplateUpdate(BaseModel):
    message_text: str
    is_active: Optional[bool] = None


@router.get("/")
async def list_templates(
    module: Optional[str] = None,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List message templates for the clinic."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    query = (
        db.table("message_templates")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .order("module")
        .order("step")
    )

    if module:
        query = query.eq("module", module)

    result = query.execute()
    return {"templates": result.data or []}


@router.patch("/{template_id}")
async def update_template(
    template_id: str,
    data: TemplateUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Update a message template."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    update_data = data.model_dump(exclude_none=True)

    result = (
        db.table("message_templates")
        .update(update_data)
        .eq("id", template_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Template não encontrado.")

    return result.data[0]


@router.post("/reset/{module}")
async def reset_templates(
    module: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Reset templates for a module back to defaults."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()

    # Delete existing templates for this module
    db.table("message_templates").delete().eq("clinic_id", tenant.clinic_id).eq("module", module).execute()

    # Re-create defaults
    db.rpc("create_default_templates", {"p_clinic_id": tenant.clinic_id}).execute()

    return {"message": f"Templates do módulo '{module}' resetados para o padrão."}
