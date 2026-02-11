"""
LK Clinic Tools - Review Responses Router
AI-generated review response management.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


class GenerateResponseRequest(BaseModel):
    review_id: str


class ApproveResponseRequest(BaseModel):
    review_id: str
    selected_response: str
    edited_text: Optional[str] = None


@router.post("/generate")
async def generate_review_responses(
    data: GenerateResponseRequest,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Generate AI response options for a Google review using Claude API."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()

    # Get the review
    review = (
        db.table("google_reviews")
        .select("*")
        .eq("id", data.review_id)
        .eq("clinic_id", tenant.clinic_id)
        .single()
        .execute()
    )

    if not review.data:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")

    # Get clinic info + response config
    clinic = db.table("clinics").select("business_name").eq("id", tenant.clinic_id).single().execute()
    config = (
        db.table("review_response_config")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    # TODO: Call Claude API to generate responses (Phase 2 - AI service)
    # For now, return placeholder
    response_options = [
        {"tone": "profissional", "text": f"Obrigado pela sua avaliação, {review.data['reviewer_name']}! Ficamos felizes em saber que teve uma boa experiência."},
        {"tone": "caloroso", "text": f"Que alegria receber seu feedback, {review.data['reviewer_name']}! É muito bom saber que conseguimos cuidar bem de você. Esperamos te ver em breve! 😊"},
        {"tone": "conciso", "text": f"Obrigado, {review.data['reviewer_name']}! Sua opinião é muito importante para nós."},
    ]

    # Save options to the review
    db.table("google_reviews").update({
        "ai_response_options": response_options,
        "response_status": "drafted",
    }).eq("id", data.review_id).execute()

    return {"review_id": data.review_id, "response_options": response_options}


@router.post("/approve")
async def approve_review_response(
    data: ApproveResponseRequest,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Approve a response to be posted to Google (copy to clipboard flow)."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    final_text = data.edited_text or data.selected_response

    result = (
        db.table("google_reviews")
        .update({
            "selected_response": final_text,
            "response_status": "approved",
        })
        .eq("id", data.review_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")

    return {"message": "Resposta aprovada. Copie e cole no Google.", "response_text": final_text}


@router.get("/config")
async def get_response_config(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get AI review response configuration for the clinic."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("review_response_config")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    return result.data[0] if result.data else {}


@router.put("/config")
async def update_response_config(
    config: dict,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Update AI review response configuration."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    config["clinic_id"] = tenant.clinic_id

    # Upsert
    result = db.table("review_response_config").upsert(config).execute()

    return result.data[0] if result.data else {}
