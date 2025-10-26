# Superset Dashboard Specifications

This document provides detailed specifications for creating each dashboard in Apache Superset.

## Dashboard Creation Guide

### General Steps

1. Log in to Superset at http://localhost:8088
2. Navigate to **Dashboards** > **+ Dashboard**
3. Give the dashboard a name and description
4. Add charts by clicking **Edit Dashboard** > **+** > **Create a new chart**
5. Configure each chart according to specifications below
6. Arrange charts in a logical layout
7. Save the dashboard

## 1. Operational Overview Dashboard

**Dashboard Name:** Operational Overview
**Description:** Monitor daily hospital operations and patient flow

### Chart 1.1: Total Patients (Big Number)

- **Chart Type:** Big Number
- **Dataset:** fact_encounter
- **Metric:** COUNT_DISTINCT(patient_key)
- **Time Range:** No filter (all time)
- **Formatting:** Number with thousands separator

**Configuration:**
```
Metric: COUNT_DISTINCT(patient_key)
Subheader: Total Unique Patients
```

### Chart 1.2: Total Encounters (Big Number)

- **Chart Type:** Big Number
- **Dataset:** fact_encounter
- **Metric:** COUNT(encounter_key)
- **Time Range:** No filter (all time)
- **Formatting:** Number with thousands separator

**Configuration:**
```
Metric: COUNT(encounter_key)
Subheader: Total Encounters
```

### Chart 1.3: Total Providers (Big Number)

- **Chart Type:** Big Number
- **Dataset:** fact_encounter
- **Metric:** COUNT_DISTINCT(provider_key)
- **Time Range:** No filter (all time)
- **Formatting:** Number with thousands separator

**Configuration:**
```
Metric: COUNT_DISTINCT(provider_key)
Subheader: Active Providers
```

### Chart 1.4: Daily Admission Trends (Line Chart)

- **Chart Type:** Line Chart
- **Dataset:** fact_encounter (joined with dim_date)
- **X-Axis:** date (from dim_date via visit_date_key)
- **Metrics:** COUNT(encounter_key)
- **Group By:** visit_type
- **Time Range:** Last 30 days
- **Time Grain:** Day

**SQL Query:**
```sql
SELECT 
    d.date,
    e.visit_type,
    COUNT(e.encounter_key) as encounter_count
FROM fact_encounter e
JOIN dim_date d ON e.visit_date_key = d.date_key
WHERE d.date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY d.date, e.visit_type
ORDER BY d.date
```

**Configuration:**
```
X-Axis: date
Metrics: COUNT(encounter_key)
Series: visit_type
Show Legend: Yes
Line Style: Smooth
```

### Chart 1.5: Top 10 Departments (Bar Chart)

- **Chart Type:** Bar Chart
- **Dataset:** fact_encounter
- **X-Axis:** department
- **Metric:** COUNT_DISTINCT(patient_key)
- **Sort:** Descending
- **Limit:** 10

**Configuration:**
```
X-Axis: department
Metric: COUNT_DISTINCT(patient_key)
Sort Descending: Yes
Row Limit: 10
Show Values: Yes
```

### Chart 1.6: Visit Type Distribution (Pie Chart)

- **Chart Type:** Pie Chart
- **Dataset:** fact_encounter
- **Dimension:** visit_type
- **Metric:** COUNT(encounter_key)

**Configuration:**
```
Dimension: visit_type
Metric: COUNT(encounter_key)
Show Labels: Yes
Show Percentage: Yes
Donut: No
```

### Chart 1.7: Recent Encounters (Table)

- **Chart Type:** Table
- **Dataset:** fact_encounter
- **Columns:** encounter_id, patient_key, provider_key, visit_date_key, visit_type, status
- **Sort:** visit_date_key DESC
- **Limit:** 20

**SQL Query:**
```sql
SELECT 
    e.encounter_id,
    e.patient_key,
    e.provider_key,
    d.date as visit_date,
    e.visit_type,
    e.status
FROM fact_encounter e
JOIN dim_date d ON e.visit_date_key = d.date_key
ORDER BY d.date DESC
LIMIT 20
```

**Configuration:**
```
Columns: encounter_id, patient_key, provider_key, visit_date, visit_type, status
Page Length: 20
Show Cell Bars: No
```

## 2. Financial Analytics Dashboard

**Dashboard Name:** Financial Analytics
**Description:** Track revenue, payments, and claim denials

### Chart 2.1: Total Billed (Big Number)

- **Chart Type:** Big Number with Trendline
- **Dataset:** fact_billing
- **Metric:** SUM(billed_amount)
- **Time Range:** Last 90 days
- **Formatting:** Currency ($)

