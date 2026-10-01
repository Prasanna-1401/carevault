import sqlite3
import json
from contextlib import contextmanager
from app.config import SQLITE_DB_PATH

def get_db_connection():
    conn = sqlite3.connect(str(SQLITE_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def db_session():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with db_session() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('PATIENT', 'DOCTOR', 'ADMIN', 'LAB')),
            full_name TEXT NOT NULL,
            mobile TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Patients table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            patient_id TEXT UNIQUE NOT NULL,
            dob TEXT NOT NULL,
            gender TEXT,
            blood_group TEXT NOT NULL,
            allergies TEXT,
            existing_conditions TEXT,
            current_medications TEXT,
            preferred_language TEXT DEFAULT 'English',
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            emergency_contact_relation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Providers (Doctors) table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            provider_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            hospital_id TEXT,
            hospital_name TEXT,
            license_number TEXT NOT NULL,
            verified INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Hospitals table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            specialties TEXT NOT NULL,       -- JSON array
            services TEXT NOT NULL,          -- JSON array
            emergency INTEGER DEFAULT 1,     -- 1: Yes, 0: No
            opening_hours TEXT DEFAULT '24/7',
            cost_range TEXT DEFAULT '$$',    -- $, $$, $$$, $$$$
            insurance_schemes TEXT,          -- JSON array
            contact_phone TEXT NOT NULL,
            contact_email TEXT,
            verification_status TEXT DEFAULT 'VERIFIED_SYNTHETIC',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Labs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS labs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            lab_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            license_number TEXT NOT NULL,
            address TEXT NOT NULL,
            contact_phone TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Medical Records table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medical_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT UNIQUE NOT NULL,
            patient_id TEXT NOT NULL,
            record_type TEXT NOT NULL,       -- Lab Reports, X-rays, CT/MRI, Prescriptions, Discharge Summaries, Doctor Notes, Vaccination Records, Previous Treatments, Other Documents
            title TEXT NOT NULL,
            hospital_name TEXT NOT NULL,
            doctor_name TEXT,
            record_date TEXT NOT NULL,
            file_path TEXT,
            file_name TEXT,
            file_size INTEGER DEFAULT 0,
            mime_type TEXT DEFAULT 'application/pdf',
            description TEXT,
            raw_text TEXT,
            tags TEXT,                       -- JSON array
            source TEXT DEFAULT 'PATIENT_UPLOAD', -- PATIENT_UPLOAD, DIRECT_LAB_TRANSFER, HOSPITAL_EHR
            verification_status TEXT DEFAULT 'VERIFIED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
        )
        """)

        # Record Files (metadata & encryption at rest)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS record_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT UNIQUE NOT NULL,
            encrypted_filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            encryption_algo TEXT DEFAULT 'AES-256-GCM-SIMULATED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (record_id) REFERENCES medical_records(record_id) ON DELETE CASCADE
        )
        """)

        # Consents table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS consents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consent_id TEXT UNIQUE NOT NULL,
            patient_id TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            provider_name TEXT,
            provider_hospital TEXT,
            requested_records TEXT NOT NULL, -- JSON array of record types or specific IDs
            purpose TEXT NOT NULL,           -- Treatment, Consultation, Second Opinion, Emergency
            duration_minutes INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('REQUESTED', 'GRANTED', 'REJECTED', 'EXPIRED', 'REVOKED')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            revoked_at TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
        )
        """)

        # Consent Records mapping
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS consent_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consent_id TEXT NOT NULL,
            record_id TEXT NOT NULL,
            FOREIGN KEY (consent_id) REFERENCES consents(consent_id) ON DELETE CASCADE,
            FOREIGN KEY (record_id) REFERENCES medical_records(record_id) ON DELETE CASCADE
        )
        """)

        # Tamper-Evident Access History / Audit Logs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            actor_id TEXT NOT NULL,
            actor_name TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            record_id TEXT,
            record_title TEXT,
            action TEXT NOT NULL,            -- access_requested, access_granted, access_rejected, access_revoked, access_expired, record_viewed, record_uploaded, record_transferred
            status TEXT NOT NULL,            -- SUCCESS, DENIED, EXPIRED, REVOKED
            ip_address TEXT DEFAULT '127.0.0.1',
            details TEXT
        )
        """)

        # Prescriptions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT UNIQUE,
            patient_id TEXT NOT NULL,
            doctor_name TEXT NOT NULL,
            clinic_name TEXT NOT NULL,
            date TEXT NOT NULL,
            medicines_json TEXT NOT NULL,    -- JSON list of medicines
            instructions TEXT,
            confidence_score REAL DEFAULT 0.95,
            is_handwritten INTEGER DEFAULT 0,
            image_path TEXT,
            status TEXT DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Tests table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT,
            patient_id TEXT NOT NULL,
            test_name TEXT NOT NULL,
            category TEXT NOT NULL,
            body_area TEXT,
            result_summary TEXT,
            date TEXT NOT NULL,
            reference_range TEXT,
            flag TEXT DEFAULT 'NORMAL',      -- NORMAL, HIGH, LOW, ABNORMAL
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Medical Conditions / Disease Reference table (for Patient Awareness)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medical_conditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            icd_code TEXT,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            symptoms TEXT NOT NULL,          -- JSON list
            risk_factors TEXT NOT NULL,      -- JSON list
            tests_used TEXT NOT NULL,        -- JSON list
            general_management TEXT NOT NULL,
            urgent_signs TEXT NOT NULL
        )
        """)

        # Notifications table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT NOT NULL,              -- RECORD_RECEIVED, ACCESS_REQUEST, ACCESS_APPROVED, ACCESS_EXPIRED, SIMILAR_TEST, PRESCRIPTION, SYSTEM
            is_read INTEGER DEFAULT 0,
            related_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Doctor Questions Checklist table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            question_text TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            is_checked INTEGER DEFAULT 0,
            is_custom INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Emergency Facilities table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_facilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id TEXT NOT NULL,
            name TEXT NOT NULL,
            emergency_type TEXT NOT NULL,    -- Level 1 Trauma, Cardiac 24/7, General ER
            helpline TEXT NOT NULL,
            ambulance_phone TEXT NOT NULL,
            trauma_level TEXT DEFAULT 'Level 1',
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            address TEXT NOT NULL,
            open_now INTEGER DEFAULT 1
        )
        """)

        # Create Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_patient ON medical_records(patient_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_date ON medical_records(record_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_consents_patient ON consents(patient_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_consents_provider ON consents(provider_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_consents_expires ON consents(expires_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hospitals_coords ON hospitals(latitude, longitude);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_patient ON access_logs(patient_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON access_logs(timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notif_patient ON notifications(patient_id);")

    print("CareVault database schema initialized successfully with all indexes and foreign keys.")
