{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select * from {{ source('silver', 'diagnoses') }}
),

cleaned as (
    select
        diagnosis_id,
        encounter_id,
        diagnosis_code,
        diagnosis_description,
        primary_flag,
        chronic_flag,
        load_timestamp,
        source_file,
        record_hash
    from source_data
)

select * from cleaned
