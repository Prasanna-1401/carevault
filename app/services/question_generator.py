from typing import List, Dict, Any

STANDARD_DOCTOR_QUESTIONS = [
    {"question": "What do these recent test findings mean for my overall health?", "category": "Results & Interpretation"},
    {"question": "What potential factors or daily habits could be contributing to these numbers?", "category": "Causes & Lifestyle"},
    {"question": "Do I need any additional diagnostic tests or imaging at this point?", "category": "Diagnostics"},
    {"question": "Is my previous test still relevant for our current clinical assessment, or is a repeat necessary?", "category": "Test Repetition"},
    {"question": "What treatment or management options do you recommend considering my medical history?", "category": "Treatment Options"},
    {"question": "What are the common benefits and potential side effects of this course of action?", "category": "Risks & Benefits"},
    {"question": "What specific symptoms or health markers should I actively monitor at home?", "category": "Self-Monitoring"},
    {"question": "When should we plan our next follow-up appointment or review?", "category": "Follow-Up"},
    {"question": "What specific warning signs or symptoms would require immediate emergency attention?", "category": "Emergency Precautions"}
]

def generate_doctor_questions_for_patient(patient_profile: dict, records: List[dict]) -> List[Dict[str, Any]]:
    """
    Generates personalized doctor questions based on patient's records, conditions, and allergies.
    """
    questions = list(STANDARD_DOCTOR_QUESTIONS)

    # Contextual questions based on existing conditions
    conditions = patient_profile.get("existing_conditions", "")
    if "diabetes" in conditions.lower():
        questions.insert(2, {
            "question": "How are my current blood glucose trends affecting my long-term kidney and cardiovascular health?",
            "category": "Condition Specific (Diabetes)"
        })
    if "hypertension" in conditions.lower() or "bp" in conditions.lower():
        questions.insert(3, {
            "question": "Is my current blood pressure target adequately controlled, and what home monitoring schedule do you suggest?",
            "category": "Condition Specific (Hypertension)"
        })

    # Contextual questions based on recent records
    for r in records[:3]:
        title = r.get("title", "")
        if "HbA1c" in title:
            questions.insert(1, {
                "question": f"Regarding my {title} report, does my 3-month average require any modification in my diet or medication?",
                "category": "Recent Lab Report"
            })
            break
        elif "Renal" in title or "Kidney" in title:
            questions.insert(1, {
                "question": f"Regarding my {title} report, are my filtration values stable compared to my baseline?",
                "category": "Recent Lab Report"
            })
            break

    # Add id and initial checked state
    result = []
    for i, q in enumerate(questions):
        result.append({
            "id": i + 1,
            "question_text": q["question"],
            "category": q["category"],
            "is_checked": False,
            "is_custom": False
        })
    return result
