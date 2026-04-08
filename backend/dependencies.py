"""
LK Clinic Tools - Auth & Tenant Isolation Dependencies
Provides FastAPI dependencies for authentication and multi-tenant data isolation.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel
import httpx

from config import Settings, get_settings


# ============================================================
# Models
# ============================================================

class TokenPayload(BaseModel):
    """Decoded JWT token payload."""
    sub: str  # auth_user_id
    email: Optional[str] = None
    role: Optional[str] = None


class CurrentUser(BaseModel):
    """Authenticated user context injected into route handlers."""
    auth_user_id: str
    user_id: Optional[str] = None  # clinic_users.id
    clinic_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    role: str  # agency_admin, agency_operator, clinic_admin, clinic_staff


class TenantContext(BaseModel):
    """
    Tenant isolation context.
    Every database query must use this to filter by clinic_id.
    """
    clinic_id: str
    user: CurrentUser

    @property
    def is_agency(self) -> bool:
        return self.user.role in ("agency_admin", "agency_operator")

    @property
    def is_clinic_admin(self) -> bool:
        return self.user.role == "clinic_admin"

    @property
    def is_staff(self) -> bool:
        return self.user.role == "clinic_staff"


# ============================================================
# Auth Dependencies
# ============================================================

async def get_token_payload(
    authorization: str = Header(..., description="Bearer <token>"),
    settings: Settings = Depends(get_settings),
) -> TokenPayload:
    """Extract and validate JWT token from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido. Use: Bearer <token>",
        )

    token = authorization.removeprefix("Bearer ")

    # Try HS256 first (older Supabase projects), then verify via Supabase API for ES256
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return TokenPayload(
            sub=payload.get("sub", ""),
            email=payload.get("email"),
            role=payload.get("role"),
        )
    except JWTError:
        pass

    # ES256 fallback: verify token via Supabase auth API
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{settings.supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": settings.supabase_anon_key,
                },
            )
            if res.status_code == 200:
                user_data = res.json()
                return TokenPayload(
                    sub=user_data.get("id", ""),
                    email=user_data.get("email"),
                    role=user_data.get("role"),
                )
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
    )


async def get_current_user(
    token: TokenPayload = Depends(get_token_payload),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    """
    Resolve the authenticated user from JWT + clinic_users table.
    Returns CurrentUser with role and clinic context.
    """
    from services.supabase_client import get_supabase_admin

    supabase = get_supabase_admin()

    # Look up user in clinic_users table
    result = (
        supabase.table("clinic_users")
        .select("id, clinic_id, name, email, role, is_active")
        .eq("auth_user_id", token.sub)
        .eq("is_active", True)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não encontrado ou desativado.",
        )

    user_data = result.data[0]

    return CurrentUser(
        auth_user_id=token.sub,
        user_id=user_data["id"],
        clinic_id=user_data.get("clinic_id"),
        email=user_data["email"],
        name=user_data["name"],
        role=user_data["role"],
    )


async def get_tenant_context(
    clinic_id: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user),
) -> TenantContext:
    """
    Resolve tenant context for data isolation.

    - Agency users can specify clinic_id to access any clinic.
    - Clinic users are locked to their own clinic_id.
    """
    # Agency users can access any clinic
    if user.role in ("agency_admin", "agency_operator"):
        resolved_clinic_id = clinic_id or user.clinic_id
        if not resolved_clinic_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="clinic_id é obrigatório para usuários da agência.",
            )
        return TenantContext(clinic_id=resolved_clinic_id, user=user)

    # Clinic users can only access their own clinic
    if not user.clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não está associado a nenhuma clínica.",
        )

    # Prevent clinic users from accessing other clinics
    if clinic_id and clinic_id != user.clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a esta clínica.",
        )

    return TenantContext(clinic_id=user.clinic_id, user=user)


# ============================================================
# Role-Based Access Dependencies
# ============================================================

def require_role(*allowed_roles: str):
    """
    Dependency factory: restrict endpoint to specific roles.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role("agency_admin"))])
    """
    async def check_role(user: CurrentUser = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso restrito. Roles permitidos: {', '.join(allowed_roles)}",
            )
        return user
    return check_role


def require_agency():
    """Restrict to agency roles only."""
    return require_role("agency_admin", "agency_operator")


def require_clinic_admin_or_above():
    """Restrict to clinic_admin, agency_operator, or agency_admin."""
    return require_role("agency_admin", "agency_operator", "clinic_admin")
