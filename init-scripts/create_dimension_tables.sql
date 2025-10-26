-- Create dimension tables for Gold layer
-- These tables support the star schema for analytics

-- Dimension: Patient (with SCD Type 2 for historical tracking)
CREATE TABLE IF NOT EXISTS dim_patient (
    patient_key SERIAL PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    dob DATE,
    age INTEGER,
    gender VARCHAR(20),
    ethnicity VARCHAR(50),
    insurance_type VARCHAR(50),
    marital_status VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(2),
    zip VARCHAR(10),
    phone VARCHAR(20),
    email VARCHAR(200),
    -- SCD Type 2 columns for tracking historical changes
    valid_from DATE NOT NULL,
    valid_to DATE,
    is_current BOOLEAN DEFAULT TRUE,
    -- Audit columns
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for dim_patient
CREATE INDEX IF NOT EXISTS idx_patient_id ON dim_patient(patient_id);
CREATE INDEX IF NOT EXISTS idx_patient_current ON dim_patient(is_current);
CREATE INDEX IF NOT EXISTS idx_patient_valid_from ON dim_patient(valid_from);
CREATE INDEX IF NOT EXISTS idx_patient_valid_to ON dim_patient(valid_to);
CREATE INDEX IF NOT EXISTS idx_patient_insurance ON dim_patient(insurance_type);

-- Dimension: Provider
CREATE TABLE IF NOT EXISTS dim_provider (
    provider_key SERIAL PRIMARY KEY,
    provider_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200),
    department VARCHAR(100),
    specialty VARCHAR(100),
    npi VARCHAR(20),
    inhouse BOOLEAN,
    location VARCHAR(50),
    years_experience INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for dim_provider
CREATE INDEX IF NOT EXISTS idx_provider_id ON dim_provider(provider_id);
CREATE INDEX IF NOT EXISTS idx_provider_department ON dim_provider(department);
CREATE INDEX IF NOT EXISTS idx_provider_specialty ON dim_provider(specialty);

-- Dimension: Date
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    week INTEGER,
    day_of_month INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(20),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN DEFAULT FALSE
);

-- Indexes for dim_date
CREATE INDEX IF NOT EXISTS idx_date_date ON dim_date(date);
CREATE INDEX IF NOT EXISTS idx_date_year_month ON dim_date(year, month);
CREATE INDEX IF NOT EXISTS idx_date_quarter ON dim_date(year, quarter);

-- Dimension: Diagnosis
CREATE TABLE IF NOT EXISTS dim_diagnosis (
    diagnosis_key SERIAL PRIMARY KEY,
    diagnosis_code VARCHAR(20) UNIQUE NOT NULL,
    diagnosis_description TEXT,
    is_chronic BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for dim_diagnosis
CREATE INDEX IF NOT EXISTS idx_diagnosis_code ON dim_diagnosis(diagnosis_code);
CREATE INDEX IF NOT EXISTS idx_diagnosis_chronic ON dim_diagnosis(is_chronic);

-- Dimension: Procedure
CREATE TABLE IF NOT EXISTS dim_procedure (
    procedure_key SERIAL PRIMARY KEY,
    procedure_code VARCHAR(20) UNIQUE NOT NULL,
    procedure_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for dim_procedure
CREATE INDEX IF NOT EXISTS idx_procedure_code ON dim_procedure(procedure_code);

-- Dimension: Medication
CREATE TABLE IF NOT EXISTS dim_medication (
    medication_key SERIAL PRIMARY KEY,
    drug_name VARCHAR(200) NOT NULL,
    dosage VARCHAR(50),
    route VARCHAR(50),
    frequency VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_medication UNIQUE(drug_name, dosage, route)
);

-- Indexes for dim_medication
CREATE INDEX IF NOT EXISTS idx_medication_drug_name ON dim_medication(drug_name);
CREATE INDEX IF NOT EXISTS idx_medication_route ON dim_medication(route);
