import json
import io
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from app.database import db_session
from app.security import get_current_patient_profile, get_current_user
from app.services.ai_assistant import (
    explain_medical_report, understand_condition,
    generate_medical_history_summary, answer_health_query
)
from app.services.prescription_reader import (
    analyze_prescription, generate_prescription_image_sample, SAMPLE_PRESETS
)
from app.services.duplicate_detector import check_duplicate_test
from app.services.translator import translate_explanation, SUPPORTED_LANGUAGES
from app.services.question_generator import generate_doctor_questions_for_patient

router = APIRouter(prefix="/api/ai", tags=["AI Clinical Assistant"])

class ChatRequest(BaseModel):
    message: str

class DuplicateCheckRequest(BaseModel):
    test_name: str
    test_date: Optional[str] = None

class AddQuestionRequest(BaseModel):
    question_text: str
    category: Optional[str] = "Custom"

class TranslateRequest(BaseModel):
    explanation_data: dict
    target_language: str

@router.get("/languages")
def get_languages():
    return list(SUPPORTED_LANGUAGES.values())

@router.post("/explain-report/{record_id}")
def explain_report(record_id: str, lang: Optional[str] = Query("en"), profile: dict = Depends(get_current_patient_profile)):
    """Explains a medical report in simple terms without diagnosing"""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM medical_records WHERE record_id = ? AND patient_id = ?", (record_id, profile["patient_id"]))
        rec = cursor.fetchone()
        if not rec:
            raise HTTPException(status_code=404, detail="Record not found.")

        rec_dict = dict(rec)

    explanation = explain_medical_report(
        record_title=rec_dict["title"],
        record_type=rec_dict["record_type"],
        raw_text=rec_dict.get("raw_text", ""),
        patient_notes=rec_dict.get("description", "")
    )

    if lang and lang != "en":
        explanation = translate_explanation(explanation, lang)

    return explanation

@router.post("/translate")
def translate_endpoint(req: TranslateRequest):
    return translate_explanation(req.explanation_data, req.target_language)

@router.post("/read-prescription")
async def read_prescription_endpoint(
    preset_key: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    AI Handwritten Prescription Reader Pipeline:
    Processes image, identifies medications, instructions, confidence score,
    and applies strict safeguards for unclear handwriting.
    """
    image_bytes = None
    if file and file.filename:
        image_bytes = await file.read()

    result = analyze_prescription(image_bytes=image_bytes, preset_key=preset_key)
    return result

@router.get("/prescription-samples")
def get_prescription_samples():
    return [
        {"key": "clear_diabetes_bp", "label": SAMPLE_PRESETS["clear_diabetes_bp"]["label"], "is_clear": True},
        {"key": "unclear_scrawled", "label": SAMPLE_PRESETS["unclear_scrawled"]["label"], "is_clear": False}
    ]

@router.get("/prescription-sample-image/{preset_key}")
def get_sample_image(preset_key: str):
    img_bytes = generate_prescription_image_sample(preset_key)
    return StreamingResponse(io.BytesIO(img_bytes), media_type="image/jpeg")

@router.post("/duplicate-check")
def check_duplicate(req: DuplicateCheckRequest, profile: dict = Depends(get_current_patient_profile)):
    """Detects potentially duplicate/recent tests using patient-controlled records"""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM medical_records WHERE patient_id = ? ORDER BY record_date DESC", (profile["patient_id"],))
        records = [dict(r) for r in cursor.fetchall()]

    from datetime import date
    test_dt = req.test_date or date.today().isoformat()
    return check_duplicate_test(req.test_name, test_dt, records)

@router.get("/medical-history-summary")
def get_history_summary(profile: dict = Depends(get_current_patient_profile)):
    """Generates verifiable chronological medical history summary"""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM medical_records WHERE patient_id = ? ORDER BY record_date DESC", (profile["patient_id"],))
        records = [dict(r) for r in cursor.fetchall()]

    return generate_medical_history_summary(profile, records)

@router.get("/understand-health")
def understand_health_condition(condition: str = Query(...)):
    """Explains a disease or condition for patient awareness"""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM medical_conditions")
        conditions_db = [dict(c) for c in cursor.fetchall()]

    return understand_condition(condition, conditions_db)

@router.get("/conditions-list")
def list_conditions():
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, icd_code, category FROM medical_conditions")
        return [dict(c) for c in cursor.fetchall()]

@router.get("/doctor-questions")
def get_doctor_questions(profile: dict = Depends(get_current_patient_profile)):
    """Returns saved questions or generates fresh personalized questions"""
    patient_id = profile["patient_id"]
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doctor_questions WHERE patient_id = ? ORDER BY id ASC", (patient_id,))
        rows = [dict(r) for r in cursor.fetchall()]

        if not rows:
            # Generate and insert personalized questions
            cursor.execute("SELECT * FROM medical_records WHERE patient_id = ? ORDER BY record_date DESC", (patient_id,))
            records = [dict(r) for r in cursor.fetchall()]
            generated = generate_doctor_questions_for_patient(profile, records)
            for q in generated:
                cursor.execute("""
                INSERT INTO doctor_questions (patient_id, question_text, category, is_checked, is_custom)
                VALUES (?, ?, ?, ?, ?)
                """, (patient_id, q["question_text"], q["category"], 1 if q["is_checked"] else 0, 1 if q["is_custom"] else 0))
            cursor.execute("SELECT * FROM doctor_questions WHERE patient_id = ? ORDER BY id ASC", (patient_id,))
            rows = [dict(r) for r in cursor.fetchall()]

    return rows

@router.post("/doctor-questions/add")
def add_doctor_question(req: AddQuestionRequest, profile: dict = Depends(get_current_patient_profile)):
    patient_id = profile["patient_id"]
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO doctor_questions (patient_id, question_text, category, is_checked, is_custom)
        VALUES (?, ?, ?, 0, 1)
        """, (patient_id, req.question_text, req.category or "Custom"))
        new_id = cursor.lastrowid
    return {"message": "Question added.", "id": new_id, "question_text": req.question_text}

@router.post("/doctor-questions/{q_id}/toggle")
def toggle_doctor_question(q_id: int, profile: dict = Depends(get_current_patient_profile)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_checked FROM doctor_questions WHERE id = ? AND patient_id = ?", (q_id, profile["patient_id"]))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Question not found.")
        new_val = 0 if row[0] == 1 else 1
        cursor.execute("UPDATE doctor_questions SET is_checked = ? WHERE id = ?", (new_val, q_id))
    return {"id": q_id, "is_checked": bool(new_val)}

@router.delete("/doctor-questions/{q_id}")
def delete_doctor_question(q_id: int, profile: dict = Depends(get_current_patient_profile)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM doctor_questions WHERE id = ? AND patient_id = ?", (q_id, profile["patient_id"]))
    return {"message": "Question deleted."}

@router.post("/chat")
def chat_with_assistant(req: ChatRequest, profile: dict = Depends(get_current_patient_profile)):
    """Conversational CareVault AI Assistant strictly grounded in patient records with guardrails"""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM medical_records WHERE patient_id = ? ORDER BY record_date DESC", (profile["patient_id"],))
        records = [dict(r) for r in cursor.fetchall()]

    return answer_health_query(req.message, profile, records)
