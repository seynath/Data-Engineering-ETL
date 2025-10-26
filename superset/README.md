# Apache Superset Dashboard Setup

This directory contains configuration and documentation for Apache Superset dashboards for the Healthcare ETL Pipeline.

## Overview

The Superset setup includes:
- Database connection to PostgreSQL healthcare_warehouse
- Datasets for all dimension and fact tables
- Calculated columns for analytics metrics
- Pre-configured dashboards for operational, financial, and clinical insights

## Quick Start

### 1. Start Superset

Superset is included in the docker-compose.yml configuration:

```bash
# Start all services including Superset
docker-compose up -d

# Check Superset logs
docker-compose logs -f superset
```

Superset will be available at: http://localhost:8088

Default credentials:
- Username: `admin`
- Password: `admin`

### 2. Setup Database Connection

Run the setup script to create the database connection:

```bash
# Wait for Superset to be fully started (may take 30-60 seconds)
python superset_setup.py --action setup --wait 60
```

This will:
- Create a database connection to healthcare_warehouse
- Test the connection
- Verify access to Gold layer tables

### 3. Create Datasets

After running the ETL pipeline to populate Gold layer tables:

```bash
python superset_setup.py --action setup-datasets
```

This will create datasets for all dimension and fact tables with calculated columns.

### 4. Create Dashboards

Dashboards can be created through the Superset UI or imported from JSON configurations.

## Database Connection Details

**Connection Name:** Healthcare Warehouse

**Connection String:**
```
postgresql://etl_user:etl_password@warehouse-db:5432/healthcare_warehouse
```

**Tables Available:**
- Dimension Tables: dim_patient, dim_provider, dim_diagnosis, dim_procedure, dim_medication, dim_date
- Fact Tables: fact_encounter, fact_billing, fact_lab_test, fact_denial

## Datasets and Calculated Columns

### fact_billing Dataset

Calculated columns for financial analytics:

1. **collection_rate** (Collection Rate %)
   ```sql
   CASE WHEN billed_amount > 0 
   THEN (paid_amount / billed_amount) * 100 
   ELSE 0 END
   ```

2. **denial_rate** (Denial Rate %)
   ```sql
   CASE WHEN billed_amount > 0 
   THEN (denied_amount / billed_amount) * 100 
   ELSE 0 END
   ```

3. **outstanding_amount** (Outstanding Amount)
   ```sql
   billed_amount - paid_amount - denied_amount
   ```

## Dashboard Specifications

### 1. Operational Overview Dashboard

**Purpose:** Monitor daily hospital operations and patient flow

**Charts:**

1. **KPI Cards**
   - Total Patients: `COUNT(DISTINCT patient_key)`
   - Total Encounters: `COUNT(encounter_key)`
   - Total Providers: `COUNT(DISTINCT provider_key)`

2. **Daily Admission Trends** (Line Chart)
   - X-axis: visit_date (from dim_date)
   - Y-axis: COUNT(encounter_key)
   - Group by: visit_type
   - Time range: Last 30 days

3. **Top 10 Departments** (Bar Chart)
   - X-axis: department
   - Y-axis: COUNT(DISTINCT patient_key)
   - Limit: 10
   - Sort: Descending

4. **Visit Type Distribution** (Pie Chart)
   - Dimension: visit_type
   - Metric: COUNT(encounter_key)

5. **Recent Encounters** (Table)
   - Columns: encounter_id, patient_key, provider_key, visit_date, visit_type, status
   - Sort: visit_date DESC
   - Limit: 20

### 2. Financial Analytics Dashboard

**Purpose:** Track revenue, payments, and claim denials

**Charts:**

1. **KPI Cards**
   - Total Billed: `SUM(billed_amount)`
   - Total Paid: `SUM(paid_amount)`
   - Collection Rate: `AVG(collection_rate)`
   - Denial Rate: `AVG(denial_rate)`

