import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from app.database import db_session
from app.security import require_roles, get_current_provider_profile
from app.services.consent_service import verify_provider_access
from app.storage import save_document, create_synthetic_document_image, generate_signed_view_token

router = APIRouter(prefix="/api/doctor", tags=["Healthcare Provider Portal"])

class AddConsultationRequest(BaseModel):
    patient_id: str
    title: str
    clinical_notes: str
    prescribed_medicines: Optional[List[dict]] = None
    recommended_tests: Optional[List[str]] = None

@router.get("/my-consents")
def get_doctor_active_sessions(provider: dict = Depends(get_current_provider_profile)):
    """Returns all active, pending, and past consent requests for this doctor"""
    prid = provider["provider_id"]
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT c.*, u.full_name as patient_name, p.dob, p.blood_group, p.allergies, p.existing_conditions
        FROM consents c
        JOIN patients p ON c.patient_id = p.patient_id
        JOIN users u ON p.user_id = u.id
        WHERE c.provider_id = ?
        ORDER BY c.created_at DESC
        """, (prid,))
        rows = [dict(r) for r in cursor.fetchall()]

    now = datetime.now(timezone.utc)
    for r in rows:
        try: r["requested_records"] = json.loads(r["requested_records"])
        except Exception: pass

        exp = datetime.fromisoformat(r["expires_at"].replace("Z", "+00:00"))
        remaining = int((exp - now).total_seconds())
        r["remaining_seconds"] = max(0, remaining)
        r["is_live"] = r["status"] == "GRANTED" and remaining > 0

    return rows

@router.get("/patient-records/{patient_id}")
def view_patient_consented_records(patient_id: str, provider: dict = Depends(get_current_provider_profile)):
    """
    Retrieves records for a patient ONLY if active granted consent exists and is unexpired.
    Filters records strictly according to granted scope.
    """
    prid = provider["provider_id"]
    access = verify_provider_access(provider_id=prid, patient_id=patient_id)

    if not access["authorized"]:
        raise HTTPException(status_code=403, detail=f"Access Denied: {access['reason']}")

    scopes = access["scopes"]

    with db_session() as conn:
        cursor = conn.cursor()

        # Get patient clinical overview
        cursor.execute("""
        SELECT p.*, u.full_name, u.email, u.mobile
        FROM patients p JOIN users u ON p.user_id = u.id
        WHERE p.patient_id = ?
        """, (patient_id,))
        pat_row = cursor.fetchone()
        if not pat_row:
            raise HTTPException(status_code=404, detail="Patient not found.")
        patient_info = dict(pat_row)

        # Query records
        cursor.execute("SELECT * FROM medical_records WHERE patient_id = ? ORDER BY record_date DESC", (patient_id,))
        all_records = [dict(r) for r in cursor.fetchall()]

        # Filter by scope
        permitted_records = []
        for r in all_records:
            rtype = r.get("record_type", "")
            if "All" in scopes or "All Records" in scopes or any(s.lower() in rtype.lower() or rtype.lower() in s.lower() for s in scopes):
                # Generate temporary watermarked view token
                token = generate_signed_view_token(
                    record_id=r["record_id"],
                    viewer_name=provider["name"],
                    viewer_role="DOCTOR",
                    expires_seconds=access["remaining_seconds"]
                )
                r["view_token"] = token
                if r.get("tags"):
                    try: r["tags"] = json.loads(r["tags"])
                    except Exception: r["tags"] = []
                permitted_records.append(r)

    return {
        "authorized": True,
        "consent_id": access["consent_id"],
        "purpose": access["purpose"],
        "expires_at": access["expires_at"],
        "remaining_seconds": access["remaining_seconds"],
        "permitted_scopes": scopes,
        "patient": {
            "name": patient_info["full_name"],
            "patient_id": patient_info["patient_id"],
            "blood_group": patient_info["blood_group"],
            "allergies": patient_info["allergies"],
            "existing_conditions": patient_info["existing_conditions"],
            "current_medications": patient_info["current_medications"]
        },
        "total_permitted_records": len(permitted_records),
        "records": permitted_records
    }

@router.post("/add-consultation")
def add_consultation_record(req: AddConsultationRequest, provider: dict = Depends(get_current_provider_profile)):
    """Doctor uploads a new clinical note or prescription during authorized session"""
    prid = provider["provider_id"]
    access = verify_provider_access(provider_id=prid, patient_id=req.patient_id)
    if not access["authorized"]:
        raise HTTPException(status_code=403, detail="Active consent is required to add medical entries for this patient.")

    record_id = f"CV-REC-{uuid.uuid4().hex[:6].upper()}"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        f"CONSULTATION: {req.title.upper()}",
        f"CLINICIAN: {provider['name']} ({provider.get('specialty')})",
        f"HOSPITAL: {provider.get('hospital_name', 'Consulting Center')}",
        f"DATE: {today}",
        "### CLINICAL NOTES & EXAMINATION:",
        f"- {req.clinical_notes}"
    ]

    if req.prescribed_medicines:
        lines.append("### RX / PRESCRIBED MEDICINES:")
        for m in req.prescribed_medicines:
            lines.append(f"- {m.get('name', 'Medicine')} {m.get('dose', '')} | Timing: {m.get('freq', 'As directed')}")

    if req.recommended_tests:
        lines.append("### RECOMMENDED INVESTIGATIONS:")
        for t in req.recommended_tests:
            lines.append(f"- {t}")

    doc_bytes = create_synthetic_document_image(req.title, provider.get("hospital_name", "Consulting Center"), provider["name"], today, lines)
    file_path, enc_name, file_sz = save_document(doc_bytes, f"{record_id}.jpg", record_id)

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO medical_records (
            record_id, patient_id, record_type, title, hospital_name, doctor_name,
            record_date, file_path, file_name, file_size, mime_type, description,
            raw_text, tags, source, verification_status
        ) VALUES (?, ?, 'Doctor Notes', ?, ?, ?, ?, ?, ?, ?, 'image/jpeg', ?, ?, ?, 'HOSPITAL_EHR', 'VERIFIED')
        """, (
            record_id, req.patient_id, req.title, provider.get("hospital_name", "Consulting Center"),
            provider["name"], today, file_path, enc_name, file_sz, req.clinical_notes,
            "\n".join(lines), json.dumps(["Doctor Note", provider.get("specialty", "Clinical"), "Consultation"])
        ))

        cursor.execute("""
        INSERT INTO record_files (record_id, encrypted_filename, original_filename, file_hash)
        VALUES (?, ?, ?, 'sha256-doctor-entry')
        """, (record_id, enc_name, f"{record_id}.jpg"))

        # Log in audit
        cursor.execute("""
        INSERT INTO access_logs (
            actor_id, actor_name, actor_role, patient_id, record_id, record_title, action, status, details
        ) VALUES (?, ?, 'DOCTOR', ?, ?, ?, 'record_uploaded', 'SUCCESS', ?)
        """, (
            prid, provider["name"], req.patient_id, record_id, req.title,
            f"Doctor {provider['name']} added clinical consultation entry."
        ))

        # Notify patient
        cursor.execute("""
        INSERT INTO notifications (
            patient_id, title, message, type, related_id
        ) VALUES (?, ?, ?, 'PRESCRIPTION', ?)
        """, (
            req.patient_id,
            f"New consultation note from {provider['name']}",
            f"{provider['name']} has added a new consultation note: '{req.title}'.",
            record_id
        ))

    return {
        "message": "Consultation record added to patient's wallet.",
        "record_id": record_id,
        "title": req.title
    }
