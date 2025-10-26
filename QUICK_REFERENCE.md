# Quick Reference Card

## 🚀 Start the Pipeline
```bash
./pipeline-cli.sh start
```

## 🛑 Stop the Pipeline
```bash
./pipeline-cli.sh stop
```

## 📊 Check Status
```bash
./pipeline-cli.sh status
```

## 🔄 Trigger ETL Run
```bash
./pipeline-cli.sh trigger-dag
```

## 📝 View Logs
```bash
./pipeline-cli.sh logs
./pipeline-cli.sh logs airflow-scheduler
```

## 🔧 Troubleshoot
```bash
./pipeline-cli.sh troubleshoot
```

## 🌐 Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow | http://localhost:8080 | airflow / airflow |
| Superset | http://localhost:8088 | admin / admin |

## 💾 Database Access

```bash
# Warehouse DB
./pipeline-cli.sh db-warehouse

# Airflow DB
./pipeline-cli.sh db-airflow
```

## 🧹 Clean Restart
```bash
./pipeline-cli.sh clean  # Removes all data
./pipeline-cli.sh start
```

## 📁 Key Directories

- `dataset/` - Source CSV files
- `data/bronze/` - Raw data
- `data/silver/` - Transformed data
- `airflow/logs/` - Pipeline logs
- `config/` - Configuration files

## 🆘 Emergency Commands

```bash
# Force stop everything
docker-compose down -v

# Check what's running
docker ps

# View specific container logs
docker logs healthcare-etl-airflow-scheduler

# Restart specific service
docker-compose restart airflow-scheduler
```

## ✅ Health Check
All services should show "(healthy)":
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## 📚 Full Documentation

- `GETTING_STARTED.md` - Start here
- `RUN_PIPELINE.md` - Detailed instructions
- `FIXED_ISSUES.md` - What was fixed
- `README.md` - Project overview

## 💡 Pro Tips

- Pipeline runs daily at 2 AM UTC automatically
- Trigger manually anytime from Airflow UI
- Data persists in Docker volumes
- Use `./pipeline-cli.sh help` for all commands
