"""
LK Clinic Tools - Auth Router
Handles authentication endpoints (login, user info, etc.).
Supabase Auth handles actual auth; this provides user context.
"""

from fastapi import APIRouter, Depends

from dependencies import CurrentUser, get_current_user

router = APIRouter()


@router.get("/me")
async def get_me(user: CurrentUser = Depends(get_current_user)):
    """Get current authenticated user info."""
    return {
        "auth_user_id": user.auth_user_id,
        "user_id": user.user_id,
        "clinic_id": user.clinic_id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
    }
