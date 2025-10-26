# Ubuntu Server Setup Guide

## 🖥️ Running on Ubuntu Server

You're running this on an Ubuntu server. Here's what you need to know.

## ✅ Prerequisites Check

### 1. Check Docker
```bash
docker --version
docker ps
```

If not installed:
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

**Important:** Log out and back in after adding user to docker group.

### 2. Check Ports
```bash
# Check if ports are available
sudo lsof -i :8080  # Airflow
sudo lsof -i :8088  # Superset
sudo lsof -i :5432  # PostgreSQL
sudo lsof -i :5433  # Warehouse DB
```

If ports are in use, either:
- Stop the conflicting service
- Change ports in `docker-compose.yml`

### 3. Check Disk Space
```bash
df -h
```

You need at least 10GB free.

### 4. Check Memory
```bash
free -h
```

You need at least 4GB available.

## 🚀 Quick Start on Ubuntu

### 1. Navigate to Project
```bash
cd /home/adata/Data-Engineering-ETL
```

### 2. Make Scripts Executable
```bash
chmod +x pipeline-cli.sh start.sh troubleshoot.sh
```

### 3. Start the Pipeline
```bash
./pipeline-cli.sh start
```

### 4. Check Status
```bash
./pipeline-cli.sh status
```

## 🌐 Accessing from Your Computer

Since you're on a server, you need to access the UIs from your local computer.

### Option 1: SSH Tunnel (Recommended)

From your local computer:

```bash
# Tunnel for Airflow
ssh -L 8080:localhost:8080 root@your-server-ip

# Tunnel for Superset (in another terminal)
ssh -L 8088:localhost:8088 root@your-server-ip
```

Then open on your local computer:
- Airflow: http://localhost:8080
- Superset: http://localhost:8088

### Option 2: Direct Access (If Firewall Allows)

Open ports in firewall:
```bash
sudo ufw allow 8080/tcp
sudo ufw allow 8088/tcp
```

Then access from your computer:
- Airflow: http://your-server-ip:8080
- Superset: http://your-server-ip:8088

**Security Note:** Only do this if you trust your network. Use SSH tunnels for production.

## 🔧 Server-Specific Commands

### Check Services
```bash
./pipeline-cli.sh status
```

### View Logs
```bash
./pipeline-cli.sh logs
./pipeline-cli.sh logs airflow-scheduler
```

### Monitor Resources
```bash
# CPU and Memory
docker stats

# Disk usage
docker system df
```

### Cleanup Old Data
```bash
# Remove old containers and images
docker system prune -a

# Remove old volumes (WARNING: deletes data)
docker volume prune
```

## 🐛 Troubleshooting on Ubuntu

### Issue: Permission Denied

**Problem:**
```
permission denied while trying to connect to the Docker daemon socket
```

**Solution:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Issue: Port Already in Use

**Check what's using the port:**
```bash
sudo lsof -i :8080
```

**Kill the process:**
```bash
sudo kill -9 <PID>
```

Or change the port in `docker-compose.yml`.

### Issue: Out of Disk Space

**Check usage:**
```bash
df -h
docker system df
```

**Clean up:**
```bash
# Remove old Docker data
docker system prune -a

# Remove old logs
sudo find /var/lib/docker/containers/ -name "*.log" -delete
```

### Issue: Out of Memory

**Check memory:**
```bash
free -h
docker stats
```

**Solution:**
- Reduce number of Airflow workers
- Increase server RAM
- Add swap space

### Issue: Services Won't Start

**Check logs:**
```bash
./pipeline-cli.sh logs
docker-compose logs -f
```

**Try clean restart:**
```bash
./pipeline-cli.sh clean  # Type 'yes'
./pipeline-cli.sh start
```

## 📊 Monitoring on Server

### Real-time Container Stats
```bash
docker stats
```

### Check Container Health
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### View Logs in Real-time
```bash
./pipeline-cli.sh logs
# Press Ctrl+C to exit
```

### Check Disk Usage
```bash
# Overall
df -h

# Docker specific
docker system df

# Detailed
docker system df -v
```

## 🔒 Security Considerations

### 1. Change Default Passwords

Edit `.env` file:
```bash
nano .env
```

Change:
```
_AIRFLOW_WWW_USER_PASSWORD=your_secure_password
POSTGRES_PASSWORD=your_secure_password
SUPERSET_SECRET_KEY=your_secure_secret_key
```

### 2. Firewall Configuration

