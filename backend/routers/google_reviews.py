"""
LK Clinic Tools - Google Reviews Router
Track and manage Google reviews for the clinic.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


@router.get("/")
async def list_google_reviews(
    sentiment: Optional[str] = None,
    response_status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List Google reviews for the clinic."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    query = (
        db.table("google_reviews")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .order("review_date", desc=True)
    )

    if sentiment:
        query = query.eq("sentiment", sentiment)
    if response_status:
        query = query.eq("response_status", response_status)

    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    return {"reviews": result.data or []}


@router.get("/stats")
async def get_review_stats(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get Google review statistics."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    reviews = (
        db.table("google_reviews")
        .select("rating, sentiment, response_status, review_date")
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    data = reviews.data or []
    total = len(data)
    avg_rating = round(sum(r["rating"] for r in data) / total, 1) if total > 0 else 0
    responded = sum(1 for r in data if r["response_status"] in ("approved", "posted"))

    return {
        "total_reviews": total,
        "average_rating": avg_rating,
        "response_rate": round(responded / total * 100, 1) if total > 0 else 0,
        "sentiment_breakdown": {
            "positive": sum(1 for r in data if r["sentiment"] == "positive"),
            "neutral": sum(1 for r in data if r["sentiment"] == "neutral"),
            "negative": sum(1 for r in data if r["sentiment"] == "negative"),
        },
    }


@router.get("/pending-response")
async def get_reviews_pending_response(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get reviews that need a response."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("google_reviews")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .in_("response_status", ["pending", "drafted"])
        .order("review_date", desc=True)
        .execute()
    )

    return {"reviews": result.data or []}
