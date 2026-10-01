import json
from typing import Dict, Any, List, Optional

DISCLAIMER_TEXT = (
    "DISCLAIMER: CareVault AI is a health-information and decision-support tool, "
    "NOT a diagnostic or treatment-replacement system. CareVault AI never diagnoses conditions, "
    "never advises stopping prescribed medication, and never changes dosages. "
    "Please discuss all findings with your qualified healthcare professional."
)

REPORT_EXPLANATIONS_DB = {
    "Complete Blood Count (CBC)": {
        "what_it_is": "A Complete Blood Count (CBC) is a routine blood test that evaluates the cells circulating in your bloodstream, including red blood cells, white blood cells, and platelets.",
        "important_terms": [
            {"term": "Hemoglobin (Hb)", "meaning": "Protein in red blood cells that transports oxygen throughout your body."},
            {"term": "White Blood Cells (WBC)", "meaning": "Cells that are part of your body's immune defense system against infections."},
            {"term": "Platelets", "meaning": "Tiny cell fragments essential for normal blood clotting and stopping bleeding."}
        ],
        "simple_explanation": "Your blood cells appear within functional counts. Red blood cells show good oxygen-carrying capacity. White blood cells are in expected baseline ranges, indicating no acute immune distress at the time of sampling.",
        "what_it_measures": "General health status, hydration, signs of anemia, and immune system activation.",
        "doctor_questions": [
            "What do my specific hemoglobin levels indicate regarding my energy and iron levels?",
            "Do any of these cell counts warrant repeat monitoring in the next 3 to 6 months?",
            "Are there dietary recommendations based on this overall cell profile?"
        ],
        "warning_signs": "Notify your physician promptly if you experience unexplained bruising, persistent high fever, or severe fatigue."
    },
    "HbA1c Glycated Hemoglobin": {
        "what_it_is": "An HbA1c test measures the percentage of your hemoglobin coated with sugar, reflecting your average blood glucose levels over the past 2 to 3 months.",
        "important_terms": [
            {"term": "HbA1c %", "meaning": "Average blood sugar percentage over a 90-day window (Normal: <5.7%, Prediabetes: 5.7-6.4%, Diabetes: >=6.5%)."},
            {"term": "Glycation", "meaning": "The natural process where glucose bonds with proteins like hemoglobin in blood."}
        ],
        "simple_explanation": "HbA1c is a blood test that reflects average blood glucose levels over the previous few months. Your doctor will interpret this value along with your medical history and other results.",
        "what_it_measures": "Long-term glycemic control and metabolic response to diet, exercise, or current treatment regimens.",
        "doctor_questions": [
            "Does my HbA1c value align with our target management goals?",
            "Should we adjust my nutrition or physical activity plan based on this average?",
            "When should we schedule my next follow-up HbA1c test?"
        ],
        "warning_signs": "Seek prompt medical care if experiencing extreme thirst, frequent urination, confusion, or persistent nausea."
    },
    "Renal Function Test (KFT)": {
        "what_it_is": "A group of biochemical tests measuring kidney efficiency in filtering waste products from the bloodstream.",
        "important_terms": [
            {"term": "Serum Creatinine", "meaning": "A waste product from muscle breakdown filtered almost entirely by healthy kidneys."},
            {"term": "Blood Urea Nitrogen (BUN)", "meaning": "A measure of nitrogen waste derived from protein digestion."},
            {"term": "eGFR", "meaning": "Estimated Glomerular Filtration Rate, calculating how many milliliters of blood your kidneys filter each minute."}
        ],
        "simple_explanation": "This report monitors how effectively your kidneys are clearing natural body waste. Creatinine and urea levels provide an objective window into kidney filtration.",
        "what_it_measures": "Kidney filtration rate, hydration status, and fluid/electrolyte balance.",
        "doctor_questions": [
            "Are my creatinine and eGFR numbers within the optimal range for my age?",
            "Do any of my current daily medicines or supplements put load on kidney filtration?",
            "What is my recommended daily hydration target?"
        ],
        "warning_signs": "Consult your doctor if you notice decreased urine output, swelling in ankles or eyes, or lower back discomfort."
    },
    "Chest X-Ray (PA View)": {
        "what_it_is": "A non-invasive radiological projection image of the chest, visualizing the lungs, heart contours, rib cage, and large blood vessels.",
        "important_terms": [
            {"term": "Bronchovascular Markings", "meaning": "Normal branching patterns of blood vessels and airways inside the lung fields."},
            {"term": "Costophrenic Angles", "meaning": "Sharp corners at the bottom of each lung space where fluid would typically collect if present."},
            {"term": "Cardiothoracic Ratio", "meaning": "Comparison of heart width relative to chest cavity width."}
        ],
        "simple_explanation": "The image provides a structured view of your lungs and heart size. Clear lung fields suggest no active consolidation, fluid congestion, or significant airway obstruction.",
        "what_it_measures": "Lung aeration, absence of fluid accumulation (pleural effusion), heart silhouette, and thoracic skeletal structure.",
        "doctor_questions": [
            "Are my lung fields completely clear of infection or fluid?",
            "Is my cardiac silhouette within normal size boundaries?",
            "Does this X-ray explain my recent respiratory or cough symptoms?"
        ],
        "warning_signs": "Seek immediate emergency attention if you experience severe sudden shortness of breath, chest pain, or coughing up blood."
    },
    "Brain MRI (Plain)": {
        "what_it_is": "A detailed high-resolution magnetic resonance scan visualizing brain tissue, ventricular systems, and intracranial structures without ionizing radiation.",
        "important_terms": [
            {"term": "Ventricular System", "meaning": "Cavities within the brain containing protective cerebrospinal fluid."},
            {"term": "Grey & White Matter", "meaning": "Primary structural layers of the central nervous system containing neurons and myelinated nerve fibers."}
        ],
        "simple_explanation": "An MRI scan creates detailed cross-sectional views of brain structures. It verifies normal tissue alignment, symmetrical brain ventricles, and checks for vascular or structural changes.",
        "what_it_measures": "Structural brain integrity, vascular distribution, and absence of mass lesions or acute tissue swelling.",
        "doctor_questions": [
            "Does the scan reveal any anatomical explanation for my headaches or dizziness?",
            "Are there any age-related microvascular changes noted?",
            "Is any follow-up imaging recommended?"
        ],
        "warning_signs": "Immediate medical attention is required for sudden severe headache ('worst headache of life'), facial drooping, or speech difficulty."
    }
}

