{{
    config(
        materialized='incremental',
        unique_key='denial_id',
        on_schema_change='fail'
    )
}}

with denials as (
    select * from {{ ref('stg_denials') }}
    {% if is_incremental() %}
    where load_timestamp::timestamp > (select max(created_at) from {{ this }})
    {% endif %}
),

billing as (
    select
        billing_key,
        billing_id
    from {{ ref('fact_billing') }}
),

final as (
    select
        row_number() over (order by dn.denial_id) as denial_key,
        dn.denial_id,
        b.billing_key,
        dn.denial_date,
        dn.appeal_resolution_date,
        -- Denial details
        dn.denial_reason_code,
        dn.denial_reason_description,
        dn.denied_amount,
        -- Appeal tracking
        dn.appeal_filed,
        dn.appeal_status,
        dn.final_outcome,
        -- Audit columns
        current_timestamp as created_at
    from denials dn
    left join billing b
        on dn.claim_id = b.billing_id
)

select * from final
