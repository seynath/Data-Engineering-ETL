{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select * from {{ source('silver', 'claims_and_billing') }}
),

cleaned as (
    select
        billing_id,
        patient_id,
        encounter_id,
        insurance_provider,
        payment_method,
        claim_id,
        claim_billing_date,
        billed_amount,
        paid_amount,
        claim_status,
        denial_reason,
        load_timestamp,
        source_file,
        record_hash
    from source_data
)

select * from cleaned
