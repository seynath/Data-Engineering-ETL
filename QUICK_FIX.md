# 🚨 Quick Fix for "pip as root" Error

## You're seeing this error:
```
You are running pip as root. Please use 'airflow' user to run pip!
ERROR: 1
```

## ⚡ Quick Fix (One Command)

```bash
./fix-and-restart.sh
```

**Wait 3-5 minutes** for the build to complete.

## ✅ That's It!

The script will:
1. Stop all containers
2. Build a proper custom Airflow image
3. Start everything correctly

## 🔍 Verify It Worked

```bash
# Check status
./pipeline-cli.sh status

# All services should show "(healthy)"
```

## 🌐 Access Your Services

- **Airflow**: http://localhost:8080 (airflow/airflow)
- **Superset**: http://localhost:8088 (admin/admin)

## 📚 Want Details?

Read [PERMISSION_FIX_SUMMARY.md](PERMISSION_FIX_SUMMARY.md) for the complete explanation.

## 🆘 Still Having Issues?

```bash
# Try a complete clean restart
docker-compose down -v
docker system prune -a
./fix-and-restart.sh
```

---

**Just run:** `./fix-and-restart.sh`
