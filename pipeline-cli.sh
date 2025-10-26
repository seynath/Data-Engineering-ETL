#!/bin/bash
# Healthcare ETL Pipeline CLI Helper

COMMAND=$1

case $COMMAND in
  fix-permissions)
    echo "Fixing directory permissions..."
    ./fix-permissions.sh
    ;;
    
  build)
    echo "Building custom Airflow image..."
    docker-compose build
    echo "Build complete!"
    ;;
    
  start)
    echo "Starting Healthcare ETL Pipeline..."
    ./start.sh
    ;;
    
  stop)
    echo "Stopping all services..."
    docker-compose down
    ;;
    
  restart)
    echo "Restarting all services..."
    docker-compose restart
    ;;
    
  clean)
    echo "Stopping and removing all data..."
    read -p "This will delete all data. Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
      docker-compose down -v
      echo "All data removed."
    else
      echo "Cancelled."
    fi
    ;;
    
  status)
    echo "Service Status:"
    docker-compose ps
    echo ""
    echo "Container Health:"
    docker ps --format "table {{.Names}}\t{{.Status}}"
    ;;
    
  logs)
    SERVICE=$2
    if [ -z "$SERVICE" ]; then
      echo "Showing logs for all services (Ctrl+C to exit)..."
      docker-compose logs -f
    else
      echo "Showing logs for $SERVICE (Ctrl+C to exit)..."
      docker-compose logs -f $SERVICE
    fi
    ;;
    
  troubleshoot)
    ./troubleshoot.sh
    ;;
    
  airflow)
    echo "Opening Airflow UI..."
    open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null || echo "Open http://localhost:8080 in your browser"
    ;;
    
  superset)
    echo "Opening Superset UI..."
    open http://localhost:8088 2>/dev/null || xdg-open http://localhost:8088 2>/dev/null || echo "Open http://localhost:8088 in your browser"
    ;;
    
  db-airflow)
    echo "Connecting to Airflow database..."
    docker exec -it healthcare-etl-postgres psql -U airflow -d airflow
    ;;
    
  db-warehouse)
    echo "Connecting to Warehouse database..."
    docker exec -it healthcare-etl-warehouse-db psql -U etl_user -d healthcare_warehouse
    ;;
    
  trigger-dag)
    echo "Triggering healthcare_etl_pipeline DAG..."
    docker exec healthcare-etl-airflow-scheduler airflow dags trigger healthcare_etl_pipeline
    echo "DAG triggered! Check Airflow UI for progress."
    ;;
    
  help|*)
    echo "Healthcare ETL Pipeline CLI"
    echo ""
    echo "Usage: ./pipeline-cli.sh [command]"
    echo ""
    echo "Commands:"
    echo "  fix-permissions - Fix directory permissions"
    echo "  build           - Build custom Airflow image"
    echo "  start           - Start all services"
    echo "  stop            - Stop all services (keep data)"
    echo "  restart         - Restart all services"
    echo "  clean           - Stop and remove all data"
    echo "  status          - Show service status"
    echo "  logs [service]  - Show logs (all or specific service)"
    echo "  troubleshoot    - Run diagnostics"
    echo "  airflow         - Open Airflow UI in browser"
    echo "  superset        - Open Superset UI in browser"
    echo "  db-airflow      - Connect to Airflow database"
    echo "  db-warehouse    - Connect to Warehouse database"
    echo "  trigger-dag     - Manually trigger the ETL pipeline"
    echo "  help            - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./pipeline-cli.sh start"
    echo "  ./pipeline-cli.sh logs airflow-scheduler"
    echo "  ./pipeline-cli.sh status"
    echo "  ./pipeline-cli.sh trigger-dag"
    ;;
esac
