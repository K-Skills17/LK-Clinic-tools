"""
LK Clinic Tools - Supabase Client
Provides authenticated and admin Supabase client instances.
"""

from functools import lru_cache

from supabase import Client, create_client

from config import get_settings


@lru_cache()
def get_supabase_admin() -> Client:
    """
    Supabase client with service_role key.
    Bypasses RLS — use only in backend services/workers.
    """
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_supabase_client(access_token: str | None = None) -> Client:
    """
    Supabase client with user's access token (respects RLS).
    Falls back to anon key if no token provided.
    """
    settings = get_settings()
    key = settings.supabase_anon_key
    client = create_client(settings.supabase_url, key)

    if access_token:
        client.auth.set_session(access_token, "")

    return client
