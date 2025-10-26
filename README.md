# Healthcare ETL Pipeline

> **🚀 New here? Start with [START_HERE.md](START_HERE.md) for the quickest path to getting running!**

An automated ETL pipeline for hospital operational data using Apache Airflow, implementing the medallion architecture (Bronze/Silver/Gold) with data quality validation and analytics visualization.

## Project Structure

```
.
├── airflow/
│   ├── dags/              # Airflow DAG definitions
│   ├── logs/              # Airflow execution logs
│   └── plugins/           # Custom Airflow plugins
├── config/                # Pipeline configuration files
├── data/
│   ├── bronze/            # Raw CSV data (immutable)
│   └── silver/            # Cleaned Parquet data
├── dataset/               # Source CSV files
├── dbt_project/           # dbt models for Gold layer
├── init-scripts/          # Database initialization scripts
├── logs/                  # Application logs
├── docker-compose.yml     # Local development environment
├── requirements.txt       # Python dependencies
└── .env.example           # Environment variable template
```

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- Python 3.11+
- At least 4GB RAM available for Docker
- 10GB free disk space

## Quick Start

### 🚀 Fastest Way to Start

```bash
./pipeline-cli.sh start
```

That's it! The CLI tool handles everything automatically.

**First time?** Read [`GETTING_STARTED.md`](GETTING_STARTED.md) for a complete walkthrough.

### Alternative Methods

#### Option 1: Use the CLI Helper (Recommended)
```bash
chmod +x pipeline-cli.sh
./pipeline-cli.sh start
./pipeline-cli.sh status
./pipeline-cli.sh help  # See all commands
```

#### Option 2: Use the Start Script
```bash
chmod +x start.sh
./start.sh
```

#### Option 3: Manual Docker Compose
See [`RUN_PIPELINE.md`](RUN_PIPELINE.md) for detailed manual instructions.

### 📚 Documentation Quick Links

- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Start here if you're new
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command cheat sheet
- **[RUN_PIPELINE.md](RUN_PIPELINE.md)** - Detailed running instructions
- **[FIXED_ISSUES.md](FIXED_ISSUES.md)** - Recent fixes and solutions

**Setup time**: 3-5 minutes on first run

### Manual Setup

If you prefer manual setup or the automated script fails:

#### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration (optional for local dev)
nano .env
```

**Important environment variables:**
- `AIRFLOW_UID`: Set to your user ID (run `id -u` on Linux/macOS)
- `POSTGRES_HOST`: Use `warehouse-db` for Docker, `localhost` for local
- `POSTGRES_PORT`: Use `5432` inside Docker, `5433` from host machine

#### 2. Create Required Directories

```bash
# Create directory structure
mkdir -p airflow/dags airflow/logs airflow/plugins
mkdir -p data/bronze data/silver
mkdir -p logs/alerts
mkdir -p great_expectations/uncommitted

# Set permissions for Airflow (Linux/macOS)
sudo chown -R 50000:0 airflow/logs airflow/dags airflow/plugins
```

#### 3. Start Services

```bash
# Start all services (Airflow, PostgreSQL, Superset)
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

**First startup takes 2-3 minutes** as services initialize.

#### 4. Initialize Warehouse Database

```bash
# Wait for services to be healthy
docker-compose ps

# Run warehouse setup
bash init-scripts/setup-warehouse.sh
```

This will:
- Verify database tables are created
- Populate the date dimension (2020-2030)
- Display table row counts

### 5. Access Services

Once setup is complete, access the following services:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Airflow UI** | http://localhost:8080 | Username: `airflow`<br>Password: `airflow` |
| **Superset** | http://localhost:8088 | Username: `admin`<br>Password: `admin` |
| **PostgreSQL (Airflow)** | localhost:5432 | Database: `airflow`<br>Username: `airflow`<br>Password: `airflow` |
| **PostgreSQL (Warehouse)** | localhost:5433 | Database: `healthcare_warehouse`<br>Username: `etl_user`<br>Password: `etl_password` |

### 6. Run the ETL Pipeline

```bash
# Option 1: Trigger from Airflow UI
# 1. Open http://localhost:8080
# 2. Find 'healthcare_etl_pipeline' DAG
# 3. Click the play button to trigger

# Option 2: Trigger from command line
docker-compose exec airflow-webserver airflow dags trigger healthcare_etl_pipeline

# Option 3: Enable scheduled runs
# The DAG runs daily at 2:00 AM UTC by default
```

### 7. Install Python Dependencies (for local development)

If you want to run Python scripts locally (outside Docker):

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Pipeline Architecture

### Medallion Architecture

