"""
LK Clinic Tools - Tenant Service
Provides tenant-isolated database operations.
All queries are filtered by clinic_id to ensure data isolation.
"""

from typing import Any, Optional
from uuid import UUID

from services.supabase_client import get_supabase_admin


class TenantService:
    """
    Base service class with tenant isolation.
    All module services should inherit from this.
    """

    def __init__(self, clinic_id: str):
        self.clinic_id = clinic_id
        self.db = get_supabase_admin()

    def _query(self, table: str):
        """Start a tenant-scoped query (always filtered by clinic_id)."""
        return self.db.table(table).select("*").eq("clinic_id", self.clinic_id)

    def _insert(self, table: str, data: dict) -> dict:
        """Insert a record with clinic_id automatically injected."""
        data["clinic_id"] = self.clinic_id
        result = self.db.table(table).insert(data).execute()
        return result.data[0] if result.data else {}

    def _update(self, table: str, record_id: str, data: dict) -> dict:
        """Update a record, ensuring it belongs to this clinic."""
        result = (
            self.db.table(table)
            .update(data)
            .eq("id", record_id)
            .eq("clinic_id", self.clinic_id)
            .execute()
        )
        return result.data[0] if result.data else {}

    def _delete(self, table: str, record_id: str) -> bool:
        """Delete a record, ensuring it belongs to this clinic."""
        result = (
            self.db.table(table)
            .delete()
            .eq("id", record_id)
            .eq("clinic_id", self.clinic_id)
            .execute()
        )
        return len(result.data) > 0 if result.data else False

    def _get_by_id(self, table: str, record_id: str) -> Optional[dict]:
        """Get a single record by ID, scoped to this clinic."""
        result = (
            self.db.table(table)
            .select("*")
            .eq("id", record_id)
            .eq("clinic_id", self.clinic_id)
            .single()
            .execute()
        )
        return result.data

    def _list(
        self,
        table: str,
        filters: Optional[dict] = None,
        order_by: str = "created_at",
        ascending: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """List records with optional filters, scoped to this clinic."""
        query = self._query(table)

        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        query = query.order(order_by, desc=not ascending)
        query = query.range(offset, offset + limit - 1)

        result = query.execute()
        return result.data or []

    def _count(self, table: str, filters: Optional[dict] = None) -> int:
        """Count records in a table, scoped to this clinic."""
        query = (
            self.db.table(table)
            .select("id", count="exact")
            .eq("clinic_id", self.clinic_id)
        )

        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        result = query.execute()
        return result.count or 0
