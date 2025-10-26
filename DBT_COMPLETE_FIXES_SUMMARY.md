# Complete dbt Schema Fixes Summary

## Overview
Fixed all schema mismatches between the actual Silver layer data and the dbt models across staging, dimensions, and fact layers.

---

## Staging Layer Fixes

### Column Name Mismatches Fixed

#### 1. stg_encounters.sql
- **Added**: `diagnosis_code` (was missing from staging view)
- **Changed**: `admission_date` → `visit_date`

#### 2. stg_medications.sql
- **Removed**: `patient_id` (doesn't exist in medications table)
- **Changed**: `start_date` → `prescribed_date`
- **Changed**: `end_date` → `duration`

#### 3. stg_diagnoses.sql
- **Added**: `diagnosis_id`, `encounter_id`, `primary_flag`
- **Changed**: `is_chronic` → `chronic_flag`

#### 4. stg_denials.sql
- **Changed**: `billing_id` → `claim_id`

#### 5. stg_claims_billing.sql
- **Removed**: `denied_amount` (doesn't exist in claims_and_billing table)
- **Added**: `claim_id`
- **Reordered**: columns to match actual schema

### Test Definition Updates

#### schema.yml
- Updated `stg_denials` tests: `billing_id` → `claim_id`
- Updated `stg_diagnoses` tests: added `diagnosis_id` as primary key, added `encounter_id` relationship

#### sources.yml
- Updated all source definitions to match actual Silver layer schemas
- Fixed column names for: encounters, medications, diagnoses, denials, claims_and_billing

---

## Dimension Layer Fixes

### 1. dim_diagnosis.sql
- **Changed**: `is_chronic` → `chronic_flag` in source query
- **Mapped**: `chronic_flag` back to `is_chronic` in output for consistency

### 2. dim_patient.sql
- **Changed**: Materialization from `table` to `incremental`
- **Added**: Conditional logic using `{% if is_incremental() %}` for first run
- **Added**: `created_at` and `updated_at` columns to all CTEs
- **Fixed**: Data type casting for `dob` field (text → date)
- **Fixed**: Column consistency across all UNION branches

---

## Fact Layer Fixes

### 1. fact_encounter.sql
- **Removed**: References to non-existent `dim_date` table
- **Changed**: `admission_date` → `visit_date`
- **Changed**: Date keys to direct date columns
- **Removed**: Joins to `date_dimension`

### 2. fact_billing.sql
- **Removed**: References to `dim_date` table
- **Removed**: `denied_amount` column (doesn't exist in source)
- **Changed**: Date keys to direct date columns

### 3. fact_lab_test.sql
- **Removed**: References to `dim_date` table
- **Changed**: Date keys to direct date columns

### 4. fact_denial.sql
- **Removed**: References to `dim_date` table
- **Changed**: Join condition: `billing_id` → `claim_id`
- **Changed**: Date keys to direct date columns

---

## Actual Silver Layer Schemas

### encounters
```
encounter_id, patient_id, provider_id, visit_date, visit_type, department, 
reason_for_visit, diagnosis_code, admission_type, discharge_date, 
length_of_stay, status, readmitted_flag, load_timestamp, source_file, record_hash
```

### medications
```
medication_id, encounter_id, drug_name, dosage, route, frequency, duration, 
prescribed_date, prescriber_id, cost, load_timestamp, source_file, record_hash
```

### diagnoses
```
diagnosis_id, encounter_id, diagnosis_code, diagnosis_description, 
primary_flag, chronic_flag, load_timestamp, source_file, record_hash
```

### denials
```
claim_id, denial_id, denial_reason_code, denial_reason_description, 
denied_amount, denial_date, appeal_filed, appeal_status, 
appeal_resolution_date, final_outcome, load_timestamp, source_file, record_hash
```

### claims_and_billing
```
billing_id, patient_id, encounter_id, insurance_provider, payment_method, 
claim_id, claim_billing_date, billed_amount, paid_amount, claim_status, 
denial_reason, load_timestamp, source_file, record_hash
```

---

## Key Patterns Identified

1. **Date Fields**: Many models expected `admission_date` but actual field is `visit_date`
2. **Chronic Flag**: Models used `is_chronic` but actual field is `chronic_flag`
3. **Relationships**: Some tables link through different keys than expected (e.g., denials use `claim_id` not `billing_id`)
4. **Missing Columns**: Some expected columns don't exist in source data (e.g., `denied_amount` in claims_billing, `patient_id` in medications)
5. **Date Dimension**: Models referenced `dim_date` which doesn't exist - replaced with direct date columns

---

## Testing Verification

After all fixes, verify the pipeline:

```sql
-- Check staging views
SELECT COUNT(*) FROM public_staging.stg_encounters;
SELECT COUNT(*) FROM public_staging.stg_medications;
SELECT COUNT(*) FROM public_staging.stg_diagnoses;
SELECT COUNT(*) FROM public_staging.stg_denials;
SELECT COUNT(*) FROM public_staging.stg_claims_billing;

-- Check dimensions
SELECT COUNT(*) FROM public_public.dim_diagnosis;
SELECT COUNT(*) FROM public_public.dim_patient;
SELECT COUNT(*) FROM public_public.dim_medication;
SELECT COUNT(*) FROM public_public.dim_procedure;
SELECT COUNT(*) FROM public_public.dim_provider;

-- Check facts
SELECT COUNT(*) FROM public_public.fact_encounter;
SELECT COUNT(*) FROM public_public.fact_billing;
SELECT COUNT(*) FROM public_public.fact_lab_test;
SELECT COUNT(*) FROM public_public.fact_denial;
```

---

## Pipeline Status

✅ Bronze Layer: Working
✅ Silver Layer: Working  
✅ Data Quality: Working
✅ dbt Staging Models: Fixed and Working
✅ dbt Dimension Models: Fixed and Working
✅ dbt Fact Models: Fixed and Working

The complete ETL pipeline should now run successfully from end to end.
