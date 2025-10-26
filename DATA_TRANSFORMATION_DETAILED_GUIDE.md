# Data Transformation Detailed Guide

## Table of Contents
1. [Transformation Overview](#transformation-overview)
2. [Bronze Layer Processing](#bronze-layer-processing)
3. [Silver Layer Transformations](#silver-layer-transformations)
4. [Gold Layer dbt Models](#gold-layer-dbt-models)
5. [File Dependencies & Relationships](#file-dependencies--relationships)
6. [Data Quality Integration](#data-quality-integration)
7. [Performance Optimization](#performance-optimization)

---

## Transformation Overview

The Healthcare ETL Pipeline implements a **three-layer medallion architecture** where each layer serves a specific purpose in the data transformation journey:

```
Raw CSV → Bronze (Ingestion) → Silver (Cleaning) → Gold (Modeling) → Analytics
```

### Transformation Philosophy
- **Bronze**: Preserve raw data exactly as received (immutable source of truth)
- **Silver**: Clean, standardize, and validate data for consistency
- **Gold**: Model data for analytics using dimensional modeling techniques

---

## Bronze Layer Processing

### File: `airflow/dags/bronze_ingestion.py`

#### Core Functions

**1. File Validation (`validate_csv_files`)**
```python
def validate_csv_files(source_dir):
    """
    Validates source CSV files before ingestion
    
    Checks performed:
    - File existence in dataset/ directory
    - File is not empty (size > 0)
    - File has valid CSV structure (readable headers)
    - Expected tables are present
    
    Returns: List of validated file paths
    Raises: BronzeIngestionError if validation fails
    """
    
    expected_tables = [
        'patients', 'encounters', 'diagnoses', 'procedures',
        'medications', 'lab_tests', 'claims_and_billing', 
        'providers', 'denials'
    ]
    
    validated_files = []
    missing_files = []
    
    for table in expected_tables:
        csv_file = Path(source_dir) / f"{table}.csv"
        
        if not csv_file.exists():
            missing_files.append(table)
            continue
            
        # Check file size
        if csv_file.stat().st_size == 0:
            raise BronzeIngestionError(f"File {table}.csv is empty")
            
        # Validate CSV structure
        try:
            df = pd.read_csv(csv_file, nrows=1)  # Read just header
            if df.empty:
                raise BronzeIngestionError(f"File {table}.csv has no data")
        except Exception as e:
            raise BronzeIngestionError(f"File {table}.csv is not valid CSV: {str(e)}")
            
        validated_files.append(csv_file)
    
    if missing_files:
        raise BronzeIngestionError(f"Missing required files: {missing_files}")
        
    return validated_files
```

**2. Data Ingestion (`ingest_csv_files`)**
```python
def ingest_csv_files(source_dir, bronze_dir, run_date):
    """
    Ingests CSV files to Bronze layer with metadata generation
    
    Process:
    1. Create date-partitioned directory structure
    2. Copy CSV files with preserved timestamps
    3. Generate file checksums for integrity verification
    4. Count rows and calculate file sizes
    5. Create comprehensive metadata file
    
    Input:  dataset/*.csv
    Output: data/bronze/{run_date}/*.csv + _metadata.json
    """
    
    # Create Bronze directory structure
    bronze_run_dir = Path(bronze_dir) / run_date
    bronze_run_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        'ingestion_timestamp': datetime.now().isoformat(),
        'run_date': run_date,
        'source_directory': str(source_dir),
        'bronze_directory': str(bronze_run_dir),
        'files': {}
    }
    
    row_counts = {}
    
    # Process each validated file
    validated_files = validate_csv_files(source_dir)
    
    for source_file in validated_files:
        table_name = source_file.stem
        target_file = bronze_run_dir / source_file.name
        
        # Copy file preserving timestamps
        shutil.copy2(source_file, target_file)
        
        # Calculate file statistics
        file_stats = source_file.stat()
        
        # Count rows (excluding header)
        with open(source_file, 'r') as f:
            row_count = sum(1 for line in f) - 1  # Subtract header
            
        # Calculate MD5 checksum
        checksum = calculate_md5_checksum(source_file)
        
        # Store metadata
        metadata['files'][table_name] = {
            'source_file': str(source_file),
            'bronze_file': str(target_file),
            'file_size_bytes': file_stats.st_size,
            'row_count': row_count,
            'checksum_md5': checksum,
            'last_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
        }
        
        row_counts[table_name] = row_count
        
        print(f"✓ Ingested {table_name}: {row_count:,} rows, {file_stats.st_size:,} bytes")
    
    # Write metadata file
    metadata_file = bronze_run_dir / '_metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Bronze ingestion completed: {len(row_counts)} files, {sum(row_counts.values()):,} total rows")
    
    return row_counts

def calculate_md5_checksum(file_path):
    """Calculate MD5 checksum for file integrity verification"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
```

#### Bronze Layer Output Structure
```
data/bronze/2024-01-15/
├── patients.csv                 # Raw patient data (unchanged)
├── encounters.csv               # Raw encounter data (unchanged)
├── diagnoses.csv               # Raw diagnosis data (unchanged)
├── procedures.csv              # Raw procedure data (unchanged)
├── medications.csv             # Raw medication data (unchanged)
├── lab_tests.csv              # Raw lab test data (unchanged)
├── claims_and_billing.csv     # Raw billing data (unchanged)
├── providers.csv              # Raw provider data (unchanged)
├── denials.csv                # Raw denial data (unchanged)
└── _metadata.json             # Ingestion metadata and statistics
```

**Metadata File Example**:
```json
{
  "ingestion_timestamp": "2024-01-15T08:30:00.123456",
  "run_date": "2024-01-15",
  "source_directory": "/opt/airflow/dataset",
  "bronze_directory": "/opt/airflow/data/bronze/2024-01-15",
  "files": {
    "patients": {
      "source_file": "/opt/airflow/dataset/patients.csv",
      "bronze_file": "/opt/airflow/data/bronze/2024-01-15/patients.csv",
      "file_size_bytes": 2048576,
      "row_count": 15420,
      "checksum_md5": "a1b2c3d4e5f6789012345678901234567890abcd",
      "last_modified": "2024-01-15T06:00:00.000000"
    }
  }
}
```

---

## Silver Layer Transformations

### File: `airflow/dags/silver_transformation.py`

#### Core Transformation Function

```python
def transform_bronze_to_silver(bronze_dir, silver_dir, config_file, run_date, table_name=None):
    """
    Transforms Bronze CSV files to Silver Parquet files with cleaning and standardization
    
    Process:
    1. Load table-specific configuration
    2. Read CSV from Bronze layer
    3. Apply data type conversions
    4. Standardize date formats
    5. Clean and normalize text fields
    6. Handle missing values
    7. Remove duplicates
    8. Add audit columns
    9. Save as compressed Parquet
    
    Input:  data/bronze/{run_date}/*.csv
    Output: data/silver/{run_date}/*.parquet
    """
    
    # Load configuration
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    bronze_run_dir = Path(bronze_dir) / run_date
    silver_run_dir = Path(silver_dir) / run_date
    silver_run_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    tables_to_process = [table_name] if table_name else config['tables'].keys()
    
    for table in tables_to_process:
        try:
            result = transform_single_table(
                table, bronze_run_dir, silver_run_dir, config['tables'][table]
            )
            results[table] = result
            print(f"✓ Transformed {table}: {result['rows_processed']} → {result['rows_output']} rows")
            
        except Exception as e:
            print(f"✗ Failed to transform {table}: {str(e)}")
            raise SilverTransformationError(f"Transformation failed for {table}: {str(e)}")
    
    return results
```

#### Table-Specific Transformation Logic

```python
def transform_single_table(table_name, bronze_dir, silver_dir, table_config):
    """
    Transforms a single table from Bronze to Silver
    
    Args:
        table_name: Name of the table to transform
        bronze_dir: Bronze layer directory path
        silver_dir: Silver layer directory path  
        table_config: Table-specific configuration from YAML
    
    Returns:
        Dictionary with transformation statistics
    """
    
    # Read Bronze CSV file
    bronze_file = bronze_dir / f"{table_name}.csv"
    if not bronze_file.exists():
        raise FileNotFoundError(f"Bronze file not found: {bronze_file}")
    
    df = pd.read_csv(bronze_file)
    original_row_count = len(df)
    
    print(f"Processing {table_name}: {original_row_count:,} rows")
    
    # 1. Data Type Conversions
    df = apply_data_type_conversions(df, table_config)
    
    # 2. Date Standardization
    df = standardize_dates(df, table_config)
    
    # 3. Text Cleaning and Normalization
    df = clean_text_fields(df, table_config)
    
    # 4. Handle Missing Values
    df = handle_missing_values(df, table_config)
    
    # 5. Remove Duplicates
    df = remove_duplicates(df, table_config)
    
    # 6. Add Audit Columns
    df = add_audit_columns(df, bronze_file.name)
    
    # 7. Validate Data Quality
    df = validate_data_quality(df, table_config)
    
    final_row_count = len(df)
    
    # 8. Save as Parquet
    silver_file = silver_dir / f"{table_name}.parquet"
    df.to_parquet(
        silver_file,
        compression='snappy',
        engine='pyarrow',
        index=False
    )
    
    return {
        'table_name': table_name,
        'bronze_file': str(bronze_file),
        'silver_file': str(silver_file),
        'rows_processed': original_row_count,
        'rows_output': final_row_count,
        'rows_removed': original_row_count - final_row_count,
        'file_size_mb': round(silver_file.stat().st_size / (1024 * 1024), 2),
        'transformation_timestamp': datetime.now().isoformat()
    }
```

#### Detailed Transformation Functions

**1. Data Type Conversions**
```python
def apply_data_type_conversions(df, table_config):
    """
    Convert columns to appropriate data types based on configuration
    """
    
    # Numeric columns
    if 'numeric_columns' in table_config:
        for col in table_config['numeric_columns']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                print(f"  ✓ Converted {col} to numeric")
    
    # Boolean columns
    if 'boolean_columns' in table_config:
        for col in table_config['boolean_columns']:
            if col in df.columns:
                df[col] = df[col].map({
                    'Y': True, 'N': False, 'Yes': True, 'No': False,
                    '1': True, '0': False, 1: True, 0: False,
                    'TRUE': True, 'FALSE': False, 'True': True, 'False': False
                })
                print(f"  ✓ Converted {col} to boolean")
    
    # Categorical columns (convert to category dtype for memory efficiency)
    if 'categorical_columns' in table_config:
        for col in table_config['categorical_columns']:
            if col in df.columns:
                df[col] = df[col].astype('category')
                print(f"  ✓ Converted {col} to category")
    
    return df
```

**2. Date Standardization**
```python
def standardize_dates(df, table_config):
    """
    Standardize date formats from DD-MM-YYYY to YYYY-MM-DD
    """
    
    if 'date_columns' not in table_config:
        return df
    
    source_format = "%d-%m-%Y"  # Input format from CSV
    target_format = "%Y-%m-%d"  # Standard ISO format
    
    for col in table_config['date_columns']:
        if col in df.columns:
            # Handle multiple date formats
            df[col] = pd.to_datetime(df[col], format=source_format, errors='coerce')
            
            # Convert to string in target format
            df[col] = df[col].dt.strftime(target_format)
            
            print(f"  ✓ Standardized {col} dates: {source_format} → {target_format}")
    
    return df
```

**3. Text Field Cleaning**
```python
def clean_text_fields(df, table_config):
    """
    Clean and normalize text fields
    """
    
    # Get text columns (string dtype columns)
    text_columns = df.select_dtypes(include=['object']).columns
    
    for col in text_columns:
        if col in df.columns:
            # Remove leading/trailing whitespace
            df[col] = df[col].astype(str).str.strip()
            
            # Handle name fields (title case)
            if any(name_field in col.lower() for name_field in ['name', 'first', 'last']):
                df[col] = df[col].str.title()
                print(f"  ✓ Applied title case to {col}")
            
            # Handle address fields (title case)
            elif 'address' in col.lower():
                df[col] = df[col].str.title()
                print(f"  ✓ Applied title case to {col}")
            
            # Handle phone numbers
            elif 'phone' in col.lower():
                df[col] = df[col].apply(format_phone_number)
                print(f"  ✓ Formatted phone numbers in {col}")
            
            # Handle email addresses (lowercase)
            elif 'email' in col.lower():
                df[col] = df[col].str.lower()
                print(f"  ✓ Normalized email addresses in {col}")
            
            # Replace empty strings with None
            df[col] = df[col].replace('', None)
    
    return df

def format_phone_number(phone):
    """Format phone number to (XXX) XXX-XXXX format"""
    if pd.isna(phone) or phone == '':
        return None
    
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, str(phone)))
    
    # Format if we have 10 digits
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    else:
        return phone  # Return original if not 10 digits
```

**4. Missing Value Handling**
```python
def handle_missing_values(df, table_config):
    """
    Handle missing values based on column type and business rules
    """
    
    missing_value_rules = table_config.get('missing_value_handling', {})
    
    for col in df.columns:
        missing_count = df[col].isnull().sum()
        if missing_count > 0:
            
            # Check for specific column rules
            if col in missing_value_rules:
                rule = missing_value_rules[col]
                
                if rule['action'] == 'fill':
                    df[col] = df[col].fillna(rule['value'])
                    print(f"  ✓ Filled {missing_count} missing values in {col} with '{rule['value']}'")
                
                elif rule['action'] == 'drop':
                    df = df.dropna(subset=[col])
                    print(f"  ✓ Dropped {missing_count} rows with missing {col}")
            
            # Default rules by data type
            else:
                if df[col].dtype in ['int64', 'float64']:
                    # Fill numeric columns with 0 or median
                    fill_value = df[col].median() if col.endswith('_amount') else 0
                    df[col] = df[col].fillna(fill_value)
                    print(f"  ✓ Filled {missing_count} missing numeric values in {col}")
                
                elif df[col].dtype == 'object':
                    # Fill text columns with 'Unknown'
                    df[col] = df[col].fillna('Unknown')
                    print(f"  ✓ Filled {missing_count} missing text values in {col}")
    
    return df
```

**5. Duplicate Removal**
```python
def remove_duplicates(df, table_config):
    """
    Remove duplicate records based on primary key or all columns
    """
    
    original_count = len(df)
    
    if 'primary_key' in table_config:
        # Remove duplicates based on primary key, keep first occurrence
        primary_key = table_config['primary_key']
        if isinstance(primary_key, str):
            primary_key = [primary_key]
        
        df = df.drop_duplicates(subset=primary_key, keep='first')
        duplicate_count = original_count - len(df)
        
        if duplicate_count > 0:
            print(f"  ✓ Removed {duplicate_count} duplicates based on {primary_key}")
    
    else:
        # Remove exact duplicates across all columns
        df = df.drop_duplicates(keep='first')
        duplicate_count = original_count - len(df)
        
        if duplicate_count > 0:
            print(f"  ✓ Removed {duplicate_count} exact duplicates")
    
    return df
```

**6. Audit Column Addition**
```python
def add_audit_columns(df, source_file_name):
    """
    Add audit columns for data lineage and tracking
    """
    
    current_timestamp = datetime.now()
    
    # Load timestamp
    df['load_timestamp'] = current_timestamp
    
    # Source file tracking
    df['source_file'] = source_file_name
    
    # Record hash for change detection
    df['record_hash'] = df.apply(
        lambda row: hashlib.md5(
            ''.join(str(row.values)).encode('utf-8')
        ).hexdigest(), 
        axis=1
    )
    
    print(f"  ✓ Added audit columns: load_timestamp, source_file, record_hash")
    
    return df
```

#### Table-Specific Transformation Examples

**Patients Table Transformation**
```python
# Input CSV (Bronze):
patient_id,first_name,last_name,dob,gender,phone,email
PAT00001,john,doe,15-03-1990,M,1234567890,JOHN.DOE@EMAIL.COM
PAT00002,jane,smith,22-07-1985,F,(555) 123-4567,jane.smith@email.com

# Configuration:
tables:
  patients:
    primary_key: patient_id
    date_columns: [dob]
    numeric_columns: []
    categorical_columns: [gender]
    missing_value_handling:
      phone:
        action: fill
        value: "Unknown"

# Output Parquet (Silver):
patient_id,first_name,last_name,dob,gender,phone,email,load_timestamp,source_file,record_hash
PAT00001,John,Doe,1990-03-15,M,(123) 456-7890,john.doe@email.com,2024-01-15 08:30:00,patients.csv,a1b2c3d4...
PAT00002,Jane,Smith,1985-07-22,F,(555) 123-4567,jane.smith@email.com,2024-01-15 08:30:00,patients.csv,e5f6g7h8...
```

**Encounters Table Transformation**
```python
# Input CSV (Bronze):
encounter_id,patient_id,admission_date,discharge_date,total_charges,length_of_stay
ENC00001,PAT00001,15-01-2024,17-01-2024,1500.50,2
ENC00002,PAT00002,16-01-2024,,2300.75,

# Configuration:
tables:
  encounters:
    primary_key: encounter_id
    date_columns: [admission_date, discharge_date]
    numeric_columns: [total_charges, length_of_stay]

# Transformations Applied:
1. Date standardization: 15-01-2024 → 2024-01-15
2. Numeric conversion: "1500.50" → 1500.50 (float)
3. Missing value handling: empty discharge_date → None
4. Length of stay calculation validation

# Output Parquet (Silver):
encounter_id,patient_id,admission_date,discharge_date,total_charges,length_of_stay,load_timestamp,source_file,record_hash
ENC00001,PAT00001,2024-01-15,2024-01-17,1500.50,2,2024-01-15 08:30:00,encounters.csv,x1y2z3a4...
ENC00002,PAT00002,2024-01-16,None,2300.75,None,2024-01-15 08:30:00,encounters.csv,b5c6d7e8...
```

---

## Gold Layer dbt Models

### File Structure and Dependencies

```
dbt_project/models/
├── staging/           # Silver → Staging (Views)
│   ├── sources.yml   # Source table definitions
│   ├── schema.yml    # Model documentation and tests
│   ├── stg_patients.sql
│   ├── stg_encounters.sql
│   ├── stg_diagnoses.sql
│   ├── stg_procedures.sql
│   ├── stg_medications.sql
│   ├── stg_lab_tests.sql
│   ├── stg_claims_billing.sql
│   ├── stg_providers.sql
│   └── stg_denials.sql
├── dimensions/        # Staging → Dimensions (Tables)
│   ├── schema.yml    # Dimension documentation and tests
│   ├── dim_patient.sql
│   ├── dim_provider.sql
│   ├── dim_diagnosis.sql
│   ├── dim_procedure.sql
│   └── dim_medication.sql
└── facts/            # Staging + Dimensions → Facts (Incremental)
    ├── schema.yml    # Fact table documentation and tests
    ├── fact_encounter.sql
    ├── fact_billing.sql
    ├── fact_lab_test.sql
    └── fact_denial.sql
```

#### Source Definitions (`staging/sources.yml`)

```yaml
version: 2

sources:
  - name: silver
    description: "Silver layer tables loaded from Parquet files"
    database: healthcare_warehouse
    schema: silver
    tables:
      - name: patients
        description: "Patient demographic and contact information"
        columns:
          - name: patient_id
            description: "Unique patient identifier"
            tests:
              - not_null
              - unique
          - name: first_name
            description: "Patient first name"
            tests:
              - not_null
          - name: last_name
            description: "Patient last name"
            tests:
              - not_null
          - name: dob
            description: "Date of birth in YYYY-MM-DD format"
            tests:
              - not_null
          - name: gender
            description: "Patient gender"
            tests:
              - accepted_values:
                  values: ['Male', 'Female', 'Other']
      
      - name: encounters
        description: "Hospital encounters and visits"
        columns:
          - name: encounter_id
            description: "Unique encounter identifier"
            tests:
              - not_null
              - unique
          - name: patient_id
            description: "Reference to patient"
            tests:
              - not_null
              - relationships:
                  to: source('silver', 'patients')
                  field: patient_id
```

#### Staging Models

**`staging/stg_patients.sql`**
```sql
{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('silver', 'patients') }}
),

cleaned AS (
    SELECT 
        -- Business keys
        patient_id,
        
        -- Demographics with additional cleaning
        TRIM(UPPER(first_name)) as first_name,
        TRIM(UPPER(last_name)) as last_name,
        full_name = CONCAT(TRIM(UPPER(first_name)), ' ', TRIM(UPPER(last_name))),
        
        -- Date handling
        CAST(dob AS DATE) as date_of_birth,
        EXTRACT(YEAR FROM AGE(CAST(dob AS DATE))) as current_age,
        
        -- Standardized categorical values
        CASE 
            WHEN UPPER(gender) IN ('M', 'MALE') THEN 'Male'
            WHEN UPPER(gender) IN ('F', 'FEMALE') THEN 'Female'
            WHEN UPPER(gender) IN ('O', 'OTHER') THEN 'Other'
            ELSE 'Unknown'
        END as gender_standardized,
        
        CASE 
            WHEN UPPER(ethnicity) = 'HISPANIC' THEN 'Hispanic/Latino'
            WHEN UPPER(ethnicity) = 'WHITE' THEN 'White'
            WHEN UPPER(ethnicity) = 'BLACK' THEN 'Black/African American'
            WHEN UPPER(ethnicity) = 'ASIAN' THEN 'Asian'
            WHEN UPPER(ethnicity) = 'NATIVE' THEN 'Native American'
            ELSE 'Other/Unknown'
        END as ethnicity_standardized,
        
        -- Insurance information
        UPPER(TRIM(insurance_type)) as insurance_type,
        
        -- Contact information (with privacy considerations)
        CASE 
            WHEN phone IS NOT NULL AND LENGTH(phone) >= 10 THEN phone
            ELSE NULL
        END as phone_clean,
        
        CASE 
            WHEN email IS NOT NULL AND email LIKE '%@%' THEN LOWER(TRIM(email))
            ELSE NULL
        END as email_clean,
        
        -- Address information
        TRIM(address) as address,
        TRIM(UPPER(city)) as city,
        TRIM(UPPER(state)) as state,
        TRIM(zipcode) as zipcode,
        
        -- Audit fields
        load_timestamp,
        source_file,
        record_hash,
        current_timestamp as dbt_updated_at

    FROM source
    WHERE patient_id IS NOT NULL
)

SELECT * FROM cleaned
```

**`staging/stg_encounters.sql`**
```sql
{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('silver', 'encounters') }}
),

cleaned AS (
    SELECT 
        -- Business keys
        encounter_id,
        patient_id,
        provider_id,
        
        -- Dates
        CAST(admission_date AS DATE) as admission_date,
        CAST(discharge_date AS DATE) as discharge_date,
        
        -- Calculated fields
        CASE 
            WHEN discharge_date IS NOT NULL AND admission_date IS NOT NULL
            THEN DATE_PART('day', CAST(discharge_date AS DATE) - CAST(admission_date AS DATE))
            ELSE length_of_stay
        END as length_of_stay_calculated,
        
        -- Encounter details
        UPPER(TRIM(encounter_type)) as encounter_type,
        UPPER(TRIM(department)) as department,
        UPPER(TRIM(discharge_status)) as discharge_status,
        
        -- Financial information
        COALESCE(total_charges, 0) as total_charges,
        
        -- Data quality flags
        CASE 
            WHEN discharge_date < admission_date THEN TRUE
            ELSE FALSE
        END as date_logic_error,
        
        CASE 
            WHEN length_of_stay < 0 OR length_of_stay > 365 THEN TRUE
            ELSE FALSE
        END as length_of_stay_error,
        
        -- Audit fields
        load_timestamp,
        source_file,
        record_hash,
        current_timestamp as dbt_updated_at

    FROM source
    WHERE encounter_id IS NOT NULL
      AND patient_id IS NOT NULL
)

SELECT * FROM cleaned
```

#### Dimension Models

**`dimensions/dim_patient.sql`**
```sql
{{ config(
    materialized='table',
    unique_key='patient_key'
) }}

WITH staging AS (
    SELECT * FROM {{ ref('stg_patients') }}
),

-- Generate surrogate keys
with_surrogate_keys AS (
    SELECT 
        {{ dbt_utils.generate_surrogate_key(['patient_id', 'dbt_updated_at']) }} as patient_key,
        *
    FROM staging
),

-- Implement SCD Type 2 (Slowly Changing Dimensions)
with_scd AS (
    SELECT 
        patient_key,
        patient_id,
        first_name,
        last_name,
        full_name,
        date_of_birth,
        current_age,
        gender_standardized as gender,
        ethnicity_standardized as ethnicity,
        insurance_type,
        phone_clean as phone,
        email_clean as email,
        address,
        city,
        state,
        zipcode,
        
        -- SCD Type 2 implementation
        dbt_updated_at as effective_date,
        COALESCE(
            LEAD(dbt_updated_at) OVER (
                PARTITION BY patient_id 
                ORDER BY dbt_updated_at
            ),
            '9999-12-31'::date
        ) as expiry_date,
        
        CASE 
            WHEN LEAD(dbt_updated_at) OVER (
                PARTITION BY patient_id 
                ORDER BY dbt_updated_at
            ) IS NULL THEN TRUE
            ELSE FALSE
        END as is_current,
        
        -- Derived attributes
        CASE 
            WHEN current_age BETWEEN 0 AND 17 THEN 'Pediatric'
            WHEN current_age BETWEEN 18 AND 64 THEN 'Adult'
            WHEN current_age >= 65 THEN 'Senior'
            ELSE 'Unknown'
        END as age_group,
        
        CASE 
            WHEN insurance_type IN ('MEDICARE', 'MEDICAID') THEN 'Government'
            WHEN insurance_type IN ('BLUE_CROSS', 'AETNA', 'CIGNA') THEN 'Commercial'
            WHEN insurance_type = 'SELF_PAY' THEN 'Self Pay'
            ELSE 'Other'
        END as insurance_category,
        
        -- Audit fields
        load_timestamp as source_load_timestamp,
        current_timestamp as created_at,
        current_timestamp as updated_at
        
    FROM with_surrogate_keys
)

SELECT * FROM with_scd
```

**`dimensions/dim_provider.sql`**
```sql
{{ config(
    materialized='table',
    unique_key='provider_key'
) }}

WITH staging AS (
    SELECT * FROM {{ ref('stg_providers') }}
),

with_surrogate_keys AS (
    SELECT 
        {{ dbt_utils.generate_surrogate_key(['provider_id', 'dbt_updated_at']) }} as provider_key,
        *
    FROM staging
),

final AS (
    SELECT 
        provider_key,
        provider_id,
        first_name,
        last_name,
        CONCAT(first_name, ' ', last_name) as full_name,
        specialty,
        department,
        license_number,
        hire_date,
        
        -- Derived attributes
        CASE 
            WHEN specialty IN ('CARDIOLOGY', 'NEUROLOGY', 'ONCOLOGY') THEN 'Specialist'
            WHEN specialty IN ('FAMILY_MEDICINE', 'INTERNAL_MEDICINE') THEN 'Primary Care'
            WHEN specialty IN ('EMERGENCY_MEDICINE', 'CRITICAL_CARE') THEN 'Emergency'
            ELSE 'Other'
        END as provider_category,
        
        EXTRACT(YEAR FROM AGE(hire_date)) as years_of_service,
        
        -- SCD Type 2 fields
        dbt_updated_at as effective_date,
        COALESCE(
            LEAD(dbt_updated_at) OVER (
                PARTITION BY provider_id 
                ORDER BY dbt_updated_at
            ),
            '9999-12-31'::date
        ) as expiry_date,
        
        CASE 
            WHEN LEAD(dbt_updated_at) OVER (
                PARTITION BY provider_id 
                ORDER BY dbt_updated_at
            ) IS NULL THEN TRUE
            ELSE FALSE
        END as is_current,
        
        -- Audit fields
        load_timestamp as source_load_timestamp,
        current_timestamp as created_at,
        current_timestamp as updated_at
        
    FROM with_surrogate_keys
)

SELECT * FROM final
```

#### Fact Models

**`facts/fact_encounter.sql`**
```sql
{{ config(
    materialized='incremental',
    unique_key='encounter_key',
    on_schema_change='fail'
) }}

WITH encounters AS (
    SELECT * FROM {{ ref('stg_encounters') }}
),

-- Join with dimensions to get surrogate keys
with_dimension_keys AS (
    SELECT 
        e.*,
        p.patient_key,
        pr.provider_key,
        
        -- Date dimension keys (assuming dim_date exists)
        da.date_key as admission_date_key,
        dd.date_key as discharge_date_key
        
    FROM encounters e
    
    -- Join with patient dimension (current record only)
    LEFT JOIN {{ ref('dim_patient') }} p 
        ON e.patient_id = p.patient_id 
        AND p.is_current = TRUE
    
    -- Join with provider dimension (current record only)
    LEFT JOIN {{ ref('dim_provider') }} pr 
        ON e.provider_id = pr.provider_id 
        AND pr.is_current = TRUE
    
    -- Join with date dimension for admission date
    LEFT JOIN {{ ref('dim_date') }} da 
        ON e.admission_date = da.full_date
    
    -- Join with date dimension for discharge date
    LEFT JOIN {{ ref('dim_date') }} dd 
        ON e.discharge_date = dd.full_date
),

-- Calculate additional measures and business logic
final AS (
    SELECT 
        {{ dbt_utils.generate_surrogate_key(['encounter_id']) }} as encounter_key,
        encounter_id,
        
        -- Foreign keys to dimensions
        patient_key,
        provider_key,
        admission_date_key,
        discharge_date_key,
        
        -- Encounter attributes
        encounter_type,
        department,
        discharge_status,
        
        -- Date fields
        admission_date,
        discharge_date,
        
        -- Measures
        length_of_stay_calculated as length_of_stay_days,
        total_charges,
        
        -- Calculated measures
        CASE 
            WHEN length_of_stay_calculated = 0 THEN total_charges
            WHEN length_of_stay_calculated > 0 THEN total_charges / length_of_stay_calculated
            ELSE NULL
        END as charges_per_day,
        
        -- Business flags
        CASE 
            WHEN encounter_type = 'EMERGENCY' THEN TRUE
            ELSE FALSE
        END as is_emergency,
        
        CASE 
            WHEN length_of_stay_calculated >= 7 THEN TRUE
            ELSE FALSE
        END as is_long_stay,
        
        CASE 
            WHEN discharge_status IN ('DISCHARGED_TO_HOME', 'DISCHARGED_HOME') THEN TRUE
            ELSE FALSE
        END as discharged_home,
        
        -- Data quality flags
        date_logic_error,
        length_of_stay_error,
        
        -- Audit fields
        load_timestamp as source_load_timestamp,
        dbt_updated_at as source_updated_at,
        current_timestamp as created_at
        
    FROM with_dimension_keys
    WHERE patient_key IS NOT NULL  -- Ensure referential integrity
)

SELECT * FROM final

-- Incremental loading logic
{% if is_incremental() %}
    WHERE source_updated_at > (SELECT MAX(source_updated_at) FROM {{ this }})
{% endif %}
```

**`facts/fact_billing.sql`**
```sql
{{ config(
    materialized='incremental',
    unique_key='billing_key',
    on_schema_change='fail'
) }}

WITH billing AS (
    SELECT * FROM {{ ref('stg_claims_billing') }}
),

with_dimension_keys AS (
    SELECT 
        b.*,
        p.patient_key,
        pr.provider_key,
        e.encounter_key,
        ds.date_key as service_date_key
        
    FROM billing b
    
    LEFT JOIN {{ ref('dim_patient') }} p 
        ON b.patient_id = p.patient_id 
        AND p.is_current = TRUE
    
    LEFT JOIN {{ ref('dim_provider') }} pr 
        ON b.provider_id = pr.provider_id 
        AND pr.is_current = TRUE
    
    LEFT JOIN {{ ref('fact_encounter') }} e 
        ON b.encounter_id = e.encounter_id
    
    LEFT JOIN {{ ref('dim_date') }} ds 
        ON b.service_date = ds.full_date
),

final AS (
    SELECT 
        {{ dbt_utils.generate_surrogate_key(['claim_id']) }} as billing_key,
        claim_id,
        
        -- Foreign keys
        patient_key,
        provider_key,
        encounter_key,
        service_date_key,
        
        -- Billing details
        service_date,
        charge_amount,
        payment_amount,
        insurance_paid,
        patient_paid,
        adjustment_amount,
        outstanding_amount,
        billing_status,
        
        -- Calculated measures
        COALESCE(charge_amount, 0) - COALESCE(payment_amount, 0) as net_amount,
        
        CASE 
            WHEN charge_amount > 0 
            THEN (payment_amount / charge_amount) * 100
            ELSE 0
        END as collection_rate_percent,
        
        CASE 
            WHEN outstanding_amount > 0 THEN TRUE
            ELSE FALSE
        END as has_outstanding_balance,
        
        CASE 
            WHEN billing_status = 'PAID' THEN TRUE
            ELSE FALSE
        END as is_fully_paid,
        
        -- Audit fields
        load_timestamp as source_load_timestamp,
        dbt_updated_at as source_updated_at,
        current_timestamp as created_at
        
    FROM with_dimension_keys
    WHERE patient_key IS NOT NULL
)

SELECT * FROM final

{% if is_incremental() %}
    WHERE source_updated_at > (SELECT MAX(source_updated_at) FROM {{ this }})
{% endif %}
```

---

## File Dependencies & Relationships

### Execution Order and Dependencies

```
1. Bronze Layer (Airflow Tasks)
   ├── validate_source_files
   ├── ingest_bronze_layer
   └── validate_bronze_layer

2. Silver Layer (Airflow Tasks - Parallel)
   ├── transform_patients
   ├── transform_encounters
   ├── transform_diagnoses
   ├── transform_procedures
   ├── transform_medications
   ├── transform_lab_tests
   ├── transform_claims_billing
   ├── transform_providers
   └── transform_denials

3. Silver Validation (Airflow Task)
   └── validate_silver_layer (Great Expectations)

4. Warehouse Loading (Airflow Task)
   └── load_to_warehouse

5. dbt Gold Layer (Airflow Tasks - Sequential)
   ├── dbt_deps
   ├── dbt_run_staging
   ├── dbt_test_staging
   ├── dbt_run_dimensions
   ├── dbt_run_facts
   └── dbt_test_gold

6. Final Validation & Reporting (Airflow Tasks)
   ├── validate_gold_layer
   ├── generate_data_quality_report
   └── refresh_superset_cache
```

### File Relationship Map

```
Configuration Files:
├── config/pipeline_config.yaml → Controls all transformation settings
├── config/silver_table_config.yaml → Table-specific transformation rules
└── dbt_project/profiles.yml → Database connection settings

Python Modules:
├── bronze_ingestion.py → Reads from dataset/, writes to data/bronze/
├── silver_transformation.py → Reads from data/bronze/, writes to data/silver/
├── data_quality.py → Validates data at each layer
└── healthcare_etl_dag.py → Orchestrates entire pipeline

dbt Models:
├── staging/*.sql → Read from silver schema, create staging views
├── dimensions/*.sql → Read from staging views, create dimension tables
└── facts/*.sql → Read from staging views + dimensions, create fact tables

Data Flow:
dataset/*.csv → data/bronze/{date}/*.csv → data/silver/{date}/*.parquet → PostgreSQL silver schema → PostgreSQL public schema (Gold)
```

### Inter-File Communication

**Configuration Propagation**:
```python
# pipeline_config.yaml settings flow to:
1. healthcare_etl_dag.py (DAG configuration)
2. bronze_ingestion.py (file paths, validation rules)
3. silver_transformation.py (transformation settings)
4. data_quality.py (validation thresholds)

# silver_table_config.yaml settings flow to:
1. silver_transformation.py (table-specific rules)
2. Great Expectations (validation expectations)
```

**Data Lineage Tracking**:
```python
# Each layer maintains lineage information:
Bronze: source_file → bronze_file mapping in _metadata.json
Silver: bronze_file → silver_file + transformation_timestamp
Gold: silver tables → gold tables via dbt lineage
```

**Error Propagation**:
```python
# Errors bubble up through the pipeline:
1. Bronze validation failure → stops entire pipeline
2. Silver transformation error → stops pipeline for that table
3. Silver validation warning → continues with alert
4. Gold dbt error → stops pipeline with detailed logs
5. Final validation error → stops pipeline
```

This detailed guide provides a comprehensive understanding of how data flows through each transformation layer, what each file does, and how they all work together to create a robust, scalable healthcare data pipeline.