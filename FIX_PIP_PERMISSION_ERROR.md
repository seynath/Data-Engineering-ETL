# Fix: Pip Permission Error

## Problem

You're seeing this error:
```
You are running pip as root. Please use 'airflow' user to run pip!
ERROR: 1
```

## Root Cause

The `_PIP_ADDITIONAL_REQUIREMENTS` environment variable in docker-compose.yml was trying to install Python packages at runtime as root user, which is:
1. Not recommended for production
2. Fragile (runs every container start)
3. Causes permission errors

## Solution Applied

I've fixed this by creating a proper custom Docker image that installs packages correctly.

### What Changed

1. **Created `Dockerfile`** - Custom Airflow image that installs packages as the airflow user
2. **Created `requirements-airflow.txt`** - List of Python dependencies
3. **Updated `docker-compose.yml`** - Now builds custom image instead of using _PIP_ADDITIONAL_REQUIREMENTS
4. **Updated `start.sh`** - Builds the image before starting services

## How to Use Now

### Clean Start (Recommended)

```bash
# Stop and remove everything
docker-compose down -v

# Remove old images
docker rmi healthcare-etl-airflow:latest 2>/dev/null || true

# Start with the new approach
./pipeline-cli.sh start
```

This will:
1. Build the custom Airflow image (takes 2-3 minutes first time)
2. Start all services
3. No more pip permission errors!

### Manual Build (If Needed)

If you want to rebuild the image manually:

```bash
# Build the image
./pipeline-cli.sh build

# Or use docker-compose directly
docker-compose build
```

## Verify It's Fixed

After running `./pipeline-cli.sh start`, check the logs:

```bash
docker-compose logs airflow-init
```

You should see:
- ✅ No "You are running pip as root" warnings
- ✅ No "ERROR: 1" at the end
- ✅ "User 'airflow' created with role 'Admin'" message
- ✅ Clean completion

## What's in the Custom Image

The custom image includes:
- pandas==2.1.4
- pyarrow==14.0.1
- great-expectations==0.18.8
- psycopg2-binary==2.9.9
- pyyaml==6.0.1
- dbt-core==1.7.4
- dbt-postgres==1.7.4

All installed properly as the airflow user during image build.

## Adding More Dependencies

If you need to add more Python packages:

1. Edit `requirements-airflow.txt`:
   ```bash
   nano requirements-airflow.txt
   ```

2. Add your package:
   ```
   your-package==1.0.0
   ```

3. Rebuild the image:
   ```bash
   ./pipeline-cli.sh build
   ```

4. Restart services:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Benefits of This Approach

✅ **Proper**: Follows Docker and Airflow best practices
✅ **Fast**: Packages installed once during build, not every start
✅ **Reliable**: No runtime installation failures
✅ **Secure**: Runs as airflow user, not root
✅ **Production-ready**: Can be used in production environments

## Troubleshooting

### Build Fails

If the image build fails:

```bash
# Check the error
docker-compose build

# Try with no cache
docker-compose build --no-cache
```

### Old Image Still Used

If you still see the error:

```bash
# Remove old containers and images
docker-compose down -v
docker rmi healthcare-etl-airflow:latest
docker rmi apache/airflow:2.8.1-python3.11

# Clean start
./pipeline-cli.sh start
```

### Disk Space Issues

If you run out of space during build:

```bash
# Clean up Docker
docker system prune -a

# Then try again
./pipeline-cli.sh start
```

## Quick Commands

```bash
# Clean start (recommended)
docker-compose down -v
./pipeline-cli.sh start

# Just rebuild image
./pipeline-cli.sh build

# Check if it worked
docker-compose logs airflow-init | grep -i error

# Verify image exists
docker images | grep healthcare-etl-airflow
```

## Next Steps

After the fix is applied and working:

1. Verify all services are healthy:
   ```bash
   ./pipeline-cli.sh status
   ```

2. Open Airflow UI:
   ```bash
   ./pipeline-cli.sh airflow
   ```

3. Trigger the pipeline:
   ```bash
   ./pipeline-cli.sh trigger-dag
   ```

---

**The fix is complete!** Just run:
```bash
docker-compose down -v
./pipeline-cli.sh start
```
