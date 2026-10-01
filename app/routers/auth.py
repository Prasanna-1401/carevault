import uuid
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, Response, status
from app.database import db_session
from app.security import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_current_patient_profile, get_current_provider_profile
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterPatientRequest(BaseModel):
    full_name: str
    email: str
    password: str
    mobile: str
    dob: str
    gender: Optional[str] = "Prefer not to say"
    blood_group: str
    allergies: Optional[str] = "None"
    existing_conditions: Optional[str] = "None"
    preferred_language: Optional[str] = "English"
    emergency_contact_name: Optional[str] = ""
    emergency_contact_phone: Optional[str] = ""
    emergency_contact_relation: Optional[str] = ""

class LoginRequest(BaseModel):
    email: str
    password: str

class SwitchRoleRequest(BaseModel):
    role: str  # PATIENT, DOCTOR, LAB, ADMIN

@router.post("/register")
def register_patient(req: RegisterPatientRequest, response: Response):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (req.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email is already registered.")

        pw_hash = hash_password(req.password)
        cursor.execute("""
        INSERT INTO users (email, password_hash, role, full_name, mobile)
        VALUES (?, ?, 'PATIENT', ?, ?)
        """, (req.email, pw_hash, req.full_name, req.mobile))
        user_id = cursor.lastrowid

        # Generate unique patient_id
        patient_id = f"CV-PAT-{uuid.uuid4().hex[:6].upper()}"

        cursor.execute("""
        INSERT INTO patients (
            user_id, patient_id, dob, gender, blood_group, allergies,
            existing_conditions, current_medications, preferred_language,
            emergency_contact_name, emergency_contact_phone, emergency_contact_relation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, '', ?, ?, ?, ?)
        """, (
            user_id, patient_id, req.dob, req.gender, req.blood_group,
            req.allergies, req.existing_conditions, req.preferred_language,
            req.emergency_contact_name, req.emergency_contact_phone, req.emergency_contact_relation
        ))

        # Log creation in audit
        cursor.execute("""
        INSERT INTO access_logs (
            actor_id, actor_name, actor_role, patient_id, action, status, details
        ) VALUES (?, ?, 'PATIENT', ?, 'user_registered', 'SUCCESS', 'New patient account created.')
        """, (patient_id, req.full_name, patient_id))

    token = create_access_token({"sub": req.email, "role": "PATIENT", "patient_id": patient_id})
    response.set_cookie(key="carevault_token", value=token, httponly=True, samesite="lax")

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": "PATIENT",
        "patient_id": patient_id,
        "full_name": req.full_name,
        "email": req.email
    }

@router.post("/login")
def login(req: LoginRequest, response: Response):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (req.email,))
        user_row = cursor.fetchone()

        if not user_row:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        user = dict(user_row)
        if not verify_password(user["password_hash"], req.password):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        extra = {}
        if user["role"] == "PATIENT":
            cursor.execute("SELECT patient_id FROM patients WHERE user_id = ?", (user["id"],))
            p = cursor.fetchone()
            if p:
                extra["patient_id"] = p["patient_id"]
        elif user["role"] == "DOCTOR":
            cursor.execute("SELECT provider_id, specialty, hospital_name FROM providers WHERE user_id = ?", (user["id"],))
            d = cursor.fetchone()
            if d:
                extra["provider_id"] = d["provider_id"]
                extra["specialty"] = d["specialty"]
                extra["hospital_name"] = d["hospital_name"]
        elif user["role"] == "LAB":
            cursor.execute("SELECT lab_id, name FROM labs WHERE user_id = ?", (user["id"],))
            l = cursor.fetchone()
            if l:
                extra["lab_id"] = l["lab_id"]

    token_data = {"sub": user["email"], "role": user["role"], **extra}
    token = create_access_token(token_data)
    response.set_cookie(key="carevault_token", value=token, httponly=True, samesite="lax")

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "full_name": user["full_name"],
        "email": user["email"],
        **extra
    }

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="carevault_token")
    return {"message": "Successfully logged out."}

@router.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    extra = {}
    with db_session() as conn:
        cursor = conn.cursor()
        if user["role"] == "PATIENT":
            cursor.execute("SELECT * FROM patients WHERE user_id = ?", (user["id"],))
            p = cursor.fetchone()
            if p:
                extra = dict(p)
        elif user["role"] == "DOCTOR":
            cursor.execute("SELECT * FROM providers WHERE user_id = ?", (user["id"],))
            d = cursor.fetchone()
            if d:
                extra = dict(d)
        elif user["role"] == "LAB":
            cursor.execute("SELECT * FROM labs WHERE user_id = ?", (user["id"],))
            l = cursor.fetchone()
            if l:
                extra = dict(l)

    return {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "full_name": user["full_name"],
        "mobile": user["mobile"],
        "profile": extra
    }

@router.post("/demo-switch")
def demo_switch(req: SwitchRoleRequest, response: Response):
    """Convenient 1-click role switcher for hackathon judges and evaluators"""
    role_email_map = {
        "PATIENT": "priya.sharma@example.com",
        "DOCTOR": "dr.mehta@example.com",
        "LAB": "lab@apexdiagnostics.com",
        "ADMIN": "admin@carevault.ai"
    }

    target_email = role_email_map.get(req.role.upper())
    if not target_email:
        raise HTTPException(status_code=400, detail="Invalid role specified.")

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (target_email,))
        user_row = cursor.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="Demo account not found.")

        user = dict(user_row)
        extra = {}
        if user["role"] == "PATIENT":
            cursor.execute("SELECT patient_id FROM patients WHERE user_id = ?", (user["id"],))
            p = cursor.fetchone()
            if p: extra["patient_id"] = p["patient_id"]
        elif user["role"] == "DOCTOR":
            cursor.execute("SELECT provider_id, specialty, hospital_name FROM providers WHERE user_id = ?", (user["id"],))
            d = cursor.fetchone()
            if d:
                extra["provider_id"] = d["provider_id"]
                extra["specialty"] = d["specialty"]
                extra["hospital_name"] = d["hospital_name"]
        elif user["role"] == "LAB":
            cursor.execute("SELECT lab_id, name FROM labs WHERE user_id = ?", (user["id"],))
            l = cursor.fetchone()
            if l: extra["lab_id"] = l["lab_id"]

    token_data = {"sub": user["email"], "role": user["role"], **extra}
    token = create_access_token(token_data)
    response.set_cookie(key="carevault_token", value=token, httponly=True, samesite="lax")

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "full_name": user["full_name"],
        "email": user["email"],
        **extra
    }
