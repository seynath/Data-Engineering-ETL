{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select * from {{ source('silver', 'providers') }}
),

cleaned as (
    select
        provider_id,
        name,
        department,
        specialty,
        npi,
        inhouse,
        location,
        years_experience,
        load_timestamp,
        source_file,
        record_hash
    from source_data
)

select * from cleaned