2. **Daily Revenue Trends** (Line Chart)
   - X-axis: claim_billing_date (from dim_date)
   - Y-axis: SUM(billed_amount), SUM(paid_amount)
   - Time range: Last 90 days

3. **Revenue by Insurance Provider** (Bar Chart)
   - X-axis: insurance_provider
   - Y-axis: SUM(billed_amount)
   - Sort: Descending
   - Limit: 10

4. **Claim Status Breakdown** (Funnel Chart)
   - Stages: claim_status
   - Metric: COUNT(billing_key)

5. **Top Denial Reasons** (Table)
   - Columns: denial_reason, COUNT(*), SUM(denied_amount)
   - Sort: COUNT(*) DESC
   - Limit: 10

### 3. Clinical Insights Dashboard

**Purpose:** Analyze diagnoses, procedures, and clinical outcomes

**Charts:**

1. **Top 20 Diagnoses** (Bar Chart)
   - X-axis: diagnosis_description (from dim_diagnosis)
   - Y-axis: COUNT(*)
   - Limit: 20
   - Sort: Descending

2. **Top 20 Procedures** (Bar Chart)
   - X-axis: procedure_description (from dim_procedure)
   - Y-axis: COUNT(*)
   - Limit: 20
   - Sort: Descending

3. **Readmission Rates Heatmap** (Heatmap)
   - X-axis: department
   - Y-axis: diagnosis_description (top 10)
   - Metric: AVG(readmitted_flag) * 100

4. **Chronic Condition Patients** (Table)
   - Filter: is_chronic = TRUE
   - Columns: diagnosis_description, COUNT(DISTINCT patient_key), COUNT(encounter_key)
   - Sort: COUNT(DISTINCT patient_key) DESC

### 4. Provider Performance Dashboard

**Purpose:** Analyze provider utilization and performance

**Charts:**

1. **Patient Volume by Provider** (Bar Chart)
   - X-axis: provider_name (from dim_provider)
   - Y-axis: COUNT(DISTINCT patient_key)
   - Limit: 20
   - Sort: Descending

2. **Experience vs Volume** (Scatter Plot)
   - X-axis: years_experience (from dim_provider)
   - Y-axis: COUNT(encounter_key)
   - Size: COUNT(DISTINCT patient_key)

3. **Provider Utilization** (Table)
   - Columns: provider_name, specialty, department, COUNT(encounter_key), COUNT(DISTINCT patient_key)
   - Sort: COUNT(encounter_key) DESC

4. **Average Length of Stay by Provider** (Bar Chart)
   - X-axis: provider_name
   - Y-axis: AVG(length_of_stay)
   - Limit: 20
   - Sort: Descending

### 5. Medication Analysis Dashboard

**Purpose:** Track medication prescriptions and costs

**Charts:**

1. **Top 20 Medications** (Bar Chart)
   - X-axis: drug_name (from dim_medication)
   - Y-axis: COUNT(*)
   - Limit: 20
   - Sort: Descending

2. **Medication Cost Trends** (Line Chart)
   - X-axis: prescription_date (from dim_date)
   - Y-axis: SUM(cost)
   - Time range: Last 90 days

3. **Prescriptions by Prescriber** (Bar Chart)
   - X-axis: provider_name (from dim_provider)
   - Y-axis: COUNT(medication_key)
   - Limit: 20
   - Sort: Descending

4. **High-Cost Medications** (Table)
   - Columns: drug_name, dosage, COUNT(*), AVG(cost)
   - Filter: cost > 100
   - Sort: AVG(cost) DESC
   - Limit: 20

## Dashboard Refresh Configuration

### Automatic Refresh

Dashboards are automatically refreshed after successful ETL pipeline completion via the `refresh_superset_cache` task in the Airflow DAG.

### Manual Refresh

To manually refresh dashboards:

