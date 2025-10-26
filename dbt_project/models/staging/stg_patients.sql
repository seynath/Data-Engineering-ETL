{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select * from {{ source('silver', 'patients') }}
),

cleaned as (
    select
        patient_id,
        first_name,
        last_name,
        dob,
        age,
        gender,
        ethnicity,
        insurance_type,
        marital_status,
        city,
        state,
        zip,
        phone,
        email,
        load_timestamp,
        source_file,
        record_hash
    from source_data
)

select * from cleaned
