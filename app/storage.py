import os
import hashlib
import time
from pathlib import Path
from typing import Optional, Tuple
import jwt
from PIL import Image, ImageDraw, ImageFont
from app.config import STORAGE_DIR, SECRET_KEY

# Storage key for at-rest obfuscation/encryption simulation
ENCRYPTION_KEY = hashlib.sha256(SECRET_KEY.encode()).digest()

def encrypt_bytes(data: bytes) -> bytes:
    # Symmetric stream XOR cipher with key hash for at-rest file protection demonstration
    key_len = len(ENCRYPTION_KEY)
    return bytes(b ^ ENCRYPTION_KEY[i % key_len] for i, b in enumerate(data))

def decrypt_bytes(encrypted_data: bytes) -> bytes:
    return encrypt_bytes(encrypted_data)

def save_document(file_bytes: bytes, original_filename: str, record_id: str) -> Tuple[str, str, int]:
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    ext = Path(original_filename).suffix.lower() or ".pdf"
    encrypted_filename = f"{record_id}_{file_hash[:12]}{ext}.enc"
    target_path = STORAGE_DIR / encrypted_filename

    # Encrypt and save
    encrypted_content = encrypt_bytes(file_bytes)
    with open(target_path, "wb") as f:
        f.write(encrypted_content)

    return str(target_path), encrypted_filename, len(file_bytes)

def read_document(file_path: str) -> Optional[bytes]:
    p = Path(file_path)
    if not p.exists():
        return None
    with open(p, "rb") as f:
        encrypted = f.read()
    return decrypt_bytes(encrypted)

def generate_signed_view_token(record_id: str, viewer_name: str, viewer_role: str, expires_seconds: int = 1800) -> str:
    payload = {
        "record_id": record_id,
        "viewer_name": viewer_name,
        "viewer_role": viewer_role,
        "exp": int(time.time()) + expires_seconds,
        "view_only": True
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_signed_view_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        return None

def apply_view_watermark(image_bytes: bytes, watermark_text: str) -> bytes:
    """Renders a diagonal security watermark on the document preview"""
    import io
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        width, height = image.size
        # Draw multiple repeating watermarks across canvas
        step_y = max(180, height // 5)
        step_x = max(240, width // 3)
        
        for y in range(50, height, step_y):
            for x in range(20, width, step_x):
                draw.text(
                    (x, y),
                    watermark_text,
                    fill=(220, 38, 38, 70),  # Red tint with transparency
                )
        
        watermarked = Image.alpha_composite(image, txt_layer).convert("RGB")
        out_buf = io.BytesIO()
        watermarked.save(out_buf, format="JPEG", quality=85)
        return out_buf.getvalue()
    except Exception:
        return image_bytes

def create_synthetic_document_image(title: str, hospital: str, doctor: str, date: str, content_lines: list) -> bytes:
    """Generates a clean, realistic document image for synthetic records"""
    import io
    width, height = 900, 1200
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle([(0, 0), (width, 110)], fill=(241, 245, 249))
    draw.rectangle([(0, 108), (width, 112)], fill=(14, 165, 233))

    # Header Text
    draw.text((40, 25), "CareVault AI - Certified Health Record", fill=(15, 23, 42))
    draw.text((40, 55), f"Issuing Facility: {hospital}", fill=(71, 85, 105))
    draw.text((40, 80), f"Attending Physician: {doctor} | Date: {date}", fill=(100, 116, 139))
    draw.text((width - 240, 25), "[DEMO / SYNTHETIC]", fill=(225, 29, 72))

    # Title
    draw.text((40, 140), title.upper(), fill=(15, 23, 42))
    draw.line([(40, 175), (width - 40, 175)], fill=(203, 213, 225), width=2)

    # Content
    y = 200
    for line in content_lines:
        if line.startswith("###"):
            y += 15
            draw.text((40, y), line.replace("###", "").strip(), fill=(30, 41, 59))
            y += 30
        elif line.startswith("-"):
            draw.text((60, y), line, fill=(51, 65, 85))
            y += 24
        else:
            draw.text((40, y), line, fill=(71, 85, 105))
            y += 22

    # Footer Notice
    draw.line([(40, height - 90), (width - 40, height - 90)], fill=(226, 232, 240), width=1)
    draw.text((40, height - 75), "DISCLAIMER: This document is synthetic demo data generated for CareVault AI evaluation.", fill=(148, 163, 184))
    draw.text((40, height - 55), "Confidential Patient Controlled Digital Health Wallet Document", fill=(148, 163, 184))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()
