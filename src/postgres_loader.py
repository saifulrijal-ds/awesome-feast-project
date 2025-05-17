import sys
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text
from datetime import datetime

# Import functions from your existing generator file
from data_generator import generate_synthetic_loan_data, generate_time_varying_data, generate_and_save_bfi_loan_data

def load_data_to_postgres(static_loan_data, time_varying_data, conn_string):
    """
    Load generated data into PostgreSQL tables for Feast
    
    Parameters:
    -----------
    static_loan_data : DataFrame
        DataFrame with static loan features
    time_varying_data : DataFrame
        DataFrame with time-varying loan features
    conn_string : str
        SQLAlchemy connection string for PostgreSQL
    """
    try:
        # Create SQLAlchemy engine
        engine = create_engine(conn_string)
        
        # Test connection first
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            print(f"Successfully connected to PostgreSQL! Test query result: {result}")
        
        # Convert timestamp columns to datetime
        static_loan_data['event_timestamp'] = pd.to_datetime(static_loan_data['event_timestamp'])
        static_loan_data['origination_date'] = pd.to_datetime(static_loan_data['origination_date'])
        time_varying_data['event_timestamp'] = pd.to_datetime(time_varying_data['event_timestamp'])
        time_varying_data['observation_date'] = pd.to_datetime(time_varying_data['observation_date'])
        
        # Drop existing tables if they exist
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS bfi_static_loan_data"))
            conn.execute(text("DROP TABLE IF EXISTS bfi_time_varying_data"))
            conn.commit()
        
        # Write DataFrames to PostgreSQL
        static_loan_data.to_sql('bfi_static_loan_data', engine, if_exists='replace', index=False)
        time_varying_data.to_sql('bfi_time_varying_data', engine, if_exists='replace', index=False)
        
        # Create indexes for better performance
        with engine.connect() as conn:
            conn.execute(text("CREATE INDEX idx_static_loan_id ON bfi_static_loan_data(loan_id)"))
            conn.execute(text("CREATE INDEX idx_static_customer_id ON bfi_static_loan_data(customer_id)"))
            conn.execute(text("CREATE INDEX idx_static_timestamp ON bfi_static_loan_data(event_timestamp)"))
            conn.execute(text("CREATE INDEX idx_time_varying_loan_id ON bfi_time_varying_data(loan_id)"))
            conn.execute(text("CREATE INDEX idx_time_varying_timestamp ON bfi_time_varying_data(event_timestamp)"))
            conn.commit()
        
        # Verify data was loaded
        with engine.connect() as conn:
            static_count = conn.execute(text("SELECT COUNT(*) FROM bfi_static_loan_data")).fetchone()[0]
            time_varying_count = conn.execute(text("SELECT COUNT(*) FROM bfi_time_varying_data")).fetchone()[0]
            
        print(f"Loaded {static_count} rows to bfi_static_loan_data table")
        print(f"Loaded {time_varying_count} rows to bfi_time_varying_data table")
        
        return True
    
    except Exception as e:
        print(f"Error loading data to PostgreSQL: {e}")
        return False

def main():
    """
    Main function to generate data and load to PostgreSQL
    """
    # Number of loans to generate
    num_loans = 5000
    
    print(f"Generating {num_loans} synthetic loans...")
    
    # Generate data using your existing function
    static_data, time_data = generate_and_save_bfi_loan_data(
        num_loans=num_loans, 
        target_default_rate=0.55,  # Make sure this parameter name matches your function definition
        output_prefix="feature_repo/data/bfi"
    )
    
    # Only use the local connection since we're running outside Docker
    print("Connecting to PostgreSQL on localhost...")
    conn_string = "postgresql://feast_user:feast_password@localhost:5432/feast"
    
    success = load_data_to_postgres(static_data, time_data, conn_string)
    
    if success:
        print("Data successfully loaded to PostgreSQL!")
        print("\nTo update feature definitions for PostgreSQL, modify features.py:")
        print("""
# Replace FileSource with PostgreSQLSource
from feast import PostgreSQLSource

# For static features
static_loan_source = PostgreSQLSource(
    query="SELECT * FROM bfi_static_loan_data",
    event_timestamp_column="event_timestamp",
)

# For time-varying features
time_varying_source = PostgreSQLSource(
    query="SELECT * FROM bfi_time_varying_data",
    event_timestamp_column="event_timestamp",
)
        """)
    else:
        print("Failed to load data to PostgreSQL.")
        print("\nTroubleshooting Steps:")
        print("1. Verify PostgreSQL credentials")
        print("2. Check if the 'feast' database exists")
        print("3. Ensure the 'feast_user' has proper permissions")
        print("4. Run this command to check DB status: docker exec bfi_feast_project-postgres-1 pg_isready")
        print("5. Verify user creation with: docker exec bfi_feast_project-postgres-1 psql -U feast_user -d feast -c 'SELECT 1'")

if __name__ == "__main__":
    main()