1. **Bronze Layer**: Raw CSV files copied with timestamps (immutable source of truth)
2. **Silver Layer**: Cleaned and validated Parquet files with standardized formats
3. **Gold Layer**: Star schema in PostgreSQL with dimension and fact tables

### Data Flow

```
CSV Files → Bronze Layer → Silver Layer → dbt Transformations → Gold Layer → Superset Dashboards
              ↓               ↓                    ↓
         Validation    Great Expectations    dbt Tests
```

## Development

### Running the Pipeline Locally

1. Place source CSV files in the `dataset/` directory
2. Trigger the DAG from Airflow UI or CLI:
   ```bash
   docker-compose exec airflow-webserver airflow dags trigger healthcare_etl_pipeline
   ```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Configuration

### Environment Variables

The pipeline is configured through environment variables in the `.env` file. Copy `.env.example` to `.env` and customize as needed.

#### Core Configuration

```bash
# Airflow Configuration
AIRFLOW_UID=50000                          # User ID for Airflow (run 'id -u' on Linux/macOS)
AIRFLOW_PROJ_DIR=.                         # Project directory
_AIRFLOW_WWW_USER_USERNAME=airflow         # Airflow UI username
_AIRFLOW_WWW_USER_PASSWORD=airflow         # Airflow UI password

# PostgreSQL Warehouse Database
POSTGRES_HOST=warehouse-db                 # Use 'warehouse-db' for Docker, 'localhost' for local
POSTGRES_PORT=5432                         # Internal port (5433 from host)
POSTGRES_DB=healthcare_warehouse           # Database name
POSTGRES_USER=etl_user                     # Database user
POSTGRES_PASSWORD=etl_password             # Database password

# File Paths (inside Docker containers)
BRONZE_DATA_PATH=/opt/airflow/data/bronze  # Raw CSV storage
SILVER_DATA_PATH=/opt/airflow/data/silver  # Cleaned Parquet storage
SOURCE_CSV_PATH=/opt/airflow/dataset       # Source CSV files

# Superset Configuration
SUPERSET_SECRET_KEY=superset_secret_key_change_me  # Change in production!

# Alerting Configuration
ALERT_EMAIL=data-team@hospital.com         # Email for alerts
SMTP_PASSWORD=                             # SMTP password (if using email alerts)
SLACK_WEBHOOK_URL=                         # Slack webhook (if using Slack alerts)

# Pipeline Configuration
PIPELINE_NAME=healthcare_etl               # Pipeline name
PIPELINE_VERSION=1.0.0                     # Version
ENVIRONMENT=development                    # Environment (development/staging/production)

# Data Quality Thresholds
DATA_QUALITY_FAIL_ON_ERROR=true           # Halt pipeline on quality failures
DATA_QUALITY_WARNING_THRESHOLD=0.05       # 5% failure rate threshold
```

#### Environment-Specific Configuration

**Development** (default):
- Uses local Docker containers
- Minimal resource requirements
- Verbose logging enabled
- Sample data recommended

**Staging**:
- Similar to production setup
- Uses staging database
- Full dataset testing
- Performance monitoring enabled

**Production**:
- Managed services (Cloud Composer, RDS, etc.)
- High availability configuration
- Strict data quality enforcement
- Comprehensive monitoring and alerting

### Pipeline Configuration Files

#### `config/pipeline_config.yaml`

Main pipeline configuration file:

```yaml
pipeline:
  name: healthcare_etl
  version: 1.0.0
  
bronze:
  source_path: ${SOURCE_CSV_PATH}
  target_path: ${BRONZE_DATA_PATH}
  tables:
    - patients
    - encounters
    - diagnoses
    - procedures
    - medications
    - lab_tests
    - claims_and_billing
    - providers
    - denials

silver:
  source_path: ${BRONZE_DATA_PATH}
  target_path: ${SILVER_DATA_PATH}
  date_format: "%d-%m-%Y"
  target_date_format: "%Y-%m-%d"
  
data_quality:
  fail_on_error: true
  warning_threshold: 0.05
  
gold:
  database: ${POSTGRES_DB}
  schema: public
  incremental_strategy: merge
```

#### `config/silver_table_config.yaml`

Table-specific transformation rules:

```yaml
tables:
  patients:
    primary_key: patient_id
    date_columns:
      - dob
    numeric_columns:
      - age
    categorical_columns:
      - gender
      - ethnicity
      - insurance_type
```

See `config/README.md` for detailed configuration options.

### dbt Configuration

#### `dbt_project/profiles.yml`

dbt database connection configuration:

