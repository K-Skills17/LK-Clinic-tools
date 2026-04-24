"""
LK Clinic Tools - AI Generation Router
Module 5: AI-powered message generation for reactivation campaigns.
Uses Claude (Anthropic) - same provider as the rest of the platform.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


# ============================================================
# Schemas
# ============================================================

class GenerateRequest(BaseModel):
    patient_name: str
    procedure: Optional[str] = None
    tone: str = "amigavel"
    context: Optional[str] = None


# ============================================================
# Endpoints
# ============================================================

@router.get("/usage")
async def get_ai_usage(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get today's AI generation usage and limits."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    return svc.get_ai_usage_today()


@router.post("/generate")
async def generate_message(
    data: GenerateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Generate a personalized reactivation message using Claude."""
    from services.campaign_service import CampaignService

    svc = CampaignService(tenant.clinic_id)
    usage = svc.get_ai_usage_today()

    if usage["remaining"] <= 0:
        raise HTTPException(
            status_code=429,
            detail=f"Limite diario de {usage['limit']} geracoes atingido. Tente novamente amanha.",
        )

    from config import get_settings
    import anthropic

    settings = get_settings()
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="Chave da API Anthropic nao configurada.",
        )

    clinic = (
        svc.db.table("clinics")
        .select("business_name, contact_name, phone")
        .eq("id", tenant.clinic_id)
        .single()
        .execute()
    )
    clinic_name = clinic.data.get("business_name", "Clinica") if clinic.data else "Clinica"
    doctor_name = clinic.data.get("contact_name", "") if clinic.data else ""

    tone_map = {
        "amigavel": "amigavel e acolhedor, como uma conversa entre conhecidos",
        "premium": "profissional e sofisticado, transmitindo excelencia e cuidado",
        "direto": "objetivo e direto ao ponto, sem rodeios",
    }
    tone_desc = tone_map.get(data.tone, tone_map["amigavel"])

    procedure_context = ""
    if data.procedure:
        procedure_context = f"\nO ultimo procedimento do paciente foi: {data.procedure}"

    extra_context = ""
    if data.context:
        extra_context = f"\nContexto adicional: {data.context}"

    prompt = (
        "Gere uma mensagem de WhatsApp para reativar um paciente inativo "
        "de uma clinica odontologica.\n\n"
        f"Clinica: {clinic_name}\n"
        f"Dentista: {doctor_name}\n"
        f"Paciente: {data.patient_name}"
        f"{procedure_context}{extra_context}\n\n"
        f"Tom: {tone_desc}\n\n"
        "Regras:\n"
        "- Maximo 300 caracteres (WhatsApp)\n"
        "- Use o primeiro nome do paciente\n"
        "- Mencione que faz tempo desde a ultima visita\n"
        "- Inclua um convite para agendar\n"
        "- NAO use emojis excessivos (maximo 2)\n"
        "- NAO inclua links ou numeros de telefone\n"
        "- Linguagem natural, como se fosse digitada por uma pessoa\n"
        "- Portugues brasileiro coloquial"
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    generated_text = response.content[0].text.strip()

    svc.increment_ai_usage()
    updated_usage = svc.get_ai_usage_today()

    return {
        "message": generated_text,
        "usage": updated_usage,
    }
