# Superset Setup Guide

Complete guide for setting up Apache Superset dashboards for the Healthcare ETL Pipeline.

## Prerequisites

1. Docker and Docker Compose installed
2. Healthcare ETL Pipeline running (docker-compose up -d)
3. ETL pipeline has run at least once to populate Gold layer tables
4. Python 3.8+ with requests library installed

## Step-by-Step Setup

### Step 1: Start Superset

Superset is included in the docker-compose.yml configuration and starts automatically:

```bash
# Start all services
docker-compose up -d

# Wait for Superset to initialize (30-60 seconds)
docker-compose logs -f superset

# Look for: "Booting worker with pid"
```

Access Superset at: **http://localhost:8088**

Default credentials:
- Username: `admin`
- Password: `admin`

### Step 2: Install Python Dependencies

```bash
# Install required Python packages
pip install requests

# Or if using requirements.txt
pip install -r requirements.txt
```

### Step 3: Create Database Connection

Run the setup script to create the PostgreSQL database connection:

```bash
# Wait for Superset to be fully started
python superset_setup.py --action setup --wait 60
```

This will:
- ✓ Connect to Superset
- ✓ Create "Healthcare Warehouse" database connection
- ✓ Test the connection
- ✓ Verify access to all Gold layer tables

**Expected Output:**
```
Logging in to Superset at http://localhost:8088...
✓ Successfully logged in to Superset
Creating database connection to healthcare_warehouse...
✓ Database connection created successfully (ID: 1)
Testing database connection (ID: 1)...
✓ Database connection test successful

Verifying access to Gold layer tables:
  ✓ dim_patient
  ✓ dim_provider
  ✓ dim_diagnosis
  ✓ dim_procedure
  ✓ dim_medication
  ✓ dim_date
  ✓ fact_encounter
  ✓ fact_billing
  ✓ fact_lab_test
  ✓ fact_denial

✓ All 10 Gold layer tables are accessible
```

### Step 4: Create Datasets

Create datasets for all dimension and fact tables:

```bash
python superset_setup.py --action setup-datasets
```

This will:
- ✓ Create datasets for all 10 Gold layer tables
- ✓ Add calculated columns (collection_rate, denial_rate, etc.)
- ✓ Configure column metadata

**Expected Output:**
```
Creating datasets for all Gold layer tables...
Creating dataset for dim_patient...
  ✓ Dataset created (ID: 1)
Creating dataset for fact_billing...
  ✓ Dataset created (ID: 7)
  Adding calculated column: collection_rate...
    ✓ Calculated column added
  Adding calculated column: denial_rate...
    ✓ Calculated column added
  Adding calculated column: outstanding_amount...
    ✓ Calculated column added

✓ Created 10 datasets
```

### Step 5: Create Dashboards

Create dashboards programmatically:

```bash
# Create all dashboards
python superset/create_dashboards.py --dashboard all

# Or create specific dashboards
python superset/create_dashboards.py --dashboard operational
python superset/create_dashboards.py --dashboard financial
```

**Expected Output:**
```
Creating Operational Overview Dashboard...
  ✓ Created chart: Total Patients (ID: 1)
  ✓ Created chart: Total Encounters (ID: 2)
  ✓ Created chart: Total Providers (ID: 3)
  ✓ Created chart: Top 10 Departments by Patient Volume (ID: 4)
  ✓ Created chart: Visit Type Distribution (ID: 5)
✓ Created dashboard: Operational Overview (ID: 1)

Creating Financial Analytics Dashboard...
  ✓ Created chart: Total Billed Amount (ID: 6)
  ✓ Created chart: Total Paid Amount (ID: 7)
  ✓ Created chart: Collection Rate (ID: 8)
  ✓ Created chart: Denial Rate (ID: 9)
  ✓ Created chart: Revenue by Insurance Provider (ID: 10)
✓ Created dashboard: Financial Analytics (ID: 2)
```

### Step 6: Verify Dashboards

1. Open Superset at http://localhost:8088
2. Navigate to **Dashboards**
3. You should see:
   - Operational Overview
   - Financial Analytics
4. Click on each dashboard to verify charts are displaying data

### Step 7: Create Additional Dashboards Manually

Some dashboards require complex SQL queries and should be created manually:

