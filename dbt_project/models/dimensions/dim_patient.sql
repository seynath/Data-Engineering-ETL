{{
    config(
        materialized='incremental',
        unique_key='patient_key',
        on_schema_change='fail'
    )
}}

with source_patients as (
    select * from {{ ref('stg_patients') }}
),

-- Get the current state of patients from the existing dimension table
-- Use a conditional to handle first run when table doesn't exist
existing_patients as (
    {% if is_incremental() %}
    select
        patient_key,
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
        valid_from,
        valid_to,
        is_current,
        created_at,
        updated_at,
        record_hash
    from {{ this }}
    where is_current = true
    {% else %}
    -- On first run, return empty set with correct structure
    select
        null::bigint as patient_key,
        null::varchar as patient_id,
        null::varchar as first_name,
        null::varchar as last_name,
        null::date as dob,
        null::integer as age,
        null::varchar as gender,
        null::varchar as ethnicity,
        null::varchar as insurance_type,
        null::varchar as marital_status,
        null::varchar as city,
        null::varchar as state,
        null::varchar as zip,
        null::varchar as phone,
        null::varchar as email,
        null::date as valid_from,
        null::date as valid_to,
        null::boolean as is_current,
        null::timestamp as created_at,
        null::timestamp as updated_at,
        null::varchar as record_hash
    where false
    {% endif %}
),

-- Identify new and changed records
changes as (
    select
        s.patient_id,
        s.first_name,
        s.last_name,
        s.dob::date as dob,
        s.age,
        s.gender,
        s.ethnicity,
        s.insurance_type,
        s.marital_status,
        s.city,
        s.state,
        s.zip,
        s.phone,
        s.email,
        s.record_hash,
        s.load_timestamp,
        e.patient_key as existing_key,
        e.record_hash as existing_hash,
        case
            when e.patient_key is null then 'new'
            when e.record_hash != s.record_hash then 'changed'
            else 'unchanged'
        end as change_type
    from source_patients s
    left join existing_patients e
        on s.patient_id = e.patient_id
),

-- Close out old records for changed patients
closed_records as (
    select
        patient_key,
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
        valid_from,
        current_date as valid_to,
        false as is_current,
        created_at,
        current_timestamp as updated_at,
        record_hash
    from existing_patients
    where patient_id in (
        select patient_id from changes where change_type = 'changed'
    )
),

-- Create new records for new and changed patients
new_records as (
    select
        row_number() over (order by patient_id) + coalesce((select max(patient_key) from existing_patients), 0) as patient_key,
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
        current_date as valid_from,
        null::date as valid_to,
        true as is_current,
        current_timestamp as created_at,
        current_timestamp as updated_at,
        record_hash
    from changes
    where change_type in ('new', 'changed')
),

-- Keep unchanged records
unchanged_records as (
    select
        patient_key,
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
        valid_from,
        valid_to,
        is_current,
        created_at,
        current_timestamp as updated_at,
        record_hash
    from existing_patients
    where patient_id in (
        select patient_id from changes where change_type = 'unchanged'
    )
),

-- Union all records
final as (
    select
        patient_key,
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
        valid_from,
        valid_to,
        is_current,
        created_at,
        updated_at,
        record_hash
    from closed_records
    
    union all
    
    select
        patient_key,
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
        valid_from,
        valid_to,
        is_current,
        created_at,
        updated_at,
        record_hash
    from new_records
    
    union all
    
    select
        patient_key,
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
        valid_from,
        valid_to,
        is_current,
        created_at,
        updated_at,
        record_hash
    from unchanged_records
)

select * from final
