{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select * from {{ source('silver', 'lab_tests') }}
),

cleaned as (
    select
        lab_id,
        encounter_id,
        test_name,
        test_code,
        test_date,
        specimen_type,
        test_result,
        status,
        load_timestamp,
        source_file,
        record_hash
    from source_data
)

select * from cleaned