1. **Clinical Insights Dashboard**
2. **Provider Performance Dashboard**
3. **Medication Analysis Dashboard**

Refer to `superset/dashboards/dashboard_specifications.md` for detailed specifications.

## Manual Dashboard Creation

### Creating a Dashboard from Scratch

1. **Navigate to Dashboards**
   - Click **Dashboards** in the top menu
   - Click **+ Dashboard** button

2. **Name Your Dashboard**
   - Enter dashboard title (e.g., "Clinical Insights")
   - Add description
   - Click **Save**

3. **Add Charts**
   - Click **Edit Dashboard**
   - Click **+** button
   - Select **Create a new chart**

4. **Configure Chart**
   - Select dataset (e.g., fact_encounter)
   - Choose visualization type (e.g., Bar Chart)
   - Configure metrics and dimensions
   - Click **Create Chart**
   - Click **Save** to add to dashboard

5. **Arrange Layout**
   - Drag and drop charts to arrange
   - Resize charts by dragging corners
   - Add text boxes for headers/descriptions

6. **Save Dashboard**
   - Click **Save** in the top right
   - Dashboard is now published

### Example: Creating "Top Diagnoses" Chart

1. **Create New Chart**
   - Dataset: fact_encounter
   - Visualization: Bar Chart (Horizontal)

2. **Configure Query**
   - Click **SQL** tab
   - Enter custom SQL:
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

3. **Configure Visualization**
   - X-Axis: diagnosis_count
   - Y-Axis: diagnosis_description
   - Show Bar Values: Yes
   - Sort: Descending

4. **Save Chart**
   - Name: "Top 20 Diagnoses"
   - Add to dashboard: "Clinical Insights"

## Troubleshooting

### Issue: Cannot Connect to Superset

**Error:** `Connection refused` or `Cannot connect to Superset`

**Solutions:**
1. Verify Superset is running:
   ```bash
   docker-compose ps superset
   ```

2. Check Superset logs:
   ```bash
   docker-compose logs superset
   ```

3. Wait longer for Superset to start (can take 60+ seconds)

4. Restart Superset:
   ```bash
   docker-compose restart superset
   ```

### Issue: Login Failed

**Error:** `Login failed: 401`

**Solutions:**
1. Verify credentials in .env file:
   ```bash
   cat .env | grep SUPERSET
   ```

2. Reset admin password:
   ```bash
   docker-compose exec superset superset fab create-admin \
       --username admin \
       --firstname Admin \
       --lastname User \
       --email admin@superset.com \
       --password admin
   ```

### Issue: Database Connection Failed

**Error:** `Cannot connect to database`

**Solutions:**
1. Verify warehouse-db is running:
   ```bash
   docker-compose ps warehouse-db
   ```

2. Test database connection:
   ```bash
   docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse -c "SELECT 1"
   ```

3. Check network connectivity:
   ```bash
   docker-compose exec superset ping warehouse-db
   ```

4. Verify credentials in .env file

### Issue: Tables Not Found

**Error:** `Table does not exist` or empty table list

**Solutions:**
1. Run the ETL pipeline to populate tables:
   ```bash
   # Trigger Airflow DAG
   docker-compose exec airflow-webserver airflow dags trigger healthcare_etl_pipeline
   ```

2. Verify tables exist:
   ```bash
   docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse -c "\dt"
   ```

3. Refresh table list in Superset:
   - Go to Data > Databases
   - Click on "Healthcare Warehouse"
   - Click "Edit"
   - Click "Refresh" button

### Issue: Charts Show "No Data"

**Error:** Charts display but show "No data"

**Solutions:**
1. Verify data exists in tables:
   ```bash
   docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse -c "SELECT COUNT(*) FROM fact_encounter"
   ```

2. Check chart SQL query:
   - Edit the chart
   - Click "SQL" tab
   - Run query in SQL Lab to test

3. Clear Superset cache:
   - Settings > Clear Cache
   - Or restart Superset

4. Check date filters:
   - Remove or adjust date range filters
   - Ensure data exists for selected date range

### Issue: Slow Dashboard Performance

**Symptoms:** Dashboards take long time to load

**Solutions:**
1. Add database indexes:
   ```sql
   CREATE INDEX idx_encounter_visit_date ON fact_encounter(visit_date_key);
   CREATE INDEX idx_billing_date ON fact_billing(claim_billing_date_key);
   ```