**Configuration:**
```
Metric: SUM(billed_amount)
Subheader: Total Billed Amount
Number Format: $,.2f
Show Trendline: Yes
```

### Chart 2.2: Total Paid (Big Number)

- **Chart Type:** Big Number with Trendline
- **Dataset:** fact_billing
- **Metric:** SUM(paid_amount)
- **Time Range:** Last 90 days
- **Formatting:** Currency ($)

**Configuration:**
```
Metric: SUM(paid_amount)
Subheader: Total Paid Amount
Number Format: $,.2f
Show Trendline: Yes
```

### Chart 2.3: Collection Rate (Big Number)

- **Chart Type:** Big Number
- **Dataset:** fact_billing
- **Metric:** AVG(collection_rate)
- **Time Range:** Last 90 days
- **Formatting:** Percentage (%)

**Configuration:**
```
Metric: AVG(collection_rate)
Subheader: Average Collection Rate
Number Format: .2f%
```

### Chart 2.4: Denial Rate (Big Number)

- **Chart Type:** Big Number
- **Dataset:** fact_billing
- **Metric:** AVG(denial_rate)
- **Time Range:** Last 90 days
- **Formatting:** Percentage (%)

**Configuration:**
```
Metric: AVG(denial_rate)
Subheader: Average Denial Rate
Number Format: .2f%
```

### Chart 2.5: Daily Revenue Trends (Line Chart)

- **Chart Type:** Line Chart
- **Dataset:** fact_billing (joined with dim_date)
- **X-Axis:** date (from dim_date)
- **Metrics:** SUM(billed_amount), SUM(paid_amount)
- **Time Range:** Last 90 days

**SQL Query:**
```sql
SELECT 
    d.date,
    SUM(b.billed_amount) as total_billed,
    SUM(b.paid_amount) as total_paid
FROM fact_billing b
JOIN dim_date d ON b.claim_billing_date_key = d.date_key
WHERE d.date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY d.date
ORDER BY d.date
```

**Configuration:**
```
X-Axis: date
Metrics: SUM(billed_amount), SUM(paid_amount)
Show Legend: Yes
Y-Axis Format: $,.0f
```

### Chart 2.6: Revenue by Insurance Provider (Bar Chart)

- **Chart Type:** Bar Chart (Horizontal)
- **Dataset:** fact_billing
- **X-Axis:** SUM(billed_amount)
- **Y-Axis:** insurance_provider
- **Sort:** Descending
- **Limit:** 10

**Configuration:**
```
Metric: SUM(billed_amount)
Series: insurance_provider
Sort Descending: Yes
Row Limit: 10
Bar Values: Yes
Number Format: $,.0f
```

### Chart 2.7: Claim Status Breakdown (Funnel Chart)

- **Chart Type:** Funnel Chart
- **Dataset:** fact_billing
- **Dimension:** claim_status
- **Metric:** COUNT(billing_key)

**SQL Query:**
```sql
SELECT 
    claim_status,
    COUNT(billing_key) as claim_count
FROM fact_billing
GROUP BY claim_status
ORDER BY claim_count DESC
```

**Configuration:**
```
Dimension: claim_status
Metric: COUNT(billing_key)
Show Labels: Yes
Show Percentage: Yes
```

### Chart 2.8: Top Denial Reasons (Table)

- **Chart Type:** Table
- **Dataset:** fact_denial (joined with fact_billing)
- **Columns:** denial_reason_description, COUNT(*), SUM(denied_amount)
- **Sort:** COUNT(*) DESC
- **Limit:** 10

**SQL Query:**
```sql
SELECT 
    d.denial_reason_description,
    COUNT(*) as denial_count,
    SUM(d.denied_amount) as total_denied
FROM fact_denial d
GROUP BY d.denial_reason_description
ORDER BY denial_count DESC
LIMIT 10
```

**Configuration:**
```
Columns: denial_reason_description, denial_count, total_denied
Page Length: 10
Number Format (total_denied): $,.2f
```

## 3. Clinical Insights Dashboard

**Dashboard Name:** Clinical Insights
**Description:** Analyze diagnoses, procedures, and clinical outcomes

### Chart 3.1: Top 20 Diagnoses (Bar Chart)

- **Chart Type:** Bar Chart (Horizontal)
- **Dataset:** fact_encounter (joined with dim_diagnosis)
- **X-Axis:** COUNT(*)
- **Y-Axis:** diagnosis_description
- **Limit:** 20

