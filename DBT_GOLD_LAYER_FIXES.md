# dbt Gold Layer (Dimension) Model Fixes

## Issue
The dbt dimension models were failing due to:
1. Column name mismatches with staging layer
2. SCD Type 2 logic referencing non-existent table on first run

## Fixes Applied

### 1. dim_diagnosis.sql
**Changed:**
- `is_chronic` → `chronic_flag` in the source query
- Mapped `chronic_flag` back to `is_chronic` in the final output for consistency

**Reason:** The staging layer uses `chronic_flag` from the Silver layer, but the dimension model was still referencing the old `is_chronic` column name.

### 2. dim_patient.sql
**Changed:**
- Materialization strategy: `table` → `incremental`
- Added conditional logic using `{% if is_incremental() %}` to handle first run
- On first run, returns empty set with correct schema structure
- Fixed reference to `{{ this }}` to work with incremental materialization

**Reason:** The original SCD Type 2 logic tried to reference the table itself (`{{ this }}`), which doesn't exist on the first run. The incremental materialization strategy properly handles this scenario.

## Technical Details

### dim_patient SCD Type 2 Logic
The patient dimension implements Slowly Changing Dimension Type 2 to track historical changes:

- **First Run**: Creates initial records for all patients with `is_current = true`
- **Subsequent Runs**: 
  - Detects changes by comparing `record_hash`
  - Closes out old records by setting `is_current = false` and `valid_to = current_date`
  - Creates new records for changed patients with new `patient_key`
  - Keeps unchanged records as-is

### Incremental Materialization
Using `incremental` materialization allows the model to:
- Check if the target table exists using `is_incremental()`
- Build incrementally on subsequent runs
- Maintain historical records without full table rebuilds

## Testing
After applying these fixes:

1. The dimension models should build successfully
2. Verify the dimensions were created:
   ```sql
   SELECT COUNT(*) FROM public_public.dim_diagnosis;
   SELECT COUNT(*) FROM public_public.dim_patient;
   SELECT COUNT(*) FROM public_public.dim_medication;
   SELECT COUNT(*) FROM public_public.dim_procedure;
   SELECT COUNT(*) FROM public_public.dim_provider;
   ```

3. Check the patient dimension SCD Type 2 structure:
   ```sql
   SELECT patient_id, patient_key, valid_from, valid_to, is_current 
   FROM public_public.dim_patient 
   WHERE patient_id = 'P001'
   ORDER BY valid_from;
   ```

## Next Steps
Once the dimension models are working, the fact tables (marts) should be able to build successfully, completing the Gold layer.
