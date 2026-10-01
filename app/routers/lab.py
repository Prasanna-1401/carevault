import uuid
import json
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.database import db_session
from app.security import require_roles, get_current_user
from app.storage import save_document, create_synthetic_document_image

router = APIRouter(prefix="/api/lab", tags=["Lab & Diagnostic Center Portal"])

class PatientSearchRequest(BaseModel):
    patient_id: str

@router.get("/search-patient")
def search_patient(patient_id: str, user: dict = Depends(require_roles(["LAB", "ADMIN", "DOCTOR"]))):
    """
    Looks up verified patient by CareVault ID without exposing unrelated medical history.
    """
    clean_id = patient_id.strip().upper()
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT p.patient_id, u.full_name, p.dob, p.gender, p.blood_group
        FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE UPPER(p.patient_id) = ?
        """, (clean_id,))
        patient = cursor.fetchone()

        if not patient:
            raise HTTPException(status_code=404, detail=f"No verified patient found with CareVault ID: {clean_id}")

        return dict(patient)

@router.post("/transfer-record")
async def transfer_record_to_wallet(
    patient_id: str = Form(...),
    title: str = Form(...),
    record_type: str = Form("Lab Reports"),
    doctor_name: str = Form("Dr. V. K. Sen, Consulting Pathologist"),
    record_date: str = Form(...),
    description: str = Form(""),
    parameters: Optional[str] = Form(""),  # multiline findings
    file: Optional[UploadFile] = File(None),
    user: dict = Depends(require_roles(["LAB", "ADMIN"]))
):
    """
    Direct Diagnostic Transfer:
    Delivers a verified medical record directly into the patient's CareVault digital wallet.
    Does NOT grant the lab access to previous records.
    """
    clean_id = patient_id.strip().upper()
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM patients WHERE UPPER(patient_id) = ?", (clean_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Target patient not found.")

        # Determine lab name
        cursor.execute("SELECT name FROM labs WHERE user_id = ?", (user["id"],))
        lab_row = cursor.fetchone()
        lab_name = lab_row[0] if lab_row else "Apex Central Diagnostics & Pathology"

    record_id = f"CV-REC-{uuid.uuid4().hex[:6].upper()}"

    lines = [
        f"TEST: {title.upper()}",
        f"CATEGORY: {record_type}",
        f"PERFORMED BY: {lab_name}",
        f"ORDERING / CONSULTING PHYSICIAN: {doctor_name}",
        f"SAMPLE DATE: {record_date}",
        "### CLINICAL OBSERVATIONS & PARAMETERS:"
    ]
    if parameters and parameters.strip():
        for l in parameters.strip().split("\n"):
            lines.append(f"- {l.strip()}")
    else:
        lines.append(f"- {description or 'Routine diagnostic analysis completed within quality limits.'}")

    if file and file.filename:
        file_bytes = await file.read()
        filename = file.filename
        mime = file.content_type or "application/pdf"
    else:
        file_bytes = create_synthetic_document_image(title, lab_name, doctor_name, record_date, lines)
        filename = f"{record_id}.jpg"
        mime = "image/jpeg"

    file_path, enc_name, file_sz = save_document(file_bytes, filename, record_id)

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO medical_records (
            record_id, patient_id, record_type, title, hospital_name, doctor_name,
            record_date, file_path, file_name, file_size, mime_type, description,
            raw_text, tags, source, verification_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DIRECT_LAB_TRANSFER', 'VERIFIED')
        """, (
            record_id, clean_id, record_type, title, lab_name, doctor_name,
            record_date, file_path, enc_name, file_sz, mime, description,
            "\n".join(lines), json.dumps([record_type, "Diagnostic Transfer", lab_name])
        ))

        cursor.execute("""
        INSERT INTO record_files (record_id, encrypted_filename, original_filename, file_hash)
        VALUES (?, ?, ?, 'sha256-lab-verified')
        """, (record_id, enc_name, filename))

        # Log direct transfer in audit
        cursor.execute("""
        INSERT INTO access_logs (
            actor_id, actor_name, actor_role, patient_id, record_id, record_title, action, status, details
        ) VALUES (?, ?, 'LAB', ?, ?, ?, 'record_transferred', 'SUCCESS', ?)
        """, (
            user["email"], lab_name, clean_id, record_id, title,
            f"Direct transfer from {lab_name} delivered to wallet."
        ))

        # Send notification to patient
        cursor.execute("""
        INSERT INTO notifications (
            patient_id, title, message, type, related_id
        ) VALUES (?, ?, ?, 'RECORD_RECEIVED', ?)
        """, (
            clean_id,
            f"New medical record received from {lab_name}",
            f"Your {title} ({record_type}) has been delivered directly into your health wallet.",
            record_id
        ))

    return {
        "message": f"Record successfully transferred to patient {clean_id}'s wallet.",
        "record_id": record_id,
        "recipient_patient_id": clean_id,
        "issuing_lab": lab_name,
        "status": "DELIVERED_TO_WALLET"
    }
