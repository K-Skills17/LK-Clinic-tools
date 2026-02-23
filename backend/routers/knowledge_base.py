"""
LK Clinic Tools - Knowledge Base Router
Manage per-clinic knowledge base for AI chatbot responses.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


class KnowledgeBaseUpdate(BaseModel):
    faqs: Optional[list] = None
    services: Optional[list] = None
    business_info: Optional[dict] = None
    doctor_profiles: Optional[list] = None
    additional_context: Optional[str] = None


@router.get("/")
async def get_knowledge_base(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get the clinic's knowledge base."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("knowledge_bases")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        # Create default if missing
        default = {
            "clinic_id": tenant.clinic_id,
            "faqs": [],
            "services": [],
            "business_info": {},
            "doctor_profiles": [],
        }
        db.table("knowledge_bases").insert(default).execute()
        return default

    return result.data[0]


@router.put("/")
async def update_knowledge_base(
    data: KnowledgeBaseUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Update the clinic's knowledge base."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    from datetime import datetime, timezone

    update_data = data.model_dump(exclude_none=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Try update first
    result = (
        db.table("knowledge_bases")
        .update(update_data)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        # Insert if not exists
        update_data["clinic_id"] = tenant.clinic_id
        result = db.table("knowledge_bases").insert(update_data).execute()

    return result.data[0] if result.data else {}


@router.post("/faqs")
async def add_faq(
    question: str,
    answer: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Add a single FAQ entry to the knowledge base."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    kb = (
        db.table("knowledge_bases")
        .select("faqs")
        .eq("clinic_id", tenant.clinic_id)
        .single()
        .execute()
    )

    if not kb.data:
        raise HTTPException(status_code=404, detail="Base de conhecimento não encontrada.")

    faqs = kb.data.get("faqs", [])
    faqs.append({"question": question, "answer": answer})

    db.table("knowledge_bases").update({"faqs": faqs}).eq("clinic_id", tenant.clinic_id).execute()

    return {"message": "FAQ adicionada.", "faqs_count": len(faqs)}
