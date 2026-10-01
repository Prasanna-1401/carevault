import os
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Union
import jwt
from fastapi import Depends, HTTPException, status, Header, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import db_session

security_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return salt.hex() + ":" + key.hex()

def verify_password(stored_password: str, provided_password: str) -> bool:
    try:
        salt_hex, key_hex = stored_password.split(":")
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000
        )
        return hmac.compare_digest(key.hex(), key_hex)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def get_current_user_optional(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    carevault_token: Optional[str] = Cookie(None)
) -> Optional[dict]:
    token = None
    if auth and auth.credentials:
        token = auth.credentials
    elif carevault_token:
        token = carevault_token

    if not token:
        return None

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if not user:
            return None
        return dict(user)

def get_current_user(user: Optional[dict] = Depends(get_current_user_optional)) -> dict:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def require_roles(allowed_roles: Union[str, List[str]]):
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

def get_current_patient_profile(current_user: dict = Depends(require_roles(["PATIENT"]))) -> dict:
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE user_id = ?", (current_user["id"],))
        patient = cursor.fetchone()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient profile not found.")
        profile = dict(patient)
        profile["full_name"] = current_user["full_name"]
        profile["email"] = current_user["email"]
        profile["mobile"] = current_user["mobile"]
        return profile

def get_current_provider_profile(current_user: dict = Depends(require_roles(["DOCTOR"]))) -> dict:
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM providers WHERE user_id = ?", (current_user["id"],))
        provider = cursor.fetchone()
        if not provider:
            raise HTTPException(status_code=404, detail="Provider profile not found.")
        doc = dict(provider)
        doc["email"] = current_user["email"]
        doc["mobile"] = current_user["mobile"]
        return doc
