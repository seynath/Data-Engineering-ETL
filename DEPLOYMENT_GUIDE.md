# Deployment Guide

## When to Use Which Script

### For DAG Code Changes Only (Most Common)

**Use: NO SCRIPT NEEDED!** ✅

Since your `docker-compose.yml` uses **bind mounts** (not volumes), changes to files in `airflow/dags/` are automatically visible to the Airflow containers. 

**Steps:**
1. Update your DAG file locally
2. Copy to your remote VM (via `scp`, git, etc.)
3. Airflow will automatically detect the change within 5 minutes
4. Or manually refresh in Airflow UI (Browse → Refresh)

**Verify changes:**
```bash
./update-dag.sh
```

---

### For Full Setup/Initial Deployment

**Use:** `complete-fix.sh` ⚠️

**When to use:**
- First time setup
- After changing Dockerfile or requirements
- After modifying docker-compose.yml
- When you need to rebuild the entire environment
- After major infrastructure changes

**What it does:**
- Rebuilds Docker images (takes 3-5 minutes)
- Reinitializes databases
- Reinstalls all dependencies
- Restarts all services

**Runtime:** 5-10 minutes

---

### For Restarting Services

**Use:** Standard docker-compose commands

```bash
# Restart just Airflow (after DAG changes)
docker-compose restart airflow-webserver airflow-scheduler

# Restart everything
docker-compose restart

# Start services
docker-compose up -d

# Stop services
docker-compose down
```

---

### Quick Reference

| Scenario | What to Do |
|----------|-----------|
| Change DAG code | Nothing! (auto-detected in ~5 min) or manually refresh in UI |
| Change Python dependencies | `complete-fix.sh` |
| Change Dockerfile | `complete-fix.sh` |
| Change docker-compose.yml | `complete-fix.sh` |
| Just need to restart | `docker-compose restart` |
| Check logs | `docker-compose logs -f airflow-scheduler` |

---

## Current Bug Fix

For the `AttributeError: 'Connection' object has no attribute 'commit'` fix:

1. ✅ Code is already updated in `airflow/dags/healthcare_etl_dag.py`
2. Copy the updated file to your remote VM
3. No rebuild needed - just wait 5 minutes or refresh in UI
4. The fix will be active on next DAG run

**To copy to remote:**
```bash
# From your local machine
scp airflow/dags/healthcare_etl_dag.py user@remote-vm:/path/to/ETL/airflow/dags/
```

**On remote VM, verify:**
```bash
./update-dag.sh
```

---

## Summary

**You DON'T need to run `complete-fix.sh` every time!** ❌

It's only for:
- Initial setup
- Infrastructure changes
- Dependency changes
- Docker image changes

**For DAG changes:** Just copy the file and refresh! ✅
