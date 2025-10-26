"""
Create test datasets for integration testing.

This script generates sample CSV files with 100 rows each for all 9 tables,
including edge cases like missing values, duplicates, and date ranges.
"""

import pandas as pd
import random
from pathlib import Path

# Set random seed for reproducibility
random.seed(42)

def create_test_patients(n=100):
    """Create test patient data with edge cases."""
    df = pd.read_csv('dataset/patients.csv', nrows=n)
    
    # Add edge cases
    # Missing phone numbers
    df.loc[5:10, 'phone'] = ''
    # Missing emails
    df.loc[15:20, 'email'] = ''
    # Missing address fields
    df.loc[25:28, 'address'] = ''
    df.loc[25:28, 'city'] = ''
    df.loc[25:28, 'state'] = ''
    df.loc[25:28, 'zip'] = ''
    
    # Add a duplicate record
    if len(df) > 50:
        df.loc[len(df)] = df.loc[50].copy()
    
    return df

def create_test_encounters(n=100):
    """Create test encounter data with edge cases."""
    df = pd.read_csv('dataset/encounters.csv', nrows=n)
    
    # Add edge cases
    # Missing discharge dates for outpatient visits (valid)
    # Missing length of stay for outpatient visits (valid)
    
    # Add a duplicate record
    if len(df) > 40:
        df.loc[len(df)] = df.loc[40].copy()
    
    # Add an encounter with admission_date > discharge_date (invalid - edge case)
    if len(df) > 10:
        df.loc[10, 'visit_date'] = '15-03-2025'
        df.loc[10, 'discharge_date'] = '10-03-2025'  # Before visit date
    
    return df

def create_test_diagnoses(n=100):
    """Create test diagnosis data."""
    df = pd.read_csv('dataset/diagnoses.csv', nrows=n)
    
    # Add a duplicate
    if len(df) > 30:
        df.loc[len(df)] = df.loc[30].copy()
    
    return df

def create_test_procedures(n=100):
    """Create test procedure data."""
    df = pd.read_csv('dataset/procedures.csv', nrows=n)
    
    # Add a duplicate
    if len(df) > 35:
        df.loc[len(df)] = df.loc[35].copy()
    
    return df

def create_test_medications(n=100):
    """Create test medication data."""
    df = pd.read_csv('dataset/medications.csv', nrows=n)
    
    # Add missing dosage (edge case)
    df.loc[10:12, 'dosage'] = ''
    
    # Add a duplicate
    if len(df) > 45:
        df.loc[len(df)] = df.loc[45].copy()
    
    return df

def create_test_lab_tests(n=100):
    """Create test lab test data."""
    df = pd.read_csv('dataset/lab_tests.csv', nrows=n)
    
    # Add missing test results (edge case)
    df.loc[8:10, 'test_result'] = ''
    
    # Add a duplicate
    if len(df) > 50:
        df.loc[len(df)] = df.loc[50].copy()
    
    return df

def create_test_claims_billing(n=100):
    """Create test claims and billing data with edge cases."""
    df = pd.read_csv('dataset/claims_and_billing.csv', nrows=n)
    
    # Add edge cases
    # Negative amounts (invalid - edge case)
    if len(df) > 5:
        df.loc[5, 'billed_amount'] = -100.50
    
    # Zero amounts (edge case)
    if len(df) > 8:
        df.loc[8, 'paid_amount'] = 0.0
    
    # Missing denial reason when status is denied
    df.loc[15:17, 'denial_reason'] = ''
    
    # Add a duplicate
    if len(df) > 55:
        df.loc[len(df)] = df.loc[55].copy()
    
    return df

def create_test_providers(n=100):
    """Create test provider data."""
    df = pd.read_csv('dataset/providers.csv', nrows=n)
    
    # Add missing NPI (edge case)
    df.loc[12:15, 'npi'] = ''
    
    # Add a duplicate
    if len(df) > 60:
        df.loc[len(df)] = df.loc[60].copy()
    
    return df

def create_test_denials(n=100):
    """Create test denial data."""
    df = pd.read_csv('dataset/denials.csv', nrows=n)
    
    # Add missing appeal dates (valid for non-appealed denials)
    # Add missing resolution dates (valid for pending appeals)
    
    # Add a duplicate
    if len(df) > 40:
        df.loc[len(df)] = df.loc[40].copy()
    
    return df

def main():
    """Generate all test datasets."""
    output_dir = Path('test_data')
    output_dir.mkdir(exist_ok=True)
    
    print("Creating test datasets with 100 rows each...")
    print("=" * 60)
    
    # Create test datasets
    datasets = {
        'patients.csv': create_test_patients(),
        'encounters.csv': create_test_encounters(),
        'diagnoses.csv': create_test_diagnoses(),
        'procedures.csv': create_test_procedures(),
        'medications.csv': create_test_medications(),
        'lab_tests.csv': create_test_lab_tests(),
        'claims_and_billing.csv': create_test_claims_billing(),
        'providers.csv': create_test_providers(),
        'denials.csv': create_test_denials()
    }
    
    # Write datasets to files
    for filename, df in datasets.items():
        output_path = output_dir / filename
        df.to_csv(output_path, index=False)
        print(f"✓ Created {filename}: {len(df)} rows")
    
    print("=" * 60)
    print(f"Test datasets created in: {output_dir}")
    print("\nEdge cases included:")
    print("  - Missing values (phone, email, address fields)")
    print("  - Duplicate records in each table")
    print("  - Invalid date logic (admission > discharge)")
    print("  - Negative amounts in billing")
    print("  - Zero amounts in payments")
    print("  - Missing optional fields")

if __name__ == '__main__':
    main()
