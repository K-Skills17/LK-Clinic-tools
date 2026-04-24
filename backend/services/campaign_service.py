"""
LK Clinic Tools - Campaign Service
Business logic for reactivation campaigns: phone normalization, blocklist, stats, AI usage.
"""

import re
from datetime import date, datetime
from typing import Optional

from services.supabase_client import get_supabase_admin
from services.tenant_service import TenantService


class CampaignService(TenantService):
    """Tenant-isolated campaign operations."""

    # ── Phone Normalization (Brazilian E.164) ──────────────────

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        Normalize a Brazilian phone number to E.164 format (+5511987654321).
        Accepts: 11987654321, (11)98765-4321, 5511987654321, +5511987654321
        """
        if not phone:
            raise ValueError("Numero de telefone e obrigatorio.")

        cleaned = re.sub(r"\D", "", phone)

        if cleaned.startswith("55"):
            cleaned = cleaned[2:]

        if len(cleaned) < 10 or len(cleaned) > 11:
            raise ValueError(
                f"Numero invalido: {len(cleaned)} digitos. Esperado 10 ou 11."
            )

        area_code = int(cleaned[:2])
        if area_code < 11 or area_code > 99:
            raise ValueError(f"DDD invalido: {cleaned[:2]}.")

        if len(cleaned) == 10:
            cleaned = cleaned[:2] + "9" + cleaned[2:]

        if len(cleaned) != 11 or cleaned[2] != "9":
            raise ValueError(f"Numero de celular invalido: {cleaned}.")

        return f"+55{cleaned}"

    @staticmethod
    def format_phone_display(phone: str) -> str:
        """Convert +5511987654321 to (11) 98765-4321."""
        if not phone.startswith("+55") or len(phone) != 14:
            return phone
        digits = phone[3:]
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"

    # ── Blocklist (LGPD) ──────────────────────────────────────

    def is_phone_blocked(self, phone: str) -> bool:
        """Check if phone is on the do-not-contact list for this clinic."""
        result = (
            self.db.table("do_not_contact")
            .select("id")
            .eq("clinic_id", self.clinic_id)
            .eq("phone", phone)
            .execute()
        )
        return bool(result.data)

    def block_phone(self, phone: str, reason: str | None = None) -> dict:
        """Add phone to blocklist."""
        normalized = self.normalize_phone(phone)
        return self._insert("do_not_contact", {
            "phone": normalized,
            "reason": reason or "Solicitacao do paciente",
        })

    def unblock_phone(self, phone_id: str) -> bool:
        """Remove phone from blocklist."""
        return self._delete("do_not_contact", phone_id)

    # ── Campaign CRUD ─────────────────────────────────────────

    def list_campaigns(
        self, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        """List campaigns with optional status filter."""
        filters = {"status": status} if status else None
        return self._list("campaigns", filters=filters, limit=limit, offset=offset)

    def get_campaign(self, campaign_id: str) -> dict | None:
        """Get campaign by ID."""
        return self._get_by_id("campaigns", campaign_id)

    def create_campaign(self, name: str) -> dict:
        """Create a new campaign."""
        return self._insert("campaigns", {"name": name, "status": "draft"})

    def update_campaign(self, campaign_id: str, data: dict) -> dict:
        """Update campaign fields."""
        return self._update("campaigns", campaign_id, data)

    def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign and its contacts."""
        self.db.table("campaign_contacts").delete().eq(
            "campaign_id", campaign_id
        ).execute()
        return self._delete("campaigns", campaign_id)

    # ── Campaign Stats ────────────────────────────────────────

    def get_campaign_stats(self, campaign_id: str) -> dict:
        """Get send statistics for a campaign."""
        result = (
            self.db.table("campaign_contacts")
            .select("status")
            .eq("campaign_id", campaign_id)
            .execute()
        )
        contacts = result.data or []
        total = len(contacts)
        pending = sum(1 for c in contacts if c["status"] == "pending")
        sent = sum(1 for c in contacts if c["status"] == "sent")
        failed = sum(1 for c in contacts if c["status"] == "failed")
        completed = sent + failed
        success_rate = round(sent / completed * 100, 1) if completed > 0 else 0

        return {
            "total": total,
            "pending": pending,
            "sent": sent,
            "failed": failed,
            "success_rate": success_rate,
        }

    # ── Contacts ──────────────────────────────────────────────

    def import_contacts(
        self, campaign_id: str, contacts: list[dict]
    ) -> dict:
        """
        Import contacts into a campaign with validation.
        Each contact: {name: str, phone: str}
        Returns: {imported: int, skipped: int, errors: list}
        """
        imported = 0
        skipped = 0
        errors = []

        for i, contact in enumerate(contacts):
            name = (contact.get("name") or "").strip()
            raw_phone = (contact.get("phone") or "").strip()

            if not raw_phone:
                errors.append({"row": i + 1, "error": "Telefone vazio."})
                continue

            try:
                phone = self.normalize_phone(raw_phone)
            except ValueError as e:
                errors.append({"row": i + 1, "phone": raw_phone, "error": str(e)})
                continue

            if self.is_phone_blocked(phone):
                skipped += 1
                continue

            existing = (
                self.db.table("campaign_contacts")
                .select("id")
                .eq("campaign_id", campaign_id)
                .eq("phone", phone)
                .execute()
            )
            if existing.data:
                skipped += 1
                continue

            self.db.table("campaign_contacts").insert({
                "campaign_id": campaign_id,
                "name": name or "Sem nome",
                "phone": phone,
                "status": "pending",
            }).execute()
            imported += 1

        return {"imported": imported, "skipped": skipped, "errors": errors}

    def list_contacts(
        self,
        campaign_id: str,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """List contacts in a campaign."""
        query = (
            self.db.table("campaign_contacts")
            .select("*")
            .eq("campaign_id", campaign_id)
            .order("created_at", desc=False)
        )
        if status:
            query = query.eq("status", status)
        query = query.range(offset, offset + limit - 1)
        result = query.execute()
        return result.data or []

    # ── Message Queue (for external sender) ───────────────────

    def get_pending_messages(self, campaign_id: str, limit: int = 50) -> list[dict]:
        """Get next batch of pending contacts to send."""
        result = (
            self.db.table("campaign_contacts")
            .select("id, name, phone, personalized_message")
            .eq("campaign_id", campaign_id)
            .eq("status", "pending")
            .order("created_at")
            .limit(limit)
            .execute()
        )
        return result.data or []

    def mark_sent(self, contact_id: str) -> dict:
        """Mark a contact as successfully sent."""
        result = (
            self.db.table("campaign_contacts")
            .update({"status": "sent", "sent_at": datetime.utcnow().isoformat()})
            .eq("id", contact_id)
            .execute()
        )
        return result.data[0] if result.data else {}

    def mark_failed(self, contact_id: str, error: str) -> dict:
        """Mark a contact as failed."""
        result = (
            self.db.table("campaign_contacts")
            .update({"status": "failed", "error_message": error})
            .eq("id", contact_id)
            .execute()
        )
        return result.data[0] if result.data else {}

    # ── Message Drafts ────────────────────────────────────────

    def list_drafts(self) -> list[dict]:
        """List saved message templates."""
        return self._list("message_drafts", order_by="created_at")

    def create_draft(self, name: str, template_text: str) -> dict:
        """Save a message template."""
        return self._insert("message_drafts", {
            "name": name,
            "template_text": template_text,
        })

    def update_draft(self, draft_id: str, data: dict) -> dict:
        """Update a message template."""
        return self._update("message_drafts", draft_id, data)

    def delete_draft(self, draft_id: str) -> bool:
        """Delete a message template."""
        return self._delete("message_drafts", draft_id)

    # ── AI Usage Tracking ─────────────────────────────────────

    def get_ai_usage_today(self) -> dict:
        """Get AI generation usage for today."""
        today = date.today().isoformat()
        result = (
            self.db.table("ai_usage_daily")
            .select("count, daily_limit")
            .eq("clinic_id", self.clinic_id)
            .eq("usage_date", today)
            .execute()
        )
        if result.data:
            row = result.data[0]
            return {
                "count": row["count"],
                "limit": row["daily_limit"],
                "remaining": max(0, row["daily_limit"] - row["count"]),
            }

        clinic = self.db.table("clinics").select("plan").eq(
            "id", self.clinic_id
        ).single().execute()
        plan = clinic.data.get("plan", "standard") if clinic.data else "standard"
        daily_limit = {"basic": 5, "standard": 10, "premium": 50}.get(plan, 10)

        self.db.table("ai_usage_daily").insert({
            "clinic_id": self.clinic_id,
            "usage_date": today,
            "count": 0,
            "daily_limit": daily_limit,
        }).execute()

        return {"count": 0, "limit": daily_limit, "remaining": daily_limit}

    def increment_ai_usage(self) -> bool:
        """Increment today's AI usage counter."""
        today = date.today().isoformat()
        current = (
            self.db.table("ai_usage_daily")
            .select("count")
            .eq("clinic_id", self.clinic_id)
            .eq("usage_date", today)
            .execute()
        )
        if current.data:
            self.db.table("ai_usage_daily").update(
                {"count": current.data[0]["count"] + 1}
            ).eq("clinic_id", self.clinic_id).eq("usage_date", today).execute()
            return True
        return False
