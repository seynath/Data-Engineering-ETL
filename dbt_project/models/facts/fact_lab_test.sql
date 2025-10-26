{{
    config(
        materialized='incremental',
        unique_key='lab_id',
        on_schema_change='fail'
    )
}}

with lab_tests as (
    select * from {{ ref('stg_lab_tests') }}
    {% if is_incremental() %}
    where load_timestamp::timestamp > (select max(created_at) from {{ this }})
    {% endif %}
),

encounters as (
    select
        encounter_key,
        encounter_id
    from {{ ref('fact_encounter') }}
),

final as (
    select
        row_number() over (order by lt.lab_id) as lab_test_key,
        lt.lab_id,
        e.encounter_key,
        lt.test_date,
        -- Test details
        lt.test_name,
        lt.test_code,
        lt.specimen_type,
        lt.test_result,
        lt.status,
        -- Determine if result is abnormal based on test_result field
        case
            when lower(lt.test_result) like '%abnormal%' then true
            when lower(lt.test_result) like '%high%' then true
            when lower(lt.test_result) like '%low%' then true
            when lower(lt.test_result) like '%critical%' then true
            when lower(lt.test_result) = 'normal' then false
            else null
        end as is_abnormal,
        -- Audit columns
        current_timestamp as created_at
    from lab_tests lt
    left join encounters e
        on lt.encounter_id = e.encounter_id
)

select * from final
