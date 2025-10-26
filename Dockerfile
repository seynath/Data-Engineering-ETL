FROM apache/airflow:2.8.1-python3.11

USER root

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create data directories with proper permissions
RUN mkdir -p /opt/airflow/data/bronze /opt/airflow/data/silver \
    && chown -R airflow:0 /opt/airflow/data \
    && chmod -R 775 /opt/airflow/data

USER airflow

# Copy requirements file
COPY requirements-airflow.txt /requirements-airflow.txt

# Install Python packages as airflow user
RUN pip install --no-cache-dir -r /requirements-airflow.txt

# Set working directory
WORKDIR /opt/airflow
