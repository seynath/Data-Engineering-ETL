{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select * from {{ source('silver', 'encounters') }}
),

cleaned as (
    select
        encounter_id,
        patient_id,
        provider_id,
        visit_type,
        department,
        visit_date,
        discharge_date,
        diagnosis_code,
        admission_type,
        length_of_stay,
        status,
        readmitted_flag,
        load_timestamp,
        source_file,
        record_hash
    from source_data
)

select * from cleaned
