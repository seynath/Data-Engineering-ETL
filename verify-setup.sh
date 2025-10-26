#!/bin/bash
# Verification script for Docker Compose setup
# Run this to verify all components are properly configured

set -e

echo "=========================================="
echo "Healthcare ETL Pipeline Setup Verification"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Track results
ERRORS=0
WARNINGS=0

echo "1. Checking Prerequisites..."
echo "----------------------------"

# Check Docker
if command -v docker &> /dev/null; then
    check_pass "Docker is installed"
    docker --version
else
    check_fail "Docker is not installed"
    ERRORS=$((ERRORS + 1))
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    check_pass "Docker Compose is installed"
    if docker compose version &> /dev/null; then
        docker compose version
    else
        docker-compose --version
    fi
else
    check_fail "Docker Compose is not installed"
    ERRORS=$((ERRORS + 1))
fi

# Check Docker is running
if docker ps &> /dev/null; then
    check_pass "Docker daemon is running"
else
    check_fail "Docker daemon is not running"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "2. Checking Project Files..."
echo "----------------------------"

# Check required files
FILES=(
    "docker-compose.yml"
    ".env.example"
    "setup.sh"
    "README.md"
    "DOCKER_SETUP.md"
    "QUICK_START.md"
    "requirements.txt"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "$file exists"
    else
        check_fail "$file is missing"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check init scripts
INIT_SCRIPTS=(
    "init-scripts/init-warehouse-db.sql"
    "init-scripts/create_dimension_tables.sql"
    "init-scripts/create_fact_tables.sql"
    "init-scripts/init-airflow.sh"
    "init-scripts/setup-warehouse.sh"
)

for script in "${INIT_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        check_pass "$script exists"
    else
        check_fail "$script is missing"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check executable permissions
EXECUTABLES=(
    "setup.sh"
    "init-scripts/init-airflow.sh"
    "init-scripts/setup-warehouse.sh"
)

for exe in "${EXECUTABLES[@]}"; do
    if [ -x "$exe" ]; then
        check_pass "$exe is executable"
    else
        check_warn "$exe is not executable (run: chmod +x $exe)"
        WARNINGS=$((WARNINGS + 1))
    fi
done

echo ""
echo "3. Checking Directory Structure..."
echo "-----------------------------------"

# Check required directories
DIRS=(
    "airflow/dags"
    "airflow/logs"
    "airflow/plugins"
    "data/bronze"
    "data/silver"
    "dataset"
    "config"
    "dbt_project"
    "great_expectations"
    "init-scripts"
    "logs"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        check_pass "$dir/ exists"
    else
        check_warn "$dir/ does not exist (will be created by setup.sh)"
        WARNINGS=$((WARNINGS + 1))
    fi
done

echo ""
echo "4. Validating Docker Compose Configuration..."
echo "----------------------------------------------"

# Validate docker-compose.yml
if docker compose config --quiet 2>&1 | grep -q "error"; then
    check_fail "docker-compose.yml has errors"
    ERRORS=$((ERRORS + 1))
else
    check_pass "docker-compose.yml is valid"
fi

# Check for required services
SERVICES=(
    "postgres"
    "warehouse-db"
    "airflow-init"
    "airflow-webserver"
    "airflow-scheduler"
    "superset"
)

for service in "${SERVICES[@]}"; do
    if docker compose config --services 2>/dev/null | grep -q "^${service}$"; then
        check_pass "Service '$service' is defined"
    else
        check_fail "Service '$service' is missing"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "5. Checking Environment Configuration..."
echo "-----------------------------------------"

if [ -f ".env" ]; then
    check_pass ".env file exists"
    
    # Check for required variables
    REQUIRED_VARS=(
        "POSTGRES_HOST"
        "POSTGRES_DB"
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
    )
    
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${var}=" .env; then
            check_pass "$var is set in .env"
        else
            check_warn "$var is not set in .env (will use default)"
            WARNINGS=$((WARNINGS + 1))
        fi
    done
else
    check_warn ".env file does not exist (will be created from .env.example)"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "6. Checking Python Dependencies..."
echo "-----------------------------------"

if [ -f "requirements.txt" ]; then
    check_pass "requirements.txt exists"
    
    # Check for key dependencies
    KEY_DEPS=(
        "pandas"
        "great-expectations"
        "psycopg2-binary"
        "pyyaml"
    )
    
    for dep in "${KEY_DEPS[@]}"; do
        if grep -q "$dep" requirements.txt; then
            check_pass "$dep is in requirements.txt"
        else
            check_warn "$dep is not in requirements.txt"
            WARNINGS=$((WARNINGS + 1))
        fi
    done
else
    check_fail "requirements.txt is missing"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "7. Checking Documentation..."
echo "-----------------------------"

DOCS=(
    "README.md"
    "DOCKER_SETUP.md"
    "QUICK_START.md"
    "airflow/dags/README.md"
    "dbt_project/README.md"
    "config/README.md"
    "init-scripts/README.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        check_pass "$doc exists"
    else
        check_warn "$doc is missing"
        WARNINGS=$((WARNINGS + 1))
    fi
done

echo ""
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Your setup is ready. Run './setup.sh' to start the pipeline."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Verification completed with $WARNINGS warning(s)${NC}"
    echo ""
    echo "Your setup should work, but some optional components are missing."
    echo "Run './setup.sh' to start the pipeline."
    exit 0
else
    echo -e "${RED}✗ Verification failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Please fix the errors above before running './setup.sh'"
    exit 1
fi