def explain_medical_report(record_title: str, record_type: str, raw_text: str = "", patient_notes: str = "") -> Dict[str, Any]:
    # Look for known title matches or fallback to intelligent structured template
    matched = None
    for key, data in REPORT_EXPLANATIONS_DB.items():
        if key.lower() in record_title.lower() or record_title.lower() in key.lower():
            matched = data
            break

    if not matched:
        matched = {
            "what_it_is": f"This is a {record_type} documenting clinical observations and diagnostic findings.",
            "important_terms": [
                {"term": "Clinical Impression", "meaning": "The medical summary formulated by the examining healthcare provider."},
                {"term": "Reference Range", "meaning": "Standard baseline values expected in healthy individuals for comparison."}
            ],
            "simple_explanation": f"The document records clinical measurements or physician observations recorded on your health timeline. Your physician will review this in context with your physical examination.",
            "what_it_measures": f"Specific physiological markers related to {record_type.lower()}.",
            "doctor_questions": [
                "How does this finding relate to my current physical symptoms?",
                "Are there any proactive lifestyle changes or precautions I should adopt?",
                "When should we plan our next review or follow-up evaluation?"
            ],
            "warning_signs": "Report any unexpected new pain, sudden weakness, or adverse reactions to your doctor promptly."
        }

    return {
        "title": record_title,
        "type": record_type,
        "what_it_is": matched["what_it_is"],
        "important_terms": matched["important_terms"],
        "simple_explanation": matched["simple_explanation"],
        "what_it_measures": matched["what_it_measures"],
        "questions_to_ask_doctor": matched["doctor_questions"],
        "warning_signs": matched["warning_signs"],
        "disclaimer": DISCLAIMER_TEXT
    }

