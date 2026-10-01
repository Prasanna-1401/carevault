import json
import uuid
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import jwt
from app.config import SECRET_KEY
from app.database import db_session

def create_consent_request(
    patient_id: str,
    provider_id: str,
    provider_name: str,
    provider_hospital: str,
    requested_records: List[str],  # e.g. ["Lab Reports", "Prescriptions"] or specific record IDs
    purpose: str,                  # "Treatment", "Second Opinion", "Emergency", "Consultation"
    duration_minutes: int = 30
) -> Dict[str, Any]:
    consent_id = f"CV-CNS-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=duration_minutes)

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO consents (
            consent_id, patient_id, provider_id, provider_name, provider_hospital,
            requested_records, purpose, duration_minutes, status, created_at, expires_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'REQUESTED', ?, ?)
        """, (
            consent_id, patient_id, provider_id, provider_name, provider_hospital,
            json.dumps(requested_records), purpose, duration_minutes,
            now.isoformat(), expires_at.isoformat()
        ))

        # Log audit entry
        cursor.execute("""
        INSERT INTO access_logs (
            actor_id, actor_name, actor_role, patient_id, action, status, details
        ) VALUES (?, ?, 'DOCTOR', ?, 'access_requested', 'PENDING', ?)
        """, (
            provider_id, provider_name, patient_id,
            f"Requested access to {', '.join(requested_records)} for purpose '{purpose}' ({duration_minutes}m)"
        ))

        # Add notification for patient
        cursor.execute("""
        INSERT INTO notifications (
            patient_id, title, message, type, related_id
        ) VALUES (?, ?, ?, 'ACCESS_REQUEST', ?)
        """, (
            patient_id,
            f"Access Request from {provider_name}",
            f"{provider_name} ({provider_hospital}) has requested access to your {', '.join(requested_records)} for {purpose}.",
            consent_id
        ))

    return {
        "consent_id": consent_id,
        "patient_id": patient_id,
        "provider_id": provider_id,
        "requested_records": requested_records,
        "purpose": purpose,
        "duration_minutes": duration_minutes,
        "status": "REQUESTED",
        "expires_at": expires_at.isoformat()
    }

def update_consent_status(consent_id: str, patient_id: str, new_status: str, actor_name: str) -> Dict[str, Any]:
    """Handles patient approval, rejection, or revocation with audit trail"""
    valid_statuses = {"GRANTED", "REJECTED", "REVOKED"}
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status: {new_status}")

    now = datetime.now(timezone.utc)
    revoked_at = now.isoformat() if new_status == "REVOKED" else None

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM consents WHERE consent_id = ? AND patient_id = ?", (consent_id, patient_id))
        consent = cursor.fetchone()
        if not consent:
            raise KeyError("Consent request not found or patient mismatch.")

        consent_dict = dict(consent)

        # Update consent
        if revoked_at:
            cursor.execute("UPDATE consents SET status = ?, revoked_at = ? WHERE consent_id = ?", (new_status, revoked_at, consent_id))
        else:
            # If granted, refresh expires_at from now based on duration
            dur = consent_dict["duration_minutes"]
            new_expires = (now + timedelta(minutes=dur)).isoformat()
            cursor.execute("UPDATE consents SET status = ?, expires_at = ? WHERE consent_id = ?", (new_status, new_expires, consent_id))

        # Map to audit action
        action_map = {
            "GRANTED": "access_granted",
            "REJECTED": "access_rejected",
            "REVOKED": "access_revoked"
        }
        cursor.execute("""
        INSERT INTO access_logs (
            actor_id, actor_name, actor_role, patient_id, action, status, details
        ) VALUES (?, ?, 'PATIENT', ?, ?, 'SUCCESS', ?)
        """, (
            patient_id, actor_name, patient_id, action_map[new_status],
            f"Patient {new_status.lower()} access request {consent_id} for {consent_dict.get('provider_name')}"
        ))

        # Notify provider (simulated by notif or status query)
        notif_msg = f"Your access request has been {new_status.lower()} by the patient."
        cursor.execute("""
        INSERT INTO notifications (
            patient_id, title, message, type, related_id
        ) VALUES (?, ?, ?, ?, ?)
        """, (
            patient_id,
            f"Access {new_status.capitalize()}",
            f"You {new_status.lower()} access for {consent_dict.get('provider_name')}.",
            f"ACCESS_{new_status}",
            consent_id
        ))

    return {"consent_id": consent_id, "status": new_status, "updated_at": now.isoformat()}

def verify_provider_access(provider_id: str, patient_id: str, record_id: Optional[str] = None, record_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Strict backend authorization verification:
    - Verifies active granted consent
    - Checks expiration
    - Checks scope containment
    """
    now = datetime.now(timezone.utc)

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM consents
        WHERE provider_id = ? AND patient_id = ? AND status = 'GRANTED'
        ORDER BY expires_at DESC LIMIT 1
        """, (provider_id, patient_id))
        row = cursor.fetchone()

        if not row:
            return {"authorized": False, "reason": "No active granted consent found for this patient."}

        consent = dict(row)
        expires_at = datetime.fromisoformat(consent["expires_at"].replace("Z", "+00:00"))

        if now > expires_at:
            # Mark expired
            cursor.execute("UPDATE consents SET status = 'EXPIRED' WHERE consent_id = ?", (consent["consent_id"],))
            cursor.execute("""
            INSERT INTO access_logs (
                actor_id, actor_name, actor_role, patient_id, action, status, details
            ) VALUES (?, ?, 'SYSTEM', ?, 'access_expired', 'EXPIRED', ?)
            """, (
                provider_id, consent.get("provider_name", "Doctor"), patient_id,
                f"Consent {consent['consent_id']} expired at {expires_at.isoformat()}"
            ))
            return {"authorized": False, "reason": "Consent duration has expired. Please request renewed authorization."}

        # Check scope
        requested_scopes = json.loads(consent["requested_records"]) if isinstance(consent["requested_records"], str) else consent["requested_records"]
        
        # If "All" or record_type in requested_scopes
        if "All" in requested_scopes or "All Records" in requested_scopes:
            is_scoped = True
        elif record_type and any(s.lower() in record_type.lower() or record_type.lower() in s.lower() for s in requested_scopes):
            is_scoped = True
        elif not record_type:
            is_scoped = True
        else:
            is_scoped = False

        if not is_scoped:
            return {
                "authorized": False,
                "reason": f"Record category '{record_type}' is outside the granted consent scope: {', '.join(requested_scopes)}"
            }

        remaining_seconds = int((expires_at - now).total_seconds())

        return {
            "authorized": True,
            "consent_id": consent["consent_id"],
            "purpose": consent["purpose"],
            "expires_at": consent["expires_at"],
            "remaining_seconds": max(0, remaining_seconds),
            "scopes": requested_scopes
        }

def generate_qr_share_token(patient_id: str, patient_name: str, allowed_scopes: List[str], duration_minutes: int = 15) -> str:
    """
    Generates a secure, cryptographically signed, short-lived QR token.
    RULE: QR NEVER contains medical records. It only contains exchange credentials.
    """
    payload = {
        "token_type": "CAREVAULT_QR_CONSENT_EXCHANGE",
        "token_id": str(uuid.uuid4())[:8],
        "patient_id": patient_id,
        "patient_name": patient_name,
        "allowed_scopes": allowed_scopes,
        "exp": int(time.time()) + (duration_minutes * 60)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_qr_share_token(qr_token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(qr_token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("token_type") != "CAREVAULT_QR_CONSENT_EXCHANGE":
            return None
        return payload
    except Exception:
        return None
