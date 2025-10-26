{{
    config(
        materialized='table',
        unique_key='provider_key'
    )
}}

with source_providers as (
    select * from {{ ref('stg_providers') }}
),

deduplicated as (
    select
        provider_id,
        name,
        department,
        specialty,
        npi,
        inhouse,
        location,
        years_experience,
        row_number() over (partition by provider_id order by load_timestamp desc) as rn
    from source_providers
),

final as (
    select
        row_number() over (order by provider_id) as provider_key,
        provider_id,
        name,
        department,
        specialty,
        npi,
        inhouse,
        location,
        years_experience,
        current_timestamp as created_at
    from deduplicated
    where rn = 1
)

select * from final
