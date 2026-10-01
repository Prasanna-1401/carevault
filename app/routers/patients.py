from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database import db_session
from app.security import get_current_patient_profile, get_current_user

router = APIRouter(prefix="/api/patients", tags=["Patients"])

class UpdateProfileRequest(BaseModel):
    preferred_language: Optional[str] = None
    allergies: Optional[str] = None
    existing_conditions: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

@router.get("/me")
def get_patient_profile(profile: dict = Depends(get_current_patient_profile)):
    return profile

@router.get("/overview")
def get_dashboard_overview(profile: dict = Depends(get_current_patient_profile)):
    patient_id = profile["patient_id"]

    with db_session() as conn:
        cursor = conn.cursor()

        # Total records
        cursor.execute("SELECT COUNT(*) FROM medical_records WHERE patient_id = ?", (patient_id,))
        total_records = cursor.fetchone()[0]

        # Recent records in last 30 days
        cursor.execute("SELECT COUNT(*) FROM medical_records WHERE patient_id = ? AND record_date >= date('now', '-30 days')", (patient_id,))
        recent_records = cursor.fetchone()[0]

        # Active consents
        cursor.execute("SELECT COUNT(*) FROM consents WHERE patient_id = ? AND status = 'GRANTED' AND expires_at > datetime('now')", (patient_id,))
        active_consents = cursor.fetchone()[0]

        # Expired / revoked consents
        cursor.execute("SELECT COUNT(*) FROM consents WHERE patient_id = ? AND (status IN ('EXPIRED', 'REVOKED') OR expires_at <= datetime('now'))", (patient_id,))
        expired_consents = cursor.fetchone()[0]

        # Prescriptions count
        cursor.execute("SELECT COUNT(*) FROM prescriptions WHERE patient_id = ? AND status = 'ACTIVE'", (patient_id,))
        active_prescriptions = cursor.fetchone()[0]

        # Unread notifications
        cursor.execute("SELECT COUNT(*) FROM notifications WHERE patient_id = ? AND is_read = 0", (patient_id,))
        unread_notifications = cursor.fetchone()[0]

        # Recent 3 records
        cursor.execute("""
        SELECT record_id, record_type, title, hospital_name, doctor_name, record_date
        FROM medical_records WHERE patient_id = ?
        ORDER BY record_date DESC LIMIT 4
        """, (patient_id,))
        recent_list = [dict(r) for r in cursor.fetchall()]

    return {
        "patient_name": profile["full_name"],
        "patient_id": patient_id,
        "blood_group": profile["blood_group"],
        "allergies": profile["allergies"],
        "existing_conditions": profile["existing_conditions"],
        "current_medications": profile["current_medications"],
        "statistics": {
            "total_records": total_records,
            "recent_records": recent_records,
            "active_consents": active_consents,
            "expired_consents": expired_consents,
            "active_prescriptions": active_prescriptions,
            "unread_notifications": unread_notifications
        },
        "recent_reports": recent_list
    }

@router.get("/emergency-card")
def get_emergency_card(profile: dict = Depends(get_current_patient_profile)):
    return {
        "title": "CareVault Emergency Medical ID",
        "patient_id": profile["patient_id"],
        "full_name": profile["full_name"],
        "blood_group": profile["blood_group"],
        "dob": profile["dob"],
        "allergies": profile["allergies"],
        "existing_conditions": profile["existing_conditions"],
        "current_medications": profile["current_medications"],
        "emergency_contact": {
            "name": profile.get("emergency_contact_name", "Not provided"),
            "phone": profile.get("emergency_contact_phone", "Not provided"),
            "relation": profile.get("emergency_contact_relation", "Not provided")
        },
        "safety_notice": "In case of emergency, present this digital card to first responders or emergency triage."
    }

@router.get("/notifications")
def get_patient_notifications(profile: dict = Depends(get_current_patient_profile)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM notifications
        WHERE patient_id = ?
        ORDER BY created_at DESC LIMIT 20
        """, (profile["patient_id"],))
        rows = [dict(r) for r in cursor.fetchall()]
    return rows

@router.post("/notifications/{notif_id}/read")
def mark_notification_read(notif_id: int, profile: dict = Depends(get_current_patient_profile)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND patient_id = ?", (notif_id, profile["patient_id"]))
    return {"message": "Notification marked as read."}

@router.put("/update-profile")
def update_profile(req: UpdateProfileRequest, profile: dict = Depends(get_current_patient_profile)):
    with db_session() as conn:
        cursor = conn.cursor()
        fields = []
        params = []
        if req.preferred_language is not None:
            fields.append("preferred_language = ?")
            params.append(req.preferred_language)
        if req.allergies is not None:
            fields.append("allergies = ?")
            params.append(req.allergies)
        if req.existing_conditions is not None:
            fields.append("existing_conditions = ?")
            params.append(req.existing_conditions)
        if req.emergency_contact_name is not None:
            fields.append("emergency_contact_name = ?")
            params.append(req.emergency_contact_name)
        if req.emergency_contact_phone is not None:
            fields.append("emergency_contact_phone = ?")
            params.append(req.emergency_contact_phone)
        if req.emergency_contact_relation is not None:
            fields.append("emergency_contact_relation = ?")
            params.append(req.emergency_contact_relation)

        if fields:
            params.append(profile["patient_id"])
            query = f"UPDATE patients SET {', '.join(fields)} WHERE patient_id = ?"
            cursor.execute(query, tuple(params))

    return {"message": "Profile updated successfully."}