**SQL Query:**
```sql
SELECT 
    diag.diagnosis_description,
    COUNT(*) as diagnosis_count
FROM fact_encounter e
JOIN dim_diagnosis diag ON e.diagnosis_key = diag.diagnosis_key
GROUP BY diag.diagnosis_description
ORDER BY diagnosis_count DESC
LIMIT 20
```

**Configuration:**
```
Metric: COUNT(*)
Series: diagnosis_description
Sort Descending: Yes
Row Limit: 20
Show Values: Yes
```

### Chart 3.2: Top 20 Procedures (Bar Chart)

- **Chart Type:** Bar Chart (Horizontal)
- **Dataset:** Custom SQL (fact_encounter with procedure data)
- **X-Axis:** COUNT(*)
- **Y-Axis:** procedure_description
- **Limit:** 20

**Note:** This requires joining with procedure data through a bridge table or denormalized structure.

### Chart 3.3: Readmission Rates Heatmap (Heatmap)

- **Chart Type:** Heatmap
- **Dataset:** fact_encounter (joined with dim_diagnosis)
- **X-Axis:** department
- **Y-Axis:** diagnosis_description (top 10)
- **Metric:** AVG(readmitted_flag) * 100

**SQL Query:**
```sql
WITH top_diagnoses AS (
    SELECT diagnosis_key
    FROM fact_encounter
    GROUP BY diagnosis_key
    ORDER BY COUNT(*) DESC
    LIMIT 10
)
SELECT 
    e.department,
    diag.diagnosis_description,
    AVG(CASE WHEN e.readmitted_flag THEN 1 ELSE 0 END) * 100 as readmission_rate
FROM fact_encounter e
JOIN dim_diagnosis diag ON e.diagnosis_key = diag.diagnosis_key
WHERE e.diagnosis_key IN (SELECT diagnosis_key FROM top_diagnoses)
GROUP BY e.department, diag.diagnosis_description
```

**Configuration:**
```
X-Axis: department
Y-Axis: diagnosis_description
Metric: readmission_rate
Color Scheme: Red-Yellow-Green (reversed)
Show Values: Yes
Number Format: .1f%
```

### Chart 3.4: Chronic Condition Patients (Table)

- **Chart Type:** Table
- **Dataset:** fact_encounter (joined with dim_diagnosis)
- **Filter:** is_chronic = TRUE
- **Columns:** diagnosis_description, unique_patients, total_encounters
- **Sort:** unique_patients DESC

**SQL Query:**
```sql
SELECT 
    diag.diagnosis_description,
    COUNT(DISTINCT e.patient_key) as unique_patients,
    COUNT(e.encounter_key) as total_encounters
FROM fact_encounter e
JOIN dim_diagnosis diag ON e.diagnosis_key = diag.diagnosis_key
WHERE diag.is_chronic = TRUE
GROUP BY diag.diagnosis_description
ORDER BY unique_patients DESC
```

**Configuration:**
```
Columns: diagnosis_description, unique_patients, total_encounters
Page Length: 20
Show Cell Bars: Yes (for numeric columns)
```

## 4. Provider Performance Dashboard

**Dashboard Name:** Provider Performance
**Description:** Analyze provider utilization and performance

### Chart 4.1: Patient Volume by Provider (Bar Chart)

- **Chart Type:** Bar Chart (Horizontal)
- **Dataset:** fact_encounter (joined with dim_provider)
- **X-Axis:** COUNT_DISTINCT(patient_key)
- **Y-Axis:** provider_name
- **Limit:** 20

**SQL Query:**
```sql
SELECT 
    p.name as provider_name,
    COUNT(DISTINCT e.patient_key) as patient_count
FROM fact_encounter e
JOIN dim_provider p ON e.provider_key = p.provider_key
GROUP BY p.name
ORDER BY patient_count DESC
LIMIT 20
```

### Chart 4.2: Experience vs Volume (Scatter Plot)

- **Chart Type:** Scatter Plot
- **Dataset:** Custom SQL (aggregated provider data)
- **X-Axis:** years_experience
- **Y-Axis:** encounter_count
- **Size:** patient_count

**SQL Query:**
```sql
SELECT 
    p.name as provider_name,
    p.years_experience,
    COUNT(e.encounter_key) as encounter_count,
    COUNT(DISTINCT e.patient_key) as patient_count
FROM dim_provider p
LEFT JOIN fact_encounter e ON p.provider_key = e.provider_key
GROUP BY p.provider_key, p.name, p.years_experience
```

**Configuration:**
```
X-Axis: years_experience
Y-Axis: encounter_count
Size: patient_count
Entity: provider_name
```

