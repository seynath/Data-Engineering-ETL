# Docker Compose Setup Guide

This guide provides detailed information about the Docker Compose setup for the Healthcare ETL Pipeline.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Services](#services)
- [Networking](#networking)
- [Volumes](#volumes)
- [Health Checks](#health-checks)
- [Environment Variables](#environment-variables)
- [Startup Sequence](#startup-sequence)
- [Maintenance](#maintenance)

## Architecture Overview

The Docker Compose setup includes the following services:

```
┌─────────────────────────────────────────────────────────────┐
│                  healthcare-etl-network                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   postgres   │  │ warehouse-db │  │   superset   │     │
│  │  (Airflow)   │  │   (Gold)     │  │     (BI)     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│  ┌──────┴──────────────────┴──────────────────┘             │
│  │                                                           │
│  │  ┌──────────────┐  ┌──────────────┐                     │
│  │  │   airflow-   │  │   airflow-   │                     │
│  │  │  webserver   │  │  scheduler   │                     │
│  │  └──────────────┘  └──────────────┘                     │
│  │                                                           │
│  └───────────────────────────────────────────────────────── │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Services

### 1. postgres (Airflow Metadata Database)

**Purpose**: Stores Airflow metadata (DAG runs, task instances, connections, etc.)

**Configuration**:
- Image: `postgres:15`
- Container name: `healthcare-etl-postgres`
- Port: `5432` (host) → `5432` (container)
- Database: `airflow`
- User: `airflow`
- Password: `airflow`

**Health Check**:
```bash
pg_isready -U airflow
```

**Volume**:
- `postgres-db-volume:/var/lib/postgresql/data` - Persistent database storage

### 2. warehouse-db (Healthcare Data Warehouse)

**Purpose**: Stores the Gold layer star schema (dimension and fact tables)

**Configuration**:
- Image: `postgres:15`
- Container name: `healthcare-etl-warehouse-db`
- Port: `5433` (host) → `5432` (container)
- Database: `healthcare_warehouse`
- User: `etl_user` (configurable via `.env`)
- Password: `etl_password` (configurable via `.env`)

**Health Check**:
```bash
pg_isready -U etl_user -d healthcare_warehouse
```

**Volumes**:
- `warehouse-db-volume:/var/lib/postgresql/data` - Persistent database storage
- `./init-scripts:/docker-entrypoint-initdb.d` - Initialization scripts

**Initialization**:
On first startup, PostgreSQL automatically runs scripts in `/docker-entrypoint-initdb.d/`:
1. `init-warehouse-db.sql` - Creates users and grants permissions
2. `create_dimension_tables.sql` - Creates dimension tables
3. `create_fact_tables.sql` - Creates fact tables

### 3. airflow-init

**Purpose**: One-time initialization service for Airflow

**Configuration**:
- Runs once on first startup
- Creates Airflow admin user
- Initializes Airflow metadata database
- Sets up directory permissions

**Tasks**:
1. Create required directories (`logs`, `dags`, `plugins`)
2. Set proper ownership (`AIRFLOW_UID:0`)
3. Run database migrations
4. Create admin user

### 4. airflow-webserver

**Purpose**: Airflow web UI for monitoring and managing DAGs

**Configuration**:
- Image: `apache/airflow:2.8.1-python3.11`
- Container name: `healthcare-etl-airflow-webserver`
- Port: `8080` (host) → `8080` (container)
- Executor: `LocalExecutor`

**Health Check**:
```bash
curl --fail http://localhost:8080/health
```

**Dependencies**:
- postgres (healthy)
- warehouse-db (healthy)
- airflow-init (completed)

**Additional Python Packages**:
Installed via `_PIP_ADDITIONAL_REQUIREMENTS`:
- pandas==2.1.4
- pyarrow==14.0.1
- great-expectations==0.18.8
- psycopg2-binary==2.9.9
- pyyaml==6.0.1
- dbt-core==1.7.4
- dbt-postgres==1.7.4

### 5. airflow-scheduler

**Purpose**: Schedules and executes DAG tasks

**Configuration**:
- Image: `apache/airflow:2.8.1-python3.11`
- Container name: `healthcare-etl-airflow-scheduler`
- No exposed ports (internal only)

**Health Check**:
```bash
curl --fail http://localhost:8974/health
```

**Dependencies**:
- postgres (healthy)
- warehouse-db (healthy)
- airflow-init (completed)

### 6. superset

**Purpose**: Business intelligence and visualization platform

**Configuration**:
- Image: `apache/superset:3.0.0`
- Container name: `healthcare-etl-superset`
- Port: `8088` (host) → `8088` (container)
- Admin user: `admin` / `admin`

**Health Check**:
```bash
curl --fail http://localhost:8088/health
```

**Dependencies**:
- warehouse-db (healthy)

**Initialization**:
On startup, Superset:
1. Upgrades database schema
2. Creates admin user (if not exists)
3. Initializes application
4. Starts Gunicorn web server (4 workers)

## Networking

All services are connected via a custom bridge network: `healthcare-etl-network`

**Benefits**:
- Services can communicate using container names (e.g., `warehouse-db`)
- Isolated from other Docker networks
- Automatic DNS resolution

**Service Communication**:
```
airflow-webserver → warehouse-db:5432
airflow-scheduler → warehouse-db:5432
superset → warehouse-db:5432
airflow-webserver → postgres:5432
airflow-scheduler → postgres:5432
```

## Volumes

### Named Volumes (Persistent Data)

1. **postgres-db-volume**
   - Stores Airflow metadata
   - Persists across container restarts
   - Location: Docker managed volume

2. **warehouse-db-volume**
   - Stores healthcare data warehouse
   - Persists across container restarts
   - Location: Docker managed volume

3. **superset-volume**
   - Stores Superset configuration and metadata
   - Persists across container restarts
   - Location: Docker managed volume

### Bind Mounts (Project Files)

Mounted from host to containers:

```yaml
# Airflow services
- ./airflow/dags:/opt/airflow/dags                    # DAG definitions
- ./airflow/logs:/opt/airflow/logs                    # Airflow logs
- ./airflow/plugins:/opt/airflow/plugins              # Custom plugins
- ./data:/opt/airflow/data                            # Bronze/Silver data
- ./dataset:/opt/airflow/dataset                      # Source CSV files
- ./config:/opt/airflow/config                        # Configuration files
- ./dbt_project:/opt/airflow/dbt_project              # dbt models
- ./great_expectations:/opt/airflow/great_expectations # GE suites
- ./logs:/opt/airflow/logs_app                        # Application logs
- .:/opt/airflow/project                              # Full project root

# Warehouse DB
- ./init-scripts:/docker-entrypoint-initdb.d          # Init scripts
```

**Benefits**:
- Live code updates (no container rebuild needed)
- Easy access to logs and data from host
- Version control integration

## Health Checks

Health checks ensure services are ready before dependent services start.

### postgres
```yaml
test: ["CMD", "pg_isready", "-U", "airflow"]
interval: 10s
timeout: 5s
retries: 5
start_period: 10s
```

### warehouse-db
```yaml
test: ["CMD", "pg_isready", "-U", "etl_user", "-d", "healthcare_warehouse"]
interval: 10s
timeout: 5s
retries: 5
start_period: 10s
```

### airflow-webserver
```yaml
test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
interval: 30s
timeout: 10s
retries: 5
start_period: 60s
```

### airflow-scheduler
```yaml
test: ["CMD", "curl", "--fail", "http://localhost:8974/health"]
interval: 30s
timeout: 10s
retries: 5
start_period: 60s
```

### superset
```yaml
test: ["CMD", "curl", "--fail", "http://localhost:8088/health"]
interval: 30s
timeout: 10s
retries: 5
start_period: 90s
```

**Check service health**:
```bash
docker-compose ps
```

## Environment Variables

### Airflow Common Environment

Shared across all Airflow services:

```yaml
AIRFLOW__CORE__EXECUTOR: LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
AIRFLOW__CORE__FERNET_KEY: ''
AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
AIRFLOW__API__AUTH_BACKENDS: 'airflow.api.auth.backend.basic_auth,airflow.api.auth.backend.session'
AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK: 'true'
```

### Pipeline Environment Variables

```yaml
POSTGRES_HOST: warehouse-db
POSTGRES_PORT: 5432
POSTGRES_DB: healthcare_warehouse
POSTGRES_USER: etl_user
POSTGRES_PASSWORD: etl_password
BRONZE_DATA_PATH: /opt/airflow/data/bronze
SILVER_DATA_PATH: /opt/airflow/data/silver
SOURCE_CSV_PATH: /opt/airflow/dataset
ALERT_EMAIL: data-team@hospital.com
ENVIRONMENT: development
```

**Override in `.env` file**:
```bash
POSTGRES_PASSWORD=my_secure_password
ALERT_EMAIL=my-team@example.com
```

## Startup Sequence

### Dependency Order

```
1. postgres (starts first)
   ↓
2. warehouse-db (starts in parallel with postgres)
   ↓
3. airflow-init (waits for postgres to be healthy)
   ↓
4. airflow-webserver (waits for postgres, warehouse-db, airflow-init)
   ↓
5. airflow-scheduler (waits for postgres, warehouse-db, airflow-init)
   ↓
6. superset (waits for warehouse-db)
```

### Timing

- **postgres**: ~10 seconds to healthy
- **warehouse-db**: ~15 seconds to healthy (includes init scripts)
- **airflow-init**: ~20 seconds to complete
- **airflow-webserver**: ~60 seconds to healthy
- **airflow-scheduler**: ~60 seconds to healthy
- **superset**: ~90 seconds to healthy

**Total startup time**: ~2-3 minutes on first run

### Monitoring Startup

```bash
# Watch all services
watch docker-compose ps

# Follow logs
docker-compose logs -f

# Check specific service
docker-compose logs -f airflow-webserver
```

## Maintenance

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d airflow-webserver

# Start with build (if Dockerfile changed)
docker-compose up -d --build
```

### Stopping Services

```bash
# Stop all services (keeps data)
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v

# Stop specific service
docker-compose stop airflow-webserver
```

### Restarting Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart airflow-scheduler

# Restart with rebuild
docker-compose up -d --build --force-recreate
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f airflow-scheduler

# Last 100 lines
docker-compose logs --tail=100 airflow-webserver

# Since timestamp
docker-compose logs --since 2024-01-01T00:00:00 warehouse-db
```

### Executing Commands

```bash
# Open bash shell
docker-compose exec airflow-webserver bash

# Run single command
docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse

# Run as different user
docker-compose exec -u root airflow-webserver bash
```

### Updating Configuration

```bash
# After changing docker-compose.yml or .env
docker-compose down
docker-compose up -d

# After changing DAG files (no restart needed)
# Scheduler picks up changes automatically

# After changing Python dependencies
docker-compose down
docker-compose up -d --build
```

### Cleaning Up

```bash
# Remove stopped containers
docker-compose rm

# Remove unused images
docker image prune

# Remove all unused resources
docker system prune -a

# Remove specific volume
docker volume rm healthcare-etl_warehouse-db-volume
```

### Backup and Restore

#### Backup Warehouse Database

```bash
# Backup to file
docker-compose exec warehouse-db pg_dump -U etl_user healthcare_warehouse > backup.sql

# Backup with compression
docker-compose exec warehouse-db pg_dump -U etl_user healthcare_warehouse | gzip > backup.sql.gz
```

#### Restore Warehouse Database

```bash
# Restore from file
docker-compose exec -T warehouse-db psql -U etl_user healthcare_warehouse < backup.sql

# Restore from compressed file
gunzip -c backup.sql.gz | docker-compose exec -T warehouse-db psql -U etl_user healthcare_warehouse
```

#### Backup Volumes

```bash
# Backup volume to tar
docker run --rm -v healthcare-etl_warehouse-db-volume:/data -v $(pwd):/backup ubuntu tar czf /backup/warehouse-backup.tar.gz /data

# Restore volume from tar
docker run --rm -v healthcare-etl_warehouse-db-volume:/data -v $(pwd):/backup ubuntu tar xzf /backup/warehouse-backup.tar.gz -C /
```

### Resource Monitoring

```bash
# View resource usage
docker stats

# View specific service
docker stats healthcare-etl-airflow-webserver

# Disk usage
docker system df

# Detailed disk usage
docker system df -v
```

### Troubleshooting

#### Service Won't Start

```bash
# Check logs
docker-compose logs [service-name]

# Check health status
docker-compose ps

# Inspect container
docker inspect healthcare-etl-airflow-webserver

# Check network
docker network inspect healthcare-etl-network
```

#### Port Already in Use

```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 [PID]

# Or change port in docker-compose.yml
ports:
  - "8081:8080"  # Use 8081 on host instead
```

#### Out of Memory

```bash
# Check Docker memory limit
docker info | grep Memory

# Increase in Docker Desktop:
# Settings > Resources > Memory > Increase to 4GB+

# Or reduce workers in docker-compose.yml
command: >
  gunicorn --workers 2  # Reduce from 4 to 2
```

## Security Considerations

### Production Deployment

For production, update the following:

1. **Change default passwords**:
   ```bash
   POSTGRES_PASSWORD=strong_random_password
   _AIRFLOW_WWW_USER_PASSWORD=strong_random_password
   SUPERSET_SECRET_KEY=strong_random_secret_key
   ```

2. **Use secrets management**:
   - Docker Secrets
   - AWS Secrets Manager
   - HashiCorp Vault

3. **Enable SSL/TLS**:
   - Configure HTTPS for Airflow and Superset
   - Use SSL for PostgreSQL connections

4. **Restrict network access**:
   - Remove port mappings for internal services
   - Use reverse proxy (nginx, Traefik)
   - Configure firewall rules

5. **Regular updates**:
   - Update base images regularly
   - Apply security patches
   - Monitor CVE databases

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [PostgreSQL Docker Documentation](https://hub.docker.com/_/postgres)
- [Apache Superset Documentation](https://superset.apache.org/docs/intro)