2. Increase cache TTL:
   - Data > Databases > Healthcare Warehouse > Edit
   - Set "Cache Timeout" to 3600 (1 hour)

3. Limit data in charts:
   - Add date range filters
   - Use TOP N or LIMIT clauses
   - Aggregate data before visualization

4. Use async queries:
   - Data > Databases > Healthcare Warehouse > Edit
   - Enable "Asynchronous Query Execution"

## Configuration Options

### Environment Variables

Add to `.env` file:

```bash
# Superset Configuration
SUPERSET_URL=http://localhost:8088
SUPERSET_USERNAME=admin
SUPERSET_PASSWORD=admin
SUPERSET_SECRET_KEY=your-secret-key-here

# Cache Configuration
SUPERSET_CACHE_DEFAULT_TIMEOUT=3600
SUPERSET_CACHE_CONFIG='{"CACHE_TYPE": "redis", "CACHE_REDIS_URL": "redis://localhost:6379/0"}'
```

### Database Connection String

The connection string format:
```
postgresql://[user]:[password]@[host]:[port]/[database]
```

Example:
```
postgresql://etl_user:etl_password@warehouse-db:5432/healthcare_warehouse
```

### Cache Configuration

Configure cache in Superset:

1. Go to **Settings** > **Database Connections**
2. Select "Healthcare Warehouse"
3. Click **Edit**
4. Under **Advanced** tab:
   - Cache Timeout: 3600 (1 hour)
   - Schema Cache Timeout: 86400 (24 hours)

## Maintenance

### Regular Tasks

**Daily:**
- Monitor dashboard performance
- Check for failed queries in logs

**Weekly:**
- Review and optimize slow queries
- Update dashboard descriptions

**Monthly:**
- Review metrics with stakeholders
- Add new charts based on feedback
- Archive unused dashboards

### Backup and Restore

**Backup Dashboards:**
```bash
# Export all dashboards
python superset/export_dashboards.py --output backups/
```

**Restore Dashboards:**
```bash
# Import dashboards
python superset/import_dashboards.py --input backups/dashboard_1.json
```

### Cleanup

Remove all Superset configuration:

```bash
# Remove datasets and database connection
python superset_setup.py --action cleanup

# This will:
# - Delete all datasets
# - Remove database connection
# - Dashboards will remain but won't have data
```

## Best Practices

1. **Use Filters:** Add date range filters to all time-series dashboards
2. **Limit Results:** Use TOP N or LIMIT for large datasets
3. **Cache Wisely:** Set appropriate cache TTL based on data freshness
4. **Document Metrics:** Add descriptions to all charts and calculated columns
5. **Test Queries:** Test SQL in SQL Lab before creating charts
6. **Monitor Performance:** Track dashboard load times
7. **Regular Reviews:** Update dashboards based on user feedback

## Additional Resources

- [Superset Documentation](https://superset.apache.org/docs/intro)
- [Creating Charts](https://superset.apache.org/docs/creating-charts-dashboards/creating-your-first-dashboard)
- [SQL Lab](https://superset.apache.org/docs/creating-charts-dashboards/exploring-data)
- [REST API](https://superset.apache.org/docs/rest-api)

## Support

For issues or questions:
1. Check this guide and troubleshooting section
2. Review Superset logs: `docker-compose logs superset`
3. Check the dashboard specifications: `superset/dashboards/dashboard_specifications.md`
4. Contact the data engineering team

## Quick Reference

### Common Commands

```bash
# Start Superset
docker-compose up -d superset

# View logs
docker-compose logs -f superset

# Restart Superset
docker-compose restart superset

# Setup database connection
python superset_setup.py --action setup

# Create datasets
python superset_setup.py --action setup-datasets

# Create dashboards
python superset/create_dashboards.py --dashboard all

# Test connection
python superset_setup.py --action test

# Cleanup
python superset_setup.py --action cleanup
```

### URLs

- Superset UI: http://localhost:8088
- Airflow UI: http://localhost:8080
- PostgreSQL: localhost:5433

### Default Credentials

- Superset: admin / admin
- Airflow: airflow / airflow
- PostgreSQL: etl_user / etl_password
