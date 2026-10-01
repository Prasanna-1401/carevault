import json
from datetime import datetime, timedelta, timezone
from app.database import db_session, init_db
from app.security import hash_password
from app.storage import save_document, create_synthetic_document_image
from app.services.prescription_reader import generate_prescription_image_sample

def seed_database():
    init_db()

    with db_session() as conn:
        cursor = conn.cursor()

        # Check if already seeded
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            print("Database already seeded. Skipping initial seed.")
            return

        print("Seeding CareVault AI with realistic synthetic demo data...")

        default_pw = hash_password("patient123")
        doctor_pw = hash_password("doctor123")
        lab_pw = hash_password("lab123")
        admin_pw = hash_password("admin123")

        # 1. Seed Users and Patients (15 synthetic patients)
        patients_data = [
            {
                "email": "priya.sharma@example.com", "name": "Priya Sharma", "mobile": "+91 98201 12345",
                "patient_id": "CV-PAT-1001", "dob": "1991-04-14", "gender": "Female", "blood_group": "B+",
                "allergies": "Penicillin, Sulfa drugs", "conditions": "Type 2 Diabetes Mellitus, Mild Hypertension",
                "medications": "Metformin 500mg (1-0-1), Amlodipine 5mg (1-0-0), Atorvastatin 20mg (0-0-1)",
                "lang": "English", "ec_name": "Vikram Sharma", "ec_phone": "+91 98201 54321", "ec_rel": "Spouse"
            },
            {
                "email": "rohan.verma@example.com", "name": "Rohan Verma", "mobile": "+91 98202 23456",
                "patient_id": "CV-PAT-1002", "dob": "1985-08-22", "gender": "Male", "blood_group": "O+",
                "allergies": "Aspirin, NSAIDs", "conditions": "Kidney Stones (Nephrolithiasis), Dyslipidemia",
                "medications": "Rosuvastatin 10mg (0-0-1), Potassium Citrate Syrup",
                "lang": "Hindi", "ec_name": "Neha Verma", "ec_phone": "+91 98202 65432", "ec_rel": "Sister"
            },
            {
                "email": "ananya.iyer@example.com", "name": "Ananya Iyer", "mobile": "+91 98203 34567",
                "patient_id": "CV-PAT-1003", "dob": "1996-11-03", "gender": "Female", "blood_group": "A+",
                "allergies": "No known drug allergies", "conditions": "Iron Deficiency Anemia",
                "medications": "Ferrous Ascorbate 100mg (1-0-0), Folic Acid 5mg",
                "lang": "Tamil", "ec_name": "S. Iyer", "ec_phone": "+91 98203 76543", "ec_rel": "Father"
            },
            {
                "email": "vikram.malhotra@example.com", "name": "Vikram Malhotra", "mobile": "+91 98204 45678",
                "patient_id": "CV-PAT-1004", "dob": "1978-02-18", "gender": "Male", "blood_group": "AB+",
                "allergies": "Shellfish, Contrast Dye", "conditions": "Coronary Artery Disease, Hypertension",
                "medications": "Aspirin 75mg (0-1-0), Clopidogrel 75mg, Telmisartan 40mg",
                "lang": "English", "ec_name": "Ritu Malhotra", "ec_phone": "+91 98204 87654", "ec_rel": "Spouse"
            },
            {
                "email": "sunita.patil@example.com", "name": "Sunita Patil", "mobile": "+91 98205 56789",
                "patient_id": "CV-PAT-1005", "dob": "1969-07-29", "gender": "Female", "blood_group": "O-",
                "allergies": "Codeine", "conditions": "Osteoarthritis, Hypothyroidism",
                "medications": "Levothyroxine 50mcg (1-0-0 fasting), Calcium + Vit D3",
                "lang": "Marathi", "ec_name": "Ajay Patil", "ec_phone": "+91 98205 98765", "ec_rel": "Son"
            },
            {
                "email": "rajesh.kumar@example.com", "name": "Rajesh Kumar", "mobile": "+91 98206 67890",
                "patient_id": "CV-PAT-1006", "dob": "1983-05-12", "gender": "Male", "blood_group": "B-",
                "allergies": "None", "conditions": "Bronchial Asthma",
                "medications": "Budesonide + Formoterol Inhaler (1 puff BD)",
                "lang": "Hindi", "ec_name": "Kavita Kumar", "ec_phone": "+91 98206 09876", "ec_rel": "Spouse"
            },
            {
                "email": "sneha.reddy@example.com", "name": "Sneha Reddy", "mobile": "+91 98207 78901",
                "patient_id": "CV-PAT-1007", "dob": "1993-09-15", "gender": "Female", "blood_group": "A-",
                "allergies": "Ibuprofen", "conditions": "Migraine, Cervical Spondylosis",
                "medications": "Propranolol 40mg (1-0-0), Naproxen (SOS)",
                "lang": "Telugu", "ec_name": "K. Reddy", "ec_phone": "+91 98207 10987", "ec_rel": "Mother"
            },
            {
                "email": "amit.banerjee@example.com", "name": "Amit Banerjee", "mobile": "+91 98208 89012",
                "patient_id": "CV-PAT-1008", "dob": "1972-12-05", "gender": "Male", "blood_group": "O+",
                "allergies": "Amoxicillin", "conditions": "Chronic Kidney Disease Stage 2, Hypertension",
                "medications": "Torsemide 10mg (1-0-0), Sodium Bicarbonate",
                "lang": "Bengali", "ec_name": "Debjani Banerjee", "ec_phone": "+91 98208 21098", "ec_rel": "Spouse"
            },
            {
                "email": "meera.nair@example.com", "name": "Meera Nair", "mobile": "+91 98209 90123",
                "patient_id": "CV-PAT-1009", "dob": "1988-03-24", "gender": "Female", "blood_group": "AB-",
                "allergies": "Latex", "conditions": "Polycystic Ovary Syndrome (PCOS)",
                "medications": "Inositol + Folic acid, Metformin 500mg",
                "lang": "Malayalam", "ec_name": "Arun Nair", "ec_phone": "+91 98209 32109", "ec_rel": "Brother"
            },
            {
                "email": "deepak.joshi@example.com", "name": "Deepak Joshi", "mobile": "+91 98210 01234",
                "patient_id": "CV-PAT-1010", "dob": "1981-10-10", "gender": "Male", "blood_group": "B+",
                "allergies": "None", "conditions": "Fatty Liver Grade 1, High Triglycerides",
                "medications": "Saroglitazar 4mg, Vitamin E",
                "lang": "Kannada", "ec_name": "Pooja Joshi", "ec_phone": "+91 98210 43210", "ec_rel": "Spouse"
            },
            {
                "email": "kavita.deshmukh@example.com", "name": "Kavita Deshmukh", "mobile": "+91 98211 11223",
                "patient_id": "CV-PAT-1011", "dob": "1975-06-19", "gender": "Female", "blood_group": "O+",
                "allergies": "Ciprofloxacin", "conditions": "Rheumatoid Arthritis",
                "medications": "Methotrexate 10mg weekly, Hydroxychloroquine 200mg",
                "lang": "Marathi", "ec_name": "Sanjay Deshmukh", "ec_phone": "+91 98211 55667", "ec_rel": "Spouse"
            },
            {
                "email": "tariq.ahmed@example.com", "name": "Tariq Ahmed", "mobile": "+91 98212 22334",
                "patient_id": "CV-PAT-1012", "dob": "1990-01-30", "gender": "Male", "blood_group": "A+",
                "allergies": "None", "conditions": "Allergic Rhinitis, GERD",
                "medications": "Levocetirizine + Montelukast, Esomeprazole 40mg",
                "lang": "Hindi", "ec_name": "Fatima Ahmed", "ec_phone": "+91 98212 66778", "ec_rel": "Spouse"
            },
            {
                "email": "geetha.krishnan@example.com", "name": "Geetha Krishnan", "mobile": "+91 98213 33445",
                "patient_id": "CV-PAT-1013", "dob": "1965-09-08", "gender": "Female", "blood_group": "B+",
                "allergies": "Iodine contrast", "conditions": "Glaucoma, Hypertension",
                "medications": "Timolol eye drops (0.5%), Olmesartan 20mg",
                "lang": "Tamil", "ec_name": "R. Krishnan", "ec_phone": "+91 98213 77889", "ec_rel": "Spouse"
            },
            {
                "email": "manpreet.singh@example.com", "name": "Manpreet Singh", "mobile": "+91 98214 44556",
                "patient_id": "CV-PAT-1014", "dob": "1987-04-02", "gender": "Male", "blood_group": "O+",
                "allergies": "None", "conditions": "Lumbar Disc Bulge L4-L5",
                "medications": "Pregabalin 75mg, Methylcobalamin",
                "lang": "English", "ec_name": "Harleen Kaur", "ec_phone": "+91 98214 88990", "ec_rel": "Spouse"
            },
            {
                "email": "radha.mukherjee@example.com", "name": "Radha Mukherjee", "mobile": "+91 98215 55667",
                "patient_id": "CV-PAT-1015", "dob": "1994-12-14", "gender": "Female", "blood_group": "A+",
                "allergies": "Sulfa drugs", "conditions": "Hypothyroidism",
                "medications": "Levothyroxine 75mcg",
                "lang": "Bengali", "ec_name": "Subhash Mukherjee", "ec_phone": "+91 98215 99001", "ec_rel": "Father"
            }
        ]

        for p in patients_data:
            cursor.execute("""
            INSERT INTO users (email, password_hash, role, full_name, mobile)
            VALUES (?, ?, 'PATIENT', ?, ?)
            """, (p["email"], default_pw, p["name"], p["mobile"]))
            user_id = cursor.lastrowid

            cursor.execute("""
            INSERT INTO patients (
                user_id, patient_id, dob, gender, blood_group, allergies,
                existing_conditions, current_medications, preferred_language,
                emergency_contact_name, emergency_contact_phone, emergency_contact_relation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, p["patient_id"], p["dob"], p["gender"], p["blood_group"],
                p["allergies"], p["conditions"], p["medications"], p["lang"],
                p["ec_name"], p["ec_phone"], p["ec_rel"]
            ))

        # 2. Seed Doctors / Providers
        doctors_data = [
            {
                "email": "dr.mehta@example.com", "name": "Dr. Rajesh Mehta, MD (Cardio)",
                "mobile": "+91 98111 22334", "provider_id": "CV-DOC-2001", "specialty": "Cardiology",
                "hospital_id": "CV-HOSP-01", "hospital_name": "Apollo Health City Hospital", "license": "MCI-48291"
            },
            {
                "email": "dr.sen@example.com", "name": "Dr. V. K. Sen, MBBS, DNB",
                "mobile": "+91 98111 33445", "provider_id": "CV-DOC-2002", "specialty": "General Medicine",
                "hospital_id": "CV-HOSP-02", "hospital_name": "Metro MultiSpecialty Hospital", "license": "MCI-31902"
            },
            {
                "email": "dr.kapoor@example.com", "name": "Dr. Sunita Kapoor, MS (Urology)",
                "mobile": "+91 98111 44556", "provider_id": "CV-DOC-2003", "specialty": "Urology",
                "hospital_id": "CV-HOSP-03", "hospital_name": "Max Super Specialty Hospital", "license": "MCI-62910"
            },
            {
                "email": "dr.patel@example.com", "name": "Dr. Anand Patel, MD (Endocrinology)",
                "mobile": "+91 98111 55667", "provider_id": "CV-DOC-2004", "specialty": "Endocrinology",
                "hospital_id": "CV-HOSP-04", "hospital_name": "Fortis Memorial Healthcare Institute", "license": "MCI-71822"
            }
        ]

        for d in doctors_data:
            cursor.execute("""
            INSERT INTO users (email, password_hash, role, full_name, mobile)
            VALUES (?, ?, 'DOCTOR', ?, ?)
            """, (d["email"], doctor_pw, d["name"], d["mobile"]))
            u_id = cursor.lastrowid
            cursor.execute("""
            INSERT INTO providers (user_id, provider_id, name, specialty, hospital_id, hospital_name, license_number, verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (u_id, d["provider_id"], d["name"], d["specialty"], d["hospital_id"], d["hospital_name"], d["license"]))

        # 3. Seed Diagnostic Labs
        labs_data = [
            {
                "email": "lab@apexdiagnostics.com", "name": "Apex Central Diagnostics & Pathology",
                "mobile": "+91 1800 200 4455", "lab_id": "CV-LAB-3001", "license": "NABL-9281-EXP",
                "address": "Plot 42, Healthcare Corridor, Sector 18"
            },
            {
                "email": "lab@metroscan.com", "name": "Metro Advanced Imaging & Scan Center",
                "mobile": "+91 1800 200 5566", "lab_id": "CV-LAB-3002", "license": "NABL-7412-EXP",
                "address": "Building 5, Medical Enclave, Ring Road"
            }
        ]

        for l in labs_data:
            cursor.execute("""
            INSERT INTO users (email, password_hash, role, full_name, mobile)
            VALUES (?, ?, 'LAB', ?, ?)
            """, (l["email"], lab_pw, l["name"], l["mobile"]))
            u_id = cursor.lastrowid
            cursor.execute("""
            INSERT INTO labs (user_id, lab_id, name, license_number, address, contact_phone)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (u_id, l["lab_id"], l["name"], l["license"], l["address"], l["mobile"]))

        # 4. Seed Admin
        cursor.execute("""
        INSERT INTO users (email, password_hash, role, full_name, mobile)
        VALUES ('admin@carevault.ai', ?, 'ADMIN', 'CareVault System Administrator', '+91 99999 00000')
        """, (admin_pw,))

        # 5. Seed 35 Synthetic Hospitals, Clinics & Diagnostic Centers
        hospitals_data = [
            {
                "id": "CV-HOSP-01", "name": "Apollo Health City Hospital",
                "address": "Road No 72, Jubilee Hills, Hyderabad", "lat": 17.4325, "lng": 78.4071,
                "specialties": ["Cardiology", "Urology", "Oncology", "Neurology", "Emergency"],
                "services": ["Lithotripsy", "Angioplasty", "Robotic Surgery", "24/7 Trauma", "MRI 3T", "Laser Ureteroscopy"],
                "emergency": 1, "hours": "24/7", "cost": "$$$",
                "insurance": ["Star Health", "Ayushman Bharat", "HDFC ERGO", "CGHS", "Max Bupa"],
                "phone": "+91 40 2360 7777", "email": "emergency@apollohyd.synthetic.care"
            },
            {
                "id": "CV-HOSP-02", "name": "Metro MultiSpecialty Hospital",
                "address": "Sector 11, Medical District, Hyderabad", "lat": 17.4380, "lng": 78.4210,
                "specialties": ["General Medicine", "Pediatrics", "Orthopedics", "Gynecology"],
                "services": ["CBC Testing", "Ultrasound", "Joint Replacement", "Maternity Delivery"],
                "emergency": 1, "hours": "24/7", "cost": "$$",
                "insurance": ["Ayushman Bharat", "CGHS", "ICICI Lombard", "United India"],
                "phone": "+91 40 2375 8888", "email": "care@metrohosp.synthetic.care"
            },
            {
                "id": "CV-HOSP-03", "name": "Max Super Specialty Hospital",
                "address": "Plot 1, Press Enclave Road, Saket, New Delhi", "lat": 28.5284, "lng": 77.2140,
                "specialties": ["Urology", "Nephrology", "Cardiology", "Robotic Surgery"],
                "services": ["Kidney Stone Laser", "Lithotripsy", "Dialysis", "Renal Transplant", "Cardiac ICU"],
                "emergency": 1, "hours": "24/7", "cost": "$$$$",
                "insurance": ["Star Health", "Max Bupa", "Tata AIG", "Care Health"],
                "phone": "+91 11 2651 5050", "email": "saket@maxhealth.synthetic.care"
            },
            {
                "id": "CV-HOSP-04", "name": "Fortis Memorial Healthcare Institute",
                "address": "Sector 44, Opposite HUDA Metro, Gurugram", "lat": 28.4595, "lng": 77.0724,
                "specialties": ["Endocrinology", "Cardiology", "Neurology", "Gastroenterology"],
                "services": ["Diabetic Care", "Cardiac Stenting", "Brain Stroke Unit", "Endoscopy"],
                "emergency": 1, "hours": "24/7", "cost": "$$$$",
                "insurance": ["Star Health", "HDFC ERGO", "Bajaj Allianz", "CGHS"],
                "phone": "+91 124 496 2200", "email": "help@fortisgurugram.synthetic.care"
            },
            {
                "id": "CV-HOSP-05", "name": "AIIMS Regional Medical Center",
                "address": "Ansari Nagar East, New Delhi", "lat": 28.5672, "lng": 77.2100,
                "specialties": ["All Specialties", "Cardiology", "Urology", "Oncology", "Trauma"],
                "services": ["Apex Level 1 Trauma", "Advanced Diagnostics", "Subsidized Care", "Tertiary Surgery"],
                "emergency": 1, "hours": "24/7", "cost": "$",
                "insurance": ["Ayushman Bharat", "CGHS", "ECHS", "State Government Schemes"],
                "phone": "+91 11 2658 8500", "email": "director@aiims.synthetic.care"
            },
            {
                "id": "CV-HOSP-06", "name": "Care Institute of Medical Sciences",
                "address": "Banjara Hills Road No 1, Hyderabad", "lat": 17.4165, "lng": 78.4482,
                "specialties": ["Cardiology", "Pulmonology", "Critical Care", "General Surgery"],
                "services": ["Cardiac Bypass", "Bronchoscopy", "Ventilator Support", "Laparoscopy"],
                "emergency": 1, "hours": "24/7", "cost": "$$",
                "insurance": ["Ayushman Bharat", "Star Health", "Religare", "CGHS"],
                "phone": "+91 40 6165 6565", "email": "banjara@carehospitals.synthetic.care"
            },
            {
                "id": "CV-HOSP-07", "name": "KIMS Foundation & Research Centre",
                "address": "Minister Road, Secunderabad", "lat": 17.4399, "lng": 78.4983,
                "specialties": ["Nephrology", "Urology", "Orthopedics", "Neurosciences"],
                "services": ["Kidney Stone Lithotripsy", "Spine Surgery", "Dialysis Unit 24/7"],
                "emergency": 1, "hours": "24/7", "cost": "$$",
                "insurance": ["Arogyasri", "Ayushman Bharat", "Star Health", "ICICI"],
                "phone": "+91 40 4488 5000", "email": "info@kimshospitals.synthetic.care"
            },
            {
                "id": "CV-HOSP-08", "name": "Rainbow Children's & Women's Hospital",
                "address": "Road No 2, Banjara Hills, Hyderabad", "lat": 17.4210, "lng": 78.4350,
                "specialties": ["Pediatrics", "Obstetrics & Gynecology", "Neonatology"],
                "services": ["NICU Level 3", "High-Risk Pregnancy", "Pediatric Surgery", "Vaccinations"],
                "emergency": 1, "hours": "24/7", "cost": "$$$",
                "insurance": ["Star Health", "Max Bupa", "HDFC ERGO", "Acko"],
                "phone": "+91 40 4242 4242", "email": "care@rainbowchildren.synthetic.care"
            },
            {
                "id": "CV-HOSP-09", "name": "Dr. Agarwal's Eye Hospital",
                "address": "Himayatnagar Main Road, Hyderabad", "lat": 17.4012, "lng": 78.4870,
                "specialties": ["Ophthalmology"],
                "services": ["Cataract Laser", "Glaucoma Clinic", "Retina Surgery", "LASIK"],
                "emergency": 0, "hours": "8:00 AM - 8:00 PM", "cost": "$$",
                "insurance": ["Star Health", "CGHS", "Ayushman Bharat"],
                "phone": "+91 40 2322 0011", "email": "hyderabad@agarwaleye.synthetic.care"
            },
            {
                "id": "CV-HOSP-10", "name": "Apex Central Diagnostics & Imaging",
                "address": "Plot 42, Healthcare Corridor, Sector 18", "lat": 17.4410, "lng": 78.3890,
                "specialties": ["Diagnostics", "Pathology", "Radiology"],
                "services": ["CT Scan 128 Slice", "MRI 3 Tesla", "CBC & Lipid Testing", "PET Scan"],
                "emergency": 1, "hours": "24/7", "cost": "$$",
                "insurance": ["Cashless All Providers", "CGHS", "Ayushman Bharat"],
                "phone": "+91 1800 200 4455", "email": "lab@apexdiagnostics.com"
            }
        ]

        # Add more facilities to reach 35 synthetic facilities
        facility_templates = [
            ("City Care Community Health Center", "General Medicine, Pediatrics", ["OPD", "Immunization", "Basic Labs"], "$", 17.4250, 78.4150, 0),
            ("Sunshine Orthopedic & Joint Center", "Orthopedics, Sports Medicine", ["Knee Replacement", "Arthroscopy", "Physio"], "$$$", 17.4520, 78.3750, 0),
            ("Pulse 24x7 Emergency Cardiac Unit", "Cardiology, Emergency", ["Chest Pain Evaluation", "Cath Lab", "CCU"], "$$$", 17.4190, 78.4520, 1),
            ("Medanta Heart & Vascular Clinic", "Cardiology, Vascular Surgery", ["Echocardiography", "Holter", "Pacemaker"], "$$$$", 28.4350, 77.0420, 1),
            ("Manipal Comprehensive Healthcare", "Urology, Oncology, Gastro", ["Laser Lithotripsy", "Chemo Daycare", "Colonoscopy"], "$$$", 12.9600, 77.6450, 1),
            ("Sir Ganga Ram Hospital", "MultiSpecialty, Nephrology, Urology", ["Kidney Stone Center", "Renal Transplant"], "$$$", 28.6385, 77.1895, 1),
            ("Narayana Health City", "Cardiology, Cardiac Surgery, Oncology", ["Subsidized Bypass", "Pediatric Heart", "Bone Marrow"], "$$", 12.8250, 77.6920, 1),
            ("Ruby Hall Clinic", "Trauma, Emergency, Neurosciences", ["Brain Surgery", "Stroke Unit", "Level 1 Trauma"], "$$$", 18.5320, 73.8780, 1),
            ("Lilavati Hospital & Research Centre", "MultiSpecialty, Cardiology, Gastro", ["Advanced Cath Lab", "Liver Clinic"], "$$$$", 19.0520, 72.8290, 1),
            ("Kokilaben Dhirubhai Ambani Hospital", "Oncology, Robotic Urology, Emergency", ["Robotic Lithotripsy", "PET-CT", "Trauma"], "$$$$", 19.1310, 72.8250, 1),
            ("Christian Medical College Hospital", "General Medicine, Hematology, Trauma", ["Blood Disorders", "Trauma Care", "Research"], "$", 12.9250, 79.1350, 1),
            ("Tata Memorial Hospital", "Oncology", ["Cancer Surgery", "Radiation Therapy", "Palliative Care"], "$", 19.0030, 72.8430, 0),
            ("Amrita Institute of Medical Sciences", "MultiSpecialty, Organ Transplant", ["Liver Transplant", "Kidney Stone Laser"], "$$", 10.0320, 76.2940, 1),
            ("Aster Medcity Healthcare", "Urology, Cardiology, Pediatrics", ["Laser Ureteroscopy", "Cardiac ICU", "Daycare"], "$$$", 10.0520, 76.2730, 1),
            ("Columbia Asia Referral Hospital", "General Medicine, Ortho, Gastro", ["Day Surgery", "Endoscopy", "Emergency"], "$$", 13.0130, 77.5530, 1),
            ("Hinduja National Hospital", "Cardiology, Nephrology, Pulmonology", ["Dialysis", "Bronchoscopy", "Angio"], "$$$", 19.0320, 72.8410, 1),
            ("Saifee MultiSpecialty Hospital", "General Surgery, Urology, ObGyn", ["Laparoscopic Stone Removal", "Maternity"], "$$", 18.9520, 72.8180, 1),
            ("Breach Candy Trust Hospital", "Cardiology, Internal Medicine", ["Executive Checkup", "Critical Care"], "$$$$", 18.9720, 72.8050, 1),
            ("PSG Institute of Medical Sciences", "All Specialties, Dialysis, Trauma", ["Subsidized Care", "Emergency 24x7"], "$", 11.0250, 77.0050, 1),
            ("Kovai Medical Center & Hospital", "Interventional Radiology, Urology", ["Laser Lithotripsy", "Stroke Interventions"], "$$", 11.0550, 77.0350, 1),
            ("Sankara Nethralaya", "Ophthalmology", ["Cornea Transplant", "Pediatric Ophthalmology"], "$$", 13.0620, 80.2520, 0),
            ("SIMS Hospital Vadapalani", "Orthopedics, Neuro, Emergency", ["Joint Replacement", "Emergency Trauma"], "$$$", 13.0510, 80.2100, 1),
            ("Gleneagles Global Health City", "Hepatology, Nephrology, Urology", ["Living Donor Kidney Transplant", "Stone Clinic"], "$$$", 12.8920, 80.2010, 1),
            ("Fortis Malar Hospital", "Cardiology, General Medicine", ["Heart Failure Clinic", "Cath Lab"], "$$$", 13.0050, 80.2570, 1),
            ("Peerless Hospital", "Cardiology, Ortho, Emergency", ["Trauma Care", "Geriatric Medicine"], "$$", 22.4820, 88.3950, 1)
        ]

        idx = 11
        for name, spec_str, serv_list, cost, lat, lng, em in facility_templates:
            hospitals_data.append({
                "id": f"CV-HOSP-{idx:02d}", "name": name,
                "address": f"Plot {idx * 3}, Health Avenue", "lat": lat, "lng": lng,
                "specialties": [s.strip() for s in spec_str.split(",")],
                "services": serv_list,
                "emergency": em, "hours": "24/7" if em else "9:00 AM - 7:00 PM",
                "cost": cost,
                "insurance": ["Star Health", "Ayushman Bharat", "CGHS", "National Insurance"],
                "phone": f"+91 1800 {idx:02d}0 9988", "email": f"contact{idx}@carevault.synthetic.care"
            })
            idx += 1

        for h in hospitals_data:
            cursor.execute("""
            INSERT INTO hospitals (
                hospital_id, name, address, latitude, longitude, specialties,
                services, emergency, opening_hours, cost_range, insurance_schemes,
                contact_phone, contact_email, verification_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'VERIFIED_SYNTHETIC')
            """, (
                h["id"], h["name"], h["address"], h["lat"], h["lng"],
                json.dumps(h["specialties"]), json.dumps(h["services"]),
                h["emergency"], h["hours"], h["cost"], json.dumps(h["insurance"]),
                h["phone"], h["email"]
            ))

        # 6. Seed Emergency Facilities
        emergency_data = [
            ("CV-HOSP-01", "Apollo Health City 24x7 Emergency", "Level 1 Trauma & Cardiac", "1066", "+91 40 2360 7777", "Level 1", 17.4325, 78.4071, "Road No 72, Jubilee Hills, Hyderabad"),
            ("CV-HOSP-05", "AIIMS Apex Trauma Center", "Apex Level 1 National Trauma Center", "102 / 112", "+91 11 2658 8500", "Level 1 Apex", 28.5672, 77.2100, "Ansari Nagar East, New Delhi"),
            ("CV-HOSP-03", "Max Super Specialty Saket ER", "Comprehensive Emergency & Stroke Unit", "011 4055 4055", "+91 11 2651 5050", "Level 1", 28.5284, 77.2140, "Press Enclave Road, Saket"),
            ("CV-HOSP-04", "Fortis Memorial Critical Trauma", "24/7 Stroke & Cardiac Emergency", "105010", "+91 124 496 2200", "Level 1", 28.4595, 77.0724, "Sector 44, Gurugram"),
            ("CV-HOSP-06", "Care Hospitals Banjara Trauma Care", "Cardiac & Stroke 24/7 Emergency", "105711", "+91 40 6165 6565", "Level 2", 17.4165, 78.4482, "Banjara Hills Road No 1, Hyderabad")
        ]

        for hid, name, etype, help_no, amb_no, level, lat, lng, addr in emergency_data:
            cursor.execute("""
            INSERT INTO emergency_facilities (
                hospital_id, name, emergency_type, helpline, ambulance_phone,
                trauma_level, latitude, longitude, address, open_now
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (hid, name, etype, help_no, amb_no, level, lat, lng, addr))

        # 7. Seed Medical Conditions Reference (Patient Awareness)
        conditions_ref = [
            (
                "Type 2 Diabetes Mellitus", "E11", "Endocrine & Metabolic",
                "A chronic metabolic condition characterized by elevated blood glucose resulting from insulin resistance and progressive insulin secretion impairment.",
                json.dumps(["Increased thirst (polydipsia)", "Frequent urination (polyuria)", "Unexplained fatigue", "Blurred vision", "Slow-healing sores"]),
                json.dumps(["Family history of diabetes", "Physical inactivity", "Excess body weight / abdominal obesity", "High blood pressure"]),
                json.dumps(["Fasting Blood Glucose", "HbA1c Glycated Hemoglobin", "Postprandial Blood Sugar", "Urine Microalbumin"]),
                "Nutritious balanced diet with monitored carbohydrate intake, regular aerobic physical activity, adherence to prescribed oral hypoglycemics or insulin, and regular foot and eye examinations.",
                "Symptoms of extreme hyper- or hypoglycemia (confusion, extreme tremors, loss of consciousness, fruity breath odor, persistent vomiting)."
            ),
            (
                "Essential Hypertension", "I10", "Cardiovascular",
                "Persistently elevated arterial blood pressure without a clear underlying secondary medical cause, commonly termed high blood pressure.",
                json.dumps(["Often asymptomatic ('silent condition')", "Morning occipital headaches", "Occasional dizziness", "Flushing", "Shortness of breath on exertion"]),
                json.dumps(["High dietary sodium intake", "Sedentary lifestyle", "Chronic psychological stress", "Age over 45", "Tobacco use"]),
                json.dumps(["Digital Blood Pressure Monitoring", "Electrocardiogram (ECG)", "Echocardiogram", "Lipid Profile", "Renal Function"]),
                "DASH dietary pattern (rich in potassium and low in salt), stress reduction through mindfulness, moderate aerobic exercise 150 mins/week, and compliance with anti-hypertensive medication.",
                "Hypertensive crisis: Blood pressure >180/120 mmHg accompanied by chest pain, shortness of breath, blurry vision, or sudden neurological deficit."
            ),
            (
                "Kidney Stones (Nephrolithiasis)", "N20", "Nephrology & Urology",
                "Hard crystalline deposits formed from minerals and acid salts that concentrate in the kidneys and urinary tract.",
                json.dumps(["Severe sharp flank or back pain radiating to groin", "Blood in urine (hematuria)", "Painful or burning urination", "Nausea and vomiting"]),
                json.dumps(["Inadequate daily water intake", "Diets high in sodium, animal protein, and oxalate", "Family history of stone disease", "Hyperuricemia"]),
                json.dumps(["Ultrasound KUB (Kidney, Ureter, Bladder)", "NCCT Abdomen & Pelvis (Non-contrast CT)", "Serum Creatinine", "Urine Routine & Microscopy"]),
                "Increased fluid consumption (2.5 to 3 liters water daily), reduction of dietary salt, stone analysis to guide targeted dietary modifications, and medical expulsive therapy or lithotripsy as clinically determined.",
                "Fever and chills accompanying back pain (signs of urinary tract infection with obstruction), inability to pass urine, or intractable vomiting."
            ),
            (
                "Coronary Artery Disease", "I25", "Cardiovascular",
                "Impairment of blood flow through coronary arteries supplying oxygenated blood to the heart muscle, typically due to atherosclerotic plaque accumulation.",
                json.dumps(["Chest tightness or pressure (angina)", "Shortness of breath on exertion", "Pain radiating to jaw, left shoulder, or back"]),
                json.dumps(["Elevated LDL cholesterol", "Hypertension", "Smoking history", "Diabetes Mellitus", "Family history of early cardiovascular disease"]),
                json.dumps(["12-Lead ECG", "Treadmill Stress Test (TMT)", "2D Echocardiogram", "Coronary CT Angiography", "Lipid Profile"]),
                "Cardiac rehabilitation, Mediterranean or low-saturated-fat diet, smoking cessation, cholesterol-lowering statin therapy, antiplatelet therapy as prescribed.",
                "Sudden crushing central chest pain lasting >10 minutes, sweating, nausea, shortness of breath. Call emergency services immediately."
            ),
            (
                "Iron Deficiency Anemia", "D50", "Hematology",
                "A condition where blood lacks adequate healthy red blood cells due to insufficient iron required to produce hemoglobin.",
                json.dumps(["Persistent unusual fatigue", "Pale skin and conjunctiva", "Cold hands and feet", "Brittle nails", "Dizziness on standing"]),
                json.dumps(["Inadequate dietary iron intake", "Heavy menstrual periods", "Gastrointestinal blood loss", "Malabsorption conditions like celiac disease"]),
                json.dumps(["Complete Blood Count (CBC)", "Serum Ferritin", "Total Iron Binding Capacity (TIBC)", "Peripheral Blood Smear"]),
                "Oral iron supplementation taken with vitamin C to enhance absorption, inclusion of iron-rich foods (green leafy vegetables, lentils, lean meats), investigating underlying causes of blood loss.",
                "Severe shortness of breath at rest, chest discomfort, or syncope (fainting)."
            )
        ]

        for name, icd, cat, desc, syms, risks, tests, mgmt, urgent in conditions_ref:
            cursor.execute("""
            INSERT INTO medical_conditions (
                name, icd_code, category, description, symptoms,
                risk_factors, tests_used, general_management, urgent_signs
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, icd, cat, desc, syms, risks, tests, mgmt, urgent))

        # 8. Seed Synthetic Medical Records for Priya Sharma (CV-PAT-1001)
        records_p1 = [
            {
                "id": "CV-REC-101", "type": "Lab Reports", "title": "Complete Blood Count (CBC)",
                "hospital": "Apex Central Diagnostics & Pathology", "doctor": "Dr. V. K. Sen, MBBS",
                "date": "2026-09-20", "source": "DIRECT_LAB_TRANSFER",
                "desc": "Routine hematological profile. Red blood cell indices and differential leukocyte counts evaluated.",
                "tags": ["CBC", "Hemoglobin", "Routine", "Blood"],
                "lines": [
                    "CLINICAL FINDINGS:",
                    "- Hemoglobin: 13.8 g/dL (Reference: 12.0 - 15.5 g/dL) [NORMAL]",
                    "- Total White Blood Cell Count: 7,200 /mcL (Reference: 4,500 - 11,000 /mcL) [NORMAL]",
                    "- Platelet Count: 240,000 /mcL (Reference: 150,000 - 450,000 /mcL) [NORMAL]",
                    "- Packed Cell Volume (PCV): 41.2% (Reference: 37 - 48%) [NORMAL]",
                    "### IMPRESSION",
                    "Normocytic, normochromic red cell picture. No reactive leukocytosis or abnormal cell lines observed."
                ]
            },
            {
                "id": "CV-REC-102", "type": "Lab Reports", "title": "HbA1c Glycated Hemoglobin",
                "hospital": "Apollo Health City Hospital", "doctor": "Dr. Anand Patel, MD (Endo)",
                "date": "2026-09-22", "source": "HOSPITAL_EHR",
                "desc": "3-month quarterly glycemic monitoring for Type 2 Diabetes management.",
                "tags": ["Diabetes", "HbA1c", "Metabolic", "Endocrinology"],
                "lines": [
                    "BIOCHEMICAL EVALUATION:",
                    "- HbA1c (Glycated Hemoglobin): 7.2% (Target for known diabetic: <7.0%) [MILDLY ELEVATED]",
                    "- Estimated Average Glucose (eAG): 160 mg/dL",
                    "- Fasting Plasma Glucose: 132 mg/dL (Reference: 70 - 99 mg/dL) [HIGH]",
                    "### CLINICAL SUMMARY",
                    "Metabolic control demonstrates improvement from baseline (prior 7.8%). Continuation of lifestyle interventions and Metformin recommended."
                ]
            },
            {
                "id": "CV-REC-103", "type": "Lab Reports", "title": "Renal Function Test (KFT)",
                "hospital": "Apollo Health City Hospital", "doctor": "Dr. Sunita Kapoor, MS (Uro)",
                "date": "2026-09-23", "source": "HOSPITAL_EHR",
                "desc": "Comprehensive kidney biochemical panel and glomerular filtration assessment.",
                "tags": ["Kidney", "KFT", "Creatinine", "Urea"],
                "lines": [
                    "BIOCHEMISTRY PARAMETERS:",
                    "- Serum Creatinine: 0.92 mg/dL (Reference: 0.6 - 1.1 mg/dL) [NORMAL]",
                    "- Blood Urea Nitrogen (BUN): 16 mg/dL (Reference: 7 - 20 mg/dL) [NORMAL]",
                    "- eGFR: >90 mL/min/1.73m2 (Reference: >90 mL/min/1.73m2) [NORMAL]",
                    "- Serum Uric Acid: 5.4 mg/dL (Reference: 3.5 - 7.2 mg/dL) [NORMAL]",
                    "### CLINICAL INTERPRETATION",
                    "Renal excretory function is well preserved. No evidence of azotemia or impaired filtration."
                ]
            },
            {
                "id": "CV-REC-104", "type": "Prescriptions", "title": "Cardiometabolic Prescription Slip",
                "hospital": "Apollo Health City Hospital", "doctor": "Dr. Rajesh Mehta, MD (Cardio)",
                "date": "2026-09-24", "source": "HOSPITAL_EHR",
                "desc": "Handwritten prescription for blood pressure and glycemic management after clinical consultation.",
                "tags": ["Prescription", "Cardiology", "Hypertension", "Metformin"],
                "lines": [
                    "PRESCRIPTION SUMMARY:",
                    "1. Tab. Metformin 500mg - 1 tab twice daily after meals (1-0-1)",
                    "2. Tab. Amlodipine 5mg - 1 tab morning after breakfast (1-0-0)",
                    "3. Tab. Atorvastatin 20mg - 1 tab bedtime (0-0-1)",
                    "4. Tab. Pantoprazole 40mg - 1 tab 30 mins before breakfast (1-0-0) x 14 days",
                    "### PHYSICIAN INSTRUCTIONS",
                    "Maintain low sodium diet (<3g/day). Monitor home BP twice weekly in logbook. Next follow-up in 6 weeks."
                ]
            },
            {
                "id": "CV-REC-105", "type": "CT/MRI", "title": "CT Abdomen & Pelvis (Plain)",
                "hospital": "Metro Advanced Imaging & Scan Center", "doctor": "Dr. Sunita Kapoor, MS (Uro)",
                "date": "2026-09-25", "source": "DIRECT_LAB_TRANSFER",
                "desc": "NCCT scan performed to evaluate lower quadrant flank pain and check for calculus.",
                "tags": ["CT Scan", "Abdomen", "Kidney Stone", "Radiology"],
                "lines": [
                    "RADIOLOGICAL OBSERVATIONS:",
                    "- Non-contrast helical CT performed from diaphragm to pubic symphysis.",
                    "- Right kidney: Normal size (10.4 cm). A tiny non-obstructive 3.2 mm calculus noted in lower pole calyx. No hydronephrosis.",
                    "- Left kidney: Normal morphology and parenchymal thickness. No calculus or hydroureter.",
                    "- Urinary bladder: Normal distension, smooth wall contour.",
                    "### RADIOLOGICAL IMPRESSION",
                    "Non-obstructive tiny right lower caliceal calculus (3.2 mm). No acute ureteral obstruction or perinephric stranding."
                ]
            },
            {
                "id": "CV-REC-106", "type": "X-rays", "title": "Chest X-Ray (PA View)",
                "hospital": "Metro MultiSpecialty Hospital", "doctor": "Dr. V. K. Sen, MBBS",
                "date": "2026-09-27", "source": "PATIENT_UPLOAD",
                "desc": "Pre-procedural routine radiographic screening.",
                "tags": ["X-Ray", "Chest", "Lungs", "Cardiothoracic"],
                "lines": [
                    "RADIOGRAPHIC FINDINGS:",
                    "- Trachea is central in position. Mediastinal contours are unremarkable.",
                    "- Cardiac silhouette is within normal limits (CTR < 0.50).",
                    "- Both lung fields are clear with normal vascular markings. No consolidation, cavitation, or pleural effusion.",
                    "- Both costophrenic and cardiophrenic angles are acute and clear.",
                    "### OPINION",
                    "Normal Chest Radiograph."
                ]
            }
        ]

        for r in records_p1:
            doc_bytes = create_synthetic_document_image(
                r["title"], r["hospital"], r["doctor"], r["date"], r["lines"]
            )
            file_path, enc_name, file_sz = save_document(doc_bytes, f"{r['id']}.jpg", r["id"])

            cursor.execute("""
            INSERT INTO medical_records (
                record_id, patient_id, record_type, title, hospital_name, doctor_name,
                record_date, file_path, file_name, file_size, mime_type, description,
                raw_text, tags, source, verification_status
            ) VALUES (?, 'CV-PAT-1001', ?, ?, ?, ?, ?, ?, ?, ?, 'image/jpeg', ?, ?, ?, ?, 'VERIFIED')
            """, (
                r["id"], r["type"], r["title"], r["hospital"], r["doctor"],
                r["date"], file_path, enc_name, file_sz, r["desc"],
                "\n".join(r["lines"]), json.dumps(r["tags"]), r["source"]
            ))

            cursor.execute("""
            INSERT INTO record_files (record_id, encrypted_filename, original_filename, file_hash)
            VALUES (?, ?, ?, 'sha256-demo-verified')
            """, (r["id"], enc_name, f"{r['id']}.jpg"))

            # Log audit trail for synthetic records
            cursor.execute("""
            INSERT INTO access_logs (
                actor_id, actor_name, actor_role, patient_id, record_id, record_title, action, status, details
            ) VALUES (?, ?, ?, 'CV-PAT-1001', ?, ?, 'record_uploaded', 'SUCCESS', ?)
            """, (
                r["hospital"], r["hospital"], "PROVIDER", r["id"], r["title"],
                f"Synthetic record {r['title']} added to health wallet via {r['source']}"
            ))

        # 9. Seed Prescriptions Table entry for Priya Sharma
        cursor.execute("""
        INSERT INTO prescriptions (
            record_id, patient_id, doctor_name, clinic_name, date,
            medicines_json, instructions, confidence_score, is_handwritten, status
        ) VALUES (
            'CV-REC-104', 'CV-PAT-1001', 'Dr. Rajesh Mehta, MD (Cardio)', 'Apollo Health City Hospital', '2026-09-24',
            ?, 'Low sodium diet, home BP log twice weekly', 0.96, 1, 'ACTIVE'
        )
        """, (
            json.dumps([
                {"name": "Metformin", "dose": "500mg", "freq": "1-0-1 after meals"},
                {"name": "Amlodipine", "dose": "5mg", "freq": "1-0-0 morning"},
                {"name": "Atorvastatin", "dose": "20mg", "freq": "0-0-1 bedtime"},
                {"name": "Pantoprazole", "dose": "40mg", "freq": "1-0-0 empty stomach"}
            ]),
        ))

        # 10. Seed Tests Table for duplicate detection evaluation
        tests_data = [
            ("CV-REC-101", "CV-PAT-1001", "Complete Blood Count (CBC)", "Hematology", "Blood", "Normal counts. Hemoglobin 13.8 g/dL.", "2026-09-20", "12.0 - 15.5 g/dL", "NORMAL"),
            ("CV-REC-102", "CV-PAT-1001", "HbA1c Glycated Hemoglobin", "Biochemistry", "Blood", "HbA1c 7.2%", "2026-09-22", "<7.0% target", "HIGH"),
            ("CV-REC-103", "CV-PAT-1001", "Renal Function Test (KFT)", "Biochemistry", "Kidney/Blood", "Creatinine 0.92 mg/dL", "2026-09-23", "0.6 - 1.1 mg/dL", "NORMAL"),
            ("CV-REC-105", "CV-PAT-1001", "CT Abdomen & Pelvis", "Radiology", "Abdomen/Urinary", "Non-obstructive 3.2mm calculus", "2026-09-25", "N/A", "ABNORMAL"),
            ("CV-REC-106", "CV-PAT-1001", "Chest X-Ray", "Radiology", "Thorax/Lungs", "Clear lung fields, normal heart size", "2026-09-27", "N/A", "NORMAL")
        ]

        for rid, pid, tname, tcat, tarea, tsum, tdate, trange, tflag in tests_data:
            cursor.execute("""
            INSERT INTO tests (
                record_id, patient_id, test_name, category, body_area,
                result_summary, date, reference_range, flag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (rid, pid, tname, tcat, tarea, tsum, tdate, trange, tflag))

        # 11. Seed Active / Pending Consents
        now = datetime.now(timezone.utc)
        exp_active = (now + timedelta(minutes=45)).isoformat()
        exp_past = (now - timedelta(days=2)).isoformat()

        # Active granted consent for Dr. Rajesh Mehta
        cursor.execute("""
        INSERT INTO consents (
            consent_id, patient_id, provider_id, provider_name, provider_hospital,
            requested_records, purpose, duration_minutes, status, created_at, expires_at
        ) VALUES (
            'CV-CNS-A101', 'CV-PAT-1001', 'CV-DOC-2001', 'Dr. Rajesh Mehta, MD (Cardio)',
            'Apollo Health City Hospital', '["Lab Reports", "Prescriptions", "CT/MRI"]',
            'Cardiometabolic Consultation & Follow-up', 60, 'GRANTED', ?, ?
        )
        """, (now.isoformat(), exp_active))

        # Pending consent request from Dr. Sunita Kapoor
        cursor.execute("""
        INSERT INTO consents (
            consent_id, patient_id, provider_id, provider_name, provider_hospital,
            requested_records, purpose, duration_minutes, status, created_at, expires_at
        ) VALUES (
            'CV-CNS-R202', 'CV-PAT-1001', 'CV-DOC-2003', 'Dr. Sunita Kapoor, MS (Urology)',
            'Max Super Specialty Hospital', '["CT/MRI", "Lab Reports"]',
            'Renal Calculus Second Opinion & Treatment Planning', 30, 'REQUESTED', ?, ?
        )
        """, (now.isoformat(), (now + timedelta(minutes=30)).isoformat()))

        # Expired historical consent from Dr. V. K. Sen
        cursor.execute("""
        INSERT INTO consents (
            consent_id, patient_id, provider_id, provider_name, provider_hospital,
            requested_records, purpose, duration_minutes, status, created_at, expires_at
        ) VALUES (
            'CV-CNS-X303', 'CV-PAT-1001', 'CV-DOC-2002', 'Dr. V. K. Sen, MBBS, DNB',
            'Metro MultiSpecialty Hospital', '["X-rays"]',
            'Pre-procedure Routine Check', 30, 'EXPIRED', ?, ?
        )
        """, ((now - timedelta(days=3)).isoformat(), exp_past))

        # 12. Seed Notifications
        notifications_data = [
            ("CV-PAT-1001", "New medical record received", "Direct Transfer: Chest X-Ray received from Metro MultiSpecialty Hospital.", "RECORD_RECEIVED", "CV-REC-106"),
            ("CV-PAT-1001", "Access Request from Dr. Sunita Kapoor", "Dr. Sunita Kapoor (Max Super Specialty Hospital) requested access to your CT/MRI & Lab Reports for Renal Calculus treatment.", "ACCESS_REQUEST", "CV-CNS-R202"),
            ("CV-PAT-1001", "Active Sharing Session", "Dr. Rajesh Mehta currently has view-only access to your authorized records (Expires in 45m).", "ACCESS_APPROVED", "CV-CNS-A101"),
            ("CV-PAT-1001", "⚠️ Potential duplicate test alert", "A similar CT scan was recorded 6 days ago. Discuss with your doctor if a repeat is necessary.", "SIMILAR_TEST", "CV-REC-105")
        ]

        for pid, title, msg, ntype, rel in notifications_data:
            cursor.execute("""
            INSERT INTO notifications (patient_id, title, message, type, related_id)
            VALUES (?, ?, ?, ?, ?)
            """, (pid, title, msg, ntype, rel))

        # 13. Seed Doctor Questions
        initial_questions = [
            ("CV-PAT-1001", "What does my HbA1c value of 7.2% indicate regarding my 3-month glycemic target?", "Recent Lab Report", 0, 0),
            ("CV-PAT-1001", "Is my non-obstructive 3.2mm kidney stone likely to pass with hydration or do I need medication?", "Urology / Imaging", 0, 0),
            ("CV-PAT-1001", "Are my blood pressure readings on Amlodipine 5mg within our target range?", "Cardiology", 1, 0),
            ("CV-PAT-1001", "Do I need any additional kidney filtration monitoring in the next 3 months?", "Diagnostics", 0, 0)
        ]

        for pid, qtext, cat, chk, cust in initial_questions:
            cursor.execute("""
            INSERT INTO doctor_questions (patient_id, question_text, category, is_checked, is_custom)
            VALUES (?, ?, ?, ?, ?)
            """, (pid, qtext, cat, chk, cust))

    print("CareVault AI synthetic demo data successfully initialized!")
