{{
    config(
        materialized='table',
        unique_key='medication_key'
    )
}}

with source_medications as (
    select * from {{ ref('stg_medications') }}
),

deduplicated as (
    select
        drug_name,
        dosage,
        route,
        frequency,
        row_number() over (
            partition by drug_name, dosage, route 
            order by load_timestamp desc
        ) as rn
    from source_medications
),

final as (
    select
        row_number() over (order by drug_name, dosage, route) as medication_key,
        drug_name,
        dosage,
        route,
        frequency,
        current_timestamp as created_at
    from deduplicated
    where rn = 1
)

select * from final
