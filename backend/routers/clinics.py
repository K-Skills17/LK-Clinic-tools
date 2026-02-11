"""
LK Clinic Tools - Clinics Router
CRUD operations for clinic management and onboarding.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from dependencies import CurrentUser, get_current_user, require_role
from services.supabase_client import get_supabase_admin

router = APIRouter()


# ============================================================
# Schemas
# ============================================================

class ClinicCreate(BaseModel):
    business_name: str
    contact_name: str
    phone: str
    email: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    google_place_id: Optional[str] = None
    google_review_link: Optional[str] = None
    whatsapp_number: Optional[str] = None
    plan: str = "standard"
    subscription_price: Optional[float] = None


class ClinicUpdate(BaseModel):
    business_name: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    google_place_id: Optional[str] = None
    google_review_link: Optional[str] = None
    google_maps_url: Optional[str] = None
    whatsapp_number: Optional[str] = None
    evolution_api_config: Optional[dict] = None
    logo_url: Optional[str] = None
    brand_colors: Optional[dict] = None
    reminder_schedule: Optional[dict] = None
    reminder_sending_hours: Optional[dict] = None
    review_request_delay_minutes: Optional[int] = None
    satisfaction_threshold: Optional[int] = None
    target_keywords: Optional[list[str]] = None
    competitor_place_ids: Optional[list[str]] = None
    plan: Optional[str] = None
    subscription_status: Optional[str] = None


# ============================================================
# Endpoints
# ============================================================

@router.get("/")
async def list_clinics(
    user: CurrentUser = Depends(require_role("agency_admin", "agency_operator")),
):
    """List all clinics (agency only)."""
    db = get_supabase_admin()
    result = db.table("clinics").select("*").eq("is_active", True).order("created_at", desc=True).execute()
    return {"clinics": result.data or []}


@router.get("/{clinic_id}")
async def get_clinic(
    clinic_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Get clinic details. Clinic users can only access their own clinic."""
    if user.role not in ("agency_admin", "agency_operator") and user.clinic_id != clinic_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    db = get_supabase_admin()
    result = db.table("clinics").select("*").eq("id", clinic_id).single().execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clínica não encontrada.")

    return result.data


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_clinic(
    data: ClinicCreate,
    user: CurrentUser = Depends(require_role("agency_admin")),
):
    """Create a new clinic (agency_admin only). Triggers onboarding setup."""
    db = get_supabase_admin()

    # Insert clinic
    clinic_data = data.model_dump(exclude_none=True)
    result = db.table("clinics").insert(clinic_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar clínica.")

    clinic = result.data[0]
    clinic_id = clinic["id"]

    # Create default message templates
    db.rpc("create_default_templates", {"p_clinic_id": clinic_id}).execute()

    # Create default dental procedures
    db.rpc("create_default_dental_procedures", {"p_clinic_id": clinic_id}).execute()

    # Create default knowledge base
    db.table("knowledge_bases").insert({
        "clinic_id": clinic_id,
        "faqs": [],
        "services": [],
        "business_info": {},
        "doctor_profiles": [],
    }).execute()

    return {"clinic": clinic, "message": "Clínica criada com sucesso. Templates padrão configurados."}


@router.patch("/{clinic_id}")
async def update_clinic(
    clinic_id: str,
    data: ClinicUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """Update clinic settings."""
    # Clinic admins can update their own clinic; agency can update any
    if user.role == "clinic_staff":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito.")
    if user.role == "clinic_admin" and user.clinic_id != clinic_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    db = get_supabase_admin()
    update_data = data.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar.")

    result = db.table("clinics").update(update_data).eq("id", clinic_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Clínica não encontrada.")

    return result.data[0]


@router.delete("/{clinic_id}")
async def deactivate_clinic(
    clinic_id: str,
    user: CurrentUser = Depends(require_role("agency_admin")),
):
    """Soft-delete a clinic (agency_admin only)."""
    db = get_supabase_admin()
    result = (
        db.table("clinics")
        .update({"is_active": False, "subscription_status": "cancelled"})
        .eq("id", clinic_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Clínica não encontrada.")

    return {"message": "Clínica desativada com sucesso."}
