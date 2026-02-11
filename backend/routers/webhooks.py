"""
LK Clinic Tools - Webhooks Router
Handles incoming webhooks from Evolution API (WhatsApp), Google Calendar, and external systems.
"""

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.post("/whatsapp/{clinic_id}")
async def whatsapp_webhook(
    clinic_id: str,
    request: Request,
):
    """
    Receive WhatsApp messages from Evolution API.
    Routes to the correct bot/conversation based on clinic_id.
    """
    payload = await request.json()

    # TODO: Phase 2 - Parse webhook, route to bot flow engine
    # 1. Parse incoming message using WhatsApp adapter
    # 2. Find or create conversation for this contact
    # 3. Execute bot flow engine for current node
    # 4. Send response back via WhatsApp adapter

    return {"status": "received", "clinic_id": clinic_id}


@router.post("/appointments")
async def external_appointment_webhook(
    request: Request,
):
    """
    Receive appointment data from external systems (automation tools).
    Expects: clinic_id, patient_name, patient_phone, date, time, procedure, doctor
    """
    payload = await request.json()

    clinic_id = payload.get("clinic_id")
    if not clinic_id:
        raise HTTPException(status_code=400, detail="clinic_id é obrigatório.")

    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()

    # Verify clinic exists
    clinic = db.table("clinics").select("id").eq("id", clinic_id).single().execute()
    if not clinic.data:
        raise HTTPException(status_code=404, detail="Clínica não encontrada.")

    appointment_data = {
        "clinic_id": clinic_id,
        "patient_name": payload.get("patient_name", ""),
        "patient_phone": payload.get("patient_phone", ""),
        "appointment_date": payload.get("date", ""),
        "appointment_time": payload.get("time", ""),
        "procedure_name": payload.get("procedure"),
        "doctor_name": payload.get("doctor"),
        "duration_minutes": payload.get("duration_minutes", 60),
        "source": "webhook",
        "external_id": payload.get("external_id"),
    }

    result = db.table("appointments").insert(appointment_data).execute()

    return {
        "status": "created",
        "appointment_id": result.data[0]["id"] if result.data else None,
    }


@router.post("/calendar/{clinic_id}")
async def google_calendar_webhook(
    clinic_id: str,
    request: Request,
):
    """
    Handle Google Calendar push notifications.
    (Alternative to polling - if configured.)
    """
    payload = await request.json()

    # TODO: Phase 2 - Process calendar event changes
    # 1. Fetch changed events from Google Calendar API
    # 2. Sync to appointments table
    # 3. Schedule/update reminders

    return {"status": "received", "clinic_id": clinic_id}
