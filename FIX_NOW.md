# Fix Permission Errors NOW

## You're seeing permission errors for:
- `/opt/airflow/data/bronze/` or `/opt/airflow/data/silver/`
- `/opt/airflow/great_expectations/uncommitted/validations`
- `/opt/airflow/logs/` or `/opt/airflow/logs_app/`
- Any other directory the pipeline tries to write to

## ⚡ Quick Fix (30 seconds)

Run this command:

```bash
./pipeline-cli.sh quick-fix
```

Then restart services:

```bash
docker-compose restart
```

## ✅ That's It!

The pipeline should now work. Go to Airflow UI and trigger the DAG again.

## 🔍 Verify the Fix

```bash
./pipeline-cli.sh verify
```

This checks all directories are properly set up.

## 🔄 Complete Fix (Recommended for Long-term)

For a permanent fix that rebuilds the image properly:

```bash
./complete-fix.sh
```

This takes 3-5 minutes but ensures everything is set up correctly.

## 📊 Verify It Works

After the fix:

1. Open Airflow: http://localhost:8080
2. Trigger the `healthcare_etl_pipeline` DAG
3. Watch it complete successfully
4. Check data was created:
   ```bash
   ls -la data/bronze/
   ls -la data/silver/
   ```

---

**Quick fix:** `./pipeline-cli.sh quick-fix` then `docker-compose restart`

**Complete fix:** `./complete-fix.sh`
