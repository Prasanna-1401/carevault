import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Response
from fastapi.responses import StreamingResponse
import io
from app.database import db_session
from app.security import get_current_user, get_current_patient_profile, require_roles
from app.storage import (
    save_document, read_document, generate_signed_view_token,
    verify_signed_view_token, apply_view_watermark, create_synthetic_document_image
)
from app.services.consent_service import verify_provider_access

router = APIRouter(prefix="/api/records", tags=["Medical Records"])

CATEGORIES = [
    "Lab Reports", "X-rays", "CT/MRI", "Prescriptions",
    "Discharge Summaries", "Doctor Notes", "Vaccination Records",
    "Previous Treatments", "Other Documents"
]

@router.get("/categories")
def get_categories():
    return CATEGORIES

@router.get("")
def list_patient_records(
    q: Optional[str] = Query(None, description="Search keyword"),
    category: Optional[str] = Query(None, description="Filter by category"),
    hospital: Optional[str] = Query(None, description="Filter by hospital"),
    sort: Optional[str] = Query("desc", description="Sort date: 'asc' or 'desc'"),
    profile: dict = Depends(get_current_patient_profile)
):
    patient_id = profile["patient_id"]

    query = "SELECT * FROM medical_records WHERE patient_id = ?"
    params = [patient_id]

    if category and category != "All":
        query += " AND record_type = ?"
        params.append(category)

    if hospital and hospital != "All":
        query += " AND hospital_name LIKE ?"
        params.append(f"%{hospital}%")

    if q and q.strip():
        term = f"%{q.strip()}%"
        query += " AND (title LIKE ? OR description LIKE ? OR hospital_name LIKE ? OR doctor_name LIKE ? OR raw_text LIKE ?)"
        params.extend([term, term, term, term, term])

    order_dir = "ASC" if sort == "asc" else "DESC"
    query += f" ORDER BY record_date {order_dir}"

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        rows = [dict(r) for r in cursor.fetchall()]

    for r in rows:
        if r.get("tags"):
            try:
                r["tags"] = json.loads(r["tags"])
            except Exception:
                r["tags"] = []

    return rows

@router.get("/timeline")
def get_records_timeline(profile: dict = Depends(get_current_patient_profile)):
    """Groups patient records chronologically by Year and Month for visual health timeline"""
    patient_id = profile["patient_id"]
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT record_id, record_type, title, hospital_name, doctor_name, record_date, verification_status
        FROM medical_records WHERE patient_id = ?
        ORDER BY record_date DESC
        """, (patient_id,))
        rows = [dict(r) for r in cursor.fetchall()]

    timeline = {}
    for r in rows:
        date_str = r.get("record_date", "2026-01-01")
        year = date_str[:4] if len(date_str) >= 4 else "2026"
        month = date_str[5:7] if len(date_str) >= 7 else "01"
        month_name = datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d").strftime("%B")

        if year not in timeline:
            timeline[year] = {}
        if month_name not in timeline[year]:
            timeline[year][month_name] = []

        timeline[year][month_name].append(r)

    formatted = []
    for y, months in sorted(timeline.items(), reverse=True):
        m_list = []
        for m, items in months.items():
            m_list.append({"month": m, "records": items})
        formatted.append({"year": y, "months": m_list})

    return formatted

@router.get("/{record_id}")
def get_record_detail(record_id: str, current_user: dict = Depends(get_current_user)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM medical_records WHERE record_id = ?", (record_id,))
        rec_row = cursor.fetchone()
        if not rec_row:
            raise HTTPException(status_code=404, detail="Medical record not found.")

        rec = dict(rec_row)

        # Check authorization
        if current_user["role"] == "PATIENT":
            cursor.execute("SELECT patient_id FROM patients WHERE user_id = ?", (current_user["id"],))
            p = cursor.fetchone()
            if not p or p["patient_id"] != rec["patient_id"]:
                raise HTTPException(status_code=403, detail="Unauthorized to view this record.")
        elif current_user["role"] == "DOCTOR":
            cursor.execute("SELECT provider_id FROM providers WHERE user_id = ?", (current_user["id"],))
            d = cursor.fetchone()
            if not d:
                raise HTTPException(status_code=403, detail="Unauthorized.")
            access = verify_provider_access(d["provider_id"], rec["patient_id"], record_id, rec["record_type"])
            if not access["authorized"]:
                raise HTTPException(status_code=403, detail=access["reason"])

        if rec.get("tags"):
            try: rec["tags"] = json.loads(rec["tags"])
            except Exception: rec["tags"] = []

        # Generate temporary view token
        viewer_name = current_user["full_name"]
        token = generate_signed_view_token(record_id, viewer_name, current_user["role"], expires_seconds=1800)
        rec["view_token"] = token

        return rec

@router.post("/upload")
async def upload_record(
    title: str = Form(...),
    record_type: str = Form(...),
    hospital_name: str = Form(...),
    doctor_name: Optional[str] = Form("Self Uploaded"),
    record_date: str = Form(...),
    description: Optional[str] = Form(""),
    tags: Optional[str] = Form("[]"),
    file: Optional[UploadFile] = File(None),
    profile: dict = Depends(get_current_patient_profile)
):
    patient_id = profile["patient_id"]
    record_id = f"CV-REC-{uuid.uuid4().hex[:6].upper()}"

    if file and file.filename:
        file_bytes = await file.read()
        filename = file.filename
        mime = file.content_type or "application/pdf"
    else:
        # Generate synthetic doc if no file uploaded
        lines = [
            f"Record Title: {title}",
            f"Record Category: {record_type}",
            f"Facility: {hospital_name}",
            f"Clinician: {doctor_name}",
            f"Observation Summary: {description or 'Clinical document uploaded by patient.'}"
        ]
        file_bytes = create_synthetic_document_image(title, hospital_name, doctor_name, record_date, lines)
        filename = f"{record_id}.jpg"
        mime = "image/jpeg"

    file_path, enc_name, file_sz = save_document(file_bytes, filename, record_id)

    tag_list = []
    try:
        tag_list = json.loads(tags) if isinstance(tags, str) and tags.startswith("[") else [t.strip() for t in tags.split(",") if t.strip()]
    except Exception:
        tag_list = [record_type]

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO medical_records (
            record_id, patient_id, record_type, title, hospital_name, doctor_name,
            record_date, file_path, file_name, file_size, mime_type, description,
            raw_text, tags, source, verification_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PATIENT_UPLOAD', 'SELF_REPORTED')
        """, (
            record_id, patient_id, record_type, title, hospital_name, doctor_name,
            record_date, file_path, enc_name, file_sz, mime, description,
            description, json.dumps(tag_list)
        ))

        cursor.execute("""
        INSERT INTO record_files (record_id, encrypted_filename, original_filename, file_hash)
        VALUES (?, ?, ?, 'sha256-uploaded')
        """, (record_id, enc_name, filename))

        cursor.execute("""
        INSERT INTO access_logs (
            actor_id, actor_name, actor_role, patient_id, record_id, record_title, action, status, details
        ) VALUES (?, ?, 'PATIENT', ?, ?, ?, 'record_uploaded', 'SUCCESS', ?)
        """, (
            patient_id, profile["full_name"], patient_id, record_id, title,
            f"Patient uploaded new {record_type}: '{title}'"
        ))

    return {
        "message": "Medical record uploaded and encrypted successfully.",
        "record_id": record_id,
        "title": title
    }

