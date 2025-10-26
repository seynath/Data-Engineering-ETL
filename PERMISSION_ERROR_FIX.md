# Fix Permission Denied Error

## Error You're Seeing
```
PermissionError: [Errno 13] Permission denied: '/opt/airflow/data/bronze/2025-10-26'
```

## Quick Fix (One Command)

```bash
./complete-fix.sh
```

Type `yes` when prompted.

## What It Does

1. Creates all required directories
2. Fixes permissions (may ask for sudo password)
3. Rebuilds Docker image with proper setup
4. Starts all services correctly

## After Running

Check status:
```bash
./pipeline-cli.sh status
```

All services should show "(healthy)".

## Trigger the Pipeline

```bash
./pipeline-cli.sh trigger-dag
```

Or open Airflow UI: http://localhost:8080

## If You Still Get Permission Errors

Run this to fix permissions manually:

```bash
sudo chmod -R 777 data/ airflow/logs/ logs/ great_expectations/
sudo chown -R 50000:0 data/ airflow/logs/ logs/ great_expectations/
```

Then restart:
```bash
docker-compose restart
```

## Understanding the Issue

The Airflow container runs as user ID 50000, but the local directories were created with different permissions. The fix:

1. Sets AIRFLOW_UID=50000 in .env
2. Creates directories with proper permissions (777)
3. Rebuilds image to create directories inside container
4. Ensures both host and container can write

## Verify It's Fixed

After running the pipeline, check:

```bash
ls -la data/bronze/
```

You should see dated directories like `2025-10-26/` with CSV files inside.

---

**Just run:** `./complete-fix.sh`
