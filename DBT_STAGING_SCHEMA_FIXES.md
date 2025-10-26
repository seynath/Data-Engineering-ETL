# dbt Staging Model Schema Fixes

## Issue
The dbt staging models were failing because they referenced column names that didn't match the actual Silver layer table schemas in PostgreSQL.

## Root Cause
The dbt models were created based on an assumed schema, but the actual CSV data and Silver layer transformations used different column names.

## Fixes Applied

### 1. stg_encounters.sql
**Changed:**
- `admission_date` → `visit_date`

**Reason:** The encounters table uses `visit_date` as the primary date field, not `admission_date`.

### 2. stg_medications.sql
**Changed:**
- Removed `patient_id` (doesn't exist in medications table)
- `start_date` → `prescribed_date`
- `end_date` → `duration`

**Reason:** The medications table links to patients through `encounter_id`, not directly via `patient_id`. Date fields use different naming.

### 3. stg_diagnoses.sql
**Changed:**
- `is_chronic` → `chronic_flag`
- Added missing columns: `diagnosis_id`, `encounter_id`, `primary_flag`

**Reason:** The diagnoses table uses `chronic_flag` instead of `is_chronic` and includes additional fields for proper relationships.

### 4. stg_denials.sql
**Changed:**
- `billing_id` → `claim_id`

**Reason:** The denials table references claims via `claim_id`, not `billing_id`.

### 5. stg_claims_billing.sql
**Changed:**
- Removed `denied_amount` (doesn't exist in claims_and_billing table)
- Reordered columns to match actual schema
- Added `claim_id` field

**Reason:** Denial amounts are tracked in the separate denials table, not in claims_and_billing.

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

## Testing
After applying these fixes, the dbt staging models should successfully create views in PostgreSQL. You can test by:

1. Triggering the healthcare_etl_pipeline DAG in Airflow
2. The `dbt_gold_layer.dbt_run_staging` task should now complete successfully
3. Verify the staging views were created:
   ```sql
   SELECT * FROM public_staging.stg_encounters LIMIT 5;
   SELECT * FROM public_staging.stg_medications LIMIT 5;
   SELECT * FROM public_staging.stg_diagnoses LIMIT 5;
   SELECT * FROM public_staging.stg_denials LIMIT 5;
   SELECT * FROM public_staging.stg_claims_billing LIMIT 5;
   ```

## Test Definition Updates

In addition to the model SQL files, the test definitions in `schema.yml` and `sources.yml` also needed updates:

### schema.yml
- **stg_denials**: Changed `billing_id` → `claim_id` in tests
- **stg_diagnoses**: Updated to test `diagnosis_id` as primary key, added `encounter_id` relationship test

### sources.yml
- **denials source**: Changed `billing_id` → `claim_id`
- **encounters source**: Changed `admission_date` → `visit_date`
- **medications source**: Removed `patient_id`, changed `start_date`/`end_date` → `prescribed_date`/`duration`
- **diagnoses source**: Changed primary key to `diagnosis_id`, added `encounter_id`, changed `is_chronic` → `chronic_flag`
- **claims_and_billing source**: Removed `denied_amount`, added `claim_id`, reordered columns

## Next Steps
Once the staging models are working, the Gold layer models (marts) should be able to build successfully, creating the final analytical tables for reporting and dashboards.
