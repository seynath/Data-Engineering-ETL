{{
    config(
        materialized='incremental',
        unique_key='encounter_id',
        on_schema_change='fail'
    )
}}

with encounters as (
    select * from {{ ref('stg_encounters') }}
    {% if is_incremental() %}
    where load_timestamp::timestamp > (select max(created_at) from {{ this }})
    {% endif %}
),

patients as (
    select
        patient_key,
        patient_id,
        is_current
    from {{ ref('dim_patient') }}
    where is_current = true
),

providers as (
    select
        provider_key,
        provider_id
    from {{ ref('dim_provider') }}
),

diagnoses as (
    select
        diagnosis_key,
        diagnosis_code
    from {{ ref('dim_diagnosis') }}
),

-- Note: dim_date not implemented yet, using date values directly
-- date_dimension as (
--     select
--         date_key,
--         date
--     from dim_date
-- ),

-- Aggregate procedure counts per encounter
procedure_counts as (
    select
        encounter_id,
        count(*) as total_procedures
    from {{ ref('stg_medications') }}
    group by encounter_id
),

-- Aggregate medication counts per encounter
medication_counts as (
    select
        encounter_id,
        count(*) as total_medications,
        sum(cost) as total_medication_cost
    from {{ ref('stg_medications') }}
    group by encounter_id
),

-- Aggregate lab test counts per encounter
lab_test_counts as (
    select
        encounter_id,
        count(*) as total_lab_tests
    from {{ ref('stg_lab_tests') }}
    group by encounter_id
),

-- Get billing amounts per encounter
billing_amounts as (
    select
        encounter_id,
        sum(billed_amount) as total_billed,
        sum(paid_amount) as total_paid
    from {{ ref('stg_claims_billing') }}
    group by encounter_id
),

final as (
    select
        row_number() over (order by e.encounter_id) as encounter_key,
        e.encounter_id,
        p.patient_key,
        pr.provider_key,
        e.visit_date,
        e.discharge_date,
        d.diagnosis_key,
        -- Denormalized attributes
        e.visit_type,
        e.department,
        e.admission_type,
        e.length_of_stay,
        e.status,
        e.readmitted_flag,
        -- Aggregated metrics
        coalesce(pc.total_procedures, 0) as total_procedures,
        coalesce(mc.total_medications, 0) as total_medications,
        coalesce(ltc.total_lab_tests, 0) as total_lab_tests,
        coalesce(ba.total_billed, 0) as total_cost,
        -- Audit columns
        current_timestamp as created_at
    from encounters e
    left join patients p
        on e.patient_id = p.patient_id
    left join providers pr
        on e.provider_id = pr.provider_id
    left join diagnoses d
        on e.diagnosis_code = d.diagnosis_code
    left join procedure_counts pc
        on e.encounter_id = pc.encounter_id
    left join medication_counts mc
        on e.encounter_id = mc.encounter_id
    left join lab_test_counts ltc
        on e.encounter_id = ltc.encounter_id
    left join billing_amounts ba
        on e.encounter_id = ba.encounter_id
)

select * from final