```yaml
healthcare_dbt:
  target: dev
  outputs:
    dev:
      type: postgres
      host: "{{ env_var('POSTGRES_HOST', 'localhost') }}"
      port: "{{ env_var('POSTGRES_PORT', '5432') | int }}"
      user: "{{ env_var('POSTGRES_USER', 'etl_user') }}"
      password: "{{ env_var('POSTGRES_PASSWORD', 'etl_password') }}"
      dbname: "{{ env_var('POSTGRES_DB', 'healthcare_warehouse') }}"
      schema: public
      threads: 4
```

### Customizing the Pipeline

#### Change Data Sources

1. Place CSV files in `dataset/` directory
2. Update table list in `config/pipeline_config.yaml`
3. Add transformation rules in `config/silver_table_config.yaml`
4. Create Great Expectations suites for new tables

#### Modify Transformations

1. Edit `silver_transformation.py` for Silver layer logic
2. Update dbt models in `dbt_project/models/` for Gold layer
3. Run dbt tests to verify changes

#### Adjust Scheduling

Edit `airflow/dags/healthcare_etl_dag.py`:

```python
dag = DAG(
    'healthcare_etl_pipeline',
    schedule_interval='0 2 * * *',  # Daily at 2 AM UTC
    # Change to:
    # schedule_interval='0 */6 * * *',  # Every 6 hours
    # schedule_interval='@weekly',       # Weekly
    # schedule_interval=None,            # Manual only
)
```

#### Configure Alerts

Update alerting in `.env`:

```bash
# Email alerts
ALERT_EMAIL=your-team@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Slack alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Services Won't Start

**Problem**: Docker Compose fails to start services

```bash
# Check Docker is running
docker ps

# Check Docker resources (need at least 4GB RAM)
docker system df

# View detailed logs
docker-compose logs airflow-webserver
docker-compose logs warehouse-db
docker-compose logs superset

# Check for port conflicts
lsof -i :8080  # Airflow
lsof -i :8088  # Superset
lsof -i :5432  # PostgreSQL (Airflow)
lsof -i :5433  # PostgreSQL (Warehouse)
```

**Solution**:
- Ensure Docker Desktop is running
- Free up disk space if needed
- Stop conflicting services on ports 8080, 8088, 5432, 5433
- Increase Docker memory allocation to at least 4GB

#### 2. Permission Errors

**Problem**: `Permission denied` errors in Airflow logs

```bash
# Check current permissions
ls -la airflow/

# Fix Airflow directory permissions (Linux/macOS)
sudo chown -R 50000:0 airflow/logs airflow/dags airflow/plugins

# Alternative: Use your user ID
export AIRFLOW_UID=$(id -u)
docker-compose down
docker-compose up -d
```

**On Windows**:
- Ensure Docker Desktop has access to the project directory
- Check "Settings > Resources > File Sharing"

#### 3. Database Connection Issues

**Problem**: Cannot connect to warehouse database

```bash
# Test connection from host machine
PGPASSWORD=etl_password psql -h localhost -p 5433 -U etl_user -d healthcare_warehouse

# Test connection from inside Docker
docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse

# Check if warehouse-db is healthy
docker-compose ps warehouse-db

# View warehouse-db logs
docker-compose logs warehouse-db
```

**Solution**:
- Wait for warehouse-db to be healthy (check with `docker-compose ps`)
- Verify environment variables in `.env` file
- Ensure port 5433 is not in use by another service

#### 4. Airflow UI Not Loading

**Problem**: Cannot access http://localhost:8080

```bash
# Check if webserver is running
docker-compose ps airflow-webserver

# Check webserver logs
docker-compose logs airflow-webserver

# Check webserver health
docker-compose exec airflow-webserver curl http://localhost:8080/health

# Restart webserver
docker-compose restart airflow-webserver
```

**Solution**:
- Wait 60-90 seconds after starting for webserver to initialize
- Check logs for errors
- Ensure port 8080 is not in use

#### 5. Superset Not Loading

**Problem**: Cannot access http://localhost:8088

```bash
# Check Superset status
docker-compose ps superset

# View Superset logs
docker-compose logs superset

# Restart Superset
docker-compose restart superset
```

**Solution**:
- Wait 90-120 seconds for Superset to initialize
- Check if warehouse-db is healthy (Superset depends on it)
- Clear browser cache and try again

#### 6. DAG Not Appearing in Airflow

**Problem**: `healthcare_etl_pipeline` DAG not visible in Airflow UI

```bash
# Check if DAG file exists
ls -la airflow/dags/healthcare_etl_dag.py

# Check DAG for syntax errors
docker-compose exec airflow-webserver python /opt/airflow/dags/healthcare_etl_dag.py

# Check scheduler logs
docker-compose logs airflow-scheduler

