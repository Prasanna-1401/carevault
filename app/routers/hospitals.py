import json
from typing import Optional, List, Dict
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import db_session
from app.services.hospital_matcher import rank_facilities, haversine_km, NLP_SPECIALTY_MAPPINGS

router = APIRouter(prefix="/api/hospitals", tags=["Healthcare Discovery & Emergency"])

# Default center point for demo if user location not passed (Jubilee Hills / Banjara Hills corridor)
DEFAULT_LAT = 17.4300
DEFAULT_LNG = 78.4100

class SearchRequest(BaseModel):
    query: Optional[str] = None
    user_lat: Optional[float] = DEFAULT_LAT
    user_lng: Optional[float] = DEFAULT_LNG
    specialty: Optional[str] = None
    cost: Optional[str] = None
    insurance: Optional[str] = None
    emergency_only: Optional[bool] = False
    max_distance_km: Optional[float] = 50.0
    weights: Optional[Dict[str, float]] = None

@router.get("/specialties")
def get_specialties_and_services():
    specialties = [
        "Cardiology", "Urology", "Nephrology", "General Medicine",
        "Orthopedics", "Neurology", "Endocrinology", "Pediatrics",
        "Obstetrics & Gynecology", "Oncology", "Ophthalmology", "Diagnostics"
    ]
    return {
        "specialties": specialties,
        "sample_queries": [
            "I need kidney stone treatment",
            "Chest pain and heart evaluation",
            "Knee pain joint replacement",
            "Diabetic foot clinic and blood sugar check",
            "Persistent headache and migraine MRI"
        ]
    }

@router.post("/search")
def search_and_match_hospitals(req: SearchRequest):
    """
    Hospital Matching Engine:
    Ranks facilities based on transparent, configurable weights and displays
    'Best matches based on your criteria' with explicit reason badges.
    """
    lat = req.user_lat or DEFAULT_LAT
    lng = req.user_lng or DEFAULT_LNG

    with db_session() as conn:
        cursor = conn.cursor()
        query_sql = "SELECT * FROM hospitals WHERE 1=1"
        params = []

        if req.emergency_only:
            query_sql += " AND emergency = 1"

        cursor.execute(query_sql, tuple(params))
        facilities = [dict(r) for r in cursor.fetchall()]

    ranked = rank_facilities(
        facilities=facilities,
        user_lat=lat,
        user_lng=lng,
        query=req.query,
        desired_specialty=req.specialty,
        desired_cost=req.cost,
        desired_insurance=req.insurance,
        weights=req.weights
    )

    # Filter by distance if specified
    if req.max_distance_km:
        ranked = [f for f in ranked if f["distance_km"] <= req.max_distance_km]

    return {
        "search_label": "Best Matches Based on Your Selected Criteria",
        "query_analyzed": req.query,
        "center_coordinates": {"latitude": lat, "longitude": lng},
        "total_matches": len(ranked),
        "results": ranked[:20],
        "applied_weights": req.weights or {
            "specialty_match": 0.40,
            "distance": 0.25,
            "cost_fit": 0.15,
            "insurance_match": 0.10,
            "facility_verification": 0.10
        },
        "disclaimer": "Matches are computed using objective criteria and distance algorithms. CareVault AI does not endorse any specific hospital as objectively 'the best'."
    }

@router.get("/nearby")
def get_nearby_for_map(
    lat: float = Query(DEFAULT_LAT),
    lng: float = Query(DEFAULT_LNG),
    radius_km: float = Query(30.0),
    specialty: Optional[str] = Query(None),
    emergency_only: bool = Query(False)
):
    """Provides geo-coordinates for interactive Leaflet map markers"""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hospitals")
        all_facs = [dict(r) for r in cursor.fetchall()]

    markers = []
    for f in all_facs:
        d = haversine_km(lat, lng, f["latitude"], f["longitude"])
        if d <= radius_km:
            specs = json.loads(f["specialties"]) if isinstance(f["specialties"], str) else f["specialties"]
            if specialty and specialty != "All" and not any(specialty.lower() in s.lower() for s in specs):
                continue
            if emergency_only and f["emergency"] != 1:
                continue

            markers.append({
                "hospital_id": f["hospital_id"],
                "name": f["name"],
                "latitude": f["latitude"],
                "longitude": f["longitude"],
                "distance_km": d,
                "address": f["address"],
                "phone": f["contact_phone"],
                "emergency": bool(f["emergency"]),
                "cost_range": f["cost_range"],
                "specialties": specs
            })

    markers.sort(key=lambda m: m["distance_km"])
    return {
        "user_location": {"lat": lat, "lng": lng},
        "count": len(markers),
        "markers": markers
    }

@router.get("/emergency")
def get_emergency_facilities(
    lat: float = Query(DEFAULT_LAT),
    lng: float = Query(DEFAULT_LNG)
):
    """
    High-speed 🚨 EMERGENCY endpoint.
    Returns nearest verified emergency trauma centers and immediate hotlines.
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM emergency_facilities WHERE open_now = 1")
        rows = [dict(r) for r in cursor.fetchall()]

    for r in rows:
        r["distance_km"] = haversine_km(lat, lng, r["latitude"], r["longitude"])

    rows.sort(key=lambda r: r["distance_km"])

    national_helplines = [
        {"name": "National Emergency Number", "number": "112", "desc": "All-in-one emergency response"},
        {"name": "Medical Emergency & Ambulance", "number": "108", "desc": "Emergency medical technician dispatch"},
        {"name": "Senior Citizens Helpline", "number": "14567", "desc": "Elderly emergency assistance"},
        {"name": "Poison Control Center", "number": "1800 116 117", "desc": "National toxic exposure guidance"}
    ]

    return {
        "urgent_header": "🚨 EMERGENCY HEALTHCARE DISCOVERY",
        "emergency_disclaimer": "CRITICAL: If you are experiencing a life-threatening medical emergency (e.g. severe chest pain, stroke symptoms, uncontrolled bleeding), call 108/112 or seek immediate professional emergency medical care.",
        "nearest_facilities": rows[:6],
        "national_helplines": national_helplines
    }