```bash
# Enable firewall
sudo ufw enable

# Allow SSH (important!)
sudo ufw allow 22/tcp

# Only allow specific IPs to access services
sudo ufw allow from YOUR_IP to any port 8080
sudo ufw allow from YOUR_IP to any port 8088
```

### 3. Use SSH Tunnels

Instead of opening ports, use SSH tunnels (see above).

## 🔄 Running in Background

### Start Services
```bash
./pipeline-cli.sh start
```

Services run in background automatically with Docker Compose.

### Check if Running
```bash
./pipeline-cli.sh status
```

### View Logs
```bash
./pipeline-cli.sh logs
```

### Stop Services
```bash
./pipeline-cli.sh stop
```

## 📅 Scheduled Runs

The pipeline runs automatically at 2 AM UTC daily.

To change the schedule, edit `airflow/dags/healthcare_etl_dag.py`:
```python
schedule_interval='0 2 * * *'  # Cron format
```

## 🔄 Auto-Start on Server Reboot

### Option 1: Docker Restart Policy (Already Configured)

Services automatically restart with Docker:
```yaml
restart: always
```

### Option 2: Systemd Service

Create `/etc/systemd/system/healthcare-etl.service`:
```ini
[Unit]
Description=Healthcare ETL Pipeline
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/adata/Data-Engineering-ETL
ExecStart=/home/adata/Data-Engineering-ETL/pipeline-cli.sh start
ExecStop=/home/adata/Data-Engineering-ETL/pipeline-cli.sh stop
User=root

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable healthcare-etl
sudo systemctl start healthcare-etl
```

## 📈 Performance Tuning

### Increase Docker Resources

Edit `/etc/docker/daemon.json`:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker:
```bash
sudo systemctl restart docker
```

### Optimize PostgreSQL

Edit `docker-compose.yml` and add to warehouse-db:
```yaml
command: postgres -c shared_buffers=256MB -c max_connections=200
```

## 🗂️ Backup Strategy

### Backup Warehouse Database
```bash
docker exec healthcare-etl-warehouse-db pg_dump -U etl_user healthcare_warehouse > backup_$(date +%Y%m%d).sql
```

### Backup Airflow Database
```bash
docker exec healthcare-etl-postgres pg_dump -U airflow airflow > airflow_backup_$(date +%Y%m%d).sql
```

### Backup Data Files
```bash
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
```

### Restore Database
```bash
cat backup_20251026.sql | docker exec -i healthcare-etl-warehouse-db psql -U etl_user healthcare_warehouse
```

## 📞 Remote Management

### SSH into Server
```bash
ssh root@your-server-ip
```

### Run Commands Remotely
```bash
ssh root@your-server-ip "cd /home/adata/Data-Engineering-ETL && ./pipeline-cli.sh status"
```

### Copy Files from Server
```bash
# Copy logs
scp root@your-server-ip:/home/adata/Data-Engineering-ETL/airflow/logs/pipeline.log .

# Copy data
scp -r root@your-server-ip:/home/adata/Data-Engineering-ETL/data/silver/ .
```

## 🎯 Quick Commands for Ubuntu

```bash
# Start
./pipeline-cli.sh start

# Status
./pipeline-cli.sh status

# Logs
./pipeline-cli.sh logs

# Troubleshoot
./pipeline-cli.sh troubleshoot

# Stop
./pipeline-cli.sh stop

# Clean restart
./pipeline-cli.sh clean && ./pipeline-cli.sh start

# Check resources
docker stats

# Check disk
df -h && docker system df
```

## 🆘 Emergency Procedures

### Complete Reset
```bash
# Stop everything
docker-compose down -v

# Remove all Docker data
docker system prune -a -f

# Start fresh
./pipeline-cli.sh start
```

### Service Not Responding
```bash
# Restart specific service
docker-compose restart airflow-scheduler

# Or restart all
docker-compose restart
```

### Out of Disk Space
```bash
# Clean Docker
docker system prune -a -f

# Clean logs
sudo find /var/lib/docker/containers/ -name "*.log" -delete

# Clean old data
rm -rf data/bronze/2025-01-*
rm -rf data/silver/2025-01-*
```

## 📚 Additional Resources

- [START_HERE.md](START_HERE.md) - Quick start guide
- [GETTING_STARTED.md](GETTING_STARTED.md) - Complete guide
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command reference
- [RUN_PIPELINE.md](RUN_PIPELINE.md) - Detailed instructions

---

**Ready to start?**
```bash
./pipeline-cli.sh start
```
