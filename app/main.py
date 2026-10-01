from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import BASE_DIR, DEMO_MODE
from app.database import init_db
from app.seed_data import seed_database
from app.routers import (
    auth, patients, records, consents, ai, hospitals, audit, lab, doctor, admin
)

app = FastAPI(
    title="CareVault AI",
    description="Your Health. Your Records. Your Control. Patient-Controlled Digital Health Wallet & Clinical Decision Support.",
    version="1.0.0"
)

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        return response

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and Templates
static_dir = BASE_DIR / "app" / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates_dir = BASE_DIR / "app" / "templates"
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Include API Routers
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(records.router)
app.include_router(consents.router)
app.include_router(ai.router)
app.include_router(hospitals.router)
app.include_router(audit.router)
app.include_router(lab.router)
app.include_router(doctor.router)
app.include_router(admin.router)

@app.on_event("startup")
def on_startup():
    print("CareVault AI Server starting up...")
    seed_database()

@app.get("/")
def serve_home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"demo_mode": DEMO_MODE})

@app.get("/health")
def healthcheck():
    return {
        "status": "healthy",
        "service": "CareVault AI",
        "tagline": "Your Health. Your Records. Your Control.",
        "version": "1.0.0",
        "demo_mode": DEMO_MODE
    }
