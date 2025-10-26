{{
    config(
        materialized='table',
        unique_key='procedure_key'
    )
}}

with source_procedures as (
    select * from {{ ref('stg_procedures') }}
),

deduplicated as (
    select
        procedure_code,
        procedure_description,
        row_number() over (partition by procedure_code order by load_timestamp desc) as rn
    from source_procedures
),

final as (
    select
        row_number() over (order by procedure_code) as procedure_key,
        procedure_code,
        procedure_description,
        current_timestamp as created_at
    from deduplicated
    where rn = 1
)

select * from final
