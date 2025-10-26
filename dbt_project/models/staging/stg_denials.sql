{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select * from {{ source('silver', 'denials') }}
),

cleaned as (
    select
        claim_id,
        denial_id,
        denial_reason_code,
        denial_reason_description,
        denied_amount,
        denial_date,
        appeal_filed,
        appeal_status,
        appeal_resolution_date,
        final_outcome,
        load_timestamp,
        source_file,
        record_hash
    from source_data
)

select * from cleaned
