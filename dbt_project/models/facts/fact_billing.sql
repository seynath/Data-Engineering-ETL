{{
    config(
        materialized='incremental',
        unique_key='billing_id',
        on_schema_change='fail'
    )
}}

with billing as (
    select * from {{ ref('stg_claims_billing') }}
    {% if is_incremental() %}
    where load_timestamp::timestamp > (select max(created_at) from {{ this }})
    {% endif %}
),

encounters as (
    select
        encounter_key,
        encounter_id
    from {{ ref('fact_encounter') }}
),

patients as (
    select
        patient_key,
        patient_id,
        is_current
    from {{ ref('dim_patient') }}
    where is_current = true
),

final as (
    select
        row_number() over (order by b.billing_id) as billing_key,
        b.billing_id,
        e.encounter_key,
        p.patient_key,
        b.claim_billing_date,
        -- Denormalized attributes
        b.insurance_provider,
        b.payment_method,
        b.claim_status,
        b.denial_reason,
        -- Financial metrics
        b.billed_amount,
        b.paid_amount,
        -- Calculate payment rate as percentage
        case
            when b.billed_amount > 0 then
                round(((b.paid_amount::numeric / b.billed_amount::numeric) * 100)::numeric, 2)
            else 0
        end as payment_rate,
        -- Audit columns
        current_timestamp as created_at
    from billing b
    left join encounters e
        on b.encounter_id = e.encounter_id
    left join patients p
        on b.patient_id = p.patient_id
)

select * from final
