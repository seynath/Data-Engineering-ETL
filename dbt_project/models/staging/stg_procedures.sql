{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select * from {{ source('silver', 'procedures') }}
),

cleaned as (
    select
        procedure_code,
        procedure_description,
        load_timestamp,
        source_file,
        record_hash
    from source_data
)

select * from cleaned