# Refresh DAGs
docker-compose exec airflow-webserver airflow dags list
```

**Solution**:
- Ensure `healthcare_etl_dag.py` is in `airflow/dags/` directory
- Fix any Python syntax errors
- Wait 30-60 seconds for scheduler to detect DAG
- Restart scheduler: `docker-compose restart airflow-scheduler`

#### 7. Pipeline Fails with Import Errors

**Problem**: DAG tasks fail with `ModuleNotFoundError`

```bash
# Check installed packages
docker-compose exec airflow-webserver pip list

# Reinstall dependencies
docker-compose down
docker-compose up -d --build
```

**Solution**:
- Verify `_PIP_ADDITIONAL_REQUIREMENTS` in docker-compose.yml
- Rebuild containers with `--build` flag
- Check that all Python modules are in the project root

#### 8. Out of Disk Space

**Problem**: Docker runs out of disk space

```bash
# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a --volumes

# Remove old images
docker image prune -a
```

**Warning**: `docker system prune` will remove all stopped containers and unused images.

#### 9. Slow Performance

**Problem**: Pipeline runs very slowly

**Solutions**:
- Increase Docker memory allocation (Settings > Resources)
- Reduce number of parallel tasks in Airflow DAG
- Use smaller dataset for testing
- Check system resources: `docker stats`

#### 10. Database Tables Not Created

**Problem**: Warehouse database has no tables

```bash
# Check if init scripts ran
docker-compose logs warehouse-db | grep "init-warehouse-db.sql"

# Manually run init scripts
docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse -f /docker-entrypoint-initdb.d/init-warehouse-db.sql

# Verify tables exist
docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse -c "\dt"
```

**Solution**:
- Init scripts only run on first container creation
- To re-run: `docker-compose down -v` (WARNING: deletes all data)
- Then: `docker-compose up -d`

### Getting Help

If you encounter issues not covered here:

1. **Check logs**: `docker-compose logs [service-name]`
2. **Check service health**: `docker-compose ps`
3. **Restart services**: `docker-compose restart`
4. **Full reset**: `docker-compose down -v && docker-compose up -d`

### Useful Commands Reference

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f airflow-scheduler

# Check service status
docker-compose ps

# Restart a service
docker-compose restart airflow-webserver

# Stop all services
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v

# Rebuild and restart
docker-compose up -d --build

# Execute command in container
docker-compose exec airflow-webserver bash

# View resource usage
docker stats
```

## Monitoring

- **Airflow UI**: Monitor DAG runs, task status, and logs
- **Superset**: View data quality dashboards and analytics
- **Logs**: Check `airflow/logs/` and `logs/` directories

## Superset Dashboards

### Setup Superset

After starting services and running the ETL pipeline:

```bash
# 1. Create database connection
python superset_setup.py --action setup --wait 60

# 2. Create datasets
python superset_setup.py --action setup-datasets

# 3. Create dashboards
python superset/create_dashboards.py --dashboard all
```

### Available Dashboards

1. **Operational Overview**: Patient flow, admissions, department volumes
2. **Financial Analytics**: Revenue, payments, denials, collection rates
3. **Clinical Insights**: Diagnoses, procedures, readmissions
4. **Provider Performance**: Utilization, volume, length of stay
5. **Medication Analysis**: Prescriptions, costs, trends

For detailed setup instructions, see `superset/SETUP_GUIDE.md`

## Project Status

✅ **Complete** - All core ETL pipeline components implemented:
- Bronze layer ingestion
- Silver layer transformations
- Great Expectations data quality validation
- Gold layer star schema (PostgreSQL)
- dbt models and tests
- Airflow DAG orchestration
- Logging and error handling
- Configuration management
- Superset dashboards

## Documentation

- **Pipeline Overview**: This README
- **Docker Setup**: `DOCKER_SETUP.md` - Detailed Docker Compose configuration and maintenance
- **Airflow DAG**: `airflow/dags/README.md` - DAG structure and task details
- **dbt Models**: `dbt_project/README.md` - Data transformation models
- **Superset Setup**: `superset/SETUP_GUIDE.md` - Dashboard setup and configuration
- **Configuration**: `config/README.md` - Pipeline configuration options
- **Database Initialization**: `init-scripts/README.md` - Database setup scripts
- **Implementation Details**: 
  - `SUPERSET_IMPLEMENTATION.md` - Superset implementation details
  - `DBT_IMPLEMENTATION_COMPLETE.md` - dbt implementation details
  - `DATA_QUALITY_IMPLEMENTATION.md` - Data quality validation details

## License

Internal use only - Hospital operational data pipeline