1. Navigate to the dashboard in Superset
2. Click the refresh button (circular arrow icon)
3. Or use the keyboard shortcut: `Ctrl+R` (Windows/Linux) or `Cmd+R` (Mac)

### Cache Configuration

**Cache TTL:** 1 hour (3600 seconds)

To configure cache settings:

1. Go to Settings > Database Connections
2. Select "Healthcare Warehouse"
3. Click "Edit"
4. Under "Advanced" tab, set cache timeout

## Troubleshooting

### Cannot Connect to Database

**Symptoms:** "Cannot connect to database" error when testing connection

**Solutions:**
1. Verify warehouse-db container is running: `docker-compose ps`
2. Check database credentials in .env file
3. Ensure network connectivity between Superset and warehouse-db containers
4. Check PostgreSQL logs: `docker-compose logs warehouse-db`

### Tables Not Found

**Symptoms:** Tables don't appear in dataset creation

**Solutions:**
1. Run the ETL pipeline to populate Gold layer tables
2. Verify tables exist in database:
   ```bash
   docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse -c "\dt"
   ```
3. Refresh table list in Superset: Data > Databases > Healthcare Warehouse > Edit > Refresh

### Charts Not Loading

**Symptoms:** Charts show "No data" or loading errors

**Solutions:**
1. Verify data exists in tables
2. Check SQL query in chart configuration
3. Clear Superset cache: Settings > Clear Cache
4. Check Superset logs: `docker-compose logs superset`

### Slow Dashboard Performance

**Symptoms:** Dashboards take long time to load

**Solutions:**
1. Add indexes to frequently queried columns in PostgreSQL
2. Increase cache TTL for stable data
3. Use dashboard filters to reduce data volume
4. Consider materializing complex queries as views

## API Integration

The `refresh_superset_cache` function in the Airflow DAG can be enhanced to use Superset's REST API:

```python
def refresh_superset_cache(**context):
    """Refresh Superset cache via API"""
    import requests
    
    superset_url = os.getenv('SUPERSET_URL', 'http://superset:8088')
    username = os.getenv('SUPERSET_USERNAME', 'admin')
    password = os.getenv('SUPERSET_PASSWORD', 'admin')
    
    # Login
    session = requests.Session()
    login_response = session.post(
        f"{superset_url}/api/v1/security/login",
        json={'username': username, 'password': password, 'provider': 'db'}
    )
    
    if login_response.status_code == 200:
        access_token = login_response.json()['access_token']
        session.headers.update({'Authorization': f'Bearer {access_token}'})
        
        # Refresh specific dashboard
        dashboard_id = 1  # Replace with actual dashboard ID
        session.post(f"{superset_url}/api/v1/dashboard/{dashboard_id}/refresh")
        
        print(f"✓ Superset cache refreshed for dashboard {dashboard_id}")
    else:
        print(f"✗ Failed to refresh Superset cache")
```

## Best Practices

1. **Use Filters:** Add date range filters to all time-series charts
2. **Limit Results:** Use TOP N or LIMIT clauses for large datasets
3. **Cache Wisely:** Set appropriate cache TTL based on data freshness requirements
4. **Document Metrics:** Add descriptions to all calculated columns
5. **Test Queries:** Test SQL queries in SQL Lab before creating charts
6. **Monitor Performance:** Track dashboard load times and optimize slow queries
7. **Regular Maintenance:** Periodically review and update dashboards based on user feedback

## Additional Resources

- [Superset Documentation](https://superset.apache.org/docs/intro)
- [Superset REST API](https://superset.apache.org/docs/rest-api)
- [Creating Charts](https://superset.apache.org/docs/creating-charts-dashboards/creating-your-first-dashboard)
- [SQL Lab](https://superset.apache.org/docs/creating-charts-dashboards/exploring-data)

## Support

For issues or questions:
1. Check Superset logs: `docker-compose logs superset`
2. Review this documentation
3. Contact the data engineering team
