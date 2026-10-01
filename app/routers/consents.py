import io
import json
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
import qrcode
from app.database import db_session
from app.security import (
    get_current_user, get_current_patient_profile,
    get_current_provider_profile, require_roles
)
from app.services.consent_service import (
    create_consent_request, update_consent_status,
    generate_qr_share_token, decode_qr_share_token
)

router = APIRouter(prefix="/api/consents", tags=["Patient-Controlled Consent"])

class RequestAccessModel(BaseModel):
    patient_id: str
    requested_records: List[str]  # ["Lab Reports", "Prescriptions", "CT/MRI"]
    purpose: str                  # "Treatment", "Second Opinion", "Emergency", "Consultation"
    duration_minutes: int = 30

class StatusUpdateModel(BaseModel):
    status: str                   # "GRANTED", "REJECTED", "REVOKED"

class GenerateQRModel(BaseModel):
    allowed_scopes: List[str] = ["Lab Reports", "Prescriptions", "CT/MRI"]
    duration_minutes: int = 30

class ScanQRModel(BaseModel):
    qr_token: str

@router.get("")
def list_consents(current_user: dict = Depends(get_current_user)):
    """Lists consents relevant to patient or doctor"""
    with db_session() as conn:
        cursor = conn.cursor()
        now_str = datetime.now(timezone.utc).isoformat()

        if current_user["role"] == "PATIENT":
            cursor.execute("SELECT patient_id FROM patients WHERE user_id = ?", (current_user["id"],))
            p = cursor.fetchone()
            if not p: return []
            pid = p["patient_id"]

            # Auto-expire outdated granted consents in database
            cursor.execute("UPDATE consents SET status = 'EXPIRED' WHERE patient_id = ? AND status = 'GRANTED' AND expires_at <= ?", (pid, now_str))

            cursor.execute("""
            SELECT * FROM consents WHERE patient_id = ?
            ORDER BY created_at DESC
            """, (pid,))
        elif current_user["role"] == "DOCTOR":
            cursor.execute("SELECT provider_id FROM providers WHERE user_id = ?", (current_user["id"],))
            d = cursor.fetchone()
            if not d: return []
            prid = d["provider_id"]

            cursor.execute("UPDATE consents SET status = 'EXPIRED' WHERE provider_id = ? AND status = 'GRANTED' AND expires_at <= ?", (prid, now_str))

            cursor.execute("""
            SELECT * FROM consents WHERE provider_id = ?
            ORDER BY created_at DESC
            """, (prid,))
        else:
            cursor.execute("SELECT * FROM consents ORDER BY created_at DESC LIMIT 50")

        rows = [dict(r) for r in cursor.fetchall()]

    for r in rows:
        try:
            r["requested_records"] = json.loads(r["requested_records"])
        except Exception:
            pass

    return rows

@router.post("/request")
def request_access(req: RequestAccessModel, provider: dict = Depends(get_current_provider_profile)):
    # Verify patient exists
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT patient_id, full_name FROM patients JOIN users ON patients.user_id = users.id WHERE patient_id = ?", (req.patient_id,))
        patient = cursor.fetchone()
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient with ID {req.patient_id} not found.")

    res = create_consent_request(
        patient_id=req.patient_id,
        provider_id=provider["provider_id"],
        provider_name=provider["name"],
        provider_hospital=provider.get("hospital_name", "Consulting Facility"),
        requested_records=req.requested_records,
        purpose=req.purpose,
        duration_minutes=req.duration_minutes
    )
    return res

@router.post("/{consent_id}/status")
def update_status(
    consent_id: str,
    req: StatusUpdateModel,
    profile: dict = Depends(get_current_patient_profile)
):
    try:
        res = update_consent_status(
            consent_id=consent_id,
            patient_id=profile["patient_id"],
            new_status=req.status,
            actor_name=profile["full_name"]
        )
        return res
    except KeyError:
        raise HTTPException(status_code=404, detail="Consent not found or access denied.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/qr/generate")
def create_share_qr(req: GenerateQRModel, profile: dict = Depends(get_current_patient_profile)):
    token = generate_qr_share_token(
        patient_id=profile["patient_id"],
        patient_name=profile["full_name"],
        allowed_scopes=req.allowed_scopes,
        duration_minutes=req.duration_minutes
    )
    return {
        "qr_token": token,
        "patient_id": profile["patient_id"],
        "patient_name": profile["full_name"],
        "allowed_scopes": req.allowed_scopes,
        "expires_in_minutes": req.duration_minutes,
        "safety_notice": "This QR token grants temporary, patient-controlled access to the specified categories. No raw health records are contained in this code."
    }

@router.get("/qr/image")
def get_qr_image(token: str = Query(...)):
    """Renders QR code image containing the secure exchange token"""
    img = qrcode.make(token)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@router.post("/qr/scan")
def scan_qr_token(req: ScanQRModel, provider: dict = Depends(get_current_provider_profile)):
    """Doctor scans QR token to claim short-lived authorized access"""
    payload = decode_qr_share_token(req.qr_token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired QR exchange token.")

    patient_id = payload["patient_id"]
    scopes = payload.get("allowed_scopes", ["All Records"])

    # Directly create a granted consent from the valid pre-authorized QR exchange token
    consent = create_consent_request(
        patient_id=patient_id,
        provider_id=provider["provider_id"],
        provider_name=provider["name"],
        provider_hospital=provider.get("hospital_name", "Consulting Facility"),
        requested_records=scopes,
        purpose="In-person QR Authorized Consultation",
        duration_minutes=30
    )
    # Automatically grant since the patient explicitly created the QR token
    update_consent_status(
        consent_id=consent["consent_id"],
        patient_id=patient_id,
        new_status="GRANTED",
        actor_name=payload.get("patient_name", "Patient (via QR)")
    )

    return {
        "message": f"Successfully connected to patient {patient_id} via QR exchange!",
        "consent_id": consent["consent_id"],
        "patient_id": patient_id,
        "scopes": scopes,
        "duration_minutes": 30
    }
