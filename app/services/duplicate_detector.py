from datetime import datetime
from typing import List, Dict, Any, Optional

DUPLICATE_ALERT_HEADER = "⚠️ Similar previous test found."
DUPLICATE_MANDATORY_DISCLAIMER = (
    "A similar recent test was found. "
    "Please discuss with your doctor whether the previous result is sufficient "
    "for the current clinical purpose or whether repeating the test is necessary."
)

# Clinical observation windows (days within which a repeated test is flagged for clinical discussion)
CLINICAL_WINDOWS_DAYS = {
    "cbc": 14,
    "complete blood count": 14,
    "hemoglobin": 14,
    "hba1c": 60,
    "glycated hemoglobin": 60,
    "lipid profile": 45,
    "cholesterol": 45,
    "kidney function": 30,
    "renal function": 30,
    "kft": 30,
    "creatinine": 30,
    "liver function": 30,
    "lft": 30,
    "chest x-ray": 30,
    "x-ray": 30,
    "ct scan": 60,
    "ct abdomen": 60,
    "ct head": 60,
    "mri": 90,
    "mri brain": 90,
    "ultrasound": 45,
    "ecg": 14,
    "electrocardiogram": 14,
    "thyroid": 60,
    "tsh": 60
}

def parse_date(date_str: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            pass
    return None

def check_duplicate_test(test_name: str, new_test_date: str, previous_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Scans patient's previous records for matching tests within the relevant clinical window.
    Strictly follows the prompt's mandated language and safety rules.
    """
    clean_test = test_name.lower().strip()
    new_dt = parse_date(new_test_date) or datetime.now()

    # Determine recommended clinical window
    window_days = 30
    for key, days in CLINICAL_WINDOWS_DAYS.items():
        if key in clean_test:
            window_days = days
            break

    matches = []
    for rec in previous_records:
        rec_title = rec.get("title", "").lower()
        rec_date_str = rec.get("record_date", "")
        rec_dt = parse_date(rec_date_str)

        # Name / keyword match
        is_match = False
        if clean_test in rec_title or rec_title in clean_test:
            is_match = True
        else:
            # Check key tokens
            tokens = [t for t in clean_test.replace("(", " ").replace(")", " ").split() if len(t) > 2]
            if any(t in rec_title for t in tokens):
                is_match = True

        if is_match and rec_dt:
            delta = abs((new_dt - rec_dt).days)
            if delta <= window_days:
                matches.append({
                    "record_id": rec.get("record_id"),
                    "title": rec.get("title"),
                    "hospital": rec.get("hospital_name"),
                    "doctor": rec.get("doctor_name"),
                    "previous_date": rec_date_str,
                    "days_ago": delta,
                    "window_threshold_days": window_days
                })

    if matches:
        # Sort by most recent
        matches.sort(key=lambda m: m["days_ago"])
        primary_match = matches[0]
        days_ago = primary_match["days_ago"]
        time_str = "today" if days_ago == 0 else f"{days_ago} day(s) ago"

        return {
            "has_duplicate": True,
            "alert_header": DUPLICATE_ALERT_HEADER,
            "summary": f"{primary_match['title']} was recorded {time_str} at {primary_match['hospital']}.",
            "guidance": DUPLICATE_MANDATORY_DISCLAIMER,
            "matched_records": matches,
            "safety_note": "CareVault AI never tells you a test is unnecessary. Your doctor will make the final clinical decision."
        }

    return {
        "has_duplicate": False,
        "alert_header": None,
        "summary": "No recent similar test found in your CareVault records within the typical clinical window.",
        "guidance": "Always follow your doctor's specific recommendations for diagnostic testing.",
        "matched_records": []
    }