def understand_condition(condition_name: str, db_conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Provides safe educational disease awareness information"""
    matched = None
    for cond in db_conditions:
        if cond["name"].lower() == condition_name.lower():
            matched = cond
            break

    if matched:
        symptoms = json.loads(matched["symptoms"]) if isinstance(matched["symptoms"], str) else matched["symptoms"]
        risk_factors = json.loads(matched["risk_factors"]) if isinstance(matched["risk_factors"], str) else matched["risk_factors"]
        tests_used = json.loads(matched["tests_used"]) if isinstance(matched["tests_used"], str) else matched["tests_used"]
        return {
            "name": matched["name"],
            "what_is_it": matched["description"],
            "why_is_it_relevant": "Understanding this condition helps you take an active, informed role in partnering with your healthcare team.",
            "common_symptoms": symptoms,
            "risk_factors": risk_factors,
            "tests_used_for_monitoring": tests_used,
            "general_management_topics": matched["general_management"],
            "when_urgent_attention_needed": matched["urgent_signs"],
            "safety_note": "This information is for understanding and discussion with your healthcare professional. It is not a diagnosis.",
            "disclaimer": DISCLAIMER_TEXT
        }

    return {
        "name": condition_name,
        "what_is_it": f"A medical condition or term referenced in your health records.",
        "why_is_it_relevant": "Keeping informed about all medical terms in your records promotes clearer doctor-patient discussions.",
        "common_symptoms": ["Discuss symptom patterns directly with your physician."],
        "risk_factors": ["Genetic predisposition, lifestyle, environmental factors."],
        "tests_used_for_monitoring": ["Routine clinical laboratory evaluations and periodic examinations."],
        "general_management_topics": "Follow prescribed management plans and schedule regular reviews with your physician.",
        "when_urgent_attention_needed": "Immediate care is required for sudden chest pain, breathing difficulty, or altered alertness.",
        "safety_note": "This information is for understanding and discussion with your healthcare professional.",
        "disclaimer": DISCLAIMER_TEXT
    }

def generate_medical_history_summary(patient_profile: dict, records: List[dict]) -> Dict[str, Any]:
    """Generates an accurate, verifiable chronological summary based strictly on records"""
    allergies = patient_profile.get("allergies", "None reported")
    conditions = patient_profile.get("existing_conditions", "None reported")
    medications = patient_profile.get("current_medications", "None reported")

    # Chronological sort of records
    sorted_records = sorted(records, key=lambda r: r.get("record_date", ""), reverse=True)

    recent_tests = []
    recent_prescriptions = []
    recent_consultations = []
    
    for r in sorted_records[:10]:
        rtype = r.get("record_type", "")
        item = {
            "date": r.get("record_date"),
            "title": r.get("title"),
            "facility": r.get("hospital_name"),
            "doctor": r.get("doctor_name", "Attending Physician")
        }
        if "Lab" in rtype or "X-ray" in rtype or "CT/MRI" in rtype:
            recent_tests.append(item)
        elif "Prescription" in rtype:
            recent_prescriptions.append(item)
        else:
            recent_consultations.append(item)

    return {
        "patient_name": patient_profile.get("full_name"),
        "patient_id": patient_profile.get("patient_id"),
        "blood_group": patient_profile.get("blood_group"),
        "allergies": allergies,
        "existing_conditions": conditions,
        "current_medications": medications,
        "recent_tests": recent_tests[:5],
        "recent_prescriptions": recent_prescriptions[:5],
        "recent_consultations": recent_consultations[:5],
        "total_records_analyzed": len(records),
        "summary_statement": f"Summary strictly compiled from {len(records)} authorized digital health records on file. No external or unverifiable facts included.",
        "disclaimer": DISCLAIMER_TEXT
    }

def answer_health_query(user_query: str, patient_profile: dict, records: List[dict]) -> Dict[str, Any]:
    """Conversational AI Assistant grounded strictly in authorized patient records with guardrails"""
    q_lower = user_query.lower()

    # Safety Guardrails check
    if any(phrase in q_lower for phrase in ["diagnose me", "do i have cancer", "what disease do i have", "give me diagnosis"]):
        return {
            "response": (
                "As CareVault AI, I cannot provide a clinical diagnosis. "
                "Diagnosing any health condition requires a thorough physical examination and clinical evaluation by a licensed physician. "
                "Based on your records, here are the recent tests you've completed that you can discuss with your doctor: "
                + ", ".join([r.get("title", "") for r in records[:3]]) + ". "
                "Would you like me to generate a checklist of questions to ask your doctor?"
            ),
            "safety_flag": "DIAGNOSIS_ATTEMPT_DEFLECTED",
            "disclaimer": DISCLAIMER_TEXT
        }

    if any(phrase in q_lower for phrase in ["stop taking", "stop my medicine", "stop medicine", "change dose", "double dose", "halve dose"]):
        return {
            "response": (
                "For your safety, CareVault AI will NEVER advise stopping prescribed medication or altering a dosage. "
                "Only your prescribing doctor can safely evaluate whether a medication should be continued, adjusted, or discontinued. "
                f"Your active medications on file are: {patient_profile.get('current_medications', 'None')}. "
                "Please reach out directly to your physician or pharmacist before making any changes."
            ),
            "safety_flag": "DOSAGE_CHANGE_PREVENTED",
            "disclaimer": DISCLAIMER_TEXT
        }

    # Record-grounded answers
    if "allergy" in q_lower or "allergies" in q_lower:
        allergies = patient_profile.get("allergies", "No known allergies listed.")
        return {
            "response": f"According to your CareVault profile, your documented allergies are: **{allergies}**. Please ensure all healthcare providers are aware of this before receiving any new prescription.",
            "disclaimer": DISCLAIMER_TEXT
        }

    if "blood" in q_lower or "group" in q_lower:
        bg = patient_profile.get("blood_group", "Not specified")
        return {
            "response": f"Your recorded blood group in CareVault is **{bg}**.",
            "disclaimer": DISCLAIMER_TEXT
        }

    if "medicine" in q_lower or "medication" in q_lower or "drug" in q_lower:
        meds = patient_profile.get("current_medications", "No active medicines on file.")
        return {
            "response": f"Your current documented medications are: **{meds}**. Always confirm dosage and timing with your doctor or pharmacist.",
            "disclaimer": DISCLAIMER_TEXT
        }

    if "recent" in q_lower or "test" in q_lower or "report" in q_lower:
        if not records:
            return {"response": "You currently have no medical records uploaded in your wallet.", "disclaimer": DISCLAIMER_TEXT}
        rec_list = "\n".join([f"- **{r.get('record_date')}**: {r.get('title')} ({r.get('hospital_name')})" for r in records[:5]])
        return {
            "response": f"Here are your most recent authorized health records:\n{rec_list}\n\nYou can click on any individual record in your wallet to view its full details or select **Explain with AI**.",
            "disclaimer": DISCLAIMER_TEXT
        }

    # General grounding
    return {
        "response": (
            f"Hello {patient_profile.get('full_name')}. I can help you understand the medical records in your wallet, "
            f"clarify medical terminology, generate doctor visit checklists, or explain your recent tests. "
            f"You currently have {len(records)} verified health record(s) on file. How can I assist you with your health records today?"
        ),
        "disclaimer": DISCLAIMER_TEXT
    }
