-- Test to ensure all fact tables have valid foreign keys to dimension tables
-- This test will fail if any orphaned records are found

-- Check fact_encounter references
with encounter_patient_check as (
    select count(*) as orphaned_count
    from {{ ref('fact_encounter') }} f
    left join {{ ref('dim_patient') }} d
        on f.patient_key = d.patient_key
    where d.patient_key is null
      and f.patient_key is not null
),

encounter_provider_check as (
    select count(*) as orphaned_count
    from {{ ref('fact_encounter') }} f
    left join {{ ref('dim_provider') }} d
        on f.provider_key = d.provider_key
    where d.provider_key is null
      and f.provider_key is not null
),

encounter_diagnosis_check as (
    select count(*) as orphaned_count
    from {{ ref('fact_encounter') }} f
    left join {{ ref('dim_diagnosis') }} d
        on f.diagnosis_key = d.diagnosis_key
    where d.diagnosis_key is null
      and f.diagnosis_key is not null
),

-- Check fact_billing references
billing_encounter_check as (
    select count(*) as orphaned_count
    from {{ ref('fact_billing') }} f
    left join {{ ref('fact_encounter') }} e
        on f.encounter_key = e.encounter_key
    where e.encounter_key is null
      and f.encounter_key is not null
),

billing_patient_check as (
    select count(*) as orphaned_count
    from {{ ref('fact_billing') }} f
    left join {{ ref('dim_patient') }} d
        on f.patient_key = d.patient_key
    where d.patient_key is null
      and f.patient_key is not null
),

-- Check fact_lab_test references
lab_encounter_check as (
    select count(*) as orphaned_count
    from {{ ref('fact_lab_test') }} f
    left join {{ ref('fact_encounter') }} e
        on f.encounter_key = e.encounter_key
    where e.encounter_key is null
      and f.encounter_key is not null
),

-- Check fact_denial references
denial_billing_check as (
    select count(*) as orphaned_count
    from {{ ref('fact_denial') }} f
    left join {{ ref('fact_billing') }} b
        on f.billing_key = b.billing_key
    where b.billing_key is null
      and f.billing_key is not null
),

-- Aggregate all checks
all_checks as (
    select 'encounter_patient' as check_name, orphaned_count from encounter_patient_check
    union all
    select 'encounter_provider', orphaned_count from encounter_provider_check
    union all
    select 'encounter_diagnosis', orphaned_count from encounter_diagnosis_check
    union all
    select 'billing_encounter', orphaned_count from billing_encounter_check
    union all
    select 'billing_patient', orphaned_count from billing_patient_check
    union all
    select 'lab_encounter', orphaned_count from lab_encounter_check
    union all
    select 'denial_billing', orphaned_count from denial_billing_check
)

-- Return rows where orphaned records exist (test fails if any rows returned)
select
    check_name,
    orphaned_count
from all_checks
where orphaned_count > 0
