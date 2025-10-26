{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select * from {{ source('silver', 'medications') }}
),

cleaned as (
    select
        medication_id,
        encounter_id,
        drug_name,
        dosage,
        route,
        frequency,
        prescribed_date,
        duration,
        prescriber_id,
        cost,
        load_timestamp,
        source_file,
        record_hash
    from source_data
)

select * from cleaned
