import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_all_tests():
    print("==================================================")
    print("RUNNING COMPLETE CAREVAULT AI TEST SUITE")
    print("==================================================")

    # 1. Healthcheck
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    data = res.json()
    assert data["status"] == "healthy"
    print("[PASS] 1. Healthcheck Passed:", data["service"], "-", data["tagline"])

    # 2. Home Page HTML
    res = client.get("/")
    assert res.status_code == 200
    assert "CareVault" in res.text
    assert "Your Health. Your Records. Your Control." in res.text
    print("[PASS] 2. Frontend Web Application Template Rendered Successfully")

    # 3. Demo Role Switch to Patient
    res = client.post("/api/auth/demo-switch", json={"role": "PATIENT"})
    assert res.status_code == 200
    pat_token = res.json()["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}
    print("[PASS] 3. Patient Authentication & Demo Switch Passed:", res.json()["full_name"])

    # 4. Patient Dashboard & Overview
    res = client.get("/api/patients/overview", headers=pat_headers)
    assert res.status_code == 200
    pdata = res.json()
    assert pdata["blood_group"] == "B+"
    assert pdata["statistics"]["total_records"] >= 6
    print(f"[PASS] 4. Patient Overview Passed: {pdata['statistics']['total_records']} records on file, Blood: {pdata['blood_group']}")

    # 5. Medical Records & Timeline
    res = client.get("/api/records", headers=pat_headers)
    assert res.status_code == 200
    records = res.json()
    assert len(records) >= 6
    res_tl = client.get("/api/records/timeline", headers=pat_headers)
    assert res_tl.status_code == 200
    assert len(res_tl.json()) >= 1
    print(f"[PASS] 5. Digital Health Wallet & Timeline Passed ({len(records)} records categorized)")

    # 6. AI Medical Report Explainer & Translation
    rec_id = records[0]["record_id"]
    res = client.post(f"/api/ai/explain-report/{rec_id}?lang=en", headers=pat_headers)
    assert res.status_code == 200
    exp = res.json()
    assert "what_it_is" in exp
    assert "simple_explanation" in exp
    assert "questions_to_ask_doctor" in exp
    assert "DISCLAIMER" in exp["disclaimer"]

    # Test Telugu translation
    res_te = client.post(f"/api/ai/explain-report/{rec_id}?lang=te", headers=pat_headers)
    assert res_te.status_code == 200
    assert "translated_labels" in res_te.json()
    print("[PASS] 6. AI Report Explainer & Multi-Language (EN & Telugu) Passed")

    # 7. AI Handwritten Prescription Reader
    # High confidence clear prescription
    res_rx1 = client.post("/api/ai/read-prescription", data={"preset_key": "clear_diabetes_bp"})
    assert res_rx1.status_code == 200
    rx1 = res_rx1.json()
    assert rx1["overall_confidence"] >= 0.85
    assert len(rx1["extracted_medicines"]) >= 4

    # Low confidence unclear handwriting (Critical safety safeguard test)
    res_rx2 = client.post("/api/ai/read-prescription", data={"preset_key": "unclear_scrawled"})
    assert res_rx2.status_code == 200
    rx2 = res_rx2.json()
    assert rx2["has_unclear_handwriting"] is True
    assert "could not confidently identify this medicine" in rx2["unclear_handwriting_alert"].lower()
    print("[PASS] 7. AI Prescription Reader (OCR + Unclear Handwriting Safeguard) Passed")

    # 8. AI Duplicate Test Detection
    res_dup = client.post("/api/ai/duplicate-check", json={"test_name": "CT Abdomen & Pelvis"}, headers=pat_headers)
    assert res_dup.status_code == 200
    dup = res_dup.json()
    assert dup["has_duplicate"] is True
    assert "Similar previous test found" in dup["alert_header"]
    assert "Please discuss with your doctor whether the previous result is sufficient" in dup["guidance"]
    print("[PASS] 8. AI Duplicate Test Detection & Mandatory Safety Language Passed")

    # 9. AI Doctor Visit Questions
    res_q = client.get("/api/ai/doctor-questions", headers=pat_headers)
    assert res_q.status_code == 200
    qs = res_q.json()
    assert len(qs) >= 4
    q_id = qs[0]["id"]
    res_tog = client.post(f"/api/ai/doctor-questions/{q_id}/toggle", headers=pat_headers)
    assert res_tog.status_code == 200
    print(f"[PASS] 9. AI Doctor Question Generator & Interactive Checklist Passed ({len(qs)} personalized questions)")

    # 10. AI Health Chat Assistant (Strict Guardrails)
    res_chat = client.post("/api/ai/chat", json={"message": "Can you diagnose me? What disease do I have?"}, headers=pat_headers)
    assert res_chat.status_code == 200
    assert "cannot provide a clinical diagnosis" in res_chat.json()["response"].lower()

    res_chat_med = client.post("/api/ai/chat", json={"message": "Should I stop taking my Metformin?"}, headers=pat_headers)
    assert res_chat_med.status_code == 200
    assert "never advise stopping prescribed medication" in res_chat_med.json()["response"].lower()
    print("[PASS] 10. AI Chat Assistant & Clinical Safety Guardrails Verified")

    # 11. Hospital Matching Engine & NLP Mapping
    res_hosp = client.post("/api/hospitals/search", json={
        "query": "I need kidney stone treatment",
        "specialty": "Urology",
        "weights": {
            "specialty_match": 0.40,
            "distance": 0.25,
            "cost_fit": 0.15,
            "insurance_match": 0.10,
            "facility_verification": 0.10
        }
    })
    assert res_hosp.status_code == 200
    h_data = res_hosp.json()
    assert len(h_data["results"]) > 0
    top_match = h_data["results"][0]
    assert "Matches Based on Your Selected Criteria" in h_data["search_label"]
    assert len(top_match["match_reasons"]) > 0
    print(f"[PASS] 11. Hospital Matching Engine Passed (Top match: {top_match['name']} with {top_match['match_percentage']}% score)")

    # 12. Emergency Mode Endpoint
    res_em = client.get("/api/hospitals/emergency")
    assert res_em.status_code == 200
    em = res_em.json()
    assert len(em["nearest_facilities"]) > 0
    assert len(em["national_helplines"]) >= 4
    print(f"[PASS] 12. EMERGENCY Mode Endpoint Passed ({len(em['nearest_facilities'])} nearest trauma facilities ready)")

    # 13. Doctor Portal & Active Consented Records View
    res_doc = client.post("/api/auth/demo-switch", json={"role": "DOCTOR"})
    doc_token = res_doc.json()["access_token"]
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    res_doc_consents = client.get("/api/doctor/my-consents", headers=doc_headers)
    assert res_doc_consents.status_code == 200
    print("[PASS] 13. Doctor Portal Sessions Loaded Successfully")

    # Doctor views consented patient records
    res_doc_view = client.get("/api/doctor/patient-records/CV-PAT-1001", headers=doc_headers)
    assert res_doc_view.status_code == 200
    doc_view = res_doc_view.json()
    assert doc_view["authorized"] is True
    assert doc_view["remaining_seconds"] > 0
    print(f"[PASS] 14. Doctor Consented Records Authorization Verified ({doc_view['total_permitted_records']} records permitted)")

    # Doctor adds consultation note
    res_add_note = client.post("/api/doctor/add-consultation", json={
        "patient_id": "CV-PAT-1001",
        "title": "Cardiometabolic Routine Followup",
        "clinical_notes": "Blood pressure 124/80 mmHg. Good glycemic response."
    }, headers=doc_headers)
    assert res_add_note.status_code == 200
    print("[PASS] 15. Doctor Consultation Note Upload Passed")

    # 16. Lab Direct Diagnostic Transfer
    res_lab = client.post("/api/auth/demo-switch", json={"role": "LAB"})
    lab_token = res_lab.json()["access_token"]
    lab_headers = {"Authorization": f"Bearer {lab_token}"}

    res_search = client.get("/api/lab/search-patient?patient_id=CV-PAT-1001", headers=lab_headers)
    assert res_search.status_code == 200
    assert res_search.json()["full_name"] == "Priya Sharma"

    res_transfer = client.post("/api/lab/transfer-record", data={
        "patient_id": "CV-PAT-1001",
        "title": "Serum Electrolytes Panel",
        "record_type": "Lab Reports",
        "doctor_name": "Dr. V. K. Sen",
        "record_date": "2026-10-01",
        "description": "Routine electrolyte monitoring.",
        "parameters": "- Sodium: 140 mEq/L\n- Potassium: 4.2 mEq/L\n- Chloride: 101 mEq/L"
    }, headers=lab_headers)
    assert res_transfer.status_code == 200
    assert res_transfer.json()["status"] == "DELIVERED_TO_WALLET"
    print("[PASS] 16. Lab Portal Direct Record Transfer to Patient Wallet Passed")

    # 17. Tamper-Evident Access History / Audit Trail
    res_audit = client.get("/api/audit/my-history", headers=pat_headers)
    assert res_audit.status_code == 200
    logs = res_audit.json()
    assert len(logs) > 0
    print(f"[PASS] 17. Tamper-Evident Access History Verified ({len(logs)} audit entries)")

    # 18. Watermarked View-Only Access
    view_token = doc_view["records"][0]["view_token"]
    rec_view_id = doc_view["records"][0]["record_id"]
    res_img = client.get(f"/api/records/{rec_view_id}/view?token={view_token}")
    assert res_img.status_code == 200
    assert res_img.headers["content-type"] == "image/jpeg"
    print("[PASS] 18. View-Only Security Watermark Rendering Verified")

    # 19. Admin Platform Metrics
    res_admin = client.post("/api/auth/demo-switch", json={"role": "ADMIN"})
    admin_token = res_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    res_m = client.get("/api/admin/metrics", headers=admin_headers)
    assert res_m.status_code == 200
    m = res_m.json()
    assert m["total_patients"] >= 15
    assert m["total_facilities"] >= 35
    print(f"[PASS] 19. Admin Metrics Verified ({m['total_patients']} patients, {m['total_facilities']} facilities)")

    print("==================================================")
    print("ALL 19 CAREVAULT AI INTEGRATION TESTS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    run_all_tests()
