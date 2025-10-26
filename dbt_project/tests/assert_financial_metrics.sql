-- Test to ensure financial metrics are logically consistent
-- This test checks that financial calculations make sense

-- Check that paid <= billed (denied_amount removed from fact_billing)
with invalid_billing_amounts as (
    select
        'billing_amounts_exceed_billed' as issue_type,
        billing_id,
        billed_amount,
        paid_amount
    from {{ ref('fact_billing') }}
    where paid_amount > billed_amount + 0.01  -- Allow for small rounding errors
),

-- Check that payment_rate is calculated correctly
invalid_payment_rates as (
    select
        'payment_rate_incorrect' as issue_type,
        billing_id,
        billed_amount,
        paid_amount,
        payment_rate,
        case
            when billed_amount > 0 then round(((paid_amount::numeric / billed_amount::numeric) * 100)::numeric, 2)
            else 0
        end as expected_rate
    from {{ ref('fact_billing') }}
    where billed_amount > 0
      and abs(payment_rate - round(((paid_amount::numeric / billed_amount::numeric) * 100)::numeric, 2)) > 0.01
),

-- Combine all financial checks
all_invalid_financials as (
    select issue_type, billing_id as record_id from invalid_billing_amounts
    union all
    select issue_type, billing_id as record_id from invalid_payment_rates
)

-- Return any invalid financial records (test fails if any rows returned)
select
    issue_type,
    count(*) as invalid_count
from all_invalid_financials
group by issue_type
