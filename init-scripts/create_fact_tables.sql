-- Create fact tables for Gold layer
-- These tables contain the measurable events and metrics

-- Fact: Encounter
CREATE TABLE IF NOT EXISTS fact_encounter (
    encounter_key SERIAL PRIMARY KEY,
    encounter_id VARCHAR(20) UNIQUE NOT NULL,
    patient_key INTEGER REFERENCES dim_patient(patient_key),
    provider_key INTEGER REFERENCES dim_provider(provider_key),
    visit_date_key INTEGER REFERENCES dim_date(date_key),
    discharge_date_key INTEGER REFERENCES dim_date(date_key),
    diagnosis_key INTEGER REFERENCES dim_diagnosis(diagnosis_key),
    -- Denormalized attributes for query performance
    visit_type VARCHAR(50),
    department VARCHAR(100),
    admission_type VARCHAR(50),
    length_of_stay INTEGER,
    status VARCHAR(50),
    readmitted_flag BOOLEAN,
    -- Aggregated metrics
    total_procedures INTEGER DEFAULT 0,
    total_medications INTEGER DEFAULT 0,
    total_lab_tests INTEGER DEFAULT 0,
    total_cost DECIMAL(10,2) DEFAULT 0,
    -- Audit columns
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fact_encounter
CREATE INDEX IF NOT EXISTS idx_encounter_patient ON fact_encounter(patient_key);
CREATE INDEX IF NOT EXISTS idx_encounter_provider ON fact_encounter(provider_key);
CREATE INDEX IF NOT EXISTS idx_encounter_visit_date ON fact_encounter(visit_date_key);
CREATE INDEX IF NOT EXISTS idx_encounter_discharge_date ON fact_encounter(discharge_date_key);
CREATE INDEX IF NOT EXISTS idx_encounter_diagnosis ON fact_encounter(diagnosis_key);
CREATE INDEX IF NOT EXISTS idx_encounter_department ON fact_encounter(department);
CREATE INDEX IF NOT EXISTS idx_encounter_visit_type ON fact_encounter(visit_type);
CREATE INDEX IF NOT EXISTS idx_encounter_status ON fact_encounter(status);

-- Fact: Billing
CREATE TABLE IF NOT EXISTS fact_billing (
    billing_key SERIAL PRIMARY KEY,
    billing_id VARCHAR(20) UNIQUE NOT NULL,
    encounter_key INTEGER REFERENCES fact_encounter(encounter_key),
    patient_key INTEGER REFERENCES dim_patient(patient_key),
    claim_billing_date_key INTEGER REFERENCES dim_date(date_key),
    -- Denormalized attributes
    insurance_provider VARCHAR(100),
    payment_method VARCHAR(50),
    claim_status VARCHAR(50),
    denial_reason VARCHAR(200),
    -- Financial metrics
    billed_amount DECIMAL(10,2),
    paid_amount DECIMAL(10,2),
    denied_amount DECIMAL(10,2),
    payment_rate DECIMAL(5,2), -- calculated: (paid/billed) * 100
    -- Audit columns
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fact_billing
CREATE INDEX IF NOT EXISTS idx_billing_encounter ON fact_billing(encounter_key);
CREATE INDEX IF NOT EXISTS idx_billing_patient ON fact_billing(patient_key);
CREATE INDEX IF NOT EXISTS idx_billing_date ON fact_billing(claim_billing_date_key);
CREATE INDEX IF NOT EXISTS idx_billing_insurance ON fact_billing(insurance_provider);
CREATE INDEX IF NOT EXISTS idx_billing_status ON fact_billing(claim_status);

-- Fact: Lab Test
CREATE TABLE IF NOT EXISTS fact_lab_test (
    lab_test_key SERIAL PRIMARY KEY,
    lab_id VARCHAR(20),
    encounter_key INTEGER REFERENCES fact_encounter(encounter_key),
    test_date_key INTEGER REFERENCES dim_date(date_key),
    -- Test details
    test_name VARCHAR(200),
    test_code VARCHAR(50),
    specimen_type VARCHAR(100),
    test_result VARCHAR(50),
    status VARCHAR(50),
    is_abnormal BOOLEAN,
    -- Audit columns
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fact_lab_test
CREATE INDEX IF NOT EXISTS idx_lab_encounter ON fact_lab_test(encounter_key);
CREATE INDEX IF NOT EXISTS idx_lab_test_date ON fact_lab_test(test_date_key);
CREATE INDEX IF NOT EXISTS idx_lab_test_name ON fact_lab_test(test_name);
CREATE INDEX IF NOT EXISTS idx_lab_test_abnormal ON fact_lab_test(is_abnormal);

-- Fact: Denial
CREATE TABLE IF NOT EXISTS fact_denial (
    denial_key SERIAL PRIMARY KEY,
    denial_id VARCHAR(20) UNIQUE NOT NULL,
    billing_key INTEGER REFERENCES fact_billing(billing_key),
    denial_date_key INTEGER REFERENCES dim_date(date_key),
    appeal_resolution_date_key INTEGER REFERENCES dim_date(date_key),
    -- Denial details
    denial_reason_code VARCHAR(20),
    denial_reason_description TEXT,
    denied_amount DECIMAL(10,2),
    -- Appeal tracking
    appeal_filed BOOLEAN,
    appeal_status VARCHAR(50),
    final_outcome VARCHAR(50),
    -- Audit columns
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fact_denial
CREATE INDEX IF NOT EXISTS idx_denial_billing ON fact_denial(billing_key);
CREATE INDEX IF NOT EXISTS idx_denial_date ON fact_denial(denial_date_key);
CREATE INDEX IF NOT EXISTS idx_denial_appeal_date ON fact_denial(appeal_resolution_date_key);
CREATE INDEX IF NOT EXISTS idx_denial_reason_code ON fact_denial(denial_reason_code);
CREATE INDEX IF NOT EXISTS idx_denial_appeal_status ON fact_denial(appeal_status);
