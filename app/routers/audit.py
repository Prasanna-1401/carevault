from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from app.database import db_session
from app.security import get_current_user, get_current_patient_profile, require_roles

router = APIRouter(prefix="/api/audit", tags=["Tamper-Evident Access History"])

@router.get("/my-history")
def get_patient_access_history(
    limit: int = Query(50, le=100),
    profile: dict = Depends(get_current_patient_profile)
):
    """
    Patient-facing Access History / Audit Trail:
    Shows chronological security logs of who requested, accessed, viewed, or received records.
    Read-only and immutable.
    """
    patient_id = profile["patient_id"]
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, timestamp, actor_id, actor_name, actor_role, record_id, record_title, action, status, details
        FROM access_logs
        WHERE patient_id = ?
        ORDER BY timestamp DESC LIMIT ?
        """, (patient_id, limit))
        rows = [dict(r) for r in cursor.fetchall()]

    return rows

@router.get("/all")
def get_all_audit_logs(
    limit: int = Query(100, le=500),
    user: dict = Depends(require_roles(["ADMIN"]))
):
    """System Administrator full audit inspection view"""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM access_logs
        ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
    return rows