@router.get("/{record_id}/view")
def view_record_watermarked(
    record_id: str,
    token: str = Query(...),
    viewer_override: Optional[str] = Query(None)
):
    """
    Renders the document preview with an explicit view-only security watermark:
    'Confidential - Viewed by [Viewer Name] - [Date/Time]'
    """
    token_data = verify_signed_view_token(token)
    if not token_data or token_data.get("record_id") != record_id:
        raise HTTPException(status_code=403, detail="Invalid or expired view token.")

    viewer = viewer_override or token_data.get("viewer_name", "Authorized Provider")
    now_str = datetime.now(timezone.utc).strftime("%d-%b-%Y %H:%M UTC")
    watermark_text = f"Confidential - Viewed by {viewer} - {now_str}"

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM medical_records WHERE record_id = ?", (record_id,))
        rec = cursor.fetchone()
        if not rec:
            raise HTTPException(status_code=404, detail="Record not found.")

        rec_dict = dict(rec)

        # Log view in audit
        cursor.execute("""
        INSERT INTO access_logs (
            actor_id, actor_name, actor_role, patient_id, record_id, record_title, action, status, details
        ) VALUES (?, ?, ?, ?, ?, ?, 'record_viewed', 'SUCCESS', ?)
        """, (
            viewer, viewer, token_data.get("viewer_role", "DOCTOR"),
            rec_dict["patient_id"], record_id, rec_dict["title"],
            f"Viewed watermarked record ({rec_dict['record_type']})"
        ))

    file_bytes = read_document(rec_dict["file_path"])
    if not file_bytes:
        # If file not found on disk, regenerate synthetic placeholder
        lines = [
            f"Document Title: {rec_dict['title']}",
            f"Category: {rec_dict['record_type']}",
            f"Issuing Center: {rec_dict['hospital_name']}",
            f"Consultant: {rec_dict['doctor_name']}",
            f"Description: {rec_dict['description']}"
        ]
        file_bytes = create_synthetic_document_image(
            rec_dict["title"], rec_dict["hospital_name"], rec_dict["doctor_name"], rec_dict["record_date"], lines
        )

    # Apply diagonal security watermark
    watermarked_bytes = apply_view_watermark(file_bytes, watermark_text)

    return StreamingResponse(io.BytesIO(watermarked_bytes), media_type="image/jpeg")
