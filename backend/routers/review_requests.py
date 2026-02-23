"""
LK Clinic Tools - Review Requests Router
Manage automated review request flow (satisfaction check → Google redirect).
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


class ReviewRequestCreate(BaseModel):
    appointment_id: Optional[str] = None
    patient_name: str
    patient_phone: str


@router.get("/")
async def list_review_requests(
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List review requests for the clinic."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    query = (
        db.table("review_requests")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .order("created_at", desc=True)
    )

    if status_filter:
        query = query.eq("status", status_filter)

    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    return {"review_requests": result.data or []}


@router.get("/stats")
async def get_review_request_stats(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get review request statistics (funnel metrics)."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    all_requests = (
        db.table("review_requests")
        .select("status, satisfaction_score")
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    data = all_requests.data or []
    total = len(data)
    sent = sum(1 for r in data if r["status"] != "scheduled")
    responded = sum(1 for r in data if r["satisfaction_score"] is not None)
    positive = sum(1 for r in data if (r["satisfaction_score"] or 0) >= 4)
    negative_caught = sum(1 for r in data if r["status"] in ("negative_caught", "neutral_caught"))
    review_posted = sum(1 for r in data if r["status"] == "review_posted")

    return {
        "total_requests": total,
        "sent": sent,
        "responded": responded,
        "response_rate": round(responded / sent * 100, 1) if sent > 0 else 0,
        "positive": positive,
        "positive_rate": round(positive / responded * 100, 1) if responded > 0 else 0,
        "negative_caught": negative_caught,
        "reviews_generated": review_posted,
        "conversion_rate": round(review_posted / positive * 100, 1) if positive > 0 else 0,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_review_request(
    data: ReviewRequestCreate,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Manually create a review request (outside the automated flow)."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()

    # Check dedup: don't send to same patient within 90 days
    dedup = (
        db.table("contact_dedup")
        .select("last_review_request_at")
        .eq("clinic_id", tenant.clinic_id)
        .eq("patient_phone", data.patient_phone)
        .execute()
    )

    if dedup.data and dedup.data[0].get("last_review_request_at"):
        from datetime import datetime, timedelta
        last_request = datetime.fromisoformat(dedup.data[0]["last_review_request_at"].replace("Z", "+00:00"))
        if datetime.now(last_request.tzinfo) - last_request < timedelta(days=90):
            raise HTTPException(
                status_code=400,
                detail="Solicitação de avaliação já enviada para este paciente nos últimos 90 dias.",
            )

    request_data = data.model_dump(exclude_none=True)
    request_data["clinic_id"] = tenant.clinic_id
    request_data["status"] = "scheduled"

    result = db.table("review_requests").insert(request_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar solicitação.")

    return result.data[0]


@router.patch("/{request_id}/satisfaction")
async def record_satisfaction(
    request_id: str,
    score: int,
    feedback: Optional[str] = None,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Record patient satisfaction response (used by webhook handler)."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()

    if score < 1 or score > 5:
        raise HTTPException(status_code=400, detail="Score deve ser entre 1 e 5.")

    from datetime import datetime, timezone

    # Determine next status based on score
    clinic = db.table("clinics").select("satisfaction_threshold").eq("id", tenant.clinic_id).single().execute()
    threshold = clinic.data.get("satisfaction_threshold", 4) if clinic.data else 4

    if score >= threshold:
        new_status = "review_link_sent"
    elif score >= 3:
        new_status = "neutral_caught"
    else:
        new_status = "negative_caught"

    update_data = {
        "satisfaction_score": score,
        "feedback_text": feedback,
        "status": new_status,
        "responded_at": datetime.now(timezone.utc).isoformat(),
    }

    result = (
        db.table("review_requests")
        .update(update_data)
        .eq("id", request_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")

    return {"status": new_status, "review_request": result.data[0]}
