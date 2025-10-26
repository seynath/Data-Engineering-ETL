# 🚀 START HERE - Healthcare ETL Pipeline

## Welcome!

This is your complete Healthcare ETL Pipeline. Everything has been fixed and is ready to run.

## ⚡ Quick Start

### First Time Setup (3-5 minutes)

```bash
./fix-and-restart.sh
```

This builds a custom Airflow image with all dependencies properly installed.

### Subsequent Starts (30 seconds)

```bash
./pipeline-cli.sh start
```

Wait ~30 seconds, then open:

- **Airflow**: http://localhost:8080 (airflow/airflow)
- **Superset**: http://localhost:8088 (admin/admin)

**That's it!** 🎉

## 📚 Documentation Index

Choose your path based on what you need:

### 🆕 First Time User

1. **[GETTING_STARTED.md](GETTING_STARTED.md)** ← Start here
   - Complete walkthrough
   - Three ways to run
   - Verification steps
   - Next steps

### 📖 Reference & Guides

2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** ← Command cheat sheet

   - All commands at a glance
   - Quick access URLs
   - Emergency commands

3. **[RUN_PIPELINE.md](RUN_PIPELINE.md)** ← Detailed instructions

   - Manual step-by-step
   - Environment variables
   - Advanced configuration

4. **[STARTUP_CHECKLIST.md](STARTUP_CHECKLIST.md)** ← Verification guide
   - Pre-flight checks
   - Step-by-step verification
   - Success criteria

### 🔧 Troubleshooting

5. **[FIXED_ISSUES.md](FIXED_ISSUES.md)** ← What was fixed

   - Problem explanation
   - Solution details
   - How to verify

6. **[SOLUTION_SUMMARY.md](SOLUTION_SUMMARY.md)** ← Complete overview
   - Everything that was done
   - How to use the new tools
   - Common operations

### 📊 Project Documentation

7. **[README.md](README.md)** ← Project overview
   - Architecture
   - Components
   - Full documentation

## 🛠️ Tools Available

### Main CLI Tool

```bash
./pipeline-cli.sh [command]
```

**Essential Commands:**

- `start` - Start everything
- `stop` - Stop services
- `status` - Check health
- `logs` - View logs
- `trigger-dag` - Run the pipeline
- `troubleshoot` - Run diagnostics
- `help` - See all commands

### Other Scripts

- `start.sh` - Automated startup (alternative to CLI)
- `troubleshoot.sh` - Diagnostics tool
- `setup.sh` - Initial setup (if needed)

## 🎯 Common Tasks

### Start the Pipeline

```bash
./pipeline-cli.sh start
```

### Check Everything is Running

```bash
./pipeline-cli.sh status
```

### Trigger an ETL Run

```bash
./pipeline-cli.sh trigger-dag
```

### View Logs

```bash
./pipeline-cli.sh logs
```

### Open Airflow UI

```bash
./pipeline-cli.sh airflow
```

### Troubleshoot Issues

```bash
./pipeline-cli.sh troubleshoot
```

### Stop Everything

```bash
./pipeline-cli.sh stop
```

## 🔍 What's Inside

### Services

- **Airflow** - Orchestrates the ETL pipeline
- **PostgreSQL (Airflow)** - Airflow metadata
- **PostgreSQL (Warehouse)** - Data warehouse
- **Superset** - Analytics and dashboards
- **Great Expectations** - Data quality validation
- **dbt** - Data transformations (Gold layer)

### Data Flow

```
Source CSV (dataset/)
    ↓
Bronze Layer (data/bronze/) - Raw ingestion
    ↓
Data Quality Validation
    ↓
Silver Layer (data/silver/) - Cleaned & transformed
    ↓
PostgreSQL Warehouse
    ↓
Gold Layer (dbt) - Dimensional models
    ↓
Superset Dashboards
```

## ✅ Verify It's Working

### 1. Start

```bash
./pipeline-cli.sh start
```

### 2. Check Status (wait 30 seconds)

```bash
./pipeline-cli.sh status
```

All services should show "(healthy)"

### 3. Open Airflow

http://localhost:8080

### 4. Trigger Pipeline

Click "Trigger DAG" on `healthcare_etl_pipeline`

### 5. Watch It Run

Monitor in Graph or Grid view

## 🆘 Need Help?

### Quick Troubleshooting

```bash
# Run diagnostics
./pipeline-cli.sh troubleshoot

# Check logs
./pipeline-cli.sh logs

# Clean restart
./pipeline-cli.sh clean  # Type 'yes'
./pipeline-cli.sh start
```

### Documentation

- Having issues? → `FIXED_ISSUES.md`
- Need commands? → `QUICK_REFERENCE.md`
- Want details? → `RUN_PIPELINE.md`
- Step-by-step? → `STARTUP_CHECKLIST.md`

## 🎓 Learning Path

### Day 1: Get It Running

1. Read this file (you're here!)
2. Run `./pipeline-cli.sh start`
3. Open Airflow UI
4. Trigger the pipeline
5. Watch it complete

### Day 2: Understand the Flow

1. Review `GETTING_STARTED.md`
2. Explore the Airflow DAG structure
3. Check the data in bronze/silver layers
4. Query the warehouse database
5. Review data quality reports

### Day 3: Customize & Extend

1. Read `RUN_PIPELINE.md` for details
2. Modify configuration files
3. Add custom transformations
4. Create Superset dashboards
5. Set up alerts

## 📊 Access Information

### Web UIs

| Service  | URL                   | Username | Password |
| -------- | --------------------- | -------- | -------- |
| Airflow  | http://localhost:8080 | airflow  | airflow  |
| Superset | http://localhost:8088 | admin    | admin    |

### Databases

| Database  | Host      | Port | Database             | User     | Password     |
| --------- | --------- | ---- | -------------------- | -------- | ------------ |
| Airflow   | localhost | 5432 | airflow              | airflow  | airflow      |
| Warehouse | localhost | 5433 | healthcare_warehouse | etl_user | etl_password |

### Connect to Databases

```bash
# Warehouse
./pipeline-cli.sh db-warehouse

# Airflow
./pipeline-cli.sh db-airflow
```

## 🎉 You're All Set!

Everything is configured and ready. Just run:

```bash
./pipeline-cli.sh start
```

Then explore the documentation as needed. Happy data engineering! 🚀

---

## 📋 Quick Links

- [GETTING_STARTED.md](GETTING_STARTED.md) - Complete guide
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command reference
- [RUN_PIPELINE.md](RUN_PIPELINE.md) - Detailed instructions
- [SOLUTION_SUMMARY.md](SOLUTION_SUMMARY.md) - What was fixed
- [README.md](README.md) - Project overview

**Questions?** Run `./pipeline-cli.sh help`
