"""
LK Clinic Tools - Appointments Router
CRUD for appointment management + CSV import + today's schedule.
"""

import csv
import io
from datetime import date, time
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from dependencies import TenantContext, get_tenant_context

router = APIRouter()


# ============================================================
# Schemas
# ============================================================

class AppointmentCreate(BaseModel):
    patient_name: str
    patient_phone: str
    appointment_date: date
    appointment_time: time
    duration_minutes: int = 60
    procedure_name: Optional[str] = None
    doctor_name: Optional[str] = None
    status: str = "pendente"
    notes: Optional[str] = None
    source: str = "manual"
    external_id: Optional[str] = None


class AppointmentUpdate(BaseModel):
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    appointment_date: Optional[date] = None
    appointment_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    procedure_name: Optional[str] = None
    doctor_name: Optional[str] = None
    status: Optional[str] = None
    confirmation_status: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# Endpoints
# ============================================================

@router.get("/")
async def list_appointments(
    date_filter: Optional[date] = None,
    status_filter: Optional[str] = None,
    doctor: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List appointments for the clinic with optional filters."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    query = (
        db.table("appointments")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .order("appointment_date", desc=True)
        .order("appointment_time", desc=False)
    )

    if date_filter:
        query = query.eq("appointment_date", date_filter.isoformat())
    if status_filter:
        query = query.eq("status", status_filter)
    if doctor:
        query = query.eq("doctor_name", doctor)

    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    return {"appointments": result.data or [], "count": len(result.data or [])}


@router.get("/today")
async def get_today_schedule(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get today's appointment schedule (timeline view)."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    today = date.today().isoformat()

    result = (
        db.table("appointments")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .eq("appointment_date", today)
        .neq("status", "cancelado")
        .order("appointment_time")
        .execute()
    )

    appointments = result.data or []

    # Summary stats
    total = len(appointments)
    confirmed = sum(1 for a in appointments if a["confirmation_status"] == "confirmado")
    pending = sum(1 for a in appointments if a["confirmation_status"] in ("nao_enviado", "enviado", "sem_resposta"))

    return {
        "date": today,
        "appointments": appointments,
        "summary": {
            "total": total,
            "confirmed": confirmed,
            "pending": pending,
            "confirmation_rate": round(confirmed / total * 100, 1) if total > 0 else 0,
        },
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_appointment(
    data: AppointmentCreate,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Create a new appointment."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    appointment_data = data.model_dump(mode="json")
    appointment_data["clinic_id"] = tenant.clinic_id

    result = db.table("appointments").insert(appointment_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar consulta.")

    # TODO: Schedule reminders for this appointment (Phase 2)

    return result.data[0]


@router.patch("/{appointment_id}")
async def update_appointment(
    appointment_id: str,
    data: AppointmentUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Update an appointment."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    update_data = data.model_dump(exclude_none=True, mode="json")

    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar.")

    result = (
        db.table("appointments")
        .update(update_data)
        .eq("id", appointment_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    return result.data[0]


@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Cancel an appointment (soft delete via status change)."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("appointments")
        .update({"status": "cancelado"})
        .eq("id", appointment_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    # TODO: Notify waitlist patients (Phase 2)

    return {"message": "Consulta cancelada com sucesso."}


@router.post("/import")
async def import_appointments_csv(
    file: UploadFile = File(...),
    tenant: TenantContext = Depends(get_tenant_context),
):
    """
    Import appointments from CSV file.
    Expected columns: patient_name, patient_phone, appointment_date (YYYY-MM-DD),
    appointment_time (HH:MM), procedure_name, doctor_name, duration_minutes, notes
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV.")

    content = await file.read()
    text = content.decode("utf-8-sig")  # Handle BOM from Excel
    reader = csv.DictReader(io.StringIO(text), delimiter=";")

    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    imported = 0
    errors = []

    for i, row in enumerate(reader, start=2):  # Row 2 (after header)
        try:
            appointment_data = {
                "clinic_id": tenant.clinic_id,
                "patient_name": row.get("patient_name", "").strip(),
                "patient_phone": row.get("patient_phone", "").strip(),
                "appointment_date": row.get("appointment_date", "").strip(),
                "appointment_time": row.get("appointment_time", "").strip(),
                "procedure_name": row.get("procedure_name", "").strip() or None,
                "doctor_name": row.get("doctor_name", "").strip() or None,
                "duration_minutes": int(row.get("duration_minutes", "60").strip() or "60"),
                "notes": row.get("notes", "").strip() or None,
                "source": "csv_import",
            }

            if not appointment_data["patient_name"] or not appointment_data["patient_phone"]:
                errors.append({"row": i, "error": "Nome e telefone são obrigatórios."})
                continue

            db.table("appointments").insert(appointment_data).execute()
            imported += 1

        except Exception as e:
            errors.append({"row": i, "error": str(e)})

    return {
        "imported": imported,
        "errors": errors,
        "message": f"{imported} consultas importadas com sucesso.",
    }
