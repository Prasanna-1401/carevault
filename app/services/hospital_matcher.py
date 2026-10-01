import math
import json
from typing import List, Dict, Any, Optional

DEFAULT_WEIGHTS = {
    "specialty_match": 0.40,
    "distance": 0.25,
    "cost_fit": 0.15,
    "insurance_match": 0.10,
    "facility_verification": 0.10
}

NLP_SPECIALTY_MAPPINGS = {
    "kidney stone": {"specialty": "Urology", "services": ["Lithotripsy", "Laser Ureteroscopy", "Nephrology Consultation"]},
    "kidney": {"specialty": "Nephrology", "services": ["Dialysis", "Renal Biopsy", "Kidney Function Evaluation"]},
    "heart": {"specialty": "Cardiology", "services": ["Angioplasty", "Echocardiogram", "Cardiac ICU"]},
    "chest pain": {"specialty": "Cardiology", "services": ["Emergency Cardiac Care", "ECG", "Troponin T"]},
    "knee pain": {"specialty": "Orthopedics", "services": ["Joint Replacement", "Arthroscopy", "Physiotherapy"]},
    "fracture": {"specialty": "Orthopedics", "services": ["Trauma Surgery", "Plaster Cast", "X-Ray"]},
    "headache": {"specialty": "Neurology", "services": ["Brain MRI", "EEG", "Migraine Clinic"]},
    "stroke": {"specialty": "Neurology", "services": ["Stroke Unit", "CT Angiography", "Neuro ICU"]},
    "fever": {"specialty": "General Medicine", "services": ["Infectious Disease Care", "CBC Testing", "IV Therapy"]},
    "diabetes": {"specialty": "Endocrinology", "services": ["Diabetic Foot Clinic", "HbA1c Monitoring", "Insulin Titration"]},
    "eye": {"specialty": "Ophthalmology", "services": ["Cataract Surgery", "Retina Laser", "Vision Check"]},
    "cancer": {"specialty": "Oncology", "services": ["Chemotherapy", "Radiation Oncology", "PET-CT"]},
    "pregnancy": {"specialty": "Obstetrics & Gynecology", "services": ["Labor Delivery", "Ultrasound Antenatal", "NICU"]},
    "child": {"specialty": "Pediatrics", "services": ["Pediatric ICU", "Vaccination", "Child Wellness"]}
}

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in kilometers"""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def map_natural_query(query: str) -> Dict[str, Any]:
    """Maps a user query like 'I need kidney stone treatment' to specialty and service category"""
    q = query.lower()
    matched_specialty = "General Medicine"
    matched_services = []

    for phrase, mapping in NLP_SPECIALTY_MAPPINGS.items():
        if phrase in q:
            matched_specialty = mapping["specialty"]
            matched_services = mapping["services"]
            break

    return {
        "query": query,
        "mapped_specialty": matched_specialty,
        "mapped_services": matched_services,
        "inferred_intent": f"Targeting facilities with {matched_specialty} departments."
    }

def rank_facilities(
    facilities: List[Dict[str, Any]],
    user_lat: float,
    user_lng: float,
    query: Optional[str] = None,
    desired_specialty: Optional[str] = None,
    desired_cost: Optional[str] = None,
    desired_insurance: Optional[str] = None,
    weights: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    Ranks hospitals based on transparent criteria and returns 'Best matches based on your selected criteria'.
    Never calls any hospital 'the best hospital'.
    """
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    # Normalize weights so they sum to 1.0
    total_w = sum(w.values()) or 1.0
    for k in w:
        w[k] = w[k] / total_w

    mapped_intent = None
    target_specialty = desired_specialty
    target_services = []

    if query:
        intent = map_natural_query(query)
        mapped_intent = intent
        if not target_specialty or target_specialty == "All":
            target_specialty = intent["mapped_specialty"]
            target_services = intent["mapped_services"]

    ranked = []

    for fac in facilities:
        reasons = []
        specs = json.loads(fac["specialties"]) if isinstance(fac["specialties"], str) else fac["specialties"]
        servs = json.loads(fac["services"]) if isinstance(fac["services"], str) else fac["services"]
        ins = json.loads(fac["insurance_schemes"]) if isinstance(fac["insurance_schemes"], str) else fac["insurance_schemes"]

        # 1. Specialty / Service Score (0.0 to 1.0)
        spec_score = 0.5  # Baseline
        if target_specialty and any(target_specialty.lower() in s.lower() for s in specs):
            spec_score = 1.0
            reasons.append(f"✓ {target_specialty} department available")
        elif target_specialty:
            spec_score = 0.2

        if any(ts.lower() in " ".join(servs).lower() for ts in target_services):
            spec_score = min(1.0, spec_score + 0.2)
            matched_serv = [ts for ts in target_services if ts.lower() in " ".join(servs).lower()]
            if matched_serv:
                reasons.append(f"✓ Offers specialized service: {matched_serv[0]}")

        # 2. Distance Score (0.0 to 1.0)
        dist_km = haversine_km(user_lat, user_lng, fac["latitude"], fac["longitude"])
        # Decay: 0 km -> 1.0, 10 km -> 0.7, 30 km -> 0.3, >50 km -> 0.1
        dist_score = max(0.05, 1.0 - (dist_km / 35.0))
        reasons.append(f"✓ Located {dist_km} km away")

        # 3. Cost Fit (0.0 to 1.0)
        cost_tier = fac.get("cost_range", "$$")
        cost_score = 0.7
        if desired_cost:
            if desired_cost == cost_tier:
                cost_score = 1.0
                reasons.append(f"✓ Matches requested cost tier ({cost_tier})")
            elif len(desired_cost) >= len(cost_tier):
                cost_score = 0.8
                reasons.append(f"✓ Within affordable cost range ({cost_tier})")
            else:
                cost_score = 0.4
        else:
            reasons.append(f"✓ Cost tier: {cost_tier}")

        # 4. Insurance / Scheme Match (0.0 to 1.0)
        ins_score = 0.6
        if desired_insurance and desired_insurance != "None":
            if any(desired_insurance.lower() in i.lower() for i in ins):
                ins_score = 1.0
                reasons.append(f"✓ Empanelled with {desired_insurance}")
            else:
                ins_score = 0.2
        elif ins:
            reasons.append(f"✓ Accepts {len(ins)} insurance scheme(s)")

        # 5. Verification & Emergency
        ver_score = 1.0 if fac.get("verification_status") in ("VERIFIED", "VERIFIED_SYNTHETIC") else 0.5
        if fac.get("emergency") == 1:
            reasons.append("✓ 24/7 Emergency & Trauma services active")

        # Total Composite Match Score
        total_score = (
            spec_score * w["specialty_match"] +
            dist_score * w["distance"] +
            cost_score * w["cost_fit"] +
            ins_score * w["insurance_match"] +
            ver_score * w["facility_verification"]
        )
        match_percentage = int(min(100, max(20, round(total_score * 100))))

        item = dict(fac)
        item["distance_km"] = dist_km
        item["match_percentage"] = match_percentage
        item["match_reasons"] = reasons
        item["specialties_list"] = specs
        item["services_list"] = servs
        item["insurance_list"] = ins
        ranked.append(item)

    ranked.sort(key=lambda x: x["match_percentage"], reverse=True)
    return ranked
