"""
Populate dim_date dimension table with date records from 2020-2030.
This script generates all date dimension attributes including year, quarter, month, week, day, and is_weekend flag.
"""

import psycopg2
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_db_connection():
    """Create and return a database connection."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'healthcare_warehouse'),
        user=os.getenv('POSTGRES_USER', 'etl_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'etl_password')
    )


def generate_date_dimension(start_year=2020, end_year=2030):
    """
    Generate date dimension records from start_year to end_year.
    
    Args:
        start_year: Starting year (inclusive)
        end_year: Ending year (inclusive)
    
    Returns:
        List of tuples containing date dimension attributes
    """
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    
    date_records = []
    current_date = start_date
    
    while current_date <= end_date:
        # Generate date_key as YYYYMMDD integer
        date_key = int(current_date.strftime('%Y%m%d'))
        
        # Extract date attributes
        year = current_date.year
        quarter = (current_date.month - 1) // 3 + 1
        month = current_date.month
        month_name = current_date.strftime('%B')
        week = current_date.isocalendar()[1]
        day_of_month = current_date.day
        day_of_week = current_date.isoweekday()  # 1=Monday, 7=Sunday
        day_name = current_date.strftime('%A')
        is_weekend = day_of_week in [6, 7]  # Saturday or Sunday
        
        # Note: is_holiday is set to False by default
        # Can be updated later with specific holiday logic
        is_holiday = False
        
        date_records.append((
            date_key,
            current_date.date(),
            year,
            quarter,
            month,
            month_name,
            week,
            day_of_month,
            day_of_week,
            day_name,
            is_weekend,
            is_holiday
        ))
        
        current_date += timedelta(days=1)
    
    return date_records


def populate_dim_date_table(start_year=2020, end_year=2030):
    """
    Populate the dim_date table with date records.
    
    Args:
        start_year: Starting year (inclusive)
        end_year: Ending year (inclusive)
    """
    print(f"Generating date dimension records from {start_year} to {end_year}...")
    date_records = generate_date_dimension(start_year, end_year)
    print(f"Generated {len(date_records)} date records")
    
    print("Connecting to database...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if table already has data
        cursor.execute("SELECT COUNT(*) FROM dim_date")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"dim_date table already contains {existing_count} records")
            response = input("Do you want to clear and repopulate? (yes/no): ")
            if response.lower() == 'yes':
                print("Clearing existing records...")
                cursor.execute("TRUNCATE TABLE dim_date CASCADE")
                conn.commit()
            else:
                print("Skipping population. Exiting.")
                return
        
        # Insert date records in batches
        print("Inserting date records...")
        insert_query = """
            INSERT INTO dim_date (
                date_key, date, year, quarter, month, month_name,
                week, day_of_month, day_of_week, day_name,
                is_weekend, is_holiday
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date_key) DO NOTHING
        """
        
        batch_size = 1000
        for i in range(0, len(date_records), batch_size):
            batch = date_records[i:i + batch_size]
            cursor.executemany(insert_query, batch)
            conn.commit()
            print(f"Inserted {min(i + batch_size, len(date_records))}/{len(date_records)} records")
        
        # Verify insertion
        cursor.execute("SELECT COUNT(*) FROM dim_date")
        final_count = cursor.fetchone()[0]
        print(f"\nSuccessfully populated dim_date table with {final_count} records")
        
        # Show sample records
        cursor.execute("""
            SELECT date_key, date, year, quarter, month, day_name, is_weekend
            FROM dim_date
            ORDER BY date
            LIMIT 5
        """)
        print("\nSample records:")
        print("date_key | date       | year | quarter | month | day_name  | is_weekend")
        print("-" * 75)
        for row in cursor.fetchall():
            print(f"{row[0]} | {row[1]} | {row[2]}  | {row[3]}       | {row[4]}     | {row[5]:<9} | {row[6]}")
        
    except Exception as e:
        print(f"Error populating dim_date table: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
        print("\nDatabase connection closed")


if __name__ == "__main__":
    populate_dim_date_table(start_year=2020, end_year=2030)
