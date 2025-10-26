{{
    config(
        materialized='table',
        unique_key='diagnosis_key'
    )
}}

with source_diagnoses as (
    select * from {{ ref('stg_diagnoses') }}
),

deduplicated as (
    select
        diagnosis_code,
        diagnosis_description,
        chronic_flag,
        row_number() over (partition by diagnosis_code order by load_timestamp desc) as rn
    from source_diagnoses
),

final as (
    select
        row_number() over (order by diagnosis_code) as diagnosis_key,
        diagnosis_code,
        diagnosis_description,
        chronic_flag as is_chronic,
        current_timestamp as created_at
    from deduplicated
    where rn = 1
)

select * from final
