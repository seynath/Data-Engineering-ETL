-- Test to ensure date logic is valid across all tables
-- This test checks that start dates are before or equal to end dates

-- Check encounter dates (visit <= discharge)
with invalid_encounter_dates as (
    select
        'encounter_invalid_dates' as issue_type,
        encounter_id as record_id,
        visit_date,
        discharge_date
    from {{ ref('fact_encounter') }}
    where discharge_date is not null
      and visit_date > discharge_date
),

-- Check patient SCD dates (valid_from <= valid_to)
invalid_patient_dates as (
    select
        'patient_invalid_scd_dates' as issue_type,
        patient_id as record_id,
        valid_from,
        valid_to
    from {{ ref('dim_patient') }}
    where valid_to is not null
      and valid_from > valid_to
),

-- Combine all date logic checks
all_invalid_dates as (
    select issue_type, record_id, visit_date::text as date1, discharge_date::text as date2
    from invalid_encounter_dates
    union all
    select issue_type, record_id, valid_from::text as date1, valid_to::text as date2
    from invalid_patient_dates
)

-- Return any invalid date records (test fails if any rows returned)
select
    issue_type,
    count(*) as invalid_count
from all_invalid_dates
group by issue_type
