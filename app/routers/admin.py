import json
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import db_session
from app.security import require_roles

router = APIRouter(prefix="/api/admin", tags=["System Administration"])

class AddHospitalModel(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    specialties: list
    services: list
    emergency: bool = True
    opening_hours: str = "24/7"
    cost_range: str = "$$"
    insurance_schemes: list
    contact_phone: str
    contact_email: Optional[str] = None

@router.get("/metrics")
def get_system_metrics(user: dict = Depends(require_roles(["ADMIN"]))):
    """Provides high-level system monitoring statistics for administrators"""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'PATIENT'")
        total_patients = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'DOCTOR'")
        total_doctors = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM hospitals")
        total_hospitals = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM medical_records")
        total_records = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM consents WHERE status = 'GRANTED' AND expires_at > datetime('now')")
        active_consents = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM access_logs")
        total_audit_events = cursor.fetchone()[0]

        # Recent audit events
        cursor.execute("SELECT * FROM access_logs ORDER BY timestamp DESC LIMIT 10")
        recent_logs = [dict(r) for r in cursor.fetchall()]

    return {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_facilities": total_hospitals,
        "total_records": total_records,
        "active_sharing_sessions": active_consents,
        "total_audit_events": total_audit_events,
        "recent_audit_events": recent_logs
    }

@router.get("/facilities")
def list_admin_facilities(user: dict = Depends(require_roles(["ADMIN"]))):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hospitals ORDER BY created_at DESC")
        rows = [dict(r) for r in cursor.fetchall()]

    for r in rows:
        try: r["specialties"] = json.loads(r["specialties"])
        except Exception: pass
        try: r["services"] = json.loads(r["services"])
        except Exception: pass
        try: r["insurance_schemes"] = json.loads(r["insurance_schemes"])
        except Exception: pass

    return rows

@router.post("/facilities/{hospital_id}/toggle-verification")
def toggle_verification(hospital_id: str, user: dict = Depends(require_roles(["ADMIN"]))):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT verification_status FROM hospitals WHERE hospital_id = ?", (hospital_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Facility not found.")

        current = row[0]
        new_status = "PENDING" if current in ("VERIFIED", "VERIFIED_SYNTHETIC") else "VERIFIED_SYNTHETIC"
        cursor.execute("UPDATE hospitals SET verification_status = ? WHERE hospital_id = ?", (new_status, hospital_id))

    return {"hospital_id": hospital_id, "verification_status": new_status}