### Chart 4.3: Provider Utilization (Table)

- **Chart Type:** Table
- **Dataset:** fact_encounter (joined with dim_provider)
- **Columns:** provider_name, specialty, department, encounter_count, patient_count
- **Sort:** encounter_count DESC

**SQL Query:**
```sql
SELECT 
    p.name as provider_name,
    p.specialty,
    p.department,
    COUNT(e.encounter_key) as encounter_count,
    COUNT(DISTINCT e.patient_key) as patient_count
FROM dim_provider p
LEFT JOIN fact_encounter e ON p.provider_key = e.provider_key
GROUP BY p.provider_key, p.name, p.specialty, p.department
ORDER BY encounter_count DESC
```

### Chart 4.4: Average Length of Stay by Provider (Bar Chart)

- **Chart Type:** Bar Chart (Horizontal)
- **Dataset:** fact_encounter (joined with dim_provider)
- **X-Axis:** AVG(length_of_stay)
- **Y-Axis:** provider_name
- **Limit:** 20

**SQL Query:**
```sql
SELECT 
    p.name as provider_name,
    AVG(e.length_of_stay) as avg_los
FROM fact_encounter e
JOIN dim_provider p ON e.provider_key = p.provider_key
WHERE e.length_of_stay IS NOT NULL
GROUP BY p.name
ORDER BY avg_los DESC
LIMIT 20
```

## 5. Medication Analysis Dashboard

**Dashboard Name:** Medication Analysis
**Description:** Track medication prescriptions and costs

### Chart 5.1: Top 20 Medications (Bar Chart)

- **Chart Type:** Bar Chart (Horizontal)
- **Dataset:** Custom SQL (medication prescriptions)
- **X-Axis:** COUNT(*)
- **Y-Axis:** drug_name
- **Limit:** 20

**Note:** This requires medication prescription data which may need to be added to the data model.

### Chart 5.2: Medication Cost Trends (Line Chart)

- **Chart Type:** Line Chart
- **Dataset:** Custom SQL (medication costs over time)
- **X-Axis:** date
- **Metric:** SUM(cost)
- **Time Range:** Last 90 days

### Chart 5.3: Prescriptions by Prescriber (Bar Chart)

- **Chart Type:** Bar Chart (Horizontal)
- **Dataset:** Custom SQL (prescriptions by provider)
- **X-Axis:** COUNT(*)
- **Y-Axis:** provider_name
- **Limit:** 20

### Chart 5.4: High-Cost Medications (Table)

- **Chart Type:** Table
- **Dataset:** Custom SQL (medication costs)
- **Filter:** cost > 100
- **Columns:** drug_name, dosage, prescription_count, avg_cost
- **Sort:** avg_cost DESC
- **Limit:** 20

## Dashboard Layout Recommendations

### Grid Layout

Use a 12-column grid system for responsive layouts:

- **KPI Cards:** 3 columns each (4 cards per row)
- **Charts:** 6-12 columns depending on complexity
- **Tables:** 12 columns (full width)

### Color Scheme

Use consistent colors across dashboards:

- **Primary:** #1f77b4 (blue)
- **Success:** #2ca02c (green)
- **Warning:** #ff7f0e (orange)
- **Danger:** #d62728 (red)
- **Info:** #9467bd (purple)

### Filters

Add dashboard-level filters for:

- **Date Range:** Allow users to filter by date
- **Department:** Filter by hospital department
- **Insurance Type:** Filter by insurance provider
- **Visit Type:** Filter by encounter type

## Export and Import

### Exporting Dashboards

1. Navigate to the dashboard
2. Click the three dots menu (⋮)
3. Select "Export"
4. Save the JSON file

### Importing Dashboards

1. Navigate to Dashboards
2. Click "Import Dashboard"
3. Upload the JSON file
4. Verify and save

## Maintenance

### Regular Tasks

1. **Weekly:** Review dashboard performance and optimize slow queries
2. **Monthly:** Update dashboard descriptions and documentation
3. **Quarterly:** Review metrics with stakeholders and adjust as needed
4. **Annually:** Archive unused dashboards and create new ones based on feedback

### Performance Optimization

1. Add database indexes for frequently queried columns
2. Use materialized views for complex aggregations
3. Implement incremental refresh for large datasets
4. Monitor query execution times and optimize SQL

## Support

For dashboard creation assistance:
- Review Superset documentation: https://superset.apache.org/docs/creating-charts-dashboards/creating-your-first-dashboard
- Contact the data engineering team
- Check the Healthcare ETL Pipeline documentation
